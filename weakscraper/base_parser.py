# -*- coding: utf-8 -*-

# python apps
import collections
import html.parser
import pdb
import pprint
from abc import ABCMeta

# out apps
from .exceptions import AssertCompleteFailure

DEBUG = False


class BaseParser(html.parser.HTMLParser, metaclass=ABCMeta):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.genealogy = [[]]

    def assert_complete(self):
        if DEBUG:
            print('\nBaseParser.assert_complete():\n\tself.genealogy:')
            pprint.pprint(self.genealogy)
            pdb.set_trace()
        assert(len(self.genealogy) == 1)
        root_node = None
        for root_node in self.genealogy[0]:
            if root_node['nodetype'] == 'tag' and root_node['name'] == 'html':
                break
        if not root_node:
            raise AssertCompleteFailure(self.genealogy)
        return root_node

    def assert_complete_old(self):
        assert(len(self.genealogy) == 1)
        if len(self.genealogy[0]) != 1:
            raise AssertCompleteFailure(self.genealogy)
        root_node = self.genealogy[0][0]
        assert(root_node['nodetype'] == 'tag')
        assert(root_node['name'] == 'html')

    def get_result(self):
        if DEBUG:
            print('\nBaseParser.get_result():\n\tself.genealogy:')
            pprint.pprint(self.genealogy)
            pdb.set_trace()
        root_node = self.assert_complete()
        return root_node

    def get_result_old(self):
        if DEBUG:
            print('\nBaseParser.get_result():\n\tself.genealogy:')
            pprint.pprint(self.genealogy)
            pdb.set_trace()
        self.assert_complete()
        root_node = self.genealogy[0][0]
        return root_node

    def handle_startendtag(self, tag, attrs):
        attrs.append(('wp-leaf', None))
        self.handle_starttag(tag, attrs)

    def handle_data(self, text):
        if DEBUG:
            print('\nBaseParser.handle_data():\n\ttext: {}\n\tself.genealogy:' \
                    .format(text))
            pprint.pprint(self.genealogy)
        text = text.strip(' \t\n\r')
        if text:
            brothers = self.genealogy[-1]
            myself = {'nodetype': 'text', 'content': text}
            brothers.append(myself)

    def handle_decl(self, decl):
        if DEBUG:
            print('\nBaseParser.handle_decl():\n\tdecl: "{}"\n\tself.genealogy:' \
                    .format(decl))
            pprint.pprint(self.genealogy)
            pdb.set_trace()
        self.handle_starttag('doctype', [('wp-decl', None)])

    def unknown_decl(self, data):
        raise ValueError('Unknown declaration.')

    def handle_starttag(self, tag, attrs):
        raise NotImplementedError('action must be defined!')

    def handle_endtag(self, tag):
        raise NotImplementedError('action must be defined!')


