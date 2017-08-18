# -*- coding: utf-8 -*-
''' 使用模板解析html页面
'''

# python apps
import json
from weakscraper import WeakScraper


name_template = 'template.html'
name_in = 'webpage.html'
name_output = 'output.json'


def main():
    with open(name_template) as f_template, open(name_in) as f_in:
        s_template = f_template.read()
        s_html = f_in.read()

    scraper = WeakScraper(s_template)
    result_data = scraper.scrap(s_html)

    with open(name_output, 'w') as f_output:
        json.dump(result_data, f_output, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()

