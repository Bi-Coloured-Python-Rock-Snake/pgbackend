import typing
from contextlib import nullcontext, contextmanager
from dataclasses import dataclass, field
from types import FunctionType
from typing import ContextManager


class TupleCm(typing.NamedTuple):
    enter: FunctionType
    exit: FunctionType

    @property
    def __enter__(self):
        return self.enter

    @property
    def __exit__(self):
        return self.exit


@dataclass
class NullableContextManager:
    _cm: ContextManager = nullcontext()
    _enter_result = None

    def __enter__(self):
        self._enter_result = self._cm.__enter__()
        return self._enter_result

    def __exit__(self, *exc_info):
        return self._cm.__exit__(*exc_info)

    def pop_context(self):
        exit = self._cm.__exit__
        del self._cm
        return TupleCm(lambda: self._enter_result, exit)

    def close(self):
        with self.pop_context():
            pass



nullable_cm = NullableContextManager





if __name__ == '__main__':
    @contextmanager
    def make_cm():
        print('<')
        yield
        print('>')

    with (cm := nullable_cm(make_cm())) as val:
        with cm.pop_context():
            1

