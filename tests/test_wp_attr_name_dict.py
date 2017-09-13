import unittest

import weakscraper
from weakscraper import exceptions


class TestWPAttrNameDict(unittest.TestCase):
    def setUp(self):
        template_string = """
            <!DOCTYPE html>
            <html>
                <body wp-name='body'>
                    <a
                        wp-name='link'
                        wp-attr-name-dict="{'href': 'url', 'class': 'class_name', 'howto': 'other'}"
                        />
                </body>
            </html>
            """

        self.scraper = weakscraper.WeakScraper(template_string)

    def test_empty(self):
        content = """
            <!DOCTYPE html>
            <html>
                <body>
                </body>
            </html>
            """

        result_data = self.scraper.scrap(content)

        self.assertEqual(result_data, {'body': {}})

    def test_match(self):
        content = """
            <!DOCTYPE html>
            <html>
                <body>
                    <a href='http://www.163.com' class='test_01' trage='_blank'>test</a>
                </body>
            </html>
            """

        result_data = self.scraper.scrap(content)

        info = {
                "body": {
                    "link": "test",
                    "url": "http://www.163.com",
                    "class_name": "test_01",
                },
            }

        self.assertEqual(result_data, info)

    def test_match_2(self):
        template_string = """
            <!DOCTYPE html>
            <html>
                <body>
                    <a wp-attr-name-dict="{'href': 'url', 'class': 'class_name', 'howto': 'other'}" />
                </body>
            </html>
            """

        content = """
            <!DOCTYPE html>
            <html>
                <body>
                    <a href='http://www.163.com' class='test_01' trage='_blank'>test</a>
                </body>
            </html>
            """

        scraper = weakscraper.WeakScraper(template_string)
        result_data = scraper.scrap(content)

        info = {
            "url": "http://www.163.com",
            "class_name": "test_01",
            }

        self.assertEqual(result_data, info)


