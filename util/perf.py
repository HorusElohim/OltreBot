import time


def my_decorator(func, ):
    def wrapper():
        print("Something is happening before the function is called.")
        func()
        print("Something is happening after the function is called.")

    return wrapper


def perf(method):
    def perf_decorator(*args, **kw):
        ts = time.time_ns()
        result = method(*args, **kw)
        e_time = time.time_ns() - ts
        if 'logger' in kw:
            kw['logger'].debug(f'@perf -> {method.__name__}  {e_time * 1e-6} ms')
        else:
            print(f'@perf -> {method.__name__} {e_time * 1e-6} ms')
        return result

    return perf_decorator
