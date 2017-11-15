# -*- coding: utf-8 -*-

# python apps
import json


PossibleParams = (
        # 标签名
        'wp-ignore',
        'wp-nugget',

        # 标签参数
        'wp-attr-name-dict',
        'wp-decl',
        'wp-function',
        'wp-function-attrs',
        'wp-ignore-attrs',
        'wp-ignore-content',
        'wp-leaf',
        'wp-list',
        'wp-name',
        'wp-name-attrs',
        'wp-optional',
        'wp-recursive',
        'wp-recursive-text',
        'wp-until',
        )


def template_parser(root, logger=None):
    ''' 深度遍历, 处理标签属性wp-*
        node.wp_info，dict类型。记录模板节点的标记信息。
    '''
    SEP = 'templateparser.template_parser() --> '
    if logger:
        logger.info('{}root: {}'.format(SEP, root))

    # 堆栈
    arr_node = [root]

    while arr_node:
        node = arr_node.pop()

        if getattr(node, 'contents', None):
            arr_node.extend(reversed(node.contents))

        arr_wp = None
        x = getattr(node, 'attrs', None)
        if x:
            arr_wp = [k for k in x.keys() if k in PossibleParams]
            if logger:
                s = '{}node: {}, attrs: {}, arr_wp: {}'
                logger.info(s.format(SEP, node, node.attrs, arr_wp))
        if not arr_wp:
            continue

        params = {}
        if len(node.contents) == 0:
            params['wp-leaf'] = None

        for k in arr_wp:
            v = node.attrs.pop(k)
            if k == 'wp-ignore':
                params[k] = None
                params['wp-ignore-content'] = None
                params['wp-ignore-attrs'] = None
            elif k in ('wp-recursive', 'wp-recursive-text'):
                params[k] = None
                params['wp-leaf'] = None
                params['wp-recursive-leaf'] = None
                params[k] = v
            elif k == 'wp-attr-name-dict':
                params[k] = json.loads(v)
            else:
                params[k] = v
        if params:
            node.wp_info = {'params': params}

        if logger:
            s = '{}attrs: {}, wp_info: {}'.format(
                    SEP, node.attrs,
                    node.wp_info if hasattr(node, 'wp_info') else None,
                    )
            logger.info(s)
