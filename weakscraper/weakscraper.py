# -*- encoding: utf-8 -*-
''' html scraper
    使用bs4建立html DOM树。
    node.wp_info，dict类型。记录模板节点的标记信息。
'''

# python apps
from bs4 import BeautifulSoup

# our apps
from .template import init_tpl
from .templateparser import template_parser
from .utils import serialize


class WeakScraper:
    def __init__(self, stream_tpl, functions=None, debug=False):
        ''' 初始化
            stream_tpl          类型: 文件 或者 字符串
            functions           类型: 函数
            debug               类型: 布尔值
        '''
        self.debug = debug

        tree_tpl = BeautifulSoup(stream_tpl, 'lxml')
        template_parser(tree_tpl, debug)
        self.info = {'tree_tpl': serialize(tree_tpl)}

        # 处理标签的"wp-*"属性
        init_tpl(tree_tpl, functions, debug)
        self.info['tree_Template'] = serialize(tree_tpl)

    def scrap(self, stream_html):
        tree_html = BeautifulSoup(stream_html, 'lxml')
        self.info['tree_html'] = serialize(tree_html)

        if self.debug:
            import json
            s = '\n{sep}\ntree_html:\n{tree_html}\n{sep}\ntree_tpl:\n' \
                    '{tree_tpl}\n{sep}\ntree_Template:\n{tree_Template}'
            info = dict(ensure_ascii=False, indent=4)
            sep = '\n' + '-' * 40
            print(s.format(
                    sep=sep,
                    tree_html=json.dumps(self.info['tree_html'], **info),
                    tree_tpl=json.dumps(self.info['tree_tpl'], **info),
                    tree_Template=json.dumps(self.info['tree_Template'], **info),
                    ))

        # results = self.template.compare(tree_html)
        results = {}
        self.info['results'] = results

        return results


