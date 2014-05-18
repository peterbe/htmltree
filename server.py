#!/usr/bin/env python
import os
import hashlib
import time

from werkzeug.contrib.cache import MemcachedCache

from flask import Flask, request, make_response, jsonify, send_file
from flask.views import MethodView

from parser import url_to_tree, sizeof_fmt

MEMCACHE_URL = os.environ.get('MEMCACHE_URL', '127.0.0.1:11211').split(',')
DEBUG = os.environ.get('DEBUG', False) in ('true', '1', 'y', 'yes')

APP_LOCATION = 'client'
if os.path.isdir('./dist') and os.listdir('./dist'):
    print "Note: Serving files from ./dist"
    APP_LOCATION = 'dist'


app = Flask(
    __name__,
    static_folder=os.path.join(APP_LOCATION, 'static')
)
cache = MemcachedCache(MEMCACHE_URL)


class URLToTreeView(MethodView):

    queue_key = 'jobs-in-queue'

    def get(self):
        value = cache.get(self.queue_key) or 0
        recent = cache.get('recent') or []
        recent = _unique(recent)
        context = {'jobs': value, 'recent': recent}
        return make_response(jsonify(context))

    def post(self):
        url = request.json['url']
        max_depth = int(request.json['max_depth'])
        if '://' not in url:
            url = 'http://' + url
        assert max_depth <= 5
        key = hashlib.md5('%s%s' % (url, max_depth)).hexdigest()
        tree = cache.get(key)
        if tree is None:

            t0 = time.time()
            tree = url_to_tree(
                url,
                use_cache=DEBUG,
                max_depth=max_depth
            )
            t1 = time.time()
            cache.set(key, tree, 60 * 60)
            tree['_from_cache'] = False
            tree['_took'] = '%.3f' % (t1 - t0)

            recent = cache.get('recent') or []
            recent.insert(0, url)
            recent = _unique(recent)
            cache.set('recent', recent[:15], 60 * 60 * 24)

        else:
            tree['_from_cache'] = True
        size = None
        for k in tree:
            if k == 'name':
                size = tree[k].split()[-1]
        tree['_size'] = size
        return make_response(jsonify(tree))


def _unique(list_):
    def _f10(seq, idfun=None):
        seen = set()
        for x in seq:
            if x in seen:
                continue
            seen.add(x)
            yield x
    return list(_f10(list_))


@app.route('/')
def index_html():
    return catch_all('index.html')


@app.route('/<path:path>')
def catch_all(path):
    if path == 'favicon.ico':
        path = 'static/favicon.ico'
    path = path or 'index.html'
    path = os.path.join(APP_LOCATION, path)

    if not (os.path.isdir(path) or os.path.isfile(path)):
        path = os.path.join(APP_LOCATION, 'index.html')
    return send_file(path)


app.add_url_rule(
    '/tree',
    view_func=URLToTreeView.as_view('tree')
)

if __name__ == '__main__':
    app.debug = DEBUG
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port)
