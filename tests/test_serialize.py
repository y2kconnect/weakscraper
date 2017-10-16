# -*- encoding: utf-8 -*-
''' 测试weakscraper.weakscraper.serialize()
'''

# python apps
import bs4
import unittest
import weakscraper


class TestSerialize(unittest.TestCase):
    def setUp(self):
        html_tpl = '''
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Title</title>
                </head>
                <body attr1="val1" wp-name="body">
                    <div>
                        Hi ! My name is <wp-nugget wp-name="name" />.
                    </div>
                </body>
            </html>
            '''
        self.tree_tpl = bs4.BeautifulSoup(html_tpl, 'lxml')
        self.info = {
            "type": "BeautifulSoup",
            "name": "[document]",
            "children": [
                {
                    "type": "Doctype",
                    "content": "html"
                    },
                {
                    "type": "Tag",
                    "name": "html",
                    "children": [
                        {
                            "type": "NavigableString",
                            "content": "\n"
                            },
                        {
                            "type": "Tag",
                            "name": "head",
                            "children": [
                                {
                                    "type": "NavigableString",
                                    "content": "\n"
                                    },
                                {
                                    "type": "Tag",
                                    "name": "title",
                                    "children": [
                                        {
                                            "type": "NavigableString",
                                            "content": "Title"
                                            }
                                        ]
                                    },
                                {
                                    "type": "NavigableString",
                                    "content": "\n"
                                    }
                                ]
                            },
                        {
                            "type": "NavigableString",
                            "content": "\n"
                            },
                        {
                            "type": "Tag",
                            "name": "body",
                            "attrs": {
                                "attr1": "val1",
                                "wp-name": "body"
                                },
                            "children": [
                                {
                                    "type": "NavigableString",
                                    "content": "\n"
                                    },
                                {
                                    "type": "Tag",
                                    "name": "div",
                                    "children": [
                                        {
                                            "type": "NavigableString",
                                            "content": "\n                        Hi ! My name is "
                                            },
                                        {
                                            "type": "Tag",
                                            "name": "wp-nugget",
                                            "attrs": {"wp-name": "name"},
                                            "children": []
                                            },
                                        {
                                            "type": "NavigableString",
                                            "content": ".\n                    "
                                            }
                                        ]
                                    },
                                {
                                    "type": "NavigableString",
                                    "content": "\n"
                                    }
                                ]
                            },
                        {
                            "type": "NavigableString",
                            "content": "\n"
                            }
                        ]
                    },
                {
                    "type": "NavigableString",
                    "content": "\n"
                    }
                ]
            }

    def test_serialize(self):
        info = weakscraper.weakscraper.serialize(self.tree_tpl)
        self.assertEqual(info, self.info)


if __name__ == '__main__':
    unittest.main()
