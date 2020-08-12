from __future__ import print_function

import contextlib
import cProfile
import functools
import logging
import os
import pstats
import random
import string
import sys
import time
import traceback

from flask import Flask

PY3 = int(sys.version[0]) > 2

if PY3:
    import io
else:
    import StringIO as io

app = Flask(__name__)

LEGACY_NDB = os.environ.get("LEGACY_NDB", "False") == "True"
PROFILE = os.environ.get("PROFILE_NDB", "False") == "True"

if LEGACY_NDB:
    from google.appengine.ext import ndb

    def ndb_wsgi_middleware(wsgi_app):
        def middleware(environ, start_response):
            context = ndb.get_context()
            context.set_cache_policy(False)
            context.set_memcache_policy(False)
            return wsgi_app(environ, start_response)

        return middleware


else:
    from google.cloud import ndb

    logging.getLogger("google.cloud.ndb").setLevel(logging.DEBUG)

    def ndb_wsgi_middleware(wsgi_app):
        ndb_client = ndb.Client()

        def middleware(environ, start_response):
            with ndb_client.context(cache_policy=False):
                return wsgi_app(environ, start_response)

        return middleware


@contextlib.contextmanager
def profile(output):
    start_time = time.time()
    if PROFILE:
        profiler = cProfile.Profile()
        profiler.enable()

    yield

    if PROFILE:
        profiler.disable()
    elapsed = time.time() - start_time

    context = ndb.get_context()
    rpc_time = get_rpc_time(context)
    wait_time = get_wait_time(context)

    print("time: {}".format(elapsed), file=output)
    print("rpc_time: {} ({}%)".format(rpc_time, int(rpc_time * 100 / elapsed)),
         file=output)
    print("wait_time: {} ({}%)".format(wait_time, int(wait_time * 100 /
                                                      elapsed)), file=output)

    if PROFILE:
        print("\n", file=output)
        stats = pstats.Stats(profiler, stream=output).sort_stats("time")
        stats.print_stats(20)


app.wsgi_app = ndb_wsgi_middleware(app.wsgi_app)


class SubData(ndb.Model):
    str0 = ndb.StringProperty()
    int0 = ndb.IntegerProperty()
    int1 = ndb.IntegerProperty()
    int2 = ndb.IntegerProperty()
    int3 = ndb.IntegerProperty()
    int4 = ndb.IntegerProperty()


class SomeData(ndb.Model):
    prop0 = ndb.StringProperty()
    prop1 = ndb.StringProperty()
    prop2 = ndb.StringProperty()
    prop3 = ndb.StringProperty()
    prop4 = ndb.StringProperty()
    prop5 = ndb.StringProperty()
    prop6 = ndb.StringProperty()
    prop7 = ndb.StringProperty()
    prop8 = ndb.StringProperty()
    flag = ndb.BooleanProperty()
    items = ndb.StructuredProperty(SubData, repeated=True)

    @classmethod
    def parent_key(cls):
        return ndb.Key("SomeData", "default")


@app.route("/init")
def init():
    random.seed(123)

    def randstr():
        return "".join(random.choice(string.ascii_lowercase) for _ in range(30))

    for _ in range(10):
        items = []
        for _ in range(40):
            item = SomeData(
                prop0=randstr(),
                prop1=randstr(),
                prop2=randstr(),
                prop3=randstr(),
                prop4=randstr(),
                prop6=randstr(),
                prop7=randstr(),
                prop8=randstr(),
                flag=random.randint(1, 2) == 1,
                items=[
                    SubData(
                        str0=randstr(),
                        int0=random.randint(1, 2000),
                        int1=random.randint(1, 2000),
                        int2=random.randint(1, 2000),
                        int3=random.randint(1, 2000),
                        int4=random.randint(1, 2000),
                    )
                    for _ in range(30)
                ],
                parent=SomeData.parent_key(),
            )
            items.append(item)
        ndb.put_multi(items)
    return "ok\n"


def _query0():
    return SomeData.query(SomeData.flag == True, ancestor=SomeData.parent_key())


def view_output(view):
    """Decorator, you know, for output."""

    @functools.wraps(view)
    def wrapper():
        output = io.StringIO()
        try:
            view(output)
            print("", file=output)
        except Exception as error:
            print("", file=output)
            if hasattr(error, "stack"):
                print(error.stack, file=output)
            else:
                traceback.print_exception(*sys.exc_info(), file=output)
        return output.getvalue()

    return wrapper


@app.route("/test1")
@view_output
def test1(output):
    with profile(output):
        result = _query0().count
        print(str(result), file=output)


@app.route("/test2")
@view_output
def test2(output):
    with profile(output):
        items = (
            _query0()
            .order(SomeData.prop0)
            .fetch(
                projection=[
                    SomeData.prop0,
                    SomeData.prop1,
                    SomeData.prop2,
                    SomeData.prop3,
                    SomeData.prop4,
                ]
            )
        )
        print(str(len(items)), file=output)


class Something(ndb.Model):
    foo = ndb.StringProperty()
    bar = ndb.BooleanProperty()


query2 = Something.query(
    Something.foo == "two",
    Something.bar == True,
)


@app.route("/test3")
@view_output
def test3(output):
    with profile(output):
        results = query2.fetch(limit=100000)
        print(str(len(results)), file=output)


@app.route("/test4")
@view_output
def test4(output):
    with profile(output):
        count = query2.count(limit=100000)
        print(str(count), file=output)


@app.route("/cleanup")
def cleanup():
    keys_left = SomeData.query().fetch(keys_only=True)
    while keys_left:
        keys = keys_left[:50]
        ndb.delete_multi(keys)
        keys_left = keys_left[50:]

    return "ok\n"


@app.route("/")
def main():
    return "ok\n"


def get_rpc_time(context):
    return getattr(context, "rpc_time", 0)


def get_wait_time(context):
    return getattr(context, "wait_time", 0)
