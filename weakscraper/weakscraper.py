# -*- coding: utf-8 -*-

# our apps
from weakscraper.template import Template
from weakscraper.htmlparser import HtmlParser
from weakscraper.templateparser import TemplateParser


DEBUG = False


class WeakScraper:
    def __init__(self, template_string, functions=None):
        template_parser = TemplateParser()
        template_parser.feed(template_string)
        tpl_tree = template_parser.get_result()

        self.template = Template(tpl_tree, functions)
        self.tpl_tree = tpl_tree

    def scrap(self, html):
        html_parser = HtmlParser()
        html_parser.feed(html)
        html_tree = html_parser.get_result()

        if DEBUG:
            import json
            with open('/tmp/tree_weakscraper.json', 'w') as f:
                print('tree_html:', file=f)
                json.dump(html_tree, f, ensure_ascii=False, indent=4)
                print('\n\n{}'.format('-' * 40), file=f)
                print('tree_tpl:', file=f)
                json.dump(self.tpl_tree, f, ensure_ascii=False, indent=4)

        results = self.template.compare(html_tree)
        return results
