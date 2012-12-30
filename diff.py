#!/usr/bin/env python

""" Command line interface to difflib.py providing diffs in four formats:

* unified:  highlights clusters of changes in an inline format.

"""

import sys, os, time, difflib, optparse
import re

def output(diff, label=[]):
    if label is not None and len(label) > 0:
        line = diff.next()
        sys.stdout.write(re.sub(r'^--- .*$', '--- '+label[0], line))
    if label is not None and len(label) > 1:
        line = diff.next()
        sys.stdout.write(re.sub(r'^\+\+\+ .*$', '+++ '+label[1], line))
    sys.stdout.writelines(diff)


def main():

    usage = "usage: %prog [options] fromfile tofile"
    parser = optparse.OptionParser(usage)
    parser.add_option("-U", "--unified", dest="NUM", type="int", default=3, help='output NUM (default 3) lines of unified context'),
    (options, args) = parser.parse_args()


    if len(args) == 0:
        parser.print_help()
        sys.exit(1)
    if len(args) != 2:
        parser.error("need to specify both a fromfile and tofile")

    fromfile, tofile = args

    fromdate = time.ctime(os.stat(fromfile).st_mtime)
    todate = time.ctime(os.stat(tofile).st_mtime)
    fromlines = open(fromfile, 'U').readlines()
    tolines = open(tofile, 'U').readlines()

    n = options.NUM
    diff = difflib.unified_diff(fromlines, tolines, fromfile, tofile, fromdate, todate, n=n)

    output(diff, None)

if __name__ == '__main__':
    main()
