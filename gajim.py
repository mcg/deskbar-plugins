#
#  gajim.py :  A module for the deskbar applet, that allows you to search and 
#                             message users from your Gajim roster.
#
#  Copyright (C) 2008 by Matthew Gregg
#  Copyright (C) 2007 by Sergey Nazarov 
#  Copyright (C) 2007 by Jason Chu
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# 
#  Authors: Matthew Gregg <mcg at no_spam_me butterfat.net>
#           Sergey Nazarov <phearnot at no_spam_me gmail.com>
#  Incorporates some ideas from:
#  http://cixar.com/~segphault/programming/code/samples/aim_deskbar.py.html
#
# 1.0 : Initial release.
# 1.1 : Updated to work with latest dbus and gajim.
# 1.2 : Added escaping
# 1.3 : Rewrite.  Can handle transports. '%' character in transport jid was an issue
# 1.4 : +Status icon support
#     : +Transport icon support
#     : +Ability to change visibility of the offline contacts
#     : +Iconset guessed from Gajim's config file
# 1.5 : Fixed issue with Gajim not running
# 1.6 : Works with Deskbar 2.19.6's new module API
# 1.7 : Added caching from Jason Chu <jchu at no_spam_me xentac.net>
# 1.8 : Fix case when gajim is installed in prefix other than /usr 
#       (Oleg Andreev <OlegOAndreev@yandex.ru>).

import sys
import os

def get_gajim_prefix():
    for prefix in ['/usr', '/usr/local']:
        if os.access(prefix + '/share/gajim', os.X_OK):
            return prefix + '/share/gajim'
    return None

GAJIM_PREFIX = get_gajim_prefix()
if GAJIM_PREFIX == None:
    raise ImportError('Unable to find gajim')

sys.path.append(GAJIM_PREFIX + '/src')
from common import exceptions
from gettext import gettext as _
import cgi, gtk
import deskbar, deskbar.core.Indexer, deskbar.interfaces.Module, deskbar.core.Utils, deskbar.interfaces.Match
from deskbar.core.GconfStore import GconfStore
import datetime

GCONF_GAJIM_SHOWOFFLINE  = GconfStore.GCONF_DIR+'/gajim/show_offline'

HANDLERS = [ 'GajimHandler'] 
VERSION = '1.8'
STATUSES = [
    'online', 'offline', 'away', 'chat',
    'dnd', 'invisible', 'xa'
]

TRANSPORTS = [
    'icq', 'aim', 'gadu-gadu', 'irc', 'msn', 'sms', 'tlen', 'weather', 'yahoo'
]

try:
    import dbus
    import dbus.service
    import dbus.glib
except:
    raise exceptions.DbusNotSuported

try:
    PREFERRED_ENCODING = locale.getpreferredencoding()
except:
    sys.exc_clear()
    PREFERRED_ENCODING = 'UTF-8'

OBJ_PATH = '/org/gajim/dbus/RemoteObject'
INTERFACE = 'org.gajim.dbus.RemoteInterface'
SERVICE = 'org.gajim.dbus'
BASENAME = 'gajim-deskbar'
try:
    sbus = dbus.SessionBus()
except:
    raise exceptions.SessionBusNotPresent

iconset = 'dcraven'
HANDLER_ICON = GAJIM_PREFIX + '/data/iconsets/dcraven/16x16/online.png'
ICON_PATH = GAJIM_PREFIX + '/data/iconsets/'
ICON_TRANSPORTS = GAJIM_PREFIX + '/data/iconsets/transports/'

class GajimAction(deskbar.interfaces.Action):
    def __init__(self, jid=None, name=None, interface=None):
        deskbar.interfaces.Action.__init__(self, name)
        self.jid = jid
        self.name = name
        self.interface = interface

    def get_verb(self):
        if self.jid:
            return _('Open chat with <b>%(name)s</b> (%(jid)s)')
        else:
            return _('Open chat with <b>%s</b>') % self.name

    def get_name(self, text=None):
        return {
                'name': cgi.escape(self.name), 
                'jid': self.jid,
                }

    def activate(self, text=None):
        self.interface.open_chat(dbus.String(self.jid),dbus.String(''))

class GajimMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, jid=None, icon=None, interface=None):
        deskbar.interfaces.Match.__init__(self, name=name, category='people', icon=icon)
        self.name = name
        self.jid = jid
        self.interface = interface
        self.add_action(GajimAction(self.jid, self.name, self.interface))

    def get_category(self):
        return 'people'

    def get_hash(self, text=None):
        return 'gajim ' + self.name
    

class GajimHandler(deskbar.interfaces.Module):

    INFOS = {'icon':  deskbar.core.Utils.load_icon(HANDLER_ICON),
            'name': _('Gajim Roster'),
            'description': _('See who is online and start a conversation'),
            'version': VERSION,
            }

    def __init__ (self):
        deskbar.interfaces.Module.__init__(self)

    def initialize(self):
        self.obj = None
        self.interface = None
        confpath = os.path.expanduser('~') + '/.gajim/config'
        conffile = open(confpath, 'r')
        for line in conffile.readlines():
            if line.startswith('iconset = '):
                iconset = line[10:].strip()
                break
        conffile.close()
        self.icons = {}
        self.transport_icons = {}
        for transport in TRANSPORTS:
                self.transport_icons[transport] = {}
        for status in STATUSES: 
            for transport in TRANSPORTS:
                self.transport_icons[transport][status] = '%s%s%s' % (ICON_TRANSPORTS, transport, '/16x16/' + status + '.png')
            self.icons[status] = '%s%s%s' % (ICON_PATH, iconset, '/16x16/' + status + '.png')

        self.lastrequest = None
        self.lastroster = None
        
    def get_cache(self, query):
        return self.lastroster

    def list_contacts(self, query):
        self.lastroster = self.interface.list_contacts(query)
        self.lastrequest = datetime.datetime.now()
        return self.lastroster

    def query(self, query):
        try:
            self.obj = sbus.get_object(SERVICE, OBJ_PATH)
            self.interface = dbus.Interface(self.obj, INTERFACE)
        except:
            print sys.exc_info()
            print 'Unable to connect to Gajim - probably it isn\'t running'
            return []
                        
        t = GconfStore.get_instance().get_client().get_bool(GCONF_GAJIM_SHOWOFFLINE)
        if t != None:
            self.show_offline = t
        else:
            self.show_offline = False
            GconfStore.get_instance().get_client().set_bool(GCONF_GAJIM_SHOWOFFLINE, False)

        message = ''
        if self.lastrequest != None and datetime.datetime.now() - self.lastrequest < datetime.timedelta(seconds=20):
            self.method = self.get_cache
            message = 'asking Cache for roster'
        else:
            self.method = self.list_contacts
            message = 'asking Gajim for roster'
        try:
            print message
            res = self.method(dbus.String(''))
            results = []
            for buddy in res:
                name = buddy['name']
                jid = buddy['jid']
                status = buddy['show']
                if self.show_offline or (status != 'offline'):
                    if query in name.lower() or query in jid.lower():
                        if '@' in jid.lower():
                            transport = jid.split('@')[1].split('.')[0]
                        else:
                            transport = jid.split('.')[0]
                        if transport in TRANSPORTS:
                            icon = self.transport_icons[transport][status]
                        else:
                            icon = self.icons[status]
                        if buddy['name'] != '':
                            results += [GajimMatch(name=name, jid=jid, icon=icon, interface=self.interface)]
                        else:
                            results += [GajimMatch(name=jid.split('@')[0], jid=jid, icon=icon, interface=self.interface)]
            self._emit_query_ready(query, results)
        except:
            print sys.exc_info()
            return []

    def has_config(self):
        return True

    def show_config(self, parent):
        dialog = gtk.Dialog(_('Gajim Configuration'), parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        dialog.set_geometry_hints(min_width=250, min_height=100)
        table = gtk.Table(rows=1, columns=1)
        show_offline = gtk.CheckButton('Show offline contacts')
        show_offline.set_mode(True)
        t = GconfStore.get_instance().get_client().get_bool(GCONF_GAJIM_SHOWOFFLINE)
        if t != None:
            show_offline.set_active(t)

        table.attach(show_offline, 1, 2, 1, 2)   
        table.show_all()
        dialog.vbox.add(table) 
        response = dialog.run()
        if response == gtk.RESPONSE_ACCEPT:
            GconfStore.get_instance().get_client().set_bool(GCONF_GAJIM_SHOWOFFLINE, show_offline.get_active())
        dialog.destroy()

    @staticmethod
    def has_requirements():
        GajimHandler.INSTRUCTIONS = _('You can configure the handler to show or hide offline contacts.')
        return True
