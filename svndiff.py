import sys
import os
import re
import copy
from optparse import OptionParser 
from subprocess import *
from tornado import template

def is_win64():
    return (os.environ.get('PROCESSOR_ARCHITEW6432', None) is not None)
def exec_cmd(*args):
    p = Popen(args, stdout=PIPE, stderr=PIPE).communicate()
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
                self._path = os.path.join(_winreg.QueryValueEx(reg, "Location")[0], "svn.exe")
            except Exception as err:
                print err
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
        for line in self.svn_cmd.run(["status", self.src_dir]):
            try:
                stat,fname = line.split()
                if stat == 'M':
                    self.files.append(fname)
                elif stat == 'A':
                    self.newfiles.append(fname)
                elif stat == 'D':
                    self.removedfiles.append(fname)
            except ValueError:
                pass

    def html_escape(self, value):
        def to_basestring(value):
            if isinstance(value, (basestring, type(None))):
                return value
            assert isinstance(value, bytes)
            return value.decode("utf-8")

        return self.ESCAPE_RE.sub(lambda m: self.ESCAPE_DICT[m.group(0)],
                to_basestring(value))

    def display_fname(self, fname):
        return fname.replace('/', os.sep).replace(self.src_dir+os.sep, '').replace(os.sep, '/')
    def hdiff_fname(self, fname):
        return fname.replace(self.src_dir+os.sep, '').replace(os.sep, '.') + '.html'

    def gen_diff_file(self, args, fname):
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
        out_html.write(self.htmltpl.generate(diff_files=diff_files, my_escape=self.html_escape))


if __name__ == "__main__":
    save_dir = "hdiff"
    src_dir = ""

    USAGE = "usage"

    parser = OptionParser(usage=USAGE)
    parser.add_option('-b', '--savedir', default="hdiff",
             help = (
                "savedir is the directory where the diff files will be stored."
                "It could be any directory name like '/tmp/mybugs/perf-bug'. "
                "If it is not specified, diff files will be stored in the directory 'hdiff'" )
             )
    parser.add_option('-s', '--srcdir', default=".",
             help = (
                "srcdir is the directory where the source code is saved. "
                "If it is not specified, the current dir will be used." )
             )
    (opts, args) = parser.parse_args()

    if opts.savedir:
        save_dir = opts.savedir
    if opts.srcdir:
        src_dir = opts.srcdir
    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)

    sd = SvnDiff(src_dir, save_dir)

    print("files =  {0}".format('  '.join([sd.display_fname(v) for v in sd.files])))
    print("newfiles =  {0}".format('  '.join([sd.display_fname(v) for v in sd.newfiles])))

    for f in sd.files:
        args = [ "diff", f, "--diff-cmd=diffcmd.exe", "-x", "-u -l10000" ]
        sd.gen_diff_file(args, ' '+f)

    args = [ "diff", src_dir ]
    sd.gen_diff_file(args, 'All-diffs')

