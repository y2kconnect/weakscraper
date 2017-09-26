# -*- encoding: utf-8 -*-

# python apps
import argparse
import json
import os
from weakscraper.htmlparser import HtmlParser


def _get_args():
    s = 'Check the correctness of the HTML file.'
    parser = argparse.ArgumentParser(description=s)
    parser.add_argument(
            '-i', '--input', type=str, help='input filename',
            )
    parser.add_argument(
            '--encoding', type=str, default='utf-8',
            help='filename encoding, default: "utf-8"',
            )
    parser.add_argument(
            '-o', '--output', type=str, default=None,
            help='output filename, default: None',
            )
    args = parser.parse_args()
    name_in, encoding, name_out = (args.input, args.encoding, args.output)

    if name_in is None:
        parser.print_help()
        exit()

    if not os.path.exists(name_in):
        print('file does not exist. {}'.format(name_in))
        exit()

    return (name_in, encoding, name_out)


def main():
    f_name, encoding, f_name_out = _get_args()
    with open(f_name, 'rb') as f_in:
        html = f_in.read().decode(encoding)
    html_parser = HtmlParser()
    html_parser.feed(html)
    html_tree = html_parser.get_result()
    if f_name_out:
        with open(f_name_out, 'w') as f_out:
            json.dump(html_tree, f_out, ensure_ascii=False, indent=4)
    print('Ok!')


if __name__ == '__main__':
    main()
