# -*- encoding: utf-8 -*-
''' html scraper
    使用bs4建立html DOM树。
    node.wp_info，dict类型。记录模板节点的标记信息。
'''

# python apps
import json
import logging.config
from bs4 import BeautifulSoup

# our apps
from .template import init_tpl, compare
from .templateparser import template_parser
from .utils import content_strip, serialize, DEFAULT_LOGGING_CONFIG 


class WeakScraper:
    json_kwargs = dict(ensure_ascii=False, indent=4)
    logger = None

    def __init__(self, stream_tpl, functions=None, logger=None, debug=False):
        ''' 初始化
            stream_tpl          类型: 文件 或者 字符串
            functions           类型: 函数
            logger              类型: logging.getLogger()实例
            debug               类型: 布尔值
        '''
        if debug:
            if logger:
                self.logger = logger
            else:
                logging.config.dictConfig(DEFAULT_LOGGING_CONFIG )
                self.logger = logging.getLogger('weakscraper')

        tree_tpl = BeautifulSoup(stream_tpl, 'lxml')
        content_strip(tree_tpl)

        template_parser(tree_tpl, self.logger)
        self.info = {'tree_tpl': serialize(tree_tpl)}

        # 处理标签的"wp-*"属性
        init_tpl(tree_tpl, functions, self.logger)
        self.tree_tpl = tree_tpl
        self.info['tree_Template'] = serialize(self.tree_tpl)

    def scrap(self, stream_html):
        tree_html = BeautifulSoup(stream_html, 'lxml')
        content_strip(tree_html)

        self.info['tree_html'] = serialize(tree_html)

        if self.logger:
            s_tree_tpl = json.dumps(self.info['tree_tpl'], **self.json_kwargs)
            s_tree_html = json.dumps(self.info['tree_html'],
                    **self.json_kwargs)
            s_tree_Template = json.dumps(self.info['tree_Template'],
                    **self.json_kwargs)

            s = '{sep}\ntree_tpl: {tree_tpl}\ntree_html: {tree_html}' \
                    '\ntree_Template: {tree_Template}'.format(
                    sep='WeakScraper.scrap() --> ',
                    tree_tpl=s_tree_tpl,
                    tree_html=s_tree_html,
                    tree_Template=s_tree_Template,
                    )
            self.logger.info(s)

        results = compare(self.tree_tpl, tree_html, self.logger)
        self.info['results'] = results

        return results
