# -*- coding: utf-8 -*-
''' 直接使用bs4建立的DOM树，进行遍历。
    使用双端队列，模拟递归。
    存在的问题：
        <wp-nugget>标签处理出错。

    node.wp_info        dict类型。记录模板节点的标记信息。
        params              模板节点的标记
        functions           处理的函数信息
        regex               正则表达式对象
        debug               显示调试的标志
'''

# python apps
import bs4
import collections
import re
import pdb

# our apps
from . import utils
from .exceptions import NodetypeError


def init_tpl(tree_tpl, functions=None, debug=False):
    '遍历模板DOM树'
    if debug:
        s = '''\n{}\ninit_tpl(): ...\n\ttree_tpl: {}\n\tfunctions: {}\n\tdebug: {}'''
        print(s.format('-' * 16, utils.serialize(tree_tpl), functions, debug))

    pdb.set_trace()

    info_default = {
            'functions': functions,
            'debug': debug,
            }
    arr_node = collections.deque()
    arr_node.append(tree_tpl)
    while arr_node:
        node = arr_node.popleft()
        if hasattr(node, 'wp_info') and node.wp_info:
            node.wp_info.update({
                    'functions': functions,
                    'debug': debug,
                    })
            if node.name == 'texts-and-nuggets':
                _init_texts_and_nuggets(node, info_default)
            else:
                _init_tag(node, info_default, arr_node)

        if _boolean_children_nugget(node):
            # 下级节点中，有<wp-nugget>节点
            _init_children_nugget(node, info_default)

        if hasattr(node, 'contents'):
            # 下级节点
            arr_node.extendleft(reversed(node.contents))


def _init_tag(node, info_default, arr_node):
    if node.wp_info['debug']:
        s = '\n{}\n_init_tag(): ...\n\tnode: {}'
        print(s.format('-' * 16, utils.node_to_json(node)))

    if node.wp_info is None or 'wp-ignore' in node.wp_info['params']:
        return

    params = node.wp_info['params']

    if 'wp-function' in params and 'wp-name' not in params:
        params['wp-name'] = params['wp-function']

    if 'wp-function-attrs' in params and 'wp-name-attrs' not in params:
        params['wp-name-attrs'] = params['wp-function-attrs']

    if 'wp-name-attrs' in params:
        params['wp-ignore-attrs'] = None

    if 'wp-ignore-content' in params:
        if 'wp-leaf' in params:
            params.pop('wp-leaf')

        ignore = bs4.Tag(name='wp-ignore')
        ignore.wp_info = {'params': {'wp-ignore': None}}
        ignore.wp_info.update(info_default)
        node.clear()
        node.append(ignore)
        return

    if 'wp-leaf' in params or not hasattr(node, 'children'):
        return

    text_flags = tuple((
            _boolean_text_or_nugget(child)
            for child in node.children
            ))

    grandchildren, node.contents, arr = [], [], node.contents
    for i, child in enumerate(arr):
        child.parent = None
        if hasattr(child, 'wp_info'):
            child.wp_info.update(info_default)
        if text_flags[i]:
            # NavigableString or wp-nugget
            grandchildren.append(child)
        else:
            if grandchildren:
                new_node = _process_grandchildren(node, grandchildren)
                arr.node.appendleft(new_node)
                grandchildren = []
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
    if node.wp_info['debug']:
        s = '\n{}\n_process_grandchildren(): ...\n\tnode: {}\n\tarr: {}'
        print(s.format('-' * 16, utils.serialize(node), arr))

    new_node = bs4.Tag(name='texts-and-nuggets')
    new_node.contents = arr
    node.append(new_node)
    for child in arr:
        child.parent = new_node
    return new_node


def _init_texts_and_nuggets(node, info_default):
    'init texts-and-nuggets'
    if info_default['debug']:
        s = '\n{}\n_init_texts_and_nuggets(): ...\nnode: {}'
        print(s.format('-' * 16, utils.serialize(node)))

    if len(node.children) == 1:
        child = node.contents[0]
        if isinstance(child, bs4.NavigableString):
            self.content = child['content']
        else:
            assert(child.name == 'wp-nugget')
        return

    node.wp_info = {
            'regex': '',
            'names': [],
            'fuctions': [],
            'debug': info_default['debug'],
            }

    if info_default['debug']:
        print('\n\tnode.wp_info["regex"]: "{}"'.format(node.wp_info['regex']))

    expected_type = node.contents[0].__class__
    for child in node.contents:
        if child.__class__ != expected_type:
            raise NodetypeError('Unexpected nodetype.')

        elif isinstance(child, bs4.NavigableString):
            node.wp_info['regex'] += re.escape(child.string)
            expected_type = bs4.Tag

        elif isinstance(child, bs4.Tag):
            node.wp_info['regex'] += '(.*)'
            name = child.wp_info['params']['wp-name']
            node.wp_info['names'].append(name)
            if 'wp-function' in child.wp_info['params']:
                function = child.wp_info['params']['wp-function']
            else:
                function = None
            node.wp_info['functions'].append(function)
            expected_type = bs4.NavigableString

        else:
            raise NodetypeError('Unexpected nodetype.')

        if info_default['debug']:
            print('\n\tnode.wp_info["regex"]: "{}"'.format(node.wp_info['regex']))
