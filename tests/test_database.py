import datetime
import random
import time
from contextlib import contextmanager

import pytest


@pytest.fixture(scope='function')
def db_sa(db):
    # To make it easier to test, we keep the test restricted to firebase_tests
    # Because of the current mutations on calls, we return it as a function.
    name = 'test_%05d' % random.randint(0, 99999)
    yield lambda: db().child(name)


@contextmanager
def make_stream(db, cbk):
    s = db.stream(cbk)
    try:
        yield s
    finally:
        s.close()


@contextmanager
def make_append_stream(db):
    l = []

    def cbk(event):
        l.append(event)

    with make_stream(db, cbk) as s:
        yield s, l

@contextmanager
def make_stream_with_exception_handler(db, cbk, xbk, auto_restart=0, daemon=False):
    s = db.stream(cbk, exception_handler=xbk, auto_restart=auto_restart, daemon=daemon)
    try: 
        yield s
    finally: 
        s.close()


class TestSimpleGetAndPut:
    def test_simple_get(self, db_sa):
        assert db_sa().get().val() is None

    def test_put_succeed(self, db_sa):
        assert db_sa().set(True)

    def test_put_then_get_keeps_value(self, db_sa):
        db_sa().set("some_value")
        assert db_sa().get().val() == "some_value"

    def test_put_dictionary(self, db_sa):
        v = dict(a=1, b="2", c=dict(x=3.1, y="3.2"))
        db_sa().set(v)

        assert db_sa().get().val() == v

    @pytest.mark.skip
    def test_put_deeper_dictionnary(self, db_sa):
        v = {'1': {'11': {'111': 42}}}
        db_sa().set(v)

        # gives: assert [None, {'11': {'111': 42}}] == {'1': {'11': {'111': 42}}}
        assert db_sa().get().val() == v


class TestJsonKwargs:

    def encoder(self, obj):
        if isinstance(obj, datetime.datetime):
            return {
                '__type__': obj.__class__.__name__,
                'value': obj.timestamp(),
            }
        return obj

    def decoder(self, obj):
        if '__type__' in obj and obj['__type__'] == datetime.datetime.__name__:
            #return datetime.datetime.utcfromtimestamp(obj['value'])
            return datetime.datetime.fromtimestamp(obj['value'])
        return obj

    def test_put_fail(self, db_sa):
        v = {'some_datetime': datetime.datetime.now()}
        with pytest.raises(TypeError):
            db_sa().set(v)

    def test_put_succeed(self, db_sa):
        v = {'some_datetime': datetime.datetime.now()}
        assert db_sa().set(v, json_kwargs={'default': str})

    def test_put_then_get_succeed(self, db_sa):
        v = {'another_datetime': datetime.datetime.now()}
        db_sa().set(v, json_kwargs={'default': self.encoder})
        assert dict(db_sa().get(json_kwargs={'object_hook': self.decoder}).val()) == v


class TestChildNavigation:
    def test_get_child_none(self, db_sa):
        assert db_sa().child('lorem').get().val() is None

    def test_get_child_after_pushing_data(self, db_sa):
        db_sa().set({'lorem': "a", 'ipsum': 2})

        assert db_sa().child('lorem').get().val() == "a"
        assert db_sa().child('ipsum').get().val() == 2

    def test_update_child(self, db_sa):
        db_sa().child('child').update({'c1/c11': 1, 'c1/c12': 2, 'c2': 3})

        assert db_sa().child('child').child('c1').get().val() == {'c11': 1, 'c12': 2}
        assert db_sa().child('child').child('c2').get().val() == 3

    def test_path_equivalence(self, db_sa):
        db_sa().set({'1': {'11': {'111': 42}}})

        assert db_sa().child('1').child('11').child('111').get().val() == 42
        assert db_sa().child('1/11/111').get().val() == 42
        assert db_sa().child('1', '11', '111').get().val() == 42
        assert db_sa().child(1, '11', '111').get().val() == 42


class TestStreaming:
    def test_create_stream_succeed(self, db_sa):
        with make_append_stream(db_sa()) as (stream, l):
            assert stream is not None

    def test_does_initial_call(self, db_sa):
        with make_append_stream(db_sa()) as (stream, l):
            time.sleep(2)
            assert len(l) == 1

    def test_responds_to_update_calls(self, db_sa):
        with make_append_stream(db_sa()) as (stream, l):
            db_sa().set({"1": "a", "1_2": "b"})
            db_sa().update({"2": "c"})
            db_sa().push("3")

            time.sleep(2)
            assert len(l) == 3

    def test_simple_stream(self, db_sa):
        print()
        lu = {'foo': 1, 'bar': 2, 'quux': 3}
        dl = []
        xl = []

        def exhandler(t, x):
            print('Exception: thread=%s exception=%s' % (repr(t), repr(x)))
            xl.append(x)
            return True

        def callback(msg):
            print('data from stream: %s' % repr(msg))
            if msg['data']:
              dl.append(lu[msg['data']])

        with make_stream_with_exception_handler(db_sa(), callback, exhandler) as stream:
            db_sa().set('foo')
            db_sa().set('bar')
            db_sa().set('baz')
            db_sa().set('quux')

            time.sleep(2)
            assert dl == [1,2,3]
            assert len(xl)

    def test_listen_and_restart(self, db_sa):
        print()
        dl = []
        xl = []

        def exhandler(t, x):
            print('Exception: thread=%s exception=%s' % (repr(t), repr(x)))
            xl.append(x)
            return True

        def callback(msg):
            print('data from stream: %s' % repr(msg))
            if msg['data']:
              dl.append(msg['data'])

        with make_stream_with_exception_handler(db_sa(), callback, exhandler) as stream:
            db_sa().set('foo')
            db_sa().set('bar')
            time.sleep(1)
                
        with make_stream_with_exception_handler(db_sa(), callback, exhandler) as stream:
            db_sa().set('baz')
            db_sa().set('quux')
            time.sleep(1)
                 
        time.sleep(1)
        assert dl == ['foo', 'bar', 'baz', 'quux']
        assert not len(xl)

    def test_without_context(self, db_sa):
        print()
        dl = []
        xl = []

        def exhandler(t, x):
            print('Exception: thread=%s exception=%s' % (repr(t), repr(x)))
            xl.append(x)
            return True

        def callback(msg):
            print('data from stream: %s' % repr(msg))
            if msg['data']:
              print('appending: %s' % msg['data'])
              dl.append(msg['data'])
            
        s = db_sa().stream(callback, exception_handler=exhandler, stream_id=111)
        db_sa().push('one')
        db_sa().push('two')
        db_sa().push('three')
        time.sleep(1)  
        s.close()

        s = db_sa().stream(callback, exception_handler=exhandler, stream_id=222)
        db_sa().push('four')
        db_sa().push('five')
        time.sleep(1)  
        s.close()

        time.sleep(3)  
        for d in dl:
            print(d)
        assert dl

    def test_auto_restart(self, db_sa):
        print()
        dd = {}

        def exhandler(t, x):
            print('Exception: thread=%s exception=%s' % (repr(t), repr(x)))
            return False

        def callback(msg):
            print('data from stream: %s' % repr(msg))
            if msg['data']:
                print('appending: %s' % msg['data'])
                d = (msg['data'])
                assert type(d) == dict
                for k,v, in d.items():
                    dd[k]=v
                        
        with make_stream_with_exception_handler(db_sa(), callback, exhandler, daemon=True, auto_restart=1) as stream:
            for s in range(5):        
                print('put: %s' % s)
                db_sa().push(s)
                time.sleep(.5)

        time.sleep(3)
        assert set(dd.values()) == set([0,1,2,3,4])
