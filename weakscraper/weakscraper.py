# -*- encoding: utf-8 -*-
''' html scraper
'''

# python apps
import bs4

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


