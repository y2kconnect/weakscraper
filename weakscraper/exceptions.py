# python apps
import collections
import json

# our apps
from .utils import serialize


def genealogy_pretty_output(genealogy):
    message = ''

    for l in genealogy:
        message += '  '
        if l:
            node = l[-1]
            node_string = str({k: v for k, v in node.items() if k != 'children'})
            if len(node_string) > 160:
                message += node_string[:160] + '...'
            else:
                message += node_string
            message += '"'
            message += '\n'

    return message


class ParsingError(Exception):
    def __init__(self, template_genealogy, html_element=None):
        self.template_genealogy = template_genealogy
        self.html_element = html_element

        if self.html_element:
            self.html_str = self.html2str(self.html_element)

    def html2str(self, html_element):
        return str(html_element)

    def __str__(self):
        message = ''
        message += self.__class__.__name__ + ' detected !\n'

        message += 'Template genealogy : \n'
        message += genealogy_pretty_output(self.template_genealogy)

        if self.html_element:
            message += 'Conflicting Html element : \n'
            message += '  ' + self.html_str + '\n'
        return message


class EndTagError(ParsingError):
    pass

class AssertCompleteFailure(ParsingError):
    pass


class EndTagDiscrepancy(ParsingError):
    pass


class NodeTypeDiscrepancy(ParsingError):
    pass


class CompareError(Exception):
    def __init__(self, template, html):
        self.html = html
        self.genealogy = collections.deque([template])

    def register_parent(self, template):
        self.genealogy.appendleft(template)

    def __str__(self):
        arr = [
                '{} detected !'.format(self.__class__.__name__),
                'Template genealogy :'
                ]

        for template in self.genealogy:
            arr_attr = []
            if hasattr(template, 'name'):
                s = 'name={}'.format(template.name)
                arr_attr.append(s)
            if hasattr(template, 'attrs'):
                s = 'attrs={}'.format(template.attrs)
                arr_attr.append(s)
            if hasattr(template, 'wp_info'):
                s = 'wp_info={}'.format(str(template.wp_info))
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
