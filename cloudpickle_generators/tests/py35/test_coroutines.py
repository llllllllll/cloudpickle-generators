from itertools import zip_longest
from types import FunctionType, coroutine

import cloudpickle


def asgen(coro):
    while True:
        try:
            yield coro.send(None)
        except StopIteration:
            return


@coroutine
def id(x):
    return (yield x)


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
    assert_tail_matches(asgen(old_coro), asgen(new_coro))

    assert old_coro.__name__ == new_coro.__name__
    assert (
        getattr(old_coro, '__qualname__', None) ==
        getattr(new_coro, '__qualname__', None))


def test_simple_coro():
    @assert_roundtips
    async def async_fn():
        for i in range(10):
            await id(i)


def test_stack():
    def nop(ob):
        return 1

    @assert_roundtips
    @coroutine
    def f():
        # this loads ``nop`` on the stack before yielding
        yield nop((yield))


def test_arguments():
    async def f(a, b):
        await id(a)
        await id(b)

    assert_roundtips(f(1, 2))


def test_exc_info():
    @assert_roundtips
    async def f():
        try:
            await id('start')
            raise ValueError('ayy lmao')
        except ValueError as e:
            assert str(e) == 'ayy lmao'
            await id(str(e))


def test_closure():
    def g(a, b):
        @assert_roundtips
        async def f():
            await id(a)
            await id(b)

    g(1, 2)


def test_freevars():
    @assert_roundtips
    async def f():
        a = 1
        await id(a)

        async def g():
            nonlocal a
            a = 2
            await id(a)

        await g()
        await id(a)


def test_freevars_and_cellvars():
    def g(a):
        @assert_roundtips
        async def f():
            b = a + 1
            await id(b)

            def g():
                nonlocal b
                b = -1

            g()
            await id(b)

    g(0)


def test_self_in_closure():
    def nop(ob):
        pass

    async def f():
        # close over ourselves; why did you do this?
        nop(gen)
        await id(1)
        await id(2)

    gen = f()
    assert_roundtips(gen)


_test_refereences_global_sentinel = None


def test_references_global():
    @assert_roundtips
    async def f():
        await id(1)
        await id(_test_refereences_global_sentinel)


def test_fully_consumed():
    async def f():
        await id(1)

    gen = f()
    gen.send(None)

    assert_roundtips(gen)
