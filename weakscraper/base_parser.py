# -*- coding: utf-8 -*-

# python apps
import collections
import html.parser
from abc import ABCMeta


class BaseParser(html.parser.HTMLParser, metaclass=ABCMeta):
    err_msg = 'This portion of code should never be reached.'

    def __init__(self):
        super().__init__(convert_charrefs=True)

        self.genealogy = []
        self.genealogy.append([])

    def assert_complete(self):
        assert(len(self.genealogy) == 1)
        if len(self.genealogy[0]) != 1:
            raise AssertCompleteFailure(self.genealogy)
        root_node = self.genealogy[0][0]
        assert(root_node['nodetype'] == 'tag')
        assert(root_node['name'] == 'html')

    def get_result(self):
        self.assert_complete()
        root_node = self.genealogy[0][0]
        return root_node

    def feed(self, data):
        super().feed(data)

    def reset(self):
        super().reset()

    def handle_starttag(self, tag, attrs):
        raise NotImplementedError('action must be defined!')

    def handle_endtag(self, tag):
        raise NotImplementedError('action must be defined!')

    def handle_startendtag(self, tag, attrs):
        attrs.append(('wp-leaf', None))
        self.handle_starttag(tag, attrs)

    def handle_data(self, text):
        text = text.strip(' \t\n\r')
        if text:
            brothers = self.genealogy[-1]
            myself = {'nodetype': 'text', 'content': text}
            brothers.append(myself)

    def handle_entityref(self, name):
        raise AssertionError(self.err_msg)

    def handle_charref(self, name):
        raise AssertionError(self.err_msg)

    def handle_comment(self, text):
        raise AssertionError(self.err_msg)

    def handle_decl(self, decl):
        raise NotImplementedError('action must be defined!')

    def handle_pi(self, decl):
        raise AssertionError('PI.')

    def unknown_decl(self, data):
        raise ValueError('Unknown declaration.')
