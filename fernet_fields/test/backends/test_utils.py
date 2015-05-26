from fernet_fields.backends.utils import tempsetattr


def test_tempsetattr_nonexistent():
    class Empty(object):
        pass

    obj = Empty()
    with tempsetattr(obj, 'foo', 'bar'):
        assert obj.foo == 'bar'

    assert not hasattr(obj, 'foo')
