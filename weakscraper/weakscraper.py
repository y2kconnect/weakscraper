# -*- encoding: utf-8 -*-

# our apps
from .htmlparser import HtmlParser
from .template import Template
from .templateparser import TemplateParser
from .utils import serialize


class WeakScraper:
    def __init__(self, template_string, functions=None, debug=False):
        self.debug = debug

        parser_template = TemplateParser()
        parser_template.feed(template_string)
        tree_tpl = parser_template.get_result()
        self.info = {'tree_tpl': tree_tpl}

        # 处理标签的"wp-*"属性
        self.template = Template(tree_tpl, functions, debug)
        self.info['tree_Template'] = serialize(self.template)

    def scrap(self, html):
        parser_html = HtmlParser()
        parser_html.feed(html)
        tree_html = parser_html.get_result()
        self.info['tree_html'] = tree_html

        if self.debug:
            import json
            s = '\n{sep}\ntree_html:\n{tree_html}\n{sep}\ntree_tpl:\n{tree_tpl}\n{sep}'
            info = dict(ensure_ascii=False, indent=4)
            sep = '\n' + '-' * 40
            print(s.format(
                    sep=sep,
                    tree_html=json.dumps(self.info['tree_html'], **info),
                    tree_tpl=json.dumps(self.info['tree_tpl'], **info),
                    ))

        results = self.template.compare(tree_html)
        self.info['results'] = results

        return results
