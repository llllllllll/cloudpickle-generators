import subprocess
import cloudpickle
import cloudpickle_generators
cloudpickle_generators.register()


def gen():
    return (yield 1)


def main():
    subprocess.check_call(["ls"])
    yield from gen()


def test_1():
    coro = main()
    coro.send(None)
    cloudpickle.dumps(coro)
