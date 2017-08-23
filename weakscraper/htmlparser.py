# -*- coding: utf-8 -*-

# python apps
import pdb
import pprint
from collections import OrderedDict

# our apps
from weakscraper.base_parser import BaseParser
from weakscraper.exceptions import EndTagDiscrepancy, NodeTypeDiscrepancy


DEBUG = False


class HtmlParser(BaseParser):
    def __str__(self):
        return '<HtmlParser(genealogy={})>'.format(self.genealogy)

    def handle_starttag(self, tag, attrs):
        if DEBUG:
            print('\nHtmlParser.handle_starttag():\n\ttag: "{}"\n\tattrs: {}' \
                    '\n\tself.genealogy:'.format(tag, attrs))
            pprint.pprint(self.genealogy)
            # pdb.set_trace()
        attrs_dict = {}
        is_leaf = False
        is_decl = False
        for k, v in attrs:
            if k == 'wp-leaf':
                is_leaf = True
            elif k == 'wp-decl':
                is_decl = True
            else:
                attrs_dict[k] = v

        if tag in ['meta', 'link', 'br', 'img', 'input']:
            is_leaf = True

        brothers = self.genealogy[-1]

        node = {
                'nodetype': 'tag',
                'name': tag,
                'attrs': attrs_dict,
                }
        # node = OrderedDict([
        #         ('nodetype', 'tag'),
        #         ('name', tag),
        #         ('attrs', attrs_dict),
        #         ])
        brothers.append(node)
        if not (is_leaf or is_decl):
            node['children'] = []
            self.genealogy.append(node['children'])

    def handle_endtag(self, tag):
        if DEBUG:
            print('\nHtmlParser.handle_endtag():\n\ttag: "{}"\n\tself.' \
                    'genealogy:'.format(tag))
            pprint.pprint(self.genealogy)
            # pdb.set_trace()
        parent = self.genealogy[-2][-1]

        if (parent['nodetype'] != 'tag'):
            raise NodeTypeDiscrepancy(self.genealogy, parent['nodetype'])
        elif (parent['name'] != tag):
            raise EndTagDiscrepancy(self.genealogy, parent['name'])
        else:
            self.genealogy.pop()

