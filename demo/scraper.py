# -*- encoding: utf-8 -*-
''' 使用模板解析html页面
'''

# python apps
import argparse
import json
import os
from weakscraper import WeakScraper
from weakscraper.utils import serialize


def _get_args():
    s = 'Check the correctness of the HTML file.'
    parser = argparse.ArgumentParser(description=s)
    parser.add_argument(
            '--tpl', type=str, help='input template filename',
            )
    parser.add_argument(
            '--encoding_tpl', type=str, default='utf-8',
            help='template file encoding, default: "utf-8"',
            )
    parser.add_argument(
            '--html', type=str, help='input html filename',
            )
    parser.add_argument(
            '--encoding_html', type=str, default='utf-8',
            help='html file encoding, default: "utf-8"',
            )
    parser.add_argument(
            '--output', type=str, help='output result info',
            )
    parser.add_argument(
            '-d', '--debug', action='store_true', help='output debug info',
            )

    args = parser.parse_args()
    name_tpl, encoding_tpl, name_html, encoding_html, name_output, debug = (
            args.tpl, args.encoding_tpl, args.html, args.encoding_html,
            args.output, args.debug,
            )

    arr = (
            name_tpl, encoding_tpl, name_html, encoding_html, name_output,
            debug,
            )
    if debug:
        s = 'name_tpl, encoding_tpl, name_html, encoding_html, name_output,' \
            ' debug:\n\t{}\n'
        print(s.format(arr))

    if name_tpl is None or name_html is None:
        parser.print_help()
        exit()

    for f_name in (name_tpl, name_html):
        if not os.path.exists(f_name):
            print('file does not exist. {}'.format(f_name))
            exit()
    return arr


def main():
    name_tpl, encoding_tpl, name_html, encoding_html, name_output, debug = \
            _get_args()
    
    with open(name_tpl, 'rb') as f_tpl, open(name_html, 'rb') as f_html:
        s_tpl = f_tpl.read().decode(encoding_tpl)
        s_html = f_html.read().decode(encoding_html)

    scraper = WeakScraper(s_tpl, debug=debug)
    result_data = scraper.scrap(s_html)

    if name_output:
        with open(name_output, 'w') as f_output:
            f_output.write('result_data:\n')
            json.dump(scraper.info['results'], f_output, ensure_ascii=False, indent=4)
            if debug:
                f_output.write('\n\n\ntree_tpl:\n')
                json.dump(scraper.info['tree_tpl'], f_output, ensure_ascii=False, indent=4)
                f_output.write('\n\n\ntree_html:\n')
                json.dump(scraper.info['tree_html'], f_output, ensure_ascii=False, indent=4)
                f_output.write('\n\n\ntree_Template:\n')
                json.dump(scraper.info['tree_Template'], f_output, ensure_ascii=False, indent=4)
    if debug:
        print('Ok!')


if __name__ == '__main__':
    main()

