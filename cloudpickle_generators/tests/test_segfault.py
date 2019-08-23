import subprocess
import cloudpickle


def gen():
    return (yield 1)


def main():
    subprocess.check_call(["ls"])
    yield from gen()


def test_1():
    coro = main()
    coro.send(None)
    cloudpickle.dumps(coro)
