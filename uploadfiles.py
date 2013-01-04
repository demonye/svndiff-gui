#!/usr/bin/env python2
# -* coding: utf-8 -*-

import sys, os
from optparse import OptionParser 
from paramiko import SSHClient, AutoAddPolicy

if __name__ == "__main__":
    src_dir = "hdiff"
    USAGE = "{} [options] hostname source_dir dest_dir".format(sys.argv[0])
    parser = OptionParser(usage=USAGE)
    parser.add_option('-u', '--username', help = "Username to log in the server")
    parser.add_option('-p', '--password', help = "Password for authentication")
    parser.add_option('-f', '--keyfile', help = "Private key file for authentication")
    parser.add_option('-t', '--timeout', type="int", default=10,
            help = "Timeout seconds to connect")
    (opts, args) = parser.parse_args()

    hostname, srcdir, dstdir = args
    conargs = {
        'hostname': hostname,
        'username': opts.username,
        'timeout': opts.timeout,
        }
    if opts.password:
        conargs['password'] = opts.password
    elif opts.keyfile:
        conargs['key_filename'] = opts.keyfile

    sshcli = SSHClient()
    sftpcli = None
    try:
        sshcli.set_missing_host_key_policy(AutoAddPolicy())
        sshcli.connect(**conargs)
        sshcli.exec_command("[ -d {0} ] && rm -rf {0}; mkdir -p {0}".format(dstdir))
        sftpcli = sshcli.open_sftp()
        for f in os.listdir(srcdir):
            if f.lower().endswith('.html'):
                localfile = os.path.join(srcdir, f)
                remotefile = os.path.join(dstdir, f).replace(os.sep, '/')
                sftpcli.put(localfile, remotefile)
    except Exception as ex:
        print u"Error: " + unicode(ex)
    finally:
        if sftpcli: sftpcli.close()
        sshcli.close()

