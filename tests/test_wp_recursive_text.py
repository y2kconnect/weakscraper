import unittest

import weakscraper
from weakscraper import exceptions

class TestWPRecursiveText(unittest.TestCase):
    def setUp(self):
        template_string = """
            <!DOCTYPE html>
            <html>
                <body>
                    <div wp-name="begin">
                        <p wp-name="content" wp-recursive-text />
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
                            1234<br>
                            test
                            <em>
                                abcdefg
                            </em>
                        </p>
                    </div>
                </body>
            </html>
            """

        result_data = self.scraper.scrap(content)

        info = {
            "begin": {
                "content": [
                    "Hi !",
                    "1234",
                    "test",
                    "abcdefg",
                ]
            }
        }

        self.assertEqual(result_data, info)
