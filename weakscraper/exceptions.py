# python apps
import bs4
import collections
import json

# our apps
from .utils import serialize


class CompareError(Exception):
    def __init__(self, template, html):
        self.html = html
        self.genealogy = collections.deque([template])

    def register_parent(self, template):
        if template != self.genealogy[0]:
            self.genealogy.appendleft(template)

    def __str__(self):
        arr = [
                '{} detected !'.format(self.__class__.__name__),
                'Template genealogy :'
                ]

        for template in self.genealogy:
            arr_attr = ['name={}'.format(template.name)]
            if hasattr(template, 'attrs'):
                s = 'attrs={}'.format(template.attrs)
                arr_attr.append(s)
            if hasattr(template, 'wp_info'):
                s = 'wp_info={}'.format(str(template.wp_info))
                arr_attr.append(s)
            if isinstance(template, bs4.NavigableString):
                s = 'content="{}"'.format(template.string)
                arr_attr.append(s)

            msg = '{SEP}<{class_name}: ({arr_attr})>'.format(
                    SEP=' ' * 4,
                    class_name=template.__class__.__name__,
                    arr_attr='; '.join(arr_attr)
                    )
            arr.append(msg)

        arr.extend([
                'Html element :',
                json.dumps(serialize(self.html), ensure_ascii=False, indent=2),
                ])

        ret = '\n'.join(arr)
        return ret


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
