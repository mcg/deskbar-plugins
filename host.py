#
#  host.py : A host lookup module for the deskbar applet.
#
#  Copyright (C) 2006 by Matthew Gregg
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
# 1.0 : Initial release.
# 1.1 : Added simple regex to only limit calls queries until something that looks like an IP is entered
# 1.2 Works with Deskbar 2.19.6's new module api
#

from gettext import gettext as _
import gtk, re
from socket import *
import deskbar, deskbar.core.Indexer, deskbar.interfaces.Module, deskbar.core.Utils, deskbar.interfaces.Match, deskbar.core.GconfStore
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction

#HELP_TEXT = _("""Given a host name or IP returns a DNS lookup""")

#def _on_more_information(x):
#  deskbar.Utils.more_information_dialog(None,_("Hostname lookups", HELP_TEXT)

HANDLERS = [ "HostLookupHandler"]


class HostLookupMatch(deskbar.interfaces.Match):
  def __init__(self, name=None, **kwargs):
        deskbar.interfaces.Match.__init__(self, name=name, icon="gtk-network", category="actions",**kwargs)
        self.name = name
        self.add_action(CopyToClipboardAction(self.name, self.name))

  def get_category(self):
      return "actions"

  def get_verb(self):
      return _("Host: <b>%(name)s</b>")
  
  def get_hash(self, name=None):
      return "foo"

class HostLookupHandler(deskbar.interfaces.Module):
  INFOS = {'icon': deskbar.core.Utils.load_icon("gtk-network"),
           "name": _("Host Lookup"),
           "description": _("Given a host name or IP returns a DNS lookup"),
           "version": "1.2",
          }

  def __init__(self):
      deskbar.interfaces.Module.__init__(self)
      self.m = re.compile('\d+?\.\d+?\.\d+?\.\d+?')

  def query(self, query):
      #deskbar.Handler.Handler.__init__(self, "gtk-network")
      result = []
      if self.m.match(query):
          try:
              print "Doing host lookup for %s" % query
              host = gethostbyaddr(query)
              #for x in self.host:
                  #  result.append(HostLookupMatch(self, name=x))
                  #return result
              self._emit_query_ready(query, [HostLookupMatch(name=host[0])])
          except:
              return []
      else:
          return []
