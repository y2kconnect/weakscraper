# -*- coding: utf-8 -*-
''' 使用class Template，递归。
'''

# python apps
import pprint
import re

# our apps
from .utils import serialize


class Template:
    def __init__(self, node, functions, debug=False):
        if debug:
            print('''----------------
                    Template.__init__(): ...
                        self: {}
                        functions: {}
                        debug: {}
                        node: {}'''.format(self, functions, debug, node))

        self.node = node
        self.debug = debug
        self.functions = functions


        if 'name' in self.node and self.node.name == 'texts-and-nuggets':
            # 处理 texts-and-nuggets
            self._init_texts_and_nuggets()
        else:
            self._init_tag()

    def __repr__(self):
        ret = serialize(self)
        return ret

    def _init_tag(self):
        pass
        if DEBUG_INIT:
            print('''----------------
                    Template._init_tag(): ...
                        self: {}'''.format(self))

        if 'name' not in self.node:
            return

        tag = self.node.name
        assert tag != 'wp-nugget'

        if tag == 'wp-ignore':
            return

        params = self.node.wp_info['params']

        i, j = ('wp-function', 'wp-name')
        if i in params and j not in params:
            params[j] = params[i]

        i, j = ('wp-function-attrs', 'wp-name-attrs')
        if i in params and j not in params:
            params[j] = params[i]

        i, j = ('wp-name-attrs', 'wp-ignore-attrs')
        if i in params:
            params[j] = None

        i, j = ('wp-ignore-content', 'wp-leaf')
        if i in params:
            del params[j]

            new_node = bs.Tag(name='wp-ignore')
            new_node.wp_info = {}
            ignore = Template(new_node, self.function, self.debug)

            self.children = [ignore]
            return

        if 'wp-leaf' in params:
            assert len(self.node.contents) == 0
            return

        text_flags = self._check_text_flag()

        self.children = []
        grandchildren = []

        for i, child in enumerate(self.node.contents):
            if text_flags[i]:
                # text or wp-nugget
                grandchildren.append(child)
            else:
                if grandchildren:
                    self._process_grandchildren(grandchildren)
                    grandchildren = []
                new_child = Template(child, self.functions, self.debug)
                self.children.append(new_child)

        if grandchildren:
            self._process_grandchildren(grandchildren)
            grandchildren = []

        self.node.contents = self.children
        for child in children:
            child.parent = self.node

    def _init_texts_and_nuggets(self):
        '处理 texts-and-nuggets'
        pass

    def _check_text_flag(self):
        'check text or wp-nugget'
        pass
        if self.debug:
            print('''
                    ----------------
                    Template._check_text_flag(): ...
                        self: {}'''.format(self))

        arr = [
                True if (
                        isinstance(child, bs4.NavigableString)
                        or child.name == 'wp-nugget'
                        ) else False
                for child in self.node.contents:
                ]

        if debug:
            print('\n\tarr: {}'.format(arr))
        return arr

    def _process_grandchildren(self, arr):
        'text or wp-nugget --> texts-and-nuggets'
        if self.debug:
            print('''----------------
                    Template._process_grandchildren(): ...
                        self: {}
                        arr: {}'''.format(self, arr))

        node_tpl = bs4.Tag(name='texts-and-nuggets')
        node_tpl.contents = arr
        node_tpl.wp_info = {
                'params': {},
                'functions': self.functions,
                'debug': self.debug,
                }
        new_child = Template(node_tpl, self.functions, self.debug)
        self.children.append(new_child)


