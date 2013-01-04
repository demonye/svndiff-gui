#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import os
import re
import copy
from optparse import OptionParser 
from subprocess import *
from tornado import template, escape

from yelib.util import force_rmdir

def is_win64():
    return (os.environ.get('PROCESSOR_ARCHITEW6432', None) is not None)
def exec_cmd(*args):
    popen_args = {
        'args': args,
        'stdout': PIPE,
        'stderr': PIPE,
        }
    if os.name != 'posix':
        popen_args['shell'] = True
    p = Popen(**popen_args).communicate()
    if len(p[1]) > 0:
        raise Exception(p[1])
    return p[0]

class SvnCmd(object):
    def __init__(self):
        self._path = None

    @property
    def path(self):
        if not self._path:
            self._path = "svn"
            try:
                import _winreg
                reg = _winreg.OpenKeyEx(
                        _winreg.HKEY_LOCAL_MACHINE,
                        "SOFTWARE\\SlikSvn\\Install", 0,
                        _winreg.KEY_READ | (is_win64() and
                            _winreg.KEY_WOW64_64KEY or
                            _winreg.KEY_WOW64_32KEY)
                        )
                self._path = os.path.join(_winreg.QueryValueEx(reg, "Location")[0], "svn")
            except ImportError:
                pass
        return self._path

    def run(self, args=[], handler=None):
        for line in exec_cmd(self.path, *args).split('\n'):
            yield line.rstrip()

class SvnDiff(object):
    ESCAPE_RE = re.compile('[&<>" \t]')
    ESCAPE_DICT = {'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', ' ':'&nbsp;', '\t':'&nbsp;'*4}

    def __init__(self, src_dir='.', save_dir='hdiff', tpl='diff_template.html', getstatus=True):
        self.src_dir = src_dir
        self.save_dir = save_dir
        self.svn_cmd = SvnCmd()
        self.files = []
        self.newfiles = []
        self.removedfiles = []
        self.htmltpl = template.Template(open(tpl).read())

        if getstatus:
            self.status()

    def set_src_dir(self, src_dir):
        self.src_dir = src_dir

    def status(self):
        def add_file(files, fn):
            if os.path.isdir(fn):
                for root, dirs, fls in os.walk(fn):
                    for f in fls:
                        files.append(os.path.join(root, f))
            else:
                files.append(fn)

        self.files = []
        self.newfiles = []
        self.removedfiles = []
        for line in self.svn_cmd.run(["status", self.src_dir]):
            try:
                stat,fname = line.split()
                if stat == 'M':
                    self.files.append(fname)
                elif stat in ('A', '?'):
                    add_file(self.newfiles, fname)
                elif stat in ('D', '!'):
                    add_file(self.removedfiles, fname)
            except ValueError:
                pass

    def html_escape(self, value):
        return self.ESCAPE_RE.sub(lambda m: self.ESCAPE_DICT[m.group(0)],
                escape.to_basestring(value))

    def display_fname(self, fname):
        return fname.replace('/', os.sep).replace(self.src_dir+os.sep, '').replace(os.sep, '/')
    def hdiff_fname(self, fname):
        return fname.replace(self.src_dir+os.sep, '').replace(os.sep, '.') + '.html'

    def gen_diff_file(self, args, fname, new_files=[], removed_files=[]):
        diff_files = []
        curr_file = {}
        curr_state = ['dump']
        left_lines = []
        right_lines = []
        fname = self.hdiff_fname(fname)

        def dump_line(tp, l, r):
            curr_line = {}
            curr_line['type'] = tp
            curr_line['left'] = len(l)>0 and l or ' '
            curr_line['right'] = len(r)>0 and r or ' '
            curr_file['lines'].append(curr_line)

        def set_fname(arr):
            if curr_file.has_key('name'):
                diff_files.append(copy.copy(curr_file))
            fn, = arr.groups()
            curr_file['name'] = self.display_fname(fn)
            curr_file['lines'] = []

        def set_line_num(arr):
            oldno, newno = arr.groups()
            dump_line('line', 'Line '+oldno, 'Line '+newno)

        def set_line(arr):
            line, c = arr.groups()
            if c == '+':
                if curr_state[0] in ('dump', 'add'):
                    curr_state[0] = 'add'
                    dump_line(curr_state[0], '', line)
                else:
                    curr_state[0] = 'change'
                    try:
                        left = left_lines.pop(0)
                    except IndexError:
                        left = ''
                    dump_line(curr_state[0], left, line)
            elif c == '-':
                curr_state[0] = 'remove'
                left_lines.append(line)
            else:
                for l in left_lines:
                    dump_line(curr_state[0], l, '')
                left_lines[:] = []
                curr_state[0] = 'dump'
                dump_line(curr_state[0], line, line)

        def new_or_removed(files):
            return [{
                'name': self.hdiff_fname(v),
                'disp_name': self.display_fname(v),
                } for v in files ]


        patterns = {
            r'^Index: (\S+)$': set_fname,
            r'^@@ -(\d+).*\+(\d+).*@@$': set_line_num,
            r'^(([-+ ](?![-+])).*)$': set_line,
            r'^((\s*))$': set_line,
        }
        for line in self.svn_cmd.run(args):
            for p, f in patterns.items():
                ret = re.match(p, line)
                if ret: f(ret)
        if curr_file.has_key('name'):
            diff_files.append(copy.copy(curr_file))

        out_html = open(os.path.join(self.save_dir, fname), 'w')
        out_html.write(self.htmltpl.generate(
            diff_files=diff_files,
            new_files=new_or_removed(new_files),
            removed_files=new_or_removed(removed_files),
            my_escape=self.html_escape ))

    def _print_files(self, stat, files):
        for fn in files:
        	print stat, self.display_fname(fn), fn


    def print_changed_files(self):
        self._print_files('M', self.files)
        self._print_files('A', self.newfiles)
        self._print_files('D', self.removedfiles)


if __name__ == "__main__":
    save_dir = "hdiff"
    src_dir = ""

    USAGE = "{} [options] diffitems".format(sys.argv[0])

    parser = OptionParser(usage=USAGE)
    parser.add_option('-s', '--srcdir', default=".",
             help = (
                "srcdir is the directory where the source code is saved. "
                "If it is not specified, the current dir will be used." )
             )
    parser.add_option('-c', '--change', action="store_true", default=False,
            help = "Output changed files")
    parser.add_option('-d', '--savedir', default="hdiff",
             help = (
                "savedir is the directory where the diff files will be stored."
                "It could be any directory name like '/tmp/mybugs/perf-bug'. "
                "If it is not specified, diff files will be stored in the "
                "directory 'hdiff'" )
             )
    (opts, args) = parser.parse_args()

    if opts.srcdir:
        src_dir = opts.srcdir
    if opts.savedir:
        save_dir = opts.savedir

    sd = SvnDiff(src_dir, save_dir)

    if opts.change:
    	sd.print_changed_files()
    	sys.exit(0)

    force_rmdir(save_dir)
    os.makedirs(save_dir)

    diff_files = []
    for f in sd.files:
        if args and f not in args:
            continue
        diff_files.append(f)
        diffargs = [ "diff", f, "--diff-cmd=diff", "-x", "-U10000" ]
        sd.gen_diff_file(diffargs, ' '+f)
    new_files = []
    for f in sd.newfiles:
        if args and f not in args:
            continue
        new_files.append(f)
        in_file = open(f)
        out_html = open(os.path.join(sd.save_dir, ' '+sd.hdiff_fname(f)), 'w')
        out_html.write("<xmp>\n")
        n = 1
        for l in in_file.readlines():
            out_html.write("%5d  %s\n" % (n, l))
            n += 1
        out_html.write("</xmp>\n")
        out_html.close()
        in_file.close()

    diffargs = [ "diff" ] + diff_files
    sd.gen_diff_file(diffargs, 'All-diffs', new_files, sd.removedfiles)

