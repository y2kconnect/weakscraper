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
import re
import pdb

# our apps
from . utils import serialize, node_to_json
from .exceptions import (
        NodetypeError, TextError, TagError, TextExpectedError,
        NonAtomicChildError,
        )


SEP = '-' * 16


# class Template:
#     node_tpl = None
#     node_html = None
#     info_default = None
# 
#     def to_json(self):
#         ret = {
#                 'node_tpl': None if self.node_tpl is None else \
#                         serialize(self.node_tpl),
#                 'node_html': None if self.node_html is None else \
#                         serialize(self.node_html),
#                 'info_default': self.info_default,
#                 }
#         return ret


def init_tpl(root_tpl, functions=None, debug=False):
    '遍历模板DOM树'
    if debug:
        s = '\n{SEP}\ninit_tpl(): ...\n\troot_tpl: {root_tpl}\n\t' \
                'functions: {functions}\n\tdebug: {debug}'.format(
                SEP=SEP, root_tpl=serialize(root_tpl),
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
            print('node: {}'.format(node_to_json(node)))


def _init_tag(node, info_default):
    if info_default['debug']:
        s = '\n{SEP}\n_init_tag(): ...\n\tnode: {node}\n\tinfo_default: ' \
                '{info_default}'.format(
                SEP=SEP, node=node_to_json(node),
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

            new_node = bs4.Tag(name='wp-ignore', parent=node)
            new_node.wp_info = {
                    'params': {},
                    'functions': info_default['functions'],
                    'debug': info_default['debug'],
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
                SEP=SEP, node=node_to_json(node),
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
    new_node.wp_info.update(info_default)
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
                SEP=SEP, node=serialize(node), info_default=info_default,
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
            node.wp_info = {
                    'params': child.wp_info['params'],
                    **info_default,
                    }

        else:
            # 其它
            raise ValueError('Unexpected nodetype.')
        return

    node.wp_info = {
            'params': {
                    'regex': '',
                    'names': [],
                    'functions': [],
                    },
            **info_default,
            }
    params = node.wp_info['params']

    if info_default['debug']:
        s = '\n\tparams["regex"]: "{}"'.format(params['regex'])
        print(s)


    expected_type = node.contents[0].__class__
    for child in node.contents:
        if child.__class__ != expected_type:
            raise ValueError('Unexpected nodetype.')

        elif isinstance(child, bs4.NavigableString):
            msg = str(child.string).strip(' \t\n\r')
            params['regex'] += re.escape(msg)

            expected_type = bs4.Tag

        elif isinstance(child, bs4.Tag):
            params['regex'] += '(.*)'

            name = child.wp_info['params']['wp-name']
            params['names'].append(name)

            if 'wp-function' in child.wp_info['params']:
                function = child.wp_info['params']['wp-function']
            else:
                function = None
            params['functions'].append(function)

            expected_type = bs4.NavigableString

        else:
            raise ValueError('Unexpected nodetype.')

        if info_default['debug']:
            s = '\n\tparams["regex"]: "{}"'.format(params['regex'])
            print(s)

    node.contents = []


def compare(node_tpl, node_html, debug=False):
    if debug:
        s = '\n{SEP}\ncompare(): ...\n\tnode_tpl: {node_tpl}\n\tnode_html: ' \
                '{node_html}\n\tdebug: {debug}'.format(SEP=SEP,
                node_tpl=node_tpl, node_html=node_html, debug=debug)
        print(s)

    results = {}

    if debug:
        s = 'node_tpl: {node_tpl}\n\tnode_tpl.name: {name_node_tpl}\n' \
                'node_html: {node_html}\n\tnode_html.name: {name_node_html}' \
                .format(
                        node_tpl=serialize(node_tpl),
                        name_node_tpl=None if hasattr(node_tpl, 'name') \
                                else node_tpl.name,
                        node_html=serialize(node_html),
                        name_node_html=None if hasattr(node_html, 'name') \
                                else node_html.name,
                        )
        print(s)

    if isinstance(node_tpl, bs4.NavigableString):
        _compare__text(node_tpl, node_html, debug)
    elif isinstance(node_tpl, bs4.Tag) and node_tpl.name == 'nugget':
        _compare__nugget(node_tpl, node_html, results, debug)
    elif isinstance(node_tpl, bs4.Tag) and node_tpl.name == 'texts-and-nuggets':
        _compare__texts_and_nuggets(node_tpl, node_html, results, debug)
    else:
        _compare__other(node_tpl, node_html, results, debug)

    if debug:
        print('\n\tresults: {}'.format(results))
    return results


def _compare__text(node_tpl, node_html, debug=False):
    ''' node_tpl is bs4.NavigableString
    Ignore, format reorder and the content is inconsistent
    '''
    if debug:
        s = '\n{SEP}\n_compare__text(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html, debug=debug,
                )
        print(s)

    if not isinstance(node_html, bs4.NavigableString):
        raise NodetypeError(node_tpl, serialize(node_html))


def _compare__nugget(node_tpl, node_html, results, debug=False):
    'node_tpl.name == "nugget"'
    if debug:
        s = '\n{SEP}\n_compare__nugget(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(SEP=SEP, node_tpl=node_tpl,
                node_html=node_html, results=results, debug=debug)
        print(s)

    content = _f(node_tpl, str(node_html.string), debug)

    k = node_tpl.wp_info['params']['wp-name']
    results[k] = content

    if debug:
        print('\n\tresults: {}'.format(results))


def _f(node_tpl, str_or_list, debug=False):
    if debug:
        s = '\n{SEP}\n_f(): ...\n\tnode_tpl: {node_tpl}\n\tstr_or_list: ' \
                '{str_or_list}\n\tdebug: {debug}'.format(SEP=SEP,
                node_tpl=node_tpl, str_or_list=str_or_list, debug=debug)
        print(s)

    params = node_tpl.wp_info['params']

    if 'wp-function' in params and 'wp-list' not in params:
        k = params['wp-function']
        func = node_tpl.wp_info['functions'][k]
        ret = func(str_or_list)

    else:
        ret = serialize(str_or_list)

    if debug:
        print('\n\tret: {}'.format(ret))

    return ret


def _compare__texts_and_nuggets(node_tpl, node_html, results, debug=False):
    'node_tpl.name == "texts-and-nuggets"'
    if debug:
        s = '\n{SEP}\n_compare__texts_and_nuggets(): ...\n\t' \
                'node_tpl: {node_tpl}\n\tnode_html: {node_html}\n\tresults:' \
                '{results}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html,
                results=results, debug=debug,
                )
        print(s)

    wp_info = node_tpl['wp-info']
    # regex = '^' + wp_info['regex'] + '$'
    regex = wp_info['regex']
    match = re.match(regex, str(node_html.string))
    if match is None:
        raise TextError(node_tpl, serialize(node_html))
    groups = match.groups()

    n = len(groups)
    assert (
            n == len(wp_info['params']['names'])
            and n == len(wp_info['functions'])
            )

    for i in range(n):
        pass
        function_name = wp_info['functions'][i]
        x = groups[i]
        if function_name:
            function = wp_info['functions'][function_name]
            x = function(x)

        k = wp_info['names'][i]
        results[k] = x

    if debug:
        print('\n\tresults: {}'.format(results))


def _compare__other(node_tpl, node_html, results, debug=False):
    if debug:
        s = '\n{SEP}\n_compare__tag(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(SEP=SEP, node_tpl=node_tpl,
                node_html=node_html, results=results, debug=debug)
        print(s)

    if (
            isinstance(node_tpl, bs4.Tag)
            and isinstance(node_html, bs4.Tag)
            and node_tpl.name != node_html.name
            ):
        raise TagError(node_tpl, node_html)

    elif _attrs_match(node_tpl, node_html.attrs, debug):
        # The properties defined in the template do not exist in the HTML
        return

    elif not ('wp_info' in node_tpl and 'params' in node_tpl.wp_info):
        return

    params = node_tpl.wp_info['params']

    if 'wp-name-attrs' in params:
        _tpl__wp_name_attrs(node_tpl, node_html, results, debug)

    if 'wp-leaf' in params:
        _tpl__wp_leaf(node_tpl, node_html, results, debug)
    elif 'contents' in node_html:
        # look at the children, ignore: ('meta', 'img', 'hr', 'br')
        _tpl__children(node_tpl, node_html, results, debug)

    if debug:
        print('\n\tresults: {}'.format(results))


def _attrs_match(node_tpl, attrs_html, debug=False):
    if debug:
        s = '\n{SEP}\n_attrs_match(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'attrs_html: {attrs_html}\n\tdebug: {debug}'.format(SEP=SEP,
                node_tpl=node_tpl, attrs_html=attrs_html, debug=debug)
        print(s)

    params = node_tpl.wp_info['params']
    attrs_tpl = node_tpl.attrs
    ret = True

    if 'wp-ignore-attrs' in params:
        for k, v in attrs_tpl.items():
            if not (k in attrs_html and attrs_html[k] == v):
                ret = False
                break

    elif 'wp-attr-name-dict' in params:
        ret = any([
                True
                for k in params['wp-attr-name-dict']
                    if k in attrs_html
                ])

    else:
        ''' At present, only compare k, not v
            (Format reordering leads to v inconsistencies)
        '''
        ret = attrs_tpl.keys() == attrs_html.keys()

    if debug:
        print('\n\tret: {}'.format(ret))


def _tpl__wp_name_attrs(node_tpl, node_html, results, debug=False):
    'Gets the contents of node_html.attrs'
    if debug:
        s = '\n{SEP}\n_tpl__wp_name_attrs(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(SEP=SEP, node_tpl=node_tpl,
                node_html=node_html, results=results, debug=debug)
        print(s)

    params = node_tpl.wp_info['params']

    content = node_html.attrs
    if 'wp-function-attrs' in params:
        k = params['wp-function-attrs']
        func = node_tpl.wp_info['functions'][k]
        content = func(content)

    k = params['wp-name-attrs']
    results[k] = content

    if debug:
        print('\n\tresults: {}'.format(results))


def _tpl__wp_leaf(node_tpl, node_html, results, debug=False):
    pass
    if debug:
        s = '\n{SEP}\n_tpl__wp_leaf(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(SEP=SEP, node_tpl=node_tpl,
                node_html=node_html, results=results, debug=debug)
        print(s)

    params = node_tpl.wp_info['params']

    if 'wp-recursive-leaf' in params:
        k, arr = _tpl__wp_recursive(node_tpl, node_html, debug)
        if 'wp-recursive-text' in params:
            arr = _get_all_content(node_html, debug)
        results[k] = arr

    elif 'wp-ignore-content' not in params:
        flag = False

        if 'wp-attr-name-dict' in params:
            info = _tpl__attr_name_dict(node_tpl, node_html, debug)
            results.update(info)
            flag = True

        if 'wp-name' in params:
            n = len(node_html.contents)
            if n == 0:
                msg = ''

            elif n == 1:
                html_child = node_html.contents[0]
                if isinstance(html_child, bs4.NavigableString):
                    msg = str(html_child.string)
                else:
                    raise TextExpectedError(node_tpl, html_child)

            else:
                raise NonAtomicChildError(node_tpl, node_html)

            k = params['wp-name']
            results[k] = _f(node_tpl, msg, debug)
            flag = True

        if not flag:
            assert not hasattr(node_html, 'contents')

    if debug:
        print('\n\tresults: {}'.format(results))


def _tpl__wp_recursive(node_tpl, node_html, debug=False):
    if debug:
        s = '\n{SEP}\n_tpl__wp_recursive(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tdebug: {debug}'.format(SEP=SEP,
                node_tpl=node_tpl, node_html=node_html, debug=debug)
        print(s)

    k = node_tpl.wp_info['params']['wp-name']
    arr = _f(node_tpl, node_html.contents, debug)

    if debug:
        s = '\n{SEP}\n\tk: {k}\n\tarr: {arr}'.format(SEP=SEP, k=k, arr=arr)
        print(s)

    return (k, arr)


def _get_all_content(node_html, debug=False):
    'wp-recursive-text: get all the text'
    if debug:
        s = '\n{SEP}\n_get_all_content(): ...\n\tnode_html: {node_html}\n\t' \
                'debug: {debug}'.format(SEP=SEP, node_html=node_html,
                debug=debug)
        print(s)

    arr = [
            str(x)
            for x in node_html.descendants
                if isinstance(x, bs4.NavigableString)
            ]

    if debug:
        s = '\n{SEP}\n\tarr: {arr}'.format(SEP=SEP, arr=arr)
        print(s)

    return arr


def _tpl__attr_name_dict(node_tpl, node_html, debug=False):
    if debug:
        s = '\n{SEP}\n_tpl__attr_name_dict(): ...\n\tnode_tpl: {node_tpl}' \
                '\n\tnode_html: {node_html}\n\tdebug: {debug}'.format(SEP=SEP,
                node_tpl=node_tpl, node_html=node_html, debug=debug)
        print(s)

    attrs_html = node_html.attrs
    info = {
            key: attrs_html[name]
            for (name, key) in self.params['wp-attr-name-dict'].items()
                if name in attrs_html
            }

    if debug:
        s = '\n{SEP}\n\tinfo: {info}'.format(SEP=SEP, info=info)
        print(s)

    return info


def _tpl__children(node_tpl, node_html, results, debug=False):
    'traversal tag children of template'
    pass
