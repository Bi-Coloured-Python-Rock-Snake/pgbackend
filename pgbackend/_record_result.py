from functools import wraps


def record_result(fn, record: dict):
    @wraps(fn)
    def wrapper(*args, **kw):
        record['result'] = fn(*args, **kw)
        return record['result']

    return wrapper