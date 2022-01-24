import sys
from itertools import zip_longest
from types import FunctionType

import cloudpickle
import pytest


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


def assert_roundtips(old_gen):
    if isinstance(old_gen, FunctionType):
        # we got a generator function, create a generator and advance it once
        old_gen = old_gen()
        next(old_gen)

    new_gen = roundtrip(old_gen)
    assert_tail_matches(old_gen, new_gen)

    assert old_gen.__name__ == new_gen.__name__
    assert (
        getattr(old_gen, '__qualname__', None) ==
        getattr(new_gen, '__qualname__', None)
    )


def test_simple_generator():
    @assert_roundtips
    def f():
        yield 1
        yield 2
        yield 3


def test_stack():
    def nop(ob):
        return 1

    @assert_roundtips
    def f():
        # this loads ``nop`` on the stack before yielding
        yield nop((yield))


def test_block_stack():
    @assert_roundtips
    def f():
        yield 1
        try:
            yield 2
        finally:
            yield 3


def test_arguments():
    def f(a, b):
        yield a
        yield b

    assert_roundtips(f(1, 2))


def test_exc_info():
    @assert_roundtips
    def f():
        try:
            yield 'start'
            raise ValueError('ayy lmao')
        except ValueError as e:
            assert str(e) == 'ayy lmao'
            yield str(e)


def test_closure():
    def g(a, b):
        @assert_roundtips
        def f():
            yield a
            yield b

    g(1, 2)


def test_freevars():
    @assert_roundtips
    def f():
        a = 1
        yield a

        def g():
            nonlocal a
            a = 2

        g()
        yield a


def test_freevars_and_cellvars():
    def g(a):
        @assert_roundtips
        def f():
            b = a + 1
            yield b

            def g():
                nonlocal b
                b = -1

            g()
            yield b

    g(0)


@pytest.mark.xfail(sys.version_info >= (3, 8, 0), reason="needs to be investigated")
def test_self_in_closure():
    def nop(ob):
        pass

    def f():
        # close over ourselves; why did you do this?
        nop(gen)
        yield 1
        yield 2

    gen = f()
    assert_roundtips(gen)


_test_refereences_global_sentinel = None


def test_references_global():
    @assert_roundtips
    def f():
        yield 1
        yield _test_refereences_global_sentinel


def test_fully_consumed():
    def f():
        yield 1

    gen = f()
    next(gen)

    assert_roundtips(gen)


def test_running():
    def f():
        yield roundtrip((yield))

    gen = f()
    next(gen)

    with pytest.raises(ValueError) as e:
        gen.send(gen)

    assert str(e.value) == 'cannot save running generator'
