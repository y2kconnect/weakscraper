# -*- coding: utf-8 -*-
''' 直接使用bs4建立的DOM树，并且使用递归进行遍历。
    参考:
        原template.py
        template_Template.py
        template_2.py

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


SEP = '-' * 16


def init_tpl(root_tpl, functions=None, debug=False):
    '遍历模板DOM树'
    if debug:
        s = '\n{SEP}\ninit_tpl(): ...\n\troot_tpl: {root_tpl}\n\t' \
                'functions: {functions}\n\tdebug: {debug}'.format(
                SEP=SEP, root_tpl=utils.serialize(root_tpl),
                functions=functions, debug=debug,
                )
        print(s)

    info_default = {
            'functions': functions,
            'debug': debug,
            }
    arr_node = []
    arr_node.append(root_tpl)

    while arr_node:
        node = arr_node.pop()

        if debug:
            print('node: {}\n\tnode.name: {}'.format(node,
                    None if hasattr(node, 'name') else node.name))

        if hasattr(node, 'name') and node.name == 'texts-and-nuggets':
            # 处理 texts-and-nuggets
            _init_texts_and_nuggets(node, info_default)
        else:
            _init_tag(node, info_default)

        if hasattr(node, 'contents'):
            # 下级节点
            arr_node.extend(reversed(node.contents))
        if debug:
            print('node: {}'.format(utils.node_to_json(node)))


def _init_tag(node, info_default):
    if info_default['debug']:
        s = '\n{SEP}\n_init_tag(): ...\n\tnode: {node}\n\tinfo_default: ' \
                '{info_default}'.format(
                SEP=SEP, node=utils.node_to_json(node),
                info_default=info_default,
                )
        print(s)

    if isinstance(node, bs4.NavigableString):
        return

    tag = node.name

    if tag == 'wp-ignore':
        return

    if 'wp_info' in node and 'params' in node['wp_info']:
        params = node.wp_info['params']

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

            new_node = bs.Tag(name='wp-ignore', parent=node)
            new_node.wp_info = {
                    'params': {},
                    'functions': functions,
                    'debug': debug,
                    }
            node.contents = [new_node]
            return

        if 'wp-leaf' in params:
            assert len(node.contents) == 0
            return

    # check node.children: text or wp-nugget
    text_flags = _check_text_flag(node, info_default)

    arr_children = []
    grandchildren = []

    for i, child in enumerate(node.contents):
        if text_flags[i]:
            # text or wp-nugget
            grandchildren.append(child)
        else:
            # other
            if grandchildren:
                _process_grandchildren(arr_children, grandchildren,
                        info_default)
            arr_children.append(child)
    if grandchildren:
        _process_grandchildren(arr_children, grandchildren, info_default)

    if arr_children:
        node.contents = arr_children
        for child in node.contents:
            child.parent = node


def _check_text_flag(node, info_default):
    'check node.children: text or wp-nugget'
    if info_default['debug']:
        s = '\n{SEP}\n_check_text_flag(): ...\n\tnode: {node}'.format(
                SEP=SEP, node=utils.node_to_json(node),
                )
        print(s)

    arr = [
            True if (
                    isinstance(child, bs4.NavigableString)
                    or child.name == 'wp-nugget'
                    ) else False
            for child in node.contents
            ]

    if info_default['debug']:
        print('\n\tarr: {}'.format(arr))
    return arr


def _boolean_text_or_nugget(node):
    '节点是 NavigableString or wp-nugget'
    flag = isinstance(node, bs4.NavigableString) \
            or isinstance(node, bs4.Tag) and node.name == 'wp-nugget'
    return flag


def _process_grandchildren(arr_children, grandchildren, info_default):
    'NavigableString or wp-nugget --> texts-and-nuggets'
    if info_default['debug']:
        s = '\n{SEP}\n_process_grandchildren(): ...\n\tarr_children: ' \
                '{arr_children}\n\tgrandchildren: {grandchildren}\n\t' \
                'info_default: {info_default}'.format(
                SEP=SEP, arr_children=arr_children,
                grandchildren=grandchildren, info_default=info_default,
                )
        print(s)

    new_node = bs4.Tag(name='texts-and-nuggets')
    new_node.wp_info = {'params': {}}
    new_node.contents = grandchildren[:]
    for child in new_node.contents:
        child.parent = new_node

    arr_children.append(new_node)
    grandchildren.clear()

    return new_node


def _init_texts_and_nuggets(node, info_default):
    'init texts-and-nuggets'
    if info_default['debug']:
        s = '\n{SEP}\n_init_texts_and_nuggets(): ...\n\tnode: {node}\n\t' \
                'info_default: {info_default}'.format(
                SEP=SEP, node=utils.serialize(node), info_default=info_default,
                )
        print(s)

    if len(node.contents) == 1:
        # 单个子节点
        child = node.contents[0]
        if isinstance(child, bs4.NavigableString):
            # 纯文本，用child替换node节点
            root = node.parent
            i = root.contents.index(node)
            root.contents[i] = child
            child.parent = root

        elif isinstance(child, bs4.Tag):
            # 文本嵌套
            assert child.name == 'wp-nugget'

            node.name = 'nugget'
            node.wp_info['params'] = child.wp_info['params']

        else:
            # 其它
            raise NodetypeError('Unexpected nodetype.')
        return

    node.wp_info = {
            'regex': '',
            'names': [],
            'functions': [],
            'debug': info_default['debug'],
            }

    if info_default['debug']:
        print('\n\tnode.wp_info["regex"]: "{}"'.format(node.wp_info['regex']))

    expected_type = node.contents[0].__class__
    for child in node.contents:
        if child.__class__ != expected_type:
            raise NodetypeError('Unexpected nodetype.')

        elif isinstance(child, bs4.NavigableString):
            msg = child.string.strip(' \t\n\r')
            node.wp_info['regex'] += re.escape(msg)
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

    node.contents = []
