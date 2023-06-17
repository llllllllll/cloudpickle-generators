from itertools import zip_longest
from types import FunctionType, coroutine

import cloudpickle
import pytest
import sys


@coroutine
def id(x):
    return (yield x)


def asyncgen_asgen(gen):
    assert gen.__aiter__() is gen
    while True:
        try:
            value = gen.__anext__().send(None)
            yield ('yield', value)
        except StopIteration as e:
            yield (StopIteration, e.value)
        except StopAsyncIteration:
            return


def roundtrip(ob):
    return cloudpickle.loads(cloudpickle.dumps(ob))


def assert_tail_matches(old, new):
    sentinel = object()
    old_tail = []
    new_tail = []
    for old_value, new_value in zip_longest(old, new, fillvalue=sentinel):
        old_tail.append(old_value)
        new_tail.append(new_value)
    assert old_tail == new_tail


def assert_roundtips(old_coro):
    if isinstance(old_coro, FunctionType):
        # we got a coroutine function, create a coroutine object
        old_coro = old_coro()

    new_coro = roundtrip(old_coro)
    assert type(old_coro) == type(new_coro)
    assert_tail_matches(asyncgen_asgen(old_coro), asyncgen_asgen(new_coro))

    assert old_coro.__name__ == new_coro.__name__
    assert (
        getattr(old_coro, '__qualname__', None) ==
        getattr(new_coro, '__qualname__', None))


def test_async_generator_0():
    @assert_roundtips
    async def genfunc():
        yield 1
        yield 2


@pytest.mark.xfail(sys.version_info >= (3, 8, 0), reason="asyncgen_asgen doesn't work on this function before roundtrip")
def test_async_generator_1():
    async def ticker(delay, to):
        # PEP525
        for i in range(to):
            yield i
            await id(1)

    assert_roundtips(ticker(1, 5))


def test_async_generator_2():
    async def square_series(series):
        async for i in series:
            yield i**2

    async def series():
        yield 1
        yield 2
        yield 3

    @assert_roundtips
    async def f():
        async for i in square_series(series()):
            yield i
