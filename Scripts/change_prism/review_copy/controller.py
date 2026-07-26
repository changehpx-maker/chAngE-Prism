import os

from change_prism.config import (
    SETTINGS_LOCATION,
    get_review_copy_destination_root,
)
MENU_LABEL = "Copy to Daily Review Folder"


class ReviewCopyController:
    def __init__(self, core):
        self.core = core
        self._copy_job = None

    def add_file_context_menu(self, origin, menu, filepath):
        paths = self._existing_paths([filepath])
        self._add_copy_action(menu, paths)

    def add_media_context_menu(self, origin, menu):
        paths = self._get_media_selection(origin)
        self._add_copy_action(menu, paths)

    def _add_copy_action(self, menu, paths):
        if not paths:
            return
        menu.addSeparator()
        action = menu.addAction(MENU_LABEL)
        action.triggered.connect(
            lambda checked=False, selected=paths: self.copy_paths(selected)
        )

    def copy_paths(self, paths):
        if self._copy_job is not None:
            self.core.popup(
                "A daily review copy is already running.",
                severity="warning",
            )
            return

        destination_root = get_review_copy_destination_root(self.core)
        if not destination_root:
            self.core.popup(
                "Review copy destination is not configured.\n"
                "Set Daily Review Destination in:\n%s" % SETTINGS_LOCATION,
                severity="warning",
            )
            return

        self._start_copy_job(paths, destination_root)

    def _start_copy_job(self, paths, destination_root):
        from change_prism.review_copy.dialog import create_copy_job

        parent = getattr(self.core, "messageParent", None)
        self._copy_job = create_copy_job(
            paths,
            destination_root,
            parent,
            self._copy_finished,
            self._copy_failed,
        )

    def _copy_finished(self, result):
        self._close_copy_job()
        try:
            message = "Copied %d item(s) to:\n%s" % (
                len(result["copied"]),
                result["destination"],
            )
            if result["failures"]:
                message += "\n\nFailed %d item(s):" % len(result["failures"])
                for failure in result["failures"]:
                    message += "\n%s\n  %s" % (
                        failure["source"],
                        failure["error"],
                    )

            severity = "warning" if result["failures"] else "info"
            self.core.popup(message, severity=severity)
        except Exception as exc:
            self.core.popup(
                "Could not summarize the daily review copy:\n%s" % exc,
                severity="warning",
            )

    def _copy_failed(self, message):
        self._close_copy_job()
        self.core.popup(
            "Could not create the daily review folder:\n%s" % message,
            severity="warning",
        )

    def _close_copy_job(self):
        job = self._copy_job
        self._copy_job = None
        if not job:
            return

        progress = job.get("progress")
        if progress is not None:
            try:
                progress.close()
            except RuntimeError:
                pass

        bridge = job.get("bridge")
        if bridge is not None:
            bridge.deleteLater()

    @classmethod
    def _get_media_selection(cls, media_player):
        try:
            contexts = media_player.getCurRenders() or []
            sequence = list(getattr(media_player, "seq", []) or [])
        except Exception:
            return []

        paths = []
        first_base = contexts[0].get("path", "") if contexts else ""
        is_sequence = bool(
            getattr(media_player, "prvIsSequence", False)
            or len(sequence) > 1
        )

        if is_sequence and first_base:
            sequence_directory = (
                first_base
                if os.path.isdir(first_base)
                else os.path.dirname(first_base)
            )
            paths.append(sequence_directory)
        elif sequence:
            for name in sequence:
                paths.append(
                    name
                    if os.path.isabs(name)
                    else os.path.join(first_base, name)
                )

        for context in contexts[1 if sequence else 0:]:
            path = context.get("path", "")
            if path:
                paths.append(path)

        return cls._existing_paths(paths)

    @staticmethod
    def _existing_paths(paths):
        existing = []
        seen = set()
        for path in paths or []:
            if not path:
                continue
            normalized = os.path.normpath(os.fspath(path))
            key = os.path.normcase(os.path.abspath(normalized))
            if key in seen or not os.path.exists(normalized):
                continue
            seen.add(key)
            existing.append(normalized)
        return existing
