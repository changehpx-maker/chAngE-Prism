import glob
import os


def get_houdini_executable(core):
    """Return the Houdini executable selected in Prism user settings."""
    if core is None:
        return ""

    executable = ""
    getter = getattr(core, "getExecutableOverride", None)
    if callable(getter):
        try:
            executable = getter("Houdini") or ""
        except Exception:
            executable = ""

    if not executable:
        try:
            enabled = core.getConfig(
                cat="dccoverrides", param="Houdini_override"
            )
            if enabled:
                executable = core.getConfig(
                    cat="dccoverrides", param="Houdini_path"
                ) or ""
        except Exception:
            executable = ""

    if isinstance(executable, (list, tuple)):
        executable = executable[0] if executable else ""
    return os.path.normpath(os.path.expandvars(str(executable))) if executable else ""


def derive_hython(houdini_executable):
    """Derive hython next to a Prism-selected Houdini executable."""
    if not houdini_executable:
        return ""
    if isinstance(houdini_executable, (list, tuple)):
        houdini_executable = (
            houdini_executable[0] if houdini_executable else ""
        )
    if not houdini_executable:
        return ""

    executable = os.path.abspath(
        os.path.expandvars(os.path.expanduser(str(houdini_executable)))
    )
    name = os.path.basename(executable).lower()
    if name in ("hython", "hython.exe") and os.path.isfile(executable):
        return executable

    directory = os.path.dirname(executable)
    preferred = "hython.exe" if os.name == "nt" else "hython"
    candidate = os.path.join(directory, preferred)
    if os.path.isfile(candidate):
        return candidate

    for candidate in sorted(glob.glob(os.path.join(directory, "hython*"))):
        if os.path.isfile(candidate):
            return os.path.normpath(candidate)
    return ""


def get_prism_hython(core):
    return derive_hython(get_houdini_executable(core))
