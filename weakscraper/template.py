# -*- coding: utf-8 -*-
'''
    node.wp_info        dict类型。记录模板节点的标记信息。
        params              模板节点的标记
        functions           处理的函数信息
        regex               正则表达式对象
        debug               显示调试的标志
'''

# python apps
import re

# our apps
from .utils import node_to_json


DEBUG_INIT = True


class Template:
    def __init__(self, root, functions, debug=False):
        '遍历模板DOM树'
        if DEBUG_INIT:
            print('''----------------
                    Template.__init__(): ...
                        self: {}
                        functions: {}
                        debug: {}
                        root: {}'''.format(self, functions, debug, root))
        self.node = root

        arr_tree = []
        arr_node = collections.deque()
        arr_node.append((root, arr_tree))

        while arr_node:
            node, arr_ret = arr_node.popleft()
            info = node.to_json()
            if (
                    isinstance(node, bs4.NavigableString)
                    or isinstance(node, bs4.Tag) and node.name == 'wp-nugget'
                    ):
                self._init_texts_and_nuggets(node)
            else:
                self._init_tag(node)

    def __repr__(self):
        info = self.to_json()
        msg = json.dumps(info, ensure_ascii=False)
        ret = '<Template({})>'.format(msg)
        return ret

    def to_json(self):
        '节点的children属性，只显示self的'
        arr_key = ('name', 'names', 'attrs', 'functions', 'params', 'regex')
        info = node_to_json(self, arr_key)

        arr = getattr(self, 'children', None)
        if arr:
            info['children'] = [item.node_to_json() for item in arr]
        return info

    def _init_tag(self, node):
        pass
        if DEBUG_INIT:
            print('''----------------
                    Template._init_tag(): ...
                        self: {}
                        node: {}'''.format(self, node))

        x = hasattr(node, 'name')
        assert not x or x and node.name != 'wp-nugget'

        if 'wp-function' in self.params and 'wp-name' not in self.params:
            self.params['wp-name'] = self.params['wp-function']



def init(tree_tpl, functions, debug=False):
    '遍历模板DOM树'
    if DEBUG_INIT:
        print('''----------------
                init(): ...
                    tree_tpl: {}
                    functions: {}
                    debug: {}'''.format(tree_tpl, functions, debug))

    arr_tree = []
    arr_node = collections.deque()
    arr_node.append((tree_tpl, arr_tree))

    while arr_node:
        node, arr_ret = arr_node.popleft()
        if hasattr(node, 'wp_info'):
            if _boolean_text_or_nugget(node):
                node.wp_info.update({
                        'functions': functions,
                        'debug': debug,
                        })
                _init_texts_and_nuggets(node)
            else:
                _init_tag(node, functions, debug)


def _init_tag(node, functions, debug=False):
    pass
    if DEBUG_INIT:
        print('''----------------
                _init_tag(): ...
                    node: {}
                    functions: {}
                    debug: {}'''.format(node, functions, debug))

    info_default = {
            'functions': functions,
            'debug': debug,
            }
    params = node.wp_info['params']

    if 'wp-ignore' in params:
        return

    if 'wp-function' in params and 'wp-name' not in params:
        params['wp-name'] = params['wp-function']

    if 'wp-function-attrs' in params and 'wp-name-attrs' not in params:
        params['wp-name-attrs'] = params['wp-function-attrs']

    if 'wp-name-attrs' in params:
        params['wp-ignore-attrs'] = None

    if 'wp-ignore-content' in params:
        if 'wp-leaf' in params:
            params.pop('wp-leaf')

        node.clear()
        ignore = bs4.Tag(name='wp-ignore', parent=node)
        ignore.wp_info = {'params': {'wp-ignore': None}}
        ignore.wp_info.update(info_default)
        return

    if 'wp-leaf' in params:
        assert len(node.children) == 0
        return

    if not hasattr(node, 'children'):
        return

    text_flags = [_boolean_text_or_nugget(node) for node in node.children]

    arr = node.contents
    node.clear()
    grandchildren = []
    for i, child in enumerate(arr):
        if text_flags[i]:
            'NavigableString or wp-nugget'
            pass
        else:
            if grandchildren:
                _process_grandchildren(node, grandchildren)
            if hasattr(child, 'wp_info'):
                child.wp_info.update(info_default)
            node.append(child)
    if grandchildren:
        _process_grandchildren(node, grandchildren)


def _boolean_text_or_nugget(node):
    '节点是 NavigableString or wp-nugget'
    flag = isinstance(node, bs4.NavigableString) \
            or isinstance(node, bs4.Tag) and node.name == 'wp-nugget'
    return flag


def _process_grandchildren(node, arr):
    'NavigableString or wp-nugget --> texts-and-nuggets'
    if DEBUG_INIT:
        print('''----------------
                _process_grandchildren(): ...
                    self: {}
                    arr: {}'''.format(self, arr))

    new_node = bs4.Tag(name='texts-and-nuggets', parent=node)
    [new_node.append(i) for i in arr]
    arr.clear()


def _init_texts_and_nuggets(node, functions, debug):
    pass
    if DEBUG_INIT:
        print('''----------------
                _init_texts_and_nuggets(): ...
                    node: {}
                    functions: {}
                    debug: {}'''.format(node, functions, debug))

    if len(node.children) == 1:
        child = raw_template['children'][0]
        if child['nodetype'] == 'text':
            self.nodetype = 'text'
            self.content = child['content']

        elif child['nodetype'] == 'tag':
            assert(child['name'] == 'wp-nugget')
            self.nodetype = 'nugget'
            self.params = child['params']

        else:
            raise ValueError('Unexpected nodetype.')
        return


