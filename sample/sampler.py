#!/usr/bin/env python
#
'''
Exec Python code embedded in Markdown documents
'''

import re

def splitter(text):
    '''split file into comment and non-comment and generate'''
    
    for comment in re.compile(r'((?P<text>.*?)<!--(?P<comment>.*?)-->|(?P<last>.*?)$)', re.DOTALL).finditer(text):
        print(comment.group('text'))
        print(comment.group('comment'))
        print(comment.group('last'))


def exec_python_directive(text):
    '''execute the PYTHON directive (#![PYTHON]<command>)'''
    pass


########################################################################
# main
########################################################################

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
            'markdown',
            type=argparse.FileType('r'),
            default=sys.stdin,
            help="Markdown File")

    args = parser.parse_args()

    splitter(args.markdown.read())
