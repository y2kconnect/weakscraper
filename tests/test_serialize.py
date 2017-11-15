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
            "attrs": {},
            "contents": [
                {
                    "nodetype": "Doctype",
                    "content": "html"
                    },
                {
                    "nodetype": "Tag",
                    "name": "html",
                    "attrs": {},
                    "contents": [
                        {
                            "nodetype": "Tag",
                            "name": "head",
                            "attrs": {},
                            "contents": [{
                                "nodetype": "Tag",
                                "name": "title",
                                "attrs": {},
                                "contents": [{
                                    "nodetype": "NavigableString",
                                    "content": "Title"
                                    }]
                                }]
                            },
                        {
                            "nodetype": "Tag",
                            "name": "body",
                            "attrs": {"attr1": "val1"},
                            "wp_info": {
                                "params": {"wp-name": "body"},
                                "functions": None,
                                },
                            "contents": [{
                                "nodetype": "Tag",
                                "name": "div",
                                "attrs": {},
                                "contents": [{
                                    "nodetype": "Tag",
                                    "name": "texts-and-nuggets",
                                    "attrs": {},
                                    "wp_info": {
                                        "params": {
                                            "regex": "Hi\\ \\!\\ My\\ name\\ is(.*)\\.",
                                            "names": ["name"],
                                            "functions": [None]
                                            },
                                        "functions": None,
                                        }
                                    }]
                                }]
                            }
                        ]
                    }
                ]
            }
        self.obj = weakscraper.WeakScraper(html_tpl)

    def test_serialize(self):
        info = self.obj.info['tree_Template']
        self.assertEqual(info, self.info)


if __name__ == '__main__':
    unittest.main()
