# -*- coding: utf-8 -*-

# python apps
import bs4
import json
import pdb

# our apps
from .utils import serialize


SEP = '-' * 16


def html_parser(root, debug=False):
    '删除字符串首尾的" \t\n\r"'
    if debug:
        msg = json.dumps(serialize(root), indent=4)
        s = '\n{SEP}\nhtmlparser.html_parser(): ...\n\tdebug: {debug}\n\t' \
                'root: {root}'.format(SEP=SEP, debug=debug, root=msg)
        print(s)

    # 堆栈
    arr_node = [root]

    while arr_node:
        node = arr_node.pop()

        if not hasattr(node, 'contents'):
            continue

        for x in node.contents:
            if x.__class__.__name__ == 'NavigableString':
                s = x.string.strip(' \t\n\r')
                x.string.replace_with(s)

        if getattr(node, 'contents', None):
            arr_node.extend(reversed(node.contents))

    if debug:
        msg = json.dumps(serialize(root), indent=4)
        s = '\n{SEP}\n\troot: {root}'.format(SEP=SEP, root=msg)
        print(s)
