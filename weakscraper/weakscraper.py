# -*- encoding: utf-8 -*-

# our apps
from weakscraper.template import Template
from weakscraper.htmlparser import HtmlParser
from weakscraper.templateparser import TemplateParser


class WeakScraper:
    def __init__(self, template_string, functions=None, debug=False):
        self.debug = debug
        template_parser = TemplateParser()
        template_parser.feed(template_string)
        tpl_tree = template_parser.get_result()
        self.info = {'tpl_tree': tpl_tree}

        self.template = Template(tpl_tree, functions, debug)

    def scrap(self, html):
        html_parser = HtmlParser()
        html_parser.feed(html)
        html_tree = html_parser.get_result()
        self.info['html_tree'] = html_tree

        if self.debug:
            import json
            s = '\n{sep}\ntree_html:\n{t_html}\n{sep}\ntree_tpl:\n{t_tpl}\n{sep}'
            info = dict(ensure_ascii=False, indent=4)
            sep = '\n' + '-' * 40
            print(s.format(
                    sep=sep,
                    t_html=json.dumps(self.info['html_tree'], **info),
                    t_tpl=json.dumps(self.info['tpl_tree'], **info),
                    ))

        results = self.template.compare(html_tree)
        return results
