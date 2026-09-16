class TaskNotFoundError(Exception):
    """Raised when a task id doesn't exist or doesn't belong to the caller.

    Both cases are reported identically on purpose — a handler must never
    reveal whether a task id belongs to someone else.
    """
