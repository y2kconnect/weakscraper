# -*- coding: utf-8 -*-

# python apps
import pdb
import pprint

# our apps
from weakscraper.template import Template
from weakscraper.htmlparser import HtmlParser
from weakscraper.templateparser import TemplateParser


DEBUG = True


class WeakScraper:
    def __init__(self, template_string, functions=None):
        template_parser = TemplateParser()
        template_parser.feed(template_string)
        raw_template = template_parser.get_result()
        if DEBUG:
            print('\nraw_template:')
            pprint.pprint(raw_template)

        self.template = Template(raw_template, functions)

    def scrap(self, html):
        html_parser = HtmlParser()
        html_parser.feed(html)
        html_tree = html_parser.get_result()
        if DEBUG:
            print('\nhtml_tree:')
            pprint.pprint(html_tree)

        results = self.template.compare(html_tree)
        return results
