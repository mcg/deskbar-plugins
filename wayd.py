#
#  wayd.py :  "What Are You Doing(WAYD) A module for the deskbar applet, that allows you to 
#              set your status on multiple networks(twitter, jaiku, etc..)
#
#  Copyright (C) 2007 Matthew Gregg 
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
#
#  Authors: Matthew Gregg <mcg at no_spam_me butterfat.net>
#           Rod Hilton <rod at no_spam_me rodhilton.com>
#
# 1.0 : Initial release(works with twitter and jaiku). I need an icon.
# 1.1 : Checking for accounts being configured
# 1.2 : More error handling for twitter
# 1.3 : Works with python-twitter 0.5
# 1.4 : Added Pownce
# 1.5 : Fixed 2 syntax errors, added a message length check (otherwise it just errored confusingly)
#       Removed Gconf storage for user/pass/key using GnomeKeyring now.(thanks Mikkel Kamstrup Erlandsen)

import gtk, twitter, pynotify, simplejson
import urllib2
import gnomekeyring
from urllib import urlencode, urlopen
import deskbar, deskbar.interfaces.Module, deskbar.core.Utils, deskbar.interfaces.Match, deskbar.interfaces.Action
from gettext import gettext as _ 
_debug=False
if _debug:
    import traceback

HANDLERS = ["WaydHandler"]
class Account :
    """
    This is an abstraction used to make it easier to move
    away from a GConf password storage solution (Seahorse anyone?)
    
    WARNING: This API is synchronous. This does not matter much to deskbar since
             web based modules will likely run in threads anyway.
    
    This class was cpoied (almost) verbatim from Sebastian Rittau's blog
    found on http://www.rittau.org/blog/20070726-00.
    """
    def __init__(self, host, realm):
        self._realm = realm
        self._host = host
        self._key = ""
        self._protocol = "http"
        self._keyring = gnomekeyring.get_default_keyring_sync()

    def has_credentials(self):
        try:
            attrs = {"server": self._host, "protocol": self._protocol}
            items = gnomekeyring.find_items_sync(gnomekeyring.ITEM_NETWORK_PASSWORD, attrs)
            if len(items) > 0 :
                if items[0].attributes["user"] != "" and \
                   items[0].secret != "" :
                   return True
                else :
                    return False
        except gnomekeyring.DeniedError:
            return False
        except gnomekeyring.NoMatchError:
            return False
    
    def get_host (self):
        return self._host
    
    def get_realm (self):
        return self._realm
    
    def get_credentials(self):
        attrs = {"server": self._host, "protocol": self._protocol}
        items = gnomekeyring.find_items_sync(gnomekeyring.ITEM_NETWORK_PASSWORD, attrs)
        return (items[0].attributes["user"], items[0].secret, items[0].attributes["key"])

    def set_credentials(self, user, pw, key=""):
        attrs = {
                "user": user,
                "server": self._host,
                "protocol": self._protocol,
                "key": key,
            }
        gnomekeyring.item_create_sync(gnomekeyring.get_default_keyring_sync(),
                gnomekeyring.ITEM_NETWORK_PASSWORD, self._realm, attrs, pw, True)

class Configured():

    def twitter(self):
        twit_account = Account ("twitter.com", "Twitter API")
        return twit_account.has_credentials()

    def jaiku(self):
        jaiku_account = Account ("jaiku.com", "Jaiku API")
        return jaiku_account.has_credentials()

    def pownce(self):
        pownce_account = Account ("pownce.com", "Pownce API")
        return pownce_account.has_credentials()


    def all(self):
        twit_account = Account ("twitter.com", "Twitter API")
        jaiku_account = Account ("jaiku.com", "Jaiku API")
        pownce_account = Account ("pownce.com", "Pownce API")
        if twit_account.has_credentials() and jaiku_account.has_credentials() and pownce_account.has_credentials():
            return True
        else:
            return False


class Status():
    def __init__(self, provider=None):
        self.provider = provider

    def update(self, text=None):
        self.text = text
        if self.provider == 'twitter':
            self.twitter()
        elif self.provider == 'jaiku':
            self.jaiku()
        elif self.provider == 'pownce':
            self.pownce()
        elif self.provider == 'all':
            self.twitter()
            self.jaiku()
            self.pownce()

    def twitter(self):
        print "Trying Twitter update"
        twit_account = Account ("twitter.com", "Twitter API")
        user, password, key = twit_account.get_credentials()
        api = twitter.Api(user, password)
        pynotify.init("Deskbar Wayd Plugin - Twitter")
        message = "Your post to Twitter might have had a problem"

        if len(self.text) > 140:
            message="Your post is too long for Twitter."
            n = pynotify.Notification("Twitter Results", message, "stock_internet")
            n.show()
            return

        try:
            results = api.PostUpdate(self.text)
            if self.text == results.text:
                message = "Your post to Twitter was successful"
            n = pynotify.Notification("Twitter Results", message, "stock_internet")
            n.show()
        except urllib2.URLError, e:
            if e.code == 401:
                message = "Incorrect Twitter Username and/or Password"
            if e.code == 403:
                message = "Your request Twitter was forbidden"
            if e.code == 404:
                message = "The URL for Twitter was not found"
            if e.code == 408:
                message = "The request to Twitter timed out.  Try again later."
            n = pynotify.Notification("Twitter Results", message, "stock_internet")
            n.show()
        except:
                message = "Something bad happened trying to post to Twitter.  Twitter might be down"
                n = pynotify.Notification("Twitter Results", message, "stock_internet")
                n.show()

    def jaiku(self):
        print "Trying Jaiku update"
        jaiku_account = Account ("jaiku.com", "Jaiku API")
        user, password, key = jaiku_account.get_credentials()
        url = "http://api.jaiku.com/json?user=%s&personal_key=%s" % (user, key)
        pynotify.init("Deskbar Wayd Plugin - Jaiku")
        message = "Your post to Jaiku might have had a problem"
        data = urlencode({"method": "presence.send", "message": self.text})

        try:
            result = simplejson.load(urlopen(url,data))
            if result['status'] == 'ok':
                message = "Your post to Jaiku was successful"
            else:
                message = result['message']
            n = pynotify.Notification("Jaiku Results", message, "stock_internet")
            n.show()
        except urllib2.URLError, e:
            if e.code == 401:
                message = "Incorrect Jaiku Username and/or Password"
            if e.code == 403:
                message = "Your Jaiku request was forbidden"
            if e.code == 404:
                message = "The URL for Jaiku was not found"
            if e.code == 408:
                message = "The request to Jaiku timed out.  Try again later."
            n = pynotify.Notification("Jaiku Results", message, "stock_internet")
            n.show()

    def pownce(self):
        print "Trying Pownce update"
        pownce_account = Account ("pownce.com", "Pownce API")
        user, password, key = pownce_account.get_credentials()
        url = "http://%s:%s@api.pownce.com/2.0/send/message.json" % (user, password)
        pynotify.init("Deskbar Wayd Plugin - Pownce")
        message = "Your post to Pownce might have had a problem"
        data = urlencode({"app_key" : "4d7p84417z5u1871edn578j300t14c4s", 
                          "note_body" : self.text,
                          "note_to" : "public"})

        try:
            result = simplejson.load(urlopen(url,data))
            if result.has_key("error"):
                message = result['error']['message']
            else:
               if result['body'] == self.text:
                    message = "Your post to Pownce was successful"
            n = pynotify.Notification("Pownce Results", message, "stock_internet")
            n.show()
        except urllib.URLError, e:
            if e.code == 401:
                message = "Incorrect Pownce Username and/or Password"
            if e.code == 403:
                message = "Your Pownce request was forbidden"
            if e.code == 404:
                message = "The URL for Pownce was not found"
            if e.code == 408:
                message = "The request to Pownce timed out.  Try again later."
            n = pynotify.Notification("Pownce Results", message, "stock_internet")
            n.show()

class AllAction(deskbar.interfaces.Action):
    def __init__(self, name=None):
        deskbar.interfaces.Action.__init__(self, name)
        self._name = name

    def activate(self, text=None):
        a = Status('all')
        a.update(self._name)

    def get_verb(self):
        return _("Set your status as <b>%(name)s</b> on all registered services")

    def get_hash(self, text=None):
        return self._name

class TwitterAction(deskbar.interfaces.Action):
    def __init__(self, name=None):
        deskbar.interfaces.Action.__init__(self, name)
        self._name = name

    def activate(self, text=None):
        t = Status('twitter')
        t.update(self._name)

    def get_verb(self):
        return _("Set your status as <b>%(name)s</b> on Twitter")

    def get_hash(self, text=None):
        return "Twitter Action"


class JaikuAction(deskbar.interfaces.Action):
    def __init__(self, name=None):
        deskbar.interfaces.Action.__init__(self, name)
        self._name = name

    def activate(self, text=None):
        j = Status('jaiku')
        j.update(self._name)

    def get_verb(self):
        return _("Set your status as <b>%(name)s</b> on Jaiku")

    def get_hash(self, text=None):
        return "Jaiku Action"

class PownceAction(deskbar.interfaces.Action):
    def __init__(self, name=None):
        deskbar.interfaces.Action.__init__(self, name)
        self._name = name

    def activate(self, text=None):
        p = Status('pownce')
        p.update(self._name)

    def get_verb(self):
        return _("Set your status as <b>%(name)s</b> on Pownce")

    def get_hash(self, text=None):
        return "Pownce Action"

class WaydMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, **kwargs):
        deskbar.interfaces.Match.__init__(self, icon="stock_internet", category="actions",  **kwargs)
        self.name = name
        c = Configured()
        if c.all():
            self.add_action(AllAction(self.name))
        if c.twitter():
            self.add_action(TwitterAction(self.name))
        if c.jaiku():
            self.add_action(JaikuAction(self.name))
        if c.pownce():
            self.add_action(PownceAction(self.name))

    def get_hash(self, text=None):
        return 'Wayd Match'

    def get_name(self, text=None):
        return _("Set your status as <b>"+self.name+"</b> on all registered services")

class WaydHandler(deskbar.interfaces.Module):
    INFOS = {'icon': deskbar.core.Utils.load_icon("stock_internet"),
             "name": _("Wayd"),
             "description": _("What are you doing? Send status to Twitter, Jaiku, Pownce, etc..."),
             "version": "1.5",
            }

    def __init__(self):
        deskbar.interfaces.Module.__init__(self)

    def query(self, query): 
        self._emit_query_ready(query, [WaydMatch(query)])

    def has_config(self):
        return True

    def show_config(self, parent):
        dialog = gtk.Dialog(_("Wayd Accounts"), parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
   
        twit_account = Account ("twitter.com", "Twitter API")
        jaiku_account = Account ("jaiku.com", "Jaiku API")
        pownce_account = Account ("pownce.com", "Pownce API")
 
        twit_table = gtk.Table(rows=3, columns=2)

        twit_table.attach(gtk.Label(_("Enter your Twitter account information")), 0, 2, 0, 1)

        twit_user_entry = gtk.Entry()
        twit_password_entry = gtk.Entry()
        twit_password_entry.set_visibility(True) #this should be false, but the value disappears when set as false
        if twit_account.has_credentials():
            user, password, key = twit_account.get_credentials()
            twit_user_entry.set_text(user)
            twit_password_entry.set_text(password)

        twit_table.attach(gtk.Label(_("Username: ")), 0, 1, 1, 2)
        twit_table.attach(twit_user_entry, 1, 2, 1, 2)

        twit_table.attach(gtk.Label(_("Password: ")), 0, 1, 2, 3)
        twit_table.attach(twit_password_entry, 1, 2, 2, 3)
        twit_table.show_all()
        dialog.vbox.add(twit_table)

        jaiku_table = gtk.Table(rows=4, columns=2)

        jaiku_user_entry = gtk.Entry()
        jaiku_password_entry = gtk.Entry()
        jaiku_key_entry = gtk.Entry()
        jaiku_table.attach(gtk.Label(_("Enter your Jaiku account information")), 0, 2, 0, 1)
        if jaiku_account.has_credentials():
            user, password, key = jaiku_account.get_credentials()
            jaiku_user_entry.set_text(user)
            jaiku_password_entry.set_text(password)
            jaiku_key_entry.set_text(key)

        jaiku_table.attach(gtk.Label(_("Username: ")), 0, 1, 1, 2)
        jaiku_table.attach(jaiku_user_entry, 1, 2, 1, 2)

        jaiku_password_entry.set_visibility(True) #this should be false, but the value disappears when set as false
        jaiku_table.attach(gtk.Label(_("Password: ")), 0, 1, 2, 3)
        jaiku_table.attach(jaiku_password_entry, 1, 2, 2, 3)

        jaiku_table.attach(gtk.Label(_("API Key: ")), 0, 1, 3, 4)
        jaiku_table.attach(jaiku_key_entry, 1, 2, 3, 4)
        jaiku_table.show_all()
        dialog.vbox.add(jaiku_table)

        pownce_table = gtk.Table(rows=3, columns=2)

        pownce_table.attach(gtk.Label(_("Enter your Pownce account information")), 0, 2, 0, 1)

        pownce_user_entry = gtk.Entry()
        pownce_password_entry = gtk.Entry()
        if pownce_account.has_credentials():
            user, password, key = pownce_account.get_credentials()
            pownce_user_entry.set_text(user)
            pownce_password_entry.set_text(password)

        pownce_table.attach(gtk.Label(_("Username: ")), 0, 1, 1, 2)
        pownce_table.attach(pownce_user_entry, 1, 2, 1, 2)

        pownce_password_entry.set_visibility(True) #this should be false, but the value disappears when set as false
        pownce_table.attach(gtk.Label(_("Password: ")), 0, 1, 2, 3)
        pownce_table.attach(pownce_password_entry, 1, 2, 2, 3)
        pownce_table.show_all()
        dialog.vbox.add(pownce_table)

        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_ACCEPT:
            self.account = Account ("twitter.com", "Twitter API")
            print("Registering credentials for %s on %s" % (self.account.get_realm(), self.account.get_host()))
            self.account.set_credentials(twit_user_entry.get_text(), twit_password_entry.get_text())

            self.account = Account ("jaiku.com", "Jaiku API")
            print("Registering credentials for %s on %s" % (self.account.get_realm(), self.account.get_host()))
            self.account.set_credentials(jaiku_user_entry.get_text(), jaiku_password_entry.get_text(), jaiku_key_entry.get_text())

            self.account = Account ("pownce.com", "Pownce API")
            print("Registering credentials for %s on %s" % (self.account.get_realm(), self.account.get_host()))
            self.account.set_credentials(pownce_user_entry.get_text(), pownce_password_entry.get_text())

    @staticmethod
    def has_requirements():
        #We need user and password
        c = Configured()

        if not c.twitter() and not c.jaiku() and not c.pownce():
            WaydHandler.INSTRUCTIONS = _("You need to configure an account.")
            return True
        else:
            WaydHandler.INSTRUCTIONS = _("You can modify your accounts.")
            return True

