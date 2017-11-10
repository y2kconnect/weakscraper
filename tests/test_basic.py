import unittest

import weakscraper
from weakscraper import exceptions

class TestBasic(unittest.TestCase):
    def setUp(self):
        template_string = """
            <!DOCTYPE html>
            <head>
              <title>Title</title>
            </head>
            <body attr1="val1" attr2="val2">
              <div>Hi !</div>
            </body>
            </html>
            """

        self.scraper = weakscraper.WeakScraper(template_string)


    def test_match(self):
        content = """
            <!DOCTYPE html>
            <head><title>Title
              </title>
            </head>


            <body attr2="val2" attr1="val1">
            <div>

                Hi !
              </div>
            </body>
              </html>
            """

        result_data = self.scraper.scrap(content)

        self.assertEqual(result_data, {})


    def test_datanomatch(self):
        content =  """
            <!DOCTYPE html>
            <head>
              <title>Title</title>
            </head>
            <body attr2="val2" attr1="val1">
              <div>
                Hello !
              </div>
            </body>
            </html>
            """

        try:
            result_data = self.scraper.scrap(content)
        except exceptions.TextError:
            return

        self.assertTrue(False)


    def test_tagnomatch(self):
        content = """
            <!DOCTYPE html>
            <head>
              <title>Title</title>
            </head>
            <body attr2="val2" attr1="val1">
              <q>
                Hi !
              </q>
            </body>
            </html>
            """

        try:
            result_data = self.scraper.scrap(content)
        except exceptions.ExcessNodeError:
            ''' 错误类型ExcessNodeError的原因：
                <body>的内容，由bs4.NavigableString变成bs4.Tag了，导致
            _html_children_other()忽略。因此错误类型也由TagError变成了
            ExcessNodeError。
            '''
            return

        self.assertTrue(False)


    def test_attrnomatch(self):
        content = """
            <!DOCTYPE html>
            <head>
              <title>Title</title>
            </head>
            <body attr3="val1" attr2="val2">
              <div>Hi !</div>
            </body>
            </html>
            """

        try:
            result_data = self.scraper.scrap(content)
        except exceptions.AttrsError:
            return

        self.assertTrue(False)
