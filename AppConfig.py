# -* coding: utf-8 -*-
from ConfigParser import ConfigParser

@singleton
class AppConfig(SafeConfigParser):

    def __init__(self, widget):
        super(AppConfig, self).__init__()
        self.widget = widget
        self.read('settings.cfg')

    def save(self):
        self.set('svn', 'username', self.curr['svn_id'])

