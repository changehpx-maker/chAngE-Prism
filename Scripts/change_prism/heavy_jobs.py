_ACTIVE_JOBS = {}


def acquire(group, owner):
    current = _ACTIVE_JOBS.get(group)
    if current is owner:
        return True
    if current is not None:
        return False
    _ACTIVE_JOBS[group] = owner
    return True


def release(group, owner):
    if _ACTIVE_JOBS.get(group) is owner:
        _ACTIVE_JOBS.pop(group, None)


def is_active(group):
    return group in _ACTIVE_JOBS
