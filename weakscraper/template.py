# -*- coding: utf-8 -*-

# python apps
import re

# our apps
from weakscraper import exceptions
from weakscraper.exceptions import (
        AttrsError, CompareError, ExcessNodeError, MissingNodeError,
        NonAtomicChildError, NodetypeError, TagError, TextError,
        TextExpectedError,
        )


def children_skip(info, i, n):
    while (
            i < n
            and info[i]['nodetype'] == 'tag'
            and info[i]['name'] == 'script'
            ):
        i += 1
    return i


def children_until(child, info, i, n):
    "'wp-until' in child.params"
    until = child.params['wp-until']
    while (
            i < n
            and not (
                    info[i]['nodetype'] == 'tag'
                    and info[i]['name'] == until
                    )
            ):
        i += 1
    return i


def check_flag(child, info, i, n):
    flag = (
            i < n
            and info[i]['nodetype'] == 'tag'
            and child.attrs_match(info[i]['attrs'])
            and info[i]['name'] == child.name
            )
    return flag


class Template():
    def __init__(self, raw_template, functions):
        self.functions = functions

        if raw_template['nodetype'] == 'tag':
            self.init_tag(raw_template)

        elif raw_template['nodetype'] == 'texts-and-nuggets':
            self.init_texts_and_nuggets(raw_template)

        else:
            msg = 'Unknown nodetype {}.'.format(raw_template['nodetype'])
            raise ValueError(msg)

    def init_tag(self, raw_template):
        tag = raw_template['name']
        assert(tag != 'wp-nugget')

        if tag == 'wp-ignore':
            self.nodetype = 'ignore'
            self.params = raw_template['params']
            return

        self.nodetype = 'tag'
        self.name = raw_template['name']
        self.attrs = raw_template['attrs']
        self.params = raw_template['params']

        if 'wp-function' in self.params and 'wp-name' not in self.params:
            self.params['wp-name'] = self.params['wp-function']

        if 'wp-function-attrs' in self.params \
                and 'wp-name-attrs' not in self.params:
            self.params['wp-name-attrs'] = self.params['wp-function-attrs']

        if 'wp-name-attrs' in self.params:
            self.params['wp-ignore-attrs'] = None

        if 'wp-ignore-content' in self.params:
            del self.params['wp-leaf']
            ignore = Template(
                    {'nodetype': 'tag', 'name': 'wp-ignore', 'params': {}},
                    self.functions,
                    )
            self.children = [ignore]
            return

        if 'wp-leaf' in self.params:
            assert(len(raw_template['children']) == 0)
            return

        text_flags = []
        for child in raw_template['children']:
            if child['nodetype'] == 'text':
                text_flags.append(True)
            else:
                assert(child['nodetype'] == 'tag')
                if child['name'] == 'wp-nugget':
                    text_flags.append(True)
                else:
                    text_flags.append(False)

        self.children = []
        grandchildren = []
        for i, child in enumerate(raw_template['children']):
            if text_flags[i]:
                grandchildren.append(child)
            else:
                if grandchildren:
                    text_template = {
                            'nodetype': 'texts-and-nuggets',
                            'children': grandchildren,
                            }
                    grandchildren = []
                    new_child = Template(text_template, self.functions)
                    self.children.append(new_child)
                new_child = Template(child, self.functions)
                self.children.append(new_child)
        if grandchildren:
            text_template = {
                    'nodetype': 'texts-and-nuggets',
                    'children': grandchildren,
                    }
            grandchildren = []
            new_child = Template(text_template, self.functions)
            self.children.append(new_child)

    def init_texts_and_nuggets(self, raw_template):
        if len(raw_template['children']) == 1:
            child = raw_template['children'][0]
            if child['nodetype'] == 'text':
                self.nodetype = 'text'
                self.content = child['content']

            elif child['nodetype'] == 'tag':
                assert(child['name'] == 'wp-nugget')
                self.nodetype = 'nugget'
                self.params = child['params']

            else:
                raise ValueError('Unexpected nodetype.')
            return

        self.nodetype = 'texts-and-nuggets'
        self.regex = ''
        self.names = []
        self.functions = []

        expected_type = raw_template['children'][0]['nodetype']
        for child in raw_template['children']:
            if child['nodetype'] != expected_type:
                raise ValueError('Unexpected nodetype.')

            elif child['nodetype'] == 'text':
                self.regex += re.escape(child['content'])
                expected_type = 'tag'

            elif child['nodetype'] == 'tag':
                self.regex += '(.*)'
                name = child['params']['wp-name']
                self.names.append(name)
                if 'wp-function' in child['params']:
                    function = child['params']['wp-function']
                else:
                    function = None
                self.functions.append(function)
                expected_type = 'text'

            else:
                raise ValueError('Unexpected nodetype.')

    def f(self, obj):
        if 'wp-function' in self.params and 'wp-list' not in self.params:
            function_name = self.params['wp-function']
            function = self.functions[function_name]
            return function(obj)
        else:
            return obj

    def compare_wrapper(self, child, html):
        try:
            results = child.compare(html)
        except CompareError as e:
            e.register_parent(self)
            raise e
        return results

    def compare_text(self, html):
        "self.nodetype == 'text'"
        if html['nodetype'] != 'text':
            raise NodetypeError(self, html)
        if html['content'] != self.content:
            raise TextError(self, html)

    def compare_nugget(self, html, results):
        "self.nodetype == 'nugget'"
        content = self.f(html['content'])

        name = self.params['wp-name']
        results[name] = content

    def compare_texts_and_nuggets(self, html, results):
        "self.nodetype == 'texts-and-nuggets'"
        regex = '^' + self.regex + '$'
        match = re.match(regex, html['content'])
        groups = match.groups()
        assert(len(groups) == len(self.names))
        assert(len(groups) == len(self.functions))

        for i in range(len(groups)):
            name = self.names[i]
            function_name = self.functions[i]
            result = groups[i]
            if function_name:
                function = self.functions[function_name]
                result = function(result)
            results[name] = result

    def tag_wp_name_attrs(self, html, results):
        name = self.params['wp-name-attrs']
        content = html['attrs']
        if 'wp-function-attrs' in self.params:
            function_name = self.params['wp-function-attrs']
            function = self.functions[function_name]
            content = function(content)
        results[name] = content

    def tag_wp_leaf(self, html, results):
        if 'wp-recursive' in self.params:
            name = self.params['wp-name']
            results[name] = self.f(html['children'])
        elif 'wp-ignore-content' not in self.params:
            if 'wp-name' in self.params:
                name = self.params['wp-name']
                if len(html['children']) == 0:
                    content = ''
                elif len(html['children']) == 1:
                    html_child = html['children'][0]
                    if html_child['nodetype'] != 'text':
                        raise TextExpectedError(self, html_child)
                    content = html_child['content']
                else:
                    raise NonAtomicChildError(self, html)
                results[name] = self.f(content)
            else:
                assert('children' not in html)

    def children_wp_list(self, child, info, i, n, children_results):
        "child.nodetype == 'tag' and 'wp-list' in child.params"
        result_list = []
        while check_flag(child, info, i, n):
            result = self.compare_wrapper(child, info[i])
            result_list.append(result)
            i += 1
        name = child.params['wp-name']
        if 'wp-function' in child.params:
            function_name = child.params['wp-function']
            function = self.functions[function_name]
            result_list = function(result_list)
        children_results[name] = result_list
        return (i, children_results)

    def children_tag(self, child, html, i, n, children_results):
        "child.nodetype in ['nugget', 'texts-and-nuggets', 'tag']"
        info = html['children']
        if not (
                child.nodetype == 'tag'
                and 'wp-optional' in child.params
                and not check_flag(child, info, i, n)
                ):
            if i >= n:
                e = MissingNodeError(child, html)
                e.register_parent(self)
                raise e
            result = self.compare_wrapper(child, info[i])
            for k, v in result.items():
                if k in children_results:
                    raise ValueError('Key already defined.')
                children_results[k] = v
            i += 1
        return i

    def tag_children(self, html, results):
        children_results = {}
        info = html['children']

        html_i = 0
        html_n = len(info)

        for child in self.children:
            html_i = children_skip(info, html_i, html_n)

            if child.nodetype == 'ignore':
                if 'wp-until' in child.params:
                    html_i = children_until(child, info, html_i, html_n)
                else:
                    html_i = html_n
            elif child.nodetype == 'tag' and 'wp-list' in child.params:
                html_i = self.children_wp_list(
                        child, info, html_i, html_n, children_results,
                        )
            elif child.nodetype == 'text':
                self.compare_wrapper(child, info[html_i])
                html_i += 1
            elif child.nodetype in ['nugget', 'texts-and-nuggets', 'tag']:
                html_i = self.children_tag(
                        child, html, html_i, html_n,
                        children_results,
                        )
            else:
                raise ValueError('Unknown child type.')

        html_i = children_skip(html, html_i, html_n)

        if html_i != html_n:
            raise ExcessNodeError(self, info[html_i])

        if 'wp-name' in self.params:
            name = self.params['wp-name']
            results[name] = self.f(children_results)
        else:
            for k, v in children_results.items():
                if k in results:
                    raise ValueError('Key already defined.')
                results[k] = v

    def compare_tag(self, html, results):
        "self.nodetype == 'tag'"
        if (html['nodetype'] != 'tag'):
            raise NodetypeError(self, html)
        elif (self.name != html['name']):
            raise TagError(self, html)
        elif not self.attrs_match(html['attrs']):
            raise AttrsError(self, html)

        if 'wp-name-attrs' in self.params:
            self.tag_wp_name_attrs(html, results)

        if 'wp-leaf' in self.params:
            self.tag_wp_leaf(html, results)
        else:
            # look at the children
            self.tag_children(html, results)

    def compare(self, html):
        results = {}

        if self.nodetype == 'text':
            self.compare_text(html)
        elif self.nodetype == 'nugget':
            self.compare_nugget(html, results)
        elif self.nodetype == 'texts-and-nuggets':
            self.compare_texts_and_nuggets(html, results)
        elif self.nodetype == 'tag':
            self.compare_tag(html, results)
        else:
            raise ValueError('Unexpected nodetype.')
        return results

    def attrs_match(self, attrs):
        if 'wp-ignore-attrs' not in self.params:
            return self.attrs == attrs

        for attr, value in self.attrs.items():
            if attr not in attrs or attrs[attr] != value:
                return False
        else:
            return True
