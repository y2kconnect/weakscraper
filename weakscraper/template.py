# -*- coding: utf-8 -*-
''' 直接使用bs4建立的DOM树，并且使用递归进行遍历。
    node.wp_info        dict类型。记录模板节点的标记信息。
        params              模板节点的标记
        functions           处理的函数信息
'''

# python apps
import bs4
import re

# our apps
from . utils import serialize, node_to_json
from .exceptions import (
        AttrsError,
        CompareError, ExcessNodeError,
        NonAtomicChildError, NodetypeError,
        TagError, TextError, TextExpectedError,
        )


def init_tpl(root_tpl, functions=None, logger=None):
    '遍历模板DOM树'
    SEP = 'init_tpl() --> '
    if logger:
        s = '{SEP}root_tpl: {root_tpl}, functions: {functions}'.format(
                SEP=SEP, functions=functions, root_tpl=serialize(root_tpl),
                )
        logger.info(s)

    info_default = {'functions': functions}
    arr_node = []
    arr_node.append(root_tpl)

    while arr_node:
        node = arr_node.pop()

        if logger:
            s = '{SEP}node: {node}\n\tnode.name: {name}'.format(
                    SEP=SEP,
                    node=node,
                    name=None if hasattr(node, 'name') else node.name,
                    )
            logger.info(s)

        if hasattr(node, 'name') and node.name == 'texts-and-nuggets':
            # 处理 texts-and-nuggets
            _init_texts_and_nuggets(node, info_default, logger)
        else:
            _init_tag(node, info_default, logger)

        if hasattr(node, 'contents'):
            # 下级节点
            arr_node.extend(reversed(node.contents))

        if logger:
            s = '{SEP}node: {node}'.format(SEP=SEP, node=node_to_json(node))
            logger.info(s)


def _init_tag(node, info_default, logger=None):
    SEP = '_init_tag() --> '
    if logger:
        s = '{SEP}node: {node}, info_default: {info_default}'.format(
                SEP=SEP, info_default=info_default,
                node=node_to_json(node, ['name', 'attrs', 'wp_info']),
                )
        logger.info(s)

    if isinstance(node, bs4.NavigableString):
        return

    if getattr(node, 'wp_info', None):
        node.wp_info.update(info_default)

    tag = node.name

    if tag == 'wp-ignore':
        return

    if getattr(node, 'wp_info', None) and 'params' in node.wp_info:
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
            new_node.wp_info = {'params': {}}
            new_node.wp_info.update(info_default)
            node.contents = [new_node]
            return

        if 'wp-leaf' in params:
            assert len(node.contents) == 0
            return

    # check node.children: text or wp-nugget
    text_flags = _check_text_flag(node, info_default, logger)

    arr_children = []
    grandchildren = []

    for i, child in enumerate(node.contents):
        if text_flags[i]:
            # text or wp-nugget
            grandchildren.append(child)
        else:
            # other
            if grandchildren:
                _process_grandchildren(
                        arr_children, grandchildren, info_default, logger,
                        )
            arr_children.append(child)
    if grandchildren:
        _process_grandchildren(
                arr_children, grandchildren, info_default, logger,
                )

    if arr_children:
        node.contents = arr_children
        for child in node.contents:
            child.parent = node


def _check_text_flag(node, info_default, logger=None):
    'check node.children: text or wp-nugget'
    SEP = '_check_text_flag() --> '
    if logger:
        s = '{SEP}node: {node}'.format(
                SEP=SEP,
                node=node_to_json(node, ['name', 'attrs', 'wp_info']),
                )
        logger.info(s)

    arr = [
            True if (
                    isinstance(child, bs4.NavigableString)
                    or child.name == 'wp-nugget'
                    ) else False
            for child in node.contents
            ]

    if logger:
        s = '{SEP}arr: {arr}'.format(SEP=SEP, arr=arr)
        logger.info(s)
    return arr


def _process_grandchildren(
        arr_children, grandchildren, info_default, logger=None,
        ):
    'NavigableString or wp-nugget --> texts-and-nuggets'
    SEP = '_process_grandchildren() --> '
    if logger:
        s = '{SEP}arr_children: {arr_children}, grandchildren: ' \
                '{grandchildren}, info_default: {info_default}'.format(
                SEP=SEP,
                arr_children=arr_children,
                grandchildren=grandchildren,
                info_default=info_default,
                )
        logger.info(s)

    new_node = bs4.Tag(name='texts-and-nuggets')
    new_node.wp_info = {'params': {}}
    new_node.wp_info.update(info_default)
    new_node.contents = grandchildren[:]
    for child in new_node.contents:
        child.parent = new_node

    arr_children.append(new_node)
    grandchildren.clear()

    return new_node


def _init_texts_and_nuggets(node, info_default, logger=None):
    'init texts-and-nuggets'
    SEP = '_init_texts_and_nuggets() --> '
    if logger:
        s = '{SEP}node: {node}, info_default: {info_default}'.format(
                SEP=SEP, node=serialize(node), info_default=info_default,
                )
        logger.info(s)

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

    if logger:
        s = '{SEP}params["regex"]: "{regex}"'.format(
                SEP=SEP, regex=params['regex'],
                )
        logger.info(s)

    expected_type = node.contents[0].__class__
    for child in node.contents:
        if child.__class__ != expected_type:
            raise ValueError('Unexpected nodetype.')

        elif isinstance(child, bs4.NavigableString):
            msg = child.string.strip()
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

        if logger:
            s = '{SEP}params["regex"]: "{regex}"'.format(
                    SEP=SEP, regex=params['regex'],
                    )
            logger.info(s)

    node.contents = []


def compare(node_tpl, node_html, logger=None):
    SEP = 'compare() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)
    results = {}

    if isinstance(node_tpl, bs4.NavigableString):
        _compare__text(node_tpl, node_html, logger)
    elif isinstance(node_tpl, bs4.Tag) and node_tpl.name == 'wp-nugget':
        _compare__nugget(node_tpl, node_html, results, logger)
    elif isinstance(node_tpl, bs4.Tag) and node_tpl.name == 'texts-and-nuggets':
        _compare__texts_and_nuggets(node_tpl, node_html, results, logger)
    else:
        _compare__tag(node_tpl, node_html, results, logger)

    if logger:
        logger.info('{SEP}results: {results}'.format(SEP=SEP, results=results))
    return results


def _compare__text(node_tpl, node_html, logger=None):
    ''' node_tpl is bs4.NavigableString
    Ignore, format reorder and the content is inconsistent
    '''
    SEP = '_compare__text() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)

    if not isinstance(node_html, bs4.NavigableString):
        raise NodetypeError(node_tpl, serialize(node_html))

    # 严格要求字符串一致
    if node_html.string != node_tpl.string:
        raise TextError(node_tpl, node_html)


def _compare__nugget(node_tpl, node_html, results, logger=None):
    'node_tpl.name == "nugget"'
    SEP = '_compare__nugget() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}, results: ' \
                '{results}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                results=results,
                )
        logger.info(s)

    content = _f(node_tpl, str(node_html.string), logger)

    k = node_tpl.wp_info['params']['wp-name']
    results[k] = content

    if logger:
        s = '{SEP}results: {results}'.format(SEP=SEP, results=results)
        logger.info(s)


def _f(node_tpl, obj, logger=None):
    SEP = '_f() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, obj: {obj}'.format(
                SEP=SEP, obj=obj,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                )
        logger.info(s)

    params = node_tpl.wp_info['params']

    ret = obj
    if 'wp-function' in params and 'wp-list' not in params:
        k = params['wp-function']
        func = node_tpl.wp_info['functions'][k]
        ret = func(obj)

    if logger:
        s = '{SEP}ret: {ret}'.format(SEP=SEP, ret=ret)
        logger.info(s)

    return ret


def _compare__texts_and_nuggets(node_tpl, node_html, results, logger=None):
    'node_tpl.name == "texts-and-nuggets"'
    SEP = '_compare__texts_and_nuggets() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}, results: ' \
                '{results}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                results=results,
                )
        logger.info(s)

    params = node_tpl.wp_info['params']

    regex = '^' + params['regex'] + '$'
    match = re.match(regex, str(node_html.string))
    if match is None:
        raise TextError(node_tpl, serialize(node_html))
    arr = match.groups()

    n = len(arr)
    assert n == len(params['names']) == len(params['functions'])

    for i in range(n):
        x = arr[i].strip()
        k = params['functions'][i]
        if k:
            func = params['functions'][k]
            x = func(x)

        k = params['names'][i]
        results[k] = x

    if logger:
        s = '{SEP}results: {results}'.format(SEP=SEP, results=results)
        logger.info(s)


def _compare__tag(node_tpl, node_html, results, logger=None):
    SEP = '_compare__tag() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}, results: ' \
                '{results}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                results=results,
                )
        logger.info(s)

    if node_tpl.name != 'texts-and-nuggets':
        if not isinstance(node_html, bs4.Tag):
            raise NodetypeError(node_tpl, node_html)
        elif node_tpl.name != node_html.name:
            raise TagError(node_tpl, node_html)
        elif not _attrs_match(node_tpl, node_html.attrs, logger):
            # The properties defined in the template do not exist in the HTML
            raise AttrsError(node_tpl, node_html)

    if getattr(node_tpl, 'wp_info', None) is None and node_tpl.contents:
        _tpl__children(node_tpl, node_html, results, logger)

    else:
        params = node_tpl.wp_info['params']

        if 'wp-name-attrs' in params:
            _tpl__wp_name_attrs(node_tpl, node_html, results, logger)

        if 'wp-leaf' in params:
            _tpl__wp_leaf(node_tpl, node_html, results, logger)

        elif node_html.contents:
            _tpl__children(node_tpl, node_html, results, logger)

        elif 'wp-name' in params:
            # node_html没有子节点
            k = params['wp-name']
            results[k] = {}

    if logger:
        s = '{SEP}results: {results}'.format(SEP=SEP, results=results)
        logger.info(s)


def _attrs_match(node_tpl, attrs_html, logger=None):
    SEP = '_attrs_match() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, attrs_html: {attrs_html}'.format(
                SEP=SEP, attrs_html=attrs_html,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                )
        logger.info(s)

    attrs_tpl = node_tpl.attrs

    if (
            isinstance(node_tpl, bs4.NavigableString)
            or getattr(node_tpl, 'wp_info', None) is None
            ):
        ret = attrs_tpl.keys() == attrs_html.keys()
    else:
        params = node_tpl.wp_info['params']
        if 'wp-ignore-attrs' in params:
            for k, v in attrs_tpl.items():
                if not (k in attrs_html and attrs_html[k] == v):
                    ret = False
                    break
            else:
                 ret = True

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

    if logger:
        s = '{SEP}ret: {ret}'.format(SEP=SEP, ret=ret)
        logger.info(s)

    return ret

def _tpl__wp_name_attrs(node_tpl, node_html, results, logger=None):
    'Gets the contents of node_html.attrs'
    SEP = '_tpl__wp_name_attrs() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}, results: ' \
                '{results}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                results=results,
                )
        logger.info(s)

    params = node_tpl.wp_info['params']

    content = node_html.attrs
    if 'wp-function-attrs' in params:
        k = params['wp-function-attrs']
        func = node_tpl.wp_info['functions'][k]
        content = func(content)

    k = params['wp-name-attrs']
    results[k] = content

    if logger:
        s = '{SEP}results: {results}'.format(SEP=SEP, results=results)
        logger.info(s)


def _tpl__wp_leaf(node_tpl, node_html, results, logger=None):
    SEP = '_tpl__wp_leaf() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}, results: ' \
                '{results}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                results=results,
                )
        logger.info(s)

    params = node_tpl.wp_info['params']

    if 'wp-recursive-leaf' in params:
        k, arr = _tpl__wp_recursive(node_tpl, node_html, logger)
        if 'wp-recursive-text' in params:
            arr = _get_all_content(node_html, logger)
        results[k] = arr

    elif 'wp-ignore-content' not in params:
        flag = False

        if 'wp-attr-name-dict' in params:
            info = _tpl__attr_name_dict(node_tpl, node_html, logger)
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
            results[k] = _f(node_tpl, msg, logger)
            flag = True

        if not flag:
            assert not hasattr(node_html, 'contents')

    if logger:
        s = '{SEP}results: {results}'.format(SEP=SEP, results=results)
        logger.info(s)


def _tpl__wp_recursive(node_tpl, node_html, logger=None):
    SEP = '_tpl__wp_recursive() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)

    k = node_tpl.wp_info['params']['wp-name']
    arr = _f(node_tpl, node_html.contents, logger)

    arr = [
            x if isinstance(x, bs4.NavigableString) else serialize(x)
            for x in arr
            ]

    if logger:
        s = '{SEP}k: {k}, arr: {arr}'.format(SEP=SEP, k=k, arr=arr)
        logger.info(s)

    return (k, arr)


def _get_all_content(node_html, logger=None):
    'wp-recursive-text: get all the text'
    SEP = '_get_all_content() --> '
    if logger:
        s = '{SEP}node_html: {node_html}'.format(
                SEP=SEP,
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)

    arr = [
            str(x)
            for x in node_html.descendants
                if isinstance(x, bs4.NavigableString)
            ]

    if logger:
        s = '{SEP}arr: {arr}'.format(SEP=SEP, arr=arr)
        logger.info(s)

    return arr


def _tpl__attr_name_dict(node_tpl, node_html, logger=None):
    SEP = '_tpl__attr_name_dict() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)

    attrs_html = node_html.attrs
    info = {
            key: attrs_html[name]
            for (name, key) in \
                    node_tpl.wp_info['params']['wp-attr-name-dict'].items()
                if name in attrs_html
            }

    if logger:
        s = '{SEP}info: {info}'.format(SEP=SEP, info=info)
        logger.info(s)

    return info


def _tpl__children(node_tpl, node_html, results, logger=None):
    'traversal tag children of template'
    SEP = '_tpl__children() --> '
    if logger:
        s = '{SEP}node_tpl: {node_tpl}, node_html: {node_html}, results: ' \
                '{results}'.format(
                SEP=SEP,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                results=results,
                )
        logger.info(s)

    children_results = {}
    arr_html_children = node_html.contents
    if not arr_html_children:
        return

    html_i, html_n = (0, len(arr_html_children))
    for tpl_child in node_tpl.contents:
        if logger:
            s = '{SEP}html_n: {html_n}, html_i: {html_i}'.format(
                    SEP=SEP, html_n=html_n, html_i=html_i,
                    )
            logger.info(s)
        html_i = _html_children_skip(arr_html_children, html_i, html_n, logger)

        if isinstance(tpl_child, bs4.NavigableString):
            _compare_wrapper(tpl_child, arr_html_children[html_i], logger)
            html_i += 1

        elif tpl_child.name == 'wp-ignore':
            if tpl_child.wp_info and 'wp-until' in tpl_child.wp_info['params']:
                html_i = _html_children_until(
                        tpl_child, arr_html_children, html_i, html_n, logger,
                        )
            else:
                html_i = html_n

        elif (
                getattr(tpl_child, 'wp_info', None)
                and 'wp-list' in tpl_child.wp_info['params']
                ):
            html_i, children_results = _html_children_wp_list(
                    tpl_child, arr_html_children, html_i, html_n,
                    children_results, logger,
                    )

        else:
            # 含texts_and_nuggets的父节点(无wp_info属性)
            i = _html_children_other(
                tpl_child, arr_html_children[html_i], children_results, logger,
                )
            html_i += i

        if html_n <= html_i:
            break

    html_i = _html_children_skip(arr_html_children, html_i, html_n, logger)

    if html_i != html_n:
        raise ExcessNodeError(node_tpl, arr_html_children[html_i])

    if (
            getattr(node_tpl, 'wp_info', None)
            and 'wp-name' in node_tpl.wp_info['params']
            ):
        name = node_tpl.wp_info['params']['wp-name']
        results[name] = _f(node_tpl, children_results, logger)
    else:
        for k, v in children_results.items():
            if k in results:
                raise ValueError('Key already defined.')
            results[k] = v

    if logger:
        s = '{SEP}results: {results}'.format(SEP=SEP, results=results)
        logger.info(s)


def _html_children_skip(arr, i, n, logger=None):
    '忽略注释和js脚本'
    SEP = '_html_children_skip() --> '

    if logger:
        s = '{SEP}arr: {arr}, i: {i}, n: {n}'.format(
                SEP=SEP, i=i, n=n,
                arr=[node_to_json(x, ['name', 'attrs', 'wp_info']) for x in arr],
                )
        logger.info(s)

    while (
            i < n
            and (
                    isinstance(arr[i], bs4.Comment)
                    or isinstance(arr[i], bs4.Tag)
                    and arr[i].name == 'script'
                    )
            ):
        i += 1

    if logger:
        s = '{SEP}i: {i}'.format(SEP=SEP, i=i)
        logger.info(s)

    return i


def _compare_wrapper(tpl_child, node_html, logger=None):
    'tpl_child is bs4.NavigableString'
    SEP = '_compare_wrapper() --> '
    if logger:
        s = '{SEP}tpl_child: {tpl_child}, node_html: {node_html}'.format(
                SEP=SEP,
                tpl_child=node_to_json(tpl_child, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)

    try:
        results = compare(tpl_child, node_html, logger)
    except CompareError as e:
        e.register_parent(tpl_child)
        raise e

    if logger:
        s = '{SEP}results: {results}'.format(SEP=SEP, results=results)
        logger.info(s)

    return results


def _html_children_until(tpl_child, arr_html, i, n, logger=None):
    ''' tpl_child is not bs4.NavigableString
        and "wp-until" in tpl_child.wp_info["params"]
    '''
    SEP = '_html_children_until() --> '
    if logger:
        s = '{SEP}tpl_child: {tpl_child}, arr_html: {arr_html}, i: {i}, n: ' \
                '{n}'.format(
                SEP=SEP, i=i, n=n,
                tpl_child=node_to_json(tpl_child, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)

    until = tpl_child.wp_info['params']['wp-until']

    while i < n and (
            isinstance(arr_html[i], bs4.NavigableString)
            or arr_html[i].name != until
            ):
        i += 1

    if logger:
        s = '{SEP}i: {i}'.format(SEP=SEP, i=i)
        logger.info(s)

    return i


def _html_children_wp_list(
        tpl_child, arr_html, html_i, html_n, children_results, logger=None,
        ):
    ''' tpl_child is not bs4.NavigableString
        and "wp-list" in tpl_child.wp_arr_html["params"]
    '''
    SEP = '_html_children_wp_list() --> '
    if logger:
        s = '{SEP}tpl_child: {tpl_child}, arr_html: {arr_html}, html_i: ' \
                '{html_i}, html_n: {html_n}, children_results: ' \
                '{children_results}'.format(
                SEP=SEP, arr_html=arr_html, html_i=html_i, html_n=html_n,
                children_results=children_results,
                node_tpl=node_to_json(node_tpl, ['name', 'attrs', 'wp_info']),
                )
        logger.info(s)

    params = tpl_child.wp_info['params']

    arr_result = []
    for i in range(html_i, html_n):
        if _check_flag(tpl_child, arr_html[i], logger):
            x = _compare_wrapper(tpl_child, arr_html[i], logger)
            arr_result.append(x)
        else:
            break
    else:
         # not "break"
         i = html_n

    if 'wp-function' in params:
        k = params['wp-function']
        func = tpl_child.wp_info['functions'][k]
        arr_result = func(arr_result)

    k = params['wp-name']
    children_results[k] = arr_result

    if logger:
        s = '{SEP}i: {i}, children_results: {children_results}'.format(
                SEP=SEP, i=i, children_results=children_results,
                )
        logger.info(s)

    return (i, children_results)


def _check_flag(tpl_child, node_html, logger=None):
    SEP = '_check_flag() --> '
    if logger:
        s = '{SEP}tpl_child: {tpl_child}, node_html: {node_html}'.format(
                SEP=SEP,
                tpl_child=node_to_json(tpl_child, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)

    flag = (
            not isinstance(node_html, bs4.NavigableString)
            and node_html.name == tpl_child.name
            and _attrs_match(tpl_child, node_html.attrs)
            )

    if logger:
        s = '{SEP}flag: {flag}'.format(SEP=SEP, flag=flag)
        logger.info(s)

    return flag


def _html_children_other(tpl_child, node_html, children_results, logger=None):
    ''' current status:
        not (
                tpl_child is bs4.NavigableString
                and tpl_child.name == "wp-ignore"
                and "wp-list" in tpl_child.wp_arr_html["params"]
                )
    '''
    SEP = '_html_children_other() --> '
    if logger:
        s = '{SEP}tpl_child: {tpl_child}, node_html: {node_html}, ' \
                'children_results: {children_results}'.format(
                SEP=SEP, children_results=children_results,
                tpl_child=node_to_json(tpl_child, ['name', 'attrs', 'wp_info']),
                node_html=node_to_json(node_html, ['name', 'attrs']),
                )
        logger.info(s)

    i = 0
    if (
            tpl_child.name in ('wp-nugget', 'texts-and-nuggets')
            or getattr(tpl_child, 'wp_info', None)
                and 'wp-optional' not in tpl_child.wp_info['params']
            or _check_flag(tpl_child, node_html, logger)
            ):
        result = _compare_wrapper(tpl_child, node_html, logger)
        for k, v in result.items():
            if k in children_results:
                raise ValueError('Key already defined.')
            else:
                children_results[k] = v
        i += 1

    elif not _attrs_match(tpl_child, node_html.attrs, logger):
        # 检查node.attrs.keys()
        raise AttrsError(tpl_child, node_html)

    if logger:
        s = '{SEP}i: {i}'.format(SEP=SEP, i=i)
        logger.info(s)

    return i
