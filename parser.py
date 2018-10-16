import time,sys
import codecs
import os
import hashlib

import requests
from lxml import etree


def get_html(url, use_cache=False):
    if use_cache:
        filename = './.downloadcache/%s.html' % hashlib.md5(url).hexdigest()
        if os.path.isfile(filename):
            with codecs.open(filename, 'r', 'utf-8') as f:
                print "READING FROM CACHE", filename
                return f.read(), 'utf-8'

    response = requests.get(url)
    print "DOWNLOADING", url
    t0 = time.time()
    assert response.status_code == 200, response.status_code
    html = response.content
    t1 = time.time()
    print >>sys.stderr, "Downloading", (t1 - t0) * 1000
    encoding = response.encoding
    if isinstance(html, str):
        html = html.decode(encoding)
    # print type(html)
    if use_cache:
        if not os.path.isdir('./.downloadcache'):
            os.mkdir('.downloadcache')
        with codecs.open(filename, 'w', 'utf-8') as f:
            f.write(html)
    return html, encoding


def url_to_tree(url, use_cache=False, max_depth=4):
    print (url, use_cache)
    html, encoding = get_html(url, use_cache=use_cache)

    t0 = time.time()
    parser = etree.HTMLParser(encoding=encoding)

    print "Parsing", len(html), "bytes"
    try:
        doc = etree.fromstring(html, parser).getroottree()
    except ValueError:
        # is it perhaps a duplicate encoding definition
        # http://twigstechtips.blogspot.com/2013/06/python-lxml-strings-with-encoding.html
        html = html.encode(encoding)
        doc = etree.fromstring(html, parser).getroottree()
    page = doc.getroot()
    t1 = time.time()
    print >>sys.stderr, "Parsing", (t1 - t0) * 1000
    tree = {}

    t0 = time.time()
    size = _node_size(page)
    tree['name'] = _describe_node(page, size)
    tree['value'] = size
    tree['percentage'] = size / size
    tree['children'] = []
    tree['children'].extend(_get_children(page, max_depth, float(size)))
    t1 = time.time()
    print >>sys.stderr, "Processing", (t1 - t0) * 1000
    return tree


def _describe_node(node, size):
    attrs = []
    for key, value in node.attrib.items():
        if key in ('class', 'id'):
            attrs.append('%s="%s"' % (key, value))
    if attrs:
        attrs.insert(0, '')
        attrs = ' '.join(attrs)
    else:
        attrs = ''
    return '<%s%s> %s' % (node.tag, attrs, sizeof_fmt(size))


def _node_size(node):
    return len(etree.tostring(node))


def sizeof_fmt(num):
    for x in ['b', 'Kb', 'Mb', 'Gb', 'Tb']:
        if num < 1024.0:
            if x == 'b':
                return "%d%s" % (num, x)
            else:
                return "%3.1f%s" % (num, x)
        num /= 1024.0


def _get_children(page, maxdepth, whole_size):
    children = []
    for thing in page:
        if thing.tag is etree.Comment:
            continue
        size = _node_size(thing)
        item = {
            'name': _describe_node(thing, size),
            'value': size,
            'percentage': size / whole_size
        }
        if maxdepth > 0:
            sub_children = _get_children(thing, maxdepth - 1, whole_size)
            if sub_children:
                item['children'] = sub_children
        children.append(item)

    return children


if __name__ == '__main__':
    import sys
    import json
    # from pprint import pprint
    urls = sys.argv[1:]
    try:
        max_depth = int(sys.argv[2])
    except (ValueError, IndexError):
        max_depth = 4
    for url in urls:
        print json.dumps(
            url_to_tree(url, use_cache=True, max_depth=max_depth),
            indent=4, sort_keys=True
        )
