# -*- coding: utf-8 -*-
''' 直接使用bs4建立的DOM树，并且使用递归进行遍历。
    node.wp_info        dict类型。记录模板节点的标记信息。
        params              模板节点的标记
        functions           处理的函数信息
        regex               正则表达式对象
        debug               显示调试的标志
'''

# python apps
import bs4
import re

# our apps
from . utils import serialize, node_to_json
from .exceptions import (
        CompareError,
        NonAtomicChildError, NodetypeError,
        TagError, TextError, TextExpectedError,
        )


DEBUG_INIT_TPL = False
DEBUG_COMPARE = True
SEP = '-' * 16
CHARACTERS_REMOVED = ' \t\n\r'


def init_tpl(root_tpl, functions=None, debug=False):
    '遍历模板DOM树'
    if debug and DEBUG_INIT_TPL:
        s = '\n{SEP}\ninit_tpl(): ...\n\troot_tpl: {root_tpl}\n\t' \
                'functions: {functions}\n\tdebug: {debug}'.format(
                SEP=SEP, root_tpl=serialize(root_tpl), functions=functions,
                debug=debug,
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

        if debug and DEBUG_INIT_TPL:
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
        if debug and DEBUG_INIT_TPL:
            print('node: {}'.format(node_to_json(node)))


def _init_tag(node, info_default):
    if info_default['debug'] and DEBUG_INIT_TPL:
        s = '\n{SEP}\n_init_tag(): ...\n\tnode: {node}\n\tinfo_default: ' \
                '{info_default}'.format(
                SEP=SEP, node=node_to_json(node), info_default=info_default,
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
    if info_default['debug'] and DEBUG_INIT_TPL:
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

    if info_default['debug'] and DEBUG_INIT_TPL:
        print('\n\tarr: {}'.format(arr))
    return arr


def _boolean_text_or_nugget(node):
    '节点是 NavigableString or wp-nugget'
    flag = isinstance(node, bs4.NavigableString) \
            or isinstance(node, bs4.Tag) and node.name == 'wp-nugget'
    return flag


def _process_grandchildren(arr_children, grandchildren, info_default):
    'NavigableString or wp-nugget --> texts-and-nuggets'
    if info_default['debug'] and DEBUG_INIT_TPL:
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
    if info_default['debug'] and DEBUG_INIT_TPL:
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

            node.name = 'wp-nugget'
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

    if info_default['debug'] and DEBUG_INIT_TPL:
        s = '\n\tparams["regex"]: "{}"'.format(params['regex'])
        print(s)


    expected_type = node.contents[0].__class__
    for child in node.contents:
        if child.__class__ != expected_type:
            raise ValueError('Unexpected nodetype.')

        elif isinstance(child, bs4.NavigableString):
            msg = child.string.strip(CHARACTERS_REMOVED)
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

        if info_default['debug'] and DEBUG_INIT_TPL:
            s = '\n\tparams["regex"]: "{}"'.format(params['regex'])
            print(s)

    node.contents = []


def compare(node_tpl, node_html, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\ncompare(): ...\n\tnode_tpl: {node_tpl}\n\tnode_html: ' \
                '{node_html}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html, debug=debug,
                )
        print(s)

    results = {}

    if isinstance(node_tpl, bs4.NavigableString):
        _compare__text(node_tpl, node_html, debug)
    elif isinstance(node_tpl, bs4.Tag) and node_tpl.name == 'wp-nugget':
        _compare__nugget(node_tpl, node_html, results, debug)
    elif isinstance(node_tpl, bs4.Tag) and node_tpl.name == 'texts-and-nuggets':
        _compare__texts_and_nuggets(node_tpl, node_html, results, debug)
    else:
        _compare__other(node_tpl, node_html, results, debug)

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))
    return results


def _compare__text(node_tpl, node_html, debug=False):
    ''' node_tpl is bs4.NavigableString
    Ignore, format reorder and the content is inconsistent
    '''
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_compare__text(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html, debug=debug,
                )
        print(s)

    if not isinstance(node_html, bs4.NavigableString):
        raise NodetypeError(node_tpl, serialize(node_html))


def _compare__nugget(node_tpl, node_html, results, debug=False):
    'node_tpl.name == "nugget"'
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_compare__nugget(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html,
                results=results, debug=debug,
                )
        print(s)

    content = _f(node_tpl, str(node_html.string), debug)

    k = node_tpl.wp_info['params']['wp-name']
    results[k] = content

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))


def _f(node_tpl, str_or_list, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_f(): ...\n\tnode_tpl: {node_tpl}\n\tstr_or_list: ' \
                '{str_or_list}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, str_or_list=str_or_list,
                debug=debug,
                )
        print(s)

    params = node_tpl.wp_info['params']

    if 'wp-function' in params and 'wp-list' not in params:
        k = params['wp-function']
        func = node_tpl.wp_info['functions'][k]
        ret = func(str_or_list)

    else:
        ret = serialize(str_or_list)

    if debug and DEBUG_COMPARE:
        print('\n\tret: {}'.format(ret))

    return ret


def _compare__texts_and_nuggets(node_tpl, node_html, results, debug=False):
    'node_tpl.name == "texts-and-nuggets"'
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_compare__texts_and_nuggets(): ...\n\t' \
                'node_tpl: {node_tpl}\n\tnode_html: {node_html}\n\tresults:' \
                '{results}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html,
                results=results, debug=debug,
                )
        print(s)

    params = node_tpl.wp_info['params']

    regex = '^' + params['regex'] + '$'
    match = re.match(regex, str(node_html.string))
    if match is None:
        raise TextError(node_tpl, serialize(node_html))
    arr = match.groups()

    n = len(arr)
    assert n == len(params['names']) == len(params['functions'])

    for i in range(n):
        x = arr[i].strip(CHARACTERS_REMOVED)
        k = params['functions'][i]
        if k:
            func = params['functions'][k]
            x = func(x)

        k = params['names'][i]
        results[k] = x

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))


def _compare__other(node_tpl, node_html, results, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_compare__tag(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html,
                results=results, debug=debug,
                )
        print(s)

    if not isinstance(node_html, bs4.Tag):
        raise NodetypeError(node_tpl, node_html)
    elif node_tpl.name != node_html.name:
        raise TagError(node_tpl, node_html)
    elif not _attrs_match(node_tpl, node_html.attrs, debug):
        # The properties defined in the template do not exist in the HTML
        return

    if node_tpl.wp_info is None and node_tpl.contents:
        _tpl__children(node_tpl, node_html, results, debug)
    else:
        params = node_tpl.wp_info['params']

        if 'wp-name-attrs' in params:
            _tpl__wp_name_attrs(node_tpl, node_html, results, debug)

        if ('wp_info' in node_tpl and 'params' in node_tpl.wp_info):
            _tpl__children(node_tpl, node_html, results, debug)
        elif node_html.contents:
            _tpl__children(node_tpl, node_html, results, debug)

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))


def _compare__other_2(node_tpl, node_html, results, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_compare__tag(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html,
                results=results, debug=debug,
                )
        print(s)

    if (
            isinstance(node_tpl, bs4.Tag)
            and isinstance(node_html, bs4.Tag)
            and node_tpl.name != node_html.name
            ):
        raise TagError(node_tpl, node_html)

    elif isinstance(node_tpl, bs4.BeautifulSoup):
        _tpl__children(node_tpl, node_html, results, debug)

    else:
        if not _attrs_match(node_tpl, node_html.attrs, debug):
            # The properties defined in the template do not exist in the HTML
            return

        elif ('wp_info' in node_tpl and 'params' in node_tpl.wp_info):
            _tpl__children(node_tpl, node_html, results, debug)

        else:
            params = node_tpl.wp_info['params']

            if 'wp-name-attrs' in params:
                _tpl__wp_name_attrs(node_tpl, node_html, results, debug)

            if 'wp-leaf' in params:
                _tpl__wp_leaf(node_tpl, node_html, results, debug)
            elif 'contents' in node_html:
                # look at the children, ignore: ('meta', 'img', 'hr', 'br')
                _tpl__children(node_tpl, node_html, results, debug)

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))


def _attrs_match(node_tpl, attrs_html, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_attrs_match(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'attrs_html: {attrs_html}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, attrs_html=attrs_html, debug=debug,
                )
        print(s)

    attrs_tpl = node_tpl.attrs

    if isinstance(node_tpl, bs4.NavigableString) or not node_tpl.wp_info:
        ret = attrs_tpl.keys() == attrs_html.keys()
    else:
        params = node_tpl.wp_info['params']
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

    if debug and DEBUG_COMPARE:
        print('\n\tret: {}'.format(ret))

    return ret

def _tpl__wp_name_attrs(node_tpl, node_html, results, debug=False):
    'Gets the contents of node_html.attrs'
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_tpl__wp_name_attrs(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html,
                results=results, debug=debug,
                )
        print(s)

    params = node_tpl.wp_info['params']

    content = node_html.attrs
    if 'wp-function-attrs' in params:
        k = params['wp-function-attrs']
        func = node_tpl.wp_info['functions'][k]
        content = func(content)

    k = params['wp-name-attrs']
    results[k] = content

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))


def _tpl__wp_leaf(node_tpl, node_html, results, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_tpl__wp_leaf(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\tdebug: ' \
                '{debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html,
                results=results, debug=debug,
                )
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

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))


def _tpl__wp_recursive(node_tpl, node_html, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_tpl__wp_recursive(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html, debug=debug,
                )
        print(s)

    k = node_tpl.wp_info['params']['wp-name']
    arr = _f(node_tpl, node_html.contents, debug)

    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n\tk: {k}\n\tarr: {arr}'.format(SEP=SEP, k=k, arr=arr)
        print(s)

    return (k, arr)


def _get_all_content(node_html, debug=False):
    'wp-recursive-text: get all the text'
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_get_all_content(): ...\n\tnode_html: {node_html}\n\t' \
                'debug: {debug}'.format(
                SEP=SEP, node_html=node_html, debug=debug,
                )
        print(s)

    arr = [
            str(x)
            for x in node_html.descendants
                if isinstance(x, bs4.NavigableString)
            ]

    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n\tarr: {arr}'.format(SEP=SEP, arr=arr)
        print(s)

    return arr


def _tpl__attr_name_dict(node_tpl, node_html, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_tpl__attr_name_dict(): ...\n\tnode_tpl: {node_tpl}' \
                '\n\tnode_html: {node_html}\n\tdebug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html, debug=debug,
                )
        print(s)

    attrs_html = node_html.attrs
    info = {
            key: attrs_html[name]
            for (name, key) in \
                    node_tpl.wp_info['params']['wp-attr-name-dict'].items()
                if name in attrs_html
            }

    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n\tinfo: {info}'.format(SEP=SEP, info=info)
        print(s)

    return info


def _tpl__children(node_tpl, node_html, results, debug=False):
    'traversal tag children of template'
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_tpl__children(): ...\n\tnode_tpl: {node_tpl}\n\t' \
                'node_html: {node_html}\n\tresults: {results}\n\t' \
                'debug: {debug}'.format(
                SEP=SEP, node_tpl=node_tpl, node_html=node_html,
                results=results, debug=debug,
                )
        print(s)

    children_results = {}
    arr_html_children = node_html.contents

    html_i, html_n = (0, len(arr_html_children))
    for tpl_child in node_tpl.contents:
        if html_n <= html_i:
            # Ignore, html_tree node does not exist
            break
        html_i = _html_children_skip(arr_html_children, html_i, html_n, debug)

        if isinstance(tpl_child, bs4.NavigableString):
            _compare_wrapper(tpl_child, arr_html_children[html_i], debug)
            html_i += 1

        elif tpl_child.name == 'ignore':
            if 'wp-until' in tpl_child.wp_info['params']:
                html_i = _html_children_until(
                        tpl_child, arr_html_children, html_i, html_n, debug,
                        )
            else:
                html_i = html_n

        elif tpl_child.wp_info and 'wp-list' in tpl_child.wp_info['params']:
            html_i, children_results = _html_children_wp_list(
                    tpl_child, arr_html_children, html_i, html_n,
                    children_results, debug,
                    )

        else:
            i = _html_children_other(
                tpl_child, arr_html_children[html_i], children_results, debug,
                )
            html_i += i
    html_i = _html_children_skip(arr_html_children, html_i, html_n, debug)

    if html_i != html_n:
        raise ExcessNodeError(node_tpl, arr_html_children[html_i])

    if node_tpl.wp_info and 'wp-name' in node_tpl.wp_info['params']:
        name = node_tpl.wp_info['params']['wp-name']
        results[name] = _f(node_tpl, children_results)
    else:
        for k, v in children_results.items():
            if k in results:
                raise ValueError('Key already defined.')
            results[k] = v

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))


def _html_children_skip(arr, i, n, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_html_children_skip(): ...\n\tarr: {arr}\n\ti: {i}' \
                '\n\tn: {n}\n\tdebug: {debug}'.format(
                SEP=SEP, arr=arr, i=i, n=n, debug=debug,
                )
        print(s)

    while i < n and isinstance(arr[i], bs4.Tag) and arr[i].name == 'script':
        i += 1

    if debug and DEBUG_COMPARE:
        print('\n\ti: {}'.format(i))

    return i


def _compare_wrapper(tpl_child, node_html, debug=False):
    'tpl_child is bs4.NavigableString'
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_compare_wrapper(): ...\n\ttpl_child: {tpl_child}\n\t' \
                'node_html: {node_html}\n\tdebug: {debug}'.format(
                SEP=SEP, tpl_child=tpl_child, node_html=node_html, debug=debug,
                )
        print(s)

    try:
        results = compare(tpl_child, node_html, debug)
    except CompareError as e:
        e.register_parent(tpl_child)
        raise e

    if debug and DEBUG_COMPARE:
        print('\n\tresults: {}'.format(results))

    return results


def _html_children_until(tpl_child, arr_html, i, n, debug=False):
    ''' tpl_child is not bs4.NavigableString
        and "wp-until" in tpl_child.wp_info["params"]
    '''
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_html_children_until(): ...\n\ttpl_child: {tpl_child}' \
                '\n\tarr_html: {arr_html}\n\ti: {i}\n\tn: {n}\n\tdebug: ' \
                '{debug}'.format(
                SEP=SEP, tpl_child=tpl_child, arr_html=arr_html, i=i, n=n,
                debug=debug,
                )
        print(s)

    until = tpl_child.wp_info['params']['wp-until']

    while (
            i < n
            and not isinstance(arr_html[i], bs4.NavigableString)
            and arr_html[i].name == until
            ):
        i += 1

    if debug and DEBUG_COMPARE:
        print('\n\ti: {}'.format(i))

    return i


def _html_children_wp_list(
        tpl_child, arr_html, html_i, html_n, children_results, debug=False,
        ):
    ''' tpl_child is not bs4.NavigableString
        and "wp-list" in tpl_child.wp_arr_html["params"]
    '''
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_html_children_wp_list(): ...\n\ttpl_child: ' \
                '{tpl_child}\n\tarr_html: {arr_html}\n\thtml_i: {html_i}\n\t' \
                'html_n: {html_n}\n\tchildren_results: {children_results}' \
                '\n\tdebug: {debug}'.format(
                SEP=SEP, tpl_child=tpl_child, arr_html=arr_html,
                html_i=html_i, html_n=html_n,
                children_results=children_results, debug=debug,
                )
        print(s)

    i = html_i
    params = tpl_child.wp_info['params']

    arr = []
    for i in range(html_i, html_n):
        if _check_flag(tpl_child, arr_html[i], debug):
            x = _compare_wrapper(tpl_child, arr_html[i], debug)
            arr.append(x)
        else:
            break

    if arr and 'wp-function' in params:
        k = params['wp-function']
        func = tpl_child.wp_info['functions'][k]
        arr = func(arr)

    k = params['wp-name']
    children_results[k] = arr

    if debug and DEBUG_COMPARE:
        print('\n\ti: {}\n\tchildren_results: {}'.format(i, children_results))

    return (i, children_results)


def _check_flag(tpl_child, node_html, debug=False):
    if debug and DEBUG_COMPARE:
        s = '\n{SEP}\n_check_flag(): ...\n\ttpl_child: {tpl_child}\n\t' \
                'node_html: {node_html}\n\tdebug: {debug}'.format(
                SEP=SEP, tpl_child=tpl_child, node_html=node_html, debug=debug,
                )
        print(s)

    flag = (
            not isinstance(node_html, bs4.NavigableString)
            and node_html.name == tpl_child.name
            and _attrs_match(tpl_child, node_html.attrs)
            )

    if debug and DEBUG_COMPARE:
        print('\n\tflag: {}'.format(flag))

    return flag


def _html_children_other(tpl_child, node_html, children_results, debug=False):
    ''' current status:
        not (
                tpl_child is bs4.NavigableString
                and tpl_child.name == "wp-ignore"
                and "wp-list" in tpl_child.wp_arr_html["params"]
                )
    '''
    if debug and DEBUG_COMPARE:
        s = (
                '\n{SEP}'
                '\n_html_children_other(): ...'
                '\n\ttpl_child: {tpl_child}'
                '\n\tnode_html: {node_html}'
                '\n\tchildren_results: {children_results}'
                '\n\tdebug: {debug}'
                ).format(
                SEP=SEP, tpl_child=tpl_child, node_html=node_html,
                children_results=children_results, debug=debug,
                )
        print(s)

    i = 0
    if (
            tpl_child.name in ('wp-nugget', 'texts-and-nuggets')
            or tpl_child.wp_info
            and 'wp-optional' not in tpl_child.wp_info['params']
            or _check_flag(tpl_child, node_html, debug)
            ):
        result = _compare_wrapper(tpl_child, node_html, debug)
        for k, v in result.items():
            if k in children_results:
                raise ValueError('Key already defined.')
            else:
                children_results[k] = v
        i += 1

    if debug and DEBUG_COMPARE:
        print('\n\ti: {}'.format(i))

    return i
    '''
    self_child.nodetype in ['nugget', 'texts-and-nuggets', 'tag']
    and not (
            (self_child.nodetype == 'tag') and
            ('wp-optional' in self_child.params) and
            (
                (html_position >= html_n_children) or
                (html['children'][html_position]['nodetype'] != 'tag') or
                (not self_child.attrs_match(html['children'][html_position]['attrs'])) or
                (html['children'][html_position]['name'] != self_child.name)
            )

    -->
    self_child.nodetype in ['nugget', 'texts-and-nuggets', 'tag']
    and (
            self_child.nodetype != 'tag'
            or 'wp-optional' not in self_child.params
            or (
                    html_position < html_n_children
                    and html['children'][html_position]['nodetype'] == 'tag'
                    and html['children'][html_position]['name'] == self_child.name
                    and self_child.attrs_match(html['children'][html_position]['attrs'])
                    )
            )
    '''

