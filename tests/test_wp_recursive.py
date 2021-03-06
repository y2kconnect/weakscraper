import unittest

import weakscraper
from weakscraper import exceptions

class TestWPRecursive(unittest.TestCase):
    def setUp(self):
        template_string = """
            <!DOCTYPE html>
            <html>
                <body>
                    <div wp-name="begin">
                        <p wp-name="content" wp-recursive />
                    </div>
                </body>
            </html>
            """

        self.scraper = weakscraper.WeakScraper(template_string)


    def test_match(self):
        content = """
            <!DOCTYPE html>
            <html>
                <body>
                    <div>
                        <p>
                            Hi !<br>
                            1234<hr>
                            test
                        </p>
                    </div>
                </body>
            </html>
            """

        result_data = self.scraper.scrap(content)

        info = {
            "begin": {
                "content": [
                    {
                        "content": "Hi !",
                        "nodetype": "text"
                    },
                    {
                        "attrs": {},
                        "name": "br",
                        "nodetype": "tag"
                    },
                    {
                        "content": "1234",
                        "nodetype": "text"
                    },
                    {
                        "attrs": {},
                        "name": "hr",
                        "nodetype": "tag"
                    },
                    {
                        "content": "test",
                        "nodetype": "text"
                    }
                ]
            }
        }

        self.assertEqual(result_data, info)
