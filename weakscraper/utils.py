# -*- encoding: utf-8 -*-
''' utility program
'''

# python apps
import bs4
import json
import sys


SEP = '-' * 16


def node_to_json(node, arr_key=None):
    '节点转JSON'
    if arr_key is None:
        arr_key = ('name', 'attrs', 'contents', 'wp_info')
    info = {'nodetype': node.__class__.__name__}
    if isinstance(node, bs4.NavigableString):
        # 文本标签的内容
        info['content'] = str(node.string)
    else:
        for s in arr_key:
            x = getattr(node, s, None)
            if x is None:
                continue
            if s == 'wp_info':
                info[s] = {
                        'params': x['params'],
                        'functions':
                                {
                                        k: str(v)
                                        for k, v in x['functions'].items()
                                        }
                                if 'functions' in x and x['functions']
                                    else None,
                        'debug': x['debug'] if 'debug' in x else None,
                        }
            else:
                info[s] = x
    return info


def serialize(root, arr_key=None):
    '序列化DOM树, 深度遍历'
    if arr_key is None:
        arr_key = ('name', 'attrs', 'wp_info')

    arr_tree = []
    arr_node = [(root, arr_tree)]

    while arr_node:
        node, arr_ret = arr_node.pop()
        info = node_to_json(node, arr_key)

        # 孩子节点
        if getattr(node, 'contents', None):
            # 删除子节点的'children'属性
            info['contents'] = arr_children = []
            # 下级节点，加入堆栈
            arr = [(node, arr_children) for node in node.contents]
            arr_node.extend(reversed(arr))

        arr_ret.append(info)

    n = len(arr_tree)
    if n == 0:
        ret = None
    elif n == 1:
        ret = arr_tree[0]
    else:
        ret = arr_tree
    return ret


def show_DOM(root, label='root_tree', stream=sys.stdout, indent=4):
    '显示DOM树'
    arr_tree = serialize(root)
    msg = json.dumps(arr_tree, ensure_ascii=False, indent=indent)
    print('{label}:\n{msg}'.format(label=label, msg=msg), file=stream)


def content_strip(root):
    ''' 若 字符串.strip() == ''，则删除 '''
    # 堆栈
    arr_node = [root]

    while arr_node:
        node = arr_node.pop()

        if hasattr(node, 'contents'):
            [
                    x.string.replace_with(x.string.strip())
                        if x.string.strip() else x.extract()
                    for x in node.contents
                        if x.__class__.__name__ == 'NavigableString'
                    ]

            if node.contents:
                arr_node.extend(reversed(node.contents))
