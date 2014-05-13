#!/usr/bin/env python
import json
import os
import hashlib

import requests

from werkzeug.contrib.cache import MemcachedCache

from flask import Flask, request, make_response, jsonify, send_file
from flask.views import MethodView

from parser import url_to_tree

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

    def post(self):
        url = request.json['url']
        max_depth = int(request.json['max_depth'])
        # treemap = bool(request.json.get('treemap'))
        if '://' not in url:
            url = 'http://' + url
        # from time import sleep
        # sleep(6)
        assert max_depth <= 5
        key = hashlib.md5(url).hexdigest()
        tree = url_to_tree(
            url,
            use_cache=DEBUG,
            max_depth=max_depth
        )
        cache.set(key, tree, 60 * 60)
        # tree = cache.get(key)
        return make_response(jsonify(tree))


@app.route('/')
def index_html():
    return catch_all('index.html')


@app.route('/<path:path>')
def catch_all(path):
    if path == 'favicon.ico':
        path = 'static/favicon.ico'
    path = path or 'index.html'
    path = os.path.join(APP_LOCATION, path)
    # print "PATH", path

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
