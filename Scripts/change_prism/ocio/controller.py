import os

from qtpy.QtWidgets import QMenu


class OCIOConvertController:
    def __init__(self, core):
        self.core = core
        self._quick_dialogs = []

    def add_media_context_menu(self, origin, menu, quick_callback):
        paths, _context = self._get_media_player_selection(origin)
        menu.addSeparator()
        submenu = QMenu("ACES / OCIO Quick Convert", menu)
        menu.addMenu(submenu)
        submenu.setEnabled(bool(paths))
        for label, formats in (
            ("H.264 MP4", (".mp4",)),
            ("ProRes 422 HQ MOV", (".mov",)),
            ("MP4 + MOV", (".mp4", ".mov")),
        ):
            action = submenu.addAction(label)
            action.triggered.connect(
                lambda checked=False, selected=formats: quick_callback(
                    origin, selected
                )
            )

    def open_dialog(self, media_player=None):
        from change_prism.ocio.dialog import OCIOConvertDialog

        paths = []
        context = {}
        if media_player is not None:
            paths, context = self._get_media_player_selection(media_player)
        parent = self.core.pb if getattr(self.core, "pb", None) else None
        dialog = OCIOConvertDialog(
            self.core,
            initial_paths=paths,
            initial_context=context,
            media_player=media_player,
            parent=parent,
        )
        dialog.exec_()

    def quick_convert(self, media_player, formats):
        from change_prism.ocio.dialog import OCIOConvertDialog

        paths, context = self._get_media_player_selection(media_player)
        if not paths:
            return
        parent = self.core.pb if getattr(self.core, "pb", None) else None
        dialog = OCIOConvertDialog(
            self.core,
            initial_paths=paths,
            initial_context=context,
            media_player=media_player,
            parent=parent,
        )
        self._quick_dialogs.append(dialog)
        dialog.conversionFinished.connect(
            lambda _result, current=dialog: self._release_quick_dialog(current)
        )
        dialog.start_quick_conversion(formats)

    def _release_quick_dialog(self, dialog):
        try:
            self._quick_dialogs.remove(dialog)
        except ValueError:
            pass

    @staticmethod
    def _get_media_player_selection(media_player):
        paths = []
        context = {}
        try:
            renders = media_player.getCurRenders() or []
            render = renders[0] if renders else {}
            base_path = render.get("path", "")
            for name in getattr(media_player, "seq", []) or []:
                path = (
                    name
                    if os.path.isabs(name)
                    else os.path.join(base_path, name)
                )
                if (
                    os.path.splitext(path)[1].lower() == ".exr"
                    and os.path.isfile(path)
                ):
                    paths.append(path)
            browser = getattr(media_player, "origin", None)
            if browser:
                context = (
                    browser.getCurrentAOV()
                    or browser.getCurrentVersion()
                    or {}
                )
        except Exception:
            return [], {}
        return paths, context
