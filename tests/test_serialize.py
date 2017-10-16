# -*- encoding: utf-8 -*-
''' 测试weakscraper.weakscraper.serialize()
'''

# python apps
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
        self.info = {
            "nodetype": "BeautifulSoup",
            "name": "[document]",
            "children": [
                {
                    "nodetype": "Doctype",
                    "content": "html"
                    },
                {
                    "nodetype": "Tag",
                    "name": "html",
                    "children": [
                        {
                            "nodetype": "NavigableString",
                            "content": "\n"
                            },
                        {
                            "nodetype": "Tag",
                            "name": "head",
                            "children": [
                                {
                                    "nodetype": "NavigableString",
                                    "content": "\n"
                                    },
                                {
                                    "nodetype": "Tag",
                                    "name": "title",
                                    "children": [{
                                        "nodetype": "NavigableString",
                                        "content": "Title"
                                        }]
                                    },
                                {
                                    "nodetype": "NavigableString",
                                    "content": "\n"
                                    }
                                ]
                            },
                        {
                            "nodetype": "NavigableString",
                            "content": "\n"
                            },
                        {
                            "nodetype": "Tag",
                            "name": "body",
                            "attrs": {"attr1": "val1"},
                            "params": {"wp-name": "body"},
                            "children": [
                                {
                                    "nodetype": "NavigableString",
                                    "content": "\n"
                                    },
                                {
                                    "nodetype": "Tag",
                                    "name": "div",
                                    "children": [
                                        {
                                            "nodetype": "NavigableString",
                                            "content": "\n                        Hi ! My name is "
                                            },
                                        {
                                            "nodetype": "Tag",
                                            "name": "wp-nugget",
                                            "params": {"wp-name": "name"},
                                            "children": []
                                            },
                                        {
                                            "nodetype": "NavigableString",
                                            "content": ".\n                    "
                                            }
                                        ]
                                    },
                                {
                                    "nodetype": "NavigableString",
                                    "content": "\n"
                                    }
                                ]
                            },
                        {
                            "nodetype": "NavigableString",
                            "content": "\n"
                            }
                        ]
                    },
                {
                    "nodetype": "NavigableString",
                    "content": "\n"
                    }
                ]
            }
        self.obj = weakscraper.WeakScraper(html_tpl)

    def test_serialize(self):
        info = weakscraper.weakscraper.serialize(self.obj.tree_tpl)
        self.assertEqual(info, self.info)


if __name__ == '__main__':
    unittest.main()
