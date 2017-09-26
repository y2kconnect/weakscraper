# -*- encoding: utf-8 -*-

# python apps
import argparse
import json
import os
from weakscraper import WeakScraper


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
            '-d', '--debug', type=bool, help='output debug info',
            )
    args = parser.parse_args()
    arr = (
            args.tpl, args.encoding_tpl, args.html, args.encoding_html,
            args.output, args.debug,
            )

    name_tpl, encoding_tpl, name_html, encoding_html, name_output, debug = arr
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
            json.dump(result_data, f_output, ensure_ascii=False, indent=4)
    print('Ok!')


if __name__ == '__main__':
    main()

