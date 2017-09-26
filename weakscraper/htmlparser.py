# -*- coding: utf-8 -*-

# our apps
from weakscraper.base_parser import BaseParser
from weakscraper.exceptions import EndTagDiscrepancy, NodeTypeDiscrepancy


class HtmlParser(BaseParser):
    def __str__(self):
        return '<HtmlParser(genealogy={})>'.format(self.genealogy)

    def handle_starttag(self, tag, attrs):
        attrs_dict = {}
        is_leaf = False
        is_decl = False

        if tag in self.NotEndTag and 'wp-leaf' not in attrs:
            attrs.append(('wp-leaf', None))

        for k, v in attrs:
            if k == 'wp-leaf':
                is_leaf = True
            elif k == 'wp-decl':
                is_decl = True
            else:
                attrs_dict[k] = v

        brothers = self.genealogy[-1]

        node = {
                'nodetype': 'tag',
                'name': tag,
                'attrs': attrs_dict,
                }
        brothers.append(node)
        if not (is_leaf or is_decl):
            node['children'] = []
            self.genealogy.append(node['children'])

    def handle_endtag(self, tag):
        parent = self.genealogy[-2][-1]

        if (parent['nodetype'] != 'tag'):
            raise NodeTypeDiscrepancy(self.genealogy, parent['nodetype'])
        elif (parent['name'] != tag):
            if not (
                    tag in self.NotEndTag
                    and self.genealogy[-1][-1]['name'] == tag
                    ):
                raise EndTagDiscrepancy(self.genealogy, parent['name'])
        else:
            self.genealogy.pop()

