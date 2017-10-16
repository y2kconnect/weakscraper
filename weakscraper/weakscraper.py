# -*- encoding: utf-8 -*-
''' html scraper
'''

# python apps
import collections
import bs4
import json
import sys

# our apps
from weakscraper.template import Template
from weakscraper.templateparser import template_parser


class WeakScraper:
    def __init__(self, stream, functions=None, debug=False):
        ''' 初始化
            stream              类型: 文件 或者 字符串
            functions           类型: 函数
            debug               类型: 布尔值
        '''
        self.debug = debug
        tree_tpl = bs4.BeautifulSoup(stream, 'lxml')

        # 处理标签的"wp-*"属性
        template_parser(tree_tpl, debug)

        self.tree_tpl = tree_tpl
        # self.template = Template(tree_tpl, functions, debug)

    def scrap(self, stream):
        tree_html = bs4.BeautifulSoup(stream, 'lxml')

        if self.debug:
            show_DOM(tree_html, 'tree_html')

        results = self.template.compare(tree_html)
        return results


def node_to_json(node, arr_key):
    '节点转JSON'
    info = {'nodetype': node.__class__.__name__}
    if isinstance(node, bs4.NavigableString):
        info['content'] = str(node.string)
    else:
        for s in arr_key:
            x = getattr(node, s, None)
            if x:
                info[s] = x
    return info


def serialize(root, arr_key=('name', 'attrs', 'params', 'children')):
    '序列化DOM树, 深度遍历'
    arr_tree = []
    arr_node = collections.deque()
    arr_node.append((root, arr_tree))

    while arr_node:
        node, arr_ret = arr_node.popleft()
        info = node_to_json(node, arr_key)

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
