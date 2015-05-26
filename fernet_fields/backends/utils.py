from contextlib import contextmanager


unset = object()


@contextmanager
def tempsetattr(obj, attr, val):
    """Context manager to set an attribute on an object and restore it."""
    orig = getattr(obj, attr, unset)
    setattr(obj, attr, val)
    try:
        yield
    finally:
        if orig is unset:
            delattr(obj, attr)
        else:
            setattr(obj, attr, orig)


@contextmanager
def noop(*args):
    yield
