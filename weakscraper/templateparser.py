# -*- coding: utf-8 -*-

# python apps
import collections
import json


PossibleParams = (
        'wp-attr-name-dict',
        'wp-decl',
        'wp-function',
        'wp-function-attrs',
        'wp-ignore',
        'wp-ignore-attrs',
        'wp-ignore-content',
        'wp-item',
        'wp-leaf',
        'wp-list',
        'wp-name',
        'wp-name-attrs',
        'wp-optional',
        'wp-recursive',
        'wp-recursive-text',
        'wp-until',
        )


def template_parser(root, debug):
    '深度遍历, 处理标签属性wp-*'
    arr_node = collections.deque()
    arr_node.append(root)

    while arr_node:
        node = arr_node.popleft()

        x = getattr(node, 'children', None)
        if x:
            arr_node.extendleft(reversed(list(x)))

        arr_wp = None
        x = getattr(node, 'attrs', None)
        if x:
            arr_wp = [k for k in x.keys() if k in PossibleParams]
            if debug:
                print('node: {}\n\tattrs: {}\n\tarr_wp: {}'.format(node,
                        node.attrs, arr_wp))
        if not arr_wp:
            continue

        params = {}
        for k in arr_wp:
            v = node.attrs.pop(k)
            if k == 'wp-ignore':
                params['wp-ignore-content'] = None
                params['wp-ignore-attrs'] = None
            elif k in ('wp-recursive', 'wp-recursive-text'):
                params['wp-leaf'] = None
                params['wp-recursive-leaf'] = None
                params[k] = v
            elif k == 'wp-attr-name-dict':
                params[k] = json.loads(v)
            else:
                params[k] = v
        node.params = params

        if debug:
            print('\tattrs: {}\n\tparams: {}'.format(node.attrs, node.params))
