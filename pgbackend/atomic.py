from contextlib import contextmanager


class Atomic:
    'TODO'

    def __init__(self, using, savepoint, durable, **kw):
        self.using = using
        self.savepoint = savepoint
        self.durable = durable

    @contextmanager
    def as_context_manager(self):
        yield

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass