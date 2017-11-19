# python apps
import bs4
import collections
import json

# our apps
from .utils import serialize, node_to_json


class CompareError(Exception):
    def __init__(self, template, html):
        self.html = html
        self.genealogy = collections.deque([template])

    def register_parent(self, template):
        if template != self.genealogy[0]:
            self.genealogy.appendleft(template)

    def __str__(self):
        msg = '{} detected !\nTemplate genealogy:\n\t{}\nHtml element:\n\t{}'.format(
                self.__class__.__name__,
                [
                        node_to_json(tpl_child, ['name', 'attrs', 'wp_info'])
                        for tpl_child in self.genealogy
                        ],
                node_to_json(self.html, ['name', 'attrs']),
                )
        return msg


class NodetypeError(CompareError):
    pass

class TextExpectedError(CompareError):
    pass

class TagError(CompareError):
    pass

class AttrsError(CompareError):
    pass

class TextError(CompareError):
    pass

class ExcessNodeError(CompareError):
    pass

class MissingNodeError(CompareError):
    pass

class NonAtomicChildError(CompareError):
    pass
