from __future__ import print_function
import argparse
import sys

from . import factory


def main(args=None):
    parser = argparse.ArgumentParser(description='A simple Python library designed to make it quick and easy to '
                                     'represent tabular data in visually appealing ASCII tables.')
    parser.add_argument('input', default=None, nargs='?', help='input filename (default is stdin)')
    input_type = parser.add_mutually_exclusive_group()
    input_type.add_argument('--csv', dest='input_type', action='store_const', const='csv', help='CSV data (default)')
    input_type.add_argument('--md', dest='input_type', action='store_const', const='md', help='Markdown data')
    input_type.add_argument('--rst', dest='input_type', action='store_const', const='rst', help='reStructuredText data')
    input_type.set_defaults(input_type='csv')
    parser.add_argument('-o', dest='output', help='output filename (default is stdout)')

    ns = parser.parse_args(args)

    fin_obj = open(ns.input, 'r') if ns.input else sys.stdin
    if ns.input_type == 'md':
        table = factory.from_md(fin_obj.read())
    elif ns.input_type == 'rst':
        parser.error('unsupported input type')
    else:
        table = factory.from_csv(fin_obj)
    fin_obj.close()

    fout_obj = open(ns.output, 'w') if ns.output else sys.stdout
    print(table.get_string(), file=fout_obj)
    return 0


if __name__ == '__main__':  # pragma: no cover
    main()
