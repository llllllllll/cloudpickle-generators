import cloudpickle
import pytest

from cloudpickle_generators import unset_value


def roundtrip(ob):
    return cloudpickle.loads(cloudpickle.dumps(ob))


def test_pickleable():
    assert roundtrip(unset_value) is unset_value


def test_repr():
    assert repr(unset_value) == 'unset_value'


def test_unique():
    with pytest.raises(TypeError):
        type(unset_value)()
