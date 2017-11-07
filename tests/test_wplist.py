import unittest

import weakscraper
from weakscraper import exceptions

class TestWPList(unittest.TestCase):
    def setUp(self):
        template_string = """
            <!DOCTYPE html>
            <body>
              <div wp-function="sum" wp-list>
                <number wp-name="number" wp-function="int"/>
              </div>
              <number wp-function="str_sum" wp-list/>
            </body>
            </html>
            """

        functions = {
            'int': int,
            'sum': (lambda l: sum([n['sum']['number'] for n in l])),
            'str_sum': (lambda l: sum([int(n['str_sum']) for n in l]))
        }


        self.scraper = weakscraper.WeakScraper(template_string, functions)



    def test_empty(self):
        content = """
            <!DOCTYPE html>
            <body>
            </body>
            </html>
            """

        result_data = self.scraper.scrap(content)

        self.assertEqual(result_data, {'sum': 0, 'str_sum': 0})


    def test_sum(self):
        content = """
            <!DOCTYPE html>
            <body>
              <div>
                <number>12</number>
              </div>
              <div>
                <number>-5</number>
              </div>
              <number>1</number>
              <number>2</number>
              <number>3</number>
            </body>
            </html>
            """

        result_data = self.scraper.scrap(content)

        self.assertEqual(result_data, {'sum': 7, 'str_sum': 6})



class TestWPListAttrNameDict(unittest.TestCase):
    def setUp(self):
        template_string = """
            <!DOCTYPE html>
            <html>
                <body wp-name='body'>
                    <a
                        wp-name='link'
                        wp-attr-name-dict='{"href": "url", "class": "class_name", "howto": "other"}'
                        wp-function='arr'
                        wp-list
                        />
                </body>
            </html>
            """

        functions = {'arr': (lambda l: l)}

        self.scraper = weakscraper.WeakScraper(template_string, functions)

    def test_match(self):
        content = """
            <!DOCTYPE html>
            <html>
                <body>
                    <a href='http://www.163.com' class='test_01' trage='_blank'>163</a>
                    <a href='http://www.sina.com' class='test_02' trage='_blank'>sina</a>
                    <a href='http://www.sohu.com' class='test_03' trage='_blank'>sohu</a>
                </body>
            </html>
            """

        result_data = self.scraper.scrap(content)

        info = {
                "body": {
                    "link": [
                        {
                            "link": "163",
                            "url": "http://www.163.com",
                            "class_name": "test_01",
                            },
                        {
                            "link": "sina",
                            "url": "http://www.sina.com",
                            "class_name": "test_02",
                            },
                        {
                            "link": "sohu",
                            "url": "http://www.sohu.com",
                            "class_name": "test_03",
                            },
                        ],
                },
            }

        self.assertEqual(result_data, info)

