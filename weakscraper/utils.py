# -*- encoding: utf-8 -*-
''' utility program
'''

# python apps
import bs4
import json
import sys

log_fmt = '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
log_fmt_with_pid = (
        '[%(asctime)s] [%(process)d-%(processName)s] {%(filename)s:%(lineno)d}'
        ' %(levelname)s - %(message)s'
        )


DEFAULT_LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
                'log_format': {
                        'format': log_fmt,
                        'datefmt': '%FT%T',
                        },
                'log_format_with_pid': {
                        'format': log_fmt_with_pid,
                        'datefmt': '%FT%T',
                        },
                },
        'handlers': {
                'console': {
                        'class': 'logging.StreamHandler',
                        'level': 'DEBUG',
                        'formatter': 'log_format',
                        'stream': 'ext://sys.stdout',
                        },
                'log_file': {
                        'level': 'DEBUG',
                        'class': 'logging.handlers.RotatingFileHandler',
                        'formatter': 'log_format_with_pid',
                        'filename': 'weakscraper_run.log',
                        'mode': 'w',
                        'maxBytes': 1024 * 1024 * 10,
                        'backupCount': 5,
                        },
                },
        'loggers': {
                '': {
                        'handlers': ['log_file'],
                        'level': 'ERROR',
                        },
                'weakscraper': {
                        'handlers': ['log_file'],
                        'level': 'DEBUG',
                        'propagate': False,
                        },
                },
        }


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
    ''' 去除bs.NavigableString的前后空格。
    若child.string.strip() == ""，则删除。
    '''
    # 堆栈
    arr_node = [root]

    while arr_node:
        node = arr_node.pop()

        if hasattr(node, 'contents'):
            [
                    child.string.replace_with(child.string.strip())
                        # if child.string.strip() else child.decompose()
                        if child.string.strip() else child.extract()
                    for child in node.contents
                        if child.__class__.__name__ == 'NavigableString'
                    ]

            if node.contents:
                arr_node.extend(reversed(node.contents))
