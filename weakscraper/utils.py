# -*- encoding: utf-8 -*-
''' utility program
'''

# python apps
import bs4
import collections
import json
import sys


def node_to_json(node, arr_key):
    '节点转JSON'
    info = {'nodetype': node.__class__.__name__}
    if isinstance(node, bs4.NavigableString):
        # 文本标签的内容
        info['content'] = str(node.string)
    else:
        for s in arr_key:
            x = getattr(node, s, None)
            if x:
                info[s] = x
    return info


def serialize(root, arr_key=('name', 'attrs', 'wp_info', 'children')):
    '序列化DOM树, 深度遍历'
    arr_tree = []
    arr_node = collections.deque()
    arr_node.append((root, arr_tree))

    while arr_node:
        node, arr_ret = arr_node.popleft()
        info = node_to_json(node, arr_key)

        # 若arr_key中包含'children'，则删除子节点的'children'属性
        k = 'children'
        if k in arr_key and k in info and info[k]:
            arr_children = []
            arr = [(node, arr_children) for node in info[k]]
            arr_node.extendleft(reversed(arr))
            info[k] = arr_children

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
