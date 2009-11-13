#
#  twitter.py :  A module for the deskbar applet, that allows you to 
#                send messages to twitter.com.
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
#
# 1.0 : Initial release.
# 1.1 : Works with Deskbar 2.19.6's new module API
# 1.2 : Small bug fix

import gtk, os, twitter, pynotify
from urllib2 import URLError
import deskbar, deskbar.core.Indexer, deskbar.interfaces.Module, deskbar.core.Utils, deskbar.interfaces.Match
from deskbar.core.GconfStore import GconfStore
from gettext import gettext as _ 
_debug=False
if _debug:
    import traceback
GCONF_TWITTER_USER = GconfStore.GCONF_DIR+"/twitter/user"
GCONF_TWITTER_PASSWORD = GconfStore.GCONF_DIR+"/twitter/password"
TWITTER_ICON = [
"16 16 127 2",
"       c None",
".      c #FBFDFD",
"+      c #F5FAFB",
"@      c #F4FBFC",
"#      c #F6FBFB",
"$      c #F8FCFC",
"%      c #FEFFFF",
"&      c #F7FCFC",
"*      c #D4F8FC",
"=      c #C2F4FB",
"-      c #CDF7FC",
";      c #F5FCFC",
">      c #FDFEFE",
",      c #FEFEFE",
"'      c #E9FAFC",
")      c #A9F1F8",
"!      c #B1F1F8",
"~      c #A5F0F8",
"{      c #E1F9FC",
"]      c #F9FCFC",
"^      c #E3F9FB",
"/      c #96EEF7",
"(      c #9AEEF7",
"_      c #93EEF7",
":      c #DEF9FC",
"<      c #FAFBFA",
"[      c #F8FBFB",
"}      c #F8FAFB",
"|      c #F9FBFC",
"1      c #FCFDFD",
"2      c #E1F9FB",
"3      c #8BECF6",
"4      c #90EDF6",
"5      c #8CECF6",
"6      c #B4F3F9",
"7      c #CAF6FB",
"8      c #C8F6FB",
"9      c #C7F6FB",
"0      c #E2FAFC",
"a      c #FAFCFD",
"b      c #DFF8FB",
"c      c #7FEAF5",
"d      c #84EBF6",
"e      c #85EBF5",
"f      c #7EEAF5",
"g      c #7CEAF5",
"h      c #7CEAF6",
"i      c #80EAF5",
"j      c #EDFBFD",
"k      c #DCF8FB",
"l      c #71E9F5",
"m      c #77EAF5",
"n      c #76E9F4",
"o      c #75E9F4",
"p      c #75EAF5",
"q      c #76E9F5",
"r      c #66E7F3",
"s      c #D7F9FC",
"t      c #D8F7FB",
"u      c #60E7F3",
"v      c #68E7F3",
"w      c #68E8F3",
"x      c #67E7F3",
"y      c #63E6F3",
"z      c #85ECF5",
"A      c #F8FEFE",
"B      c #FFFEFE",
"C      c #D5F7FA",
"D      c #50E5F1",
"E      c #58E6F2",
"F      c #4EE4F1",
"G      c #BCF4F9",
"H      c #F0FBFD",
"I      c #EAFAFC",
"J      c #E6FAFB",
"K      c #FAFDFE",
"L      c #FFFFFE",
"M      c #CFF6FA",
"N      c #3AE3F0",
"O      c #46E4F1",
"P      c #39E2F0",
"Q      c #C6F6FA",
"R      c #FBFCFC",
"S      c #FCFEFE",
"T      c #D4F6FA",
"U      c #23E1EF",
"V      c #29E2F0",
"W      c #18E0EF",
"X      c #9EF1F8",
"Y      c #FFFDFC",
"Z      c #FDFDFD",
"`      c #FEFDFD",
" .     c #FCFCFC",
"..     c #FEFFFE",
"+.     c #F1FBFB",
"@.     c #00DFEF",
"#.     c #00E0EF",
"$.     c #14E0EF",
"%.     c #8AEEF6",
"&.     c #A6F1F8",
"*.     c #A2F1F8",
"=.     c #A0F1F8",
"-.     c #A4F1F8",
";.     c #86EDF6",
">.     c #00DBEC",
",.     c #00DEEE",
"'.     c #00DCED",
").     c #00DCEC",
"!.     c #00DBED",
"~.     c #19DEEE",
"{.     c #E7FAFD",
"].     c #F9FCFD",
"^.     c #5EE7F3",
"/.     c #00DAEC",
"(.     c #00DDEE",
"_.     c #BEF5FA",
":.     c #94EEF7",
"<.     c #07DDED",
"[.     c #08DDED",
"}.     c #38E2F0",
"|.     c #F2FCFD",
"1.     c #FAFAF9",
"2.     c #F1FAFC",
"3.     c #DAF8FB",
"4.     c #D8F8FB",
"5.     c #D9F8FB",
"6.     c #F3FBFC",
"    . + @ # $                   ",
"  % & * = - ; >                 ",
"  , ' ) ! ~ { ]                 ",
"  , ^ / ( _ : < [ [ } | 1       ",
"  , 2 3 4 5 6 7 8 9 9 8 0 a     ",
"    b c d e f g g h g g i j     ",
"    k l m n n o p q n m r s     ",
"  , t u v w v x v x x y z A     ",
"  B C D E F G H ' I ' J K       ",
"  L M N O P Q R % , , S         ",
"  , T U V W X Y Z ` `  ...      ",
"  , +.V @.#.$.%.&.*.=.-.:       ",
"    Y ;.>.,.,.'.'.'.).!.~.{.    ",
"    > ].^./.(.,.,.,.,.,./._.    ",
"      1 Z :.U <.<.[.[.'.}.|.    ",
"        > 1.2.3.4.5.5.4.6.]     "
]
ICON = gtk.gdk.pixbuf_new_from_xpm_data(TWITTER_ICON)

HANDLERS = ["TwitterHandler"]

class TwitterAction(deskbar.interfaces.Action):
    def __init__(self, name=None):
        deskbar.interfaces.Action.__init__(self, name)
        self._name = name

    def activate(self, text=None):
        self.user = GconfStore.get_instance().get_client().get_string(GCONF_TWITTER_USER)
        self.password = GconfStore.get_instance().get_client().get_string(GCONF_TWITTER_PASSWORD)
        api = twitter.Api()
        pynotify.init("Deskbar Twitter Plugin")
        message = "Your post to Twitter might have had a problem"
        try:
            results = api.PostUpdate(self.user, self.password, self._name)
            if self._name == results.text:
                message = "Your post to Twitter was successful"
            n = pynotify.Notification("Twitter Results", message)
            n.set_icon_from_pixbuf(ICON)
            n.show()
        except URLError, e:
            if e.code == 401:
                message = "Incorrect Twitter Username and/or Password"
            if e.code == 403:
                message = "Your request Twitter was forbidden"
            if e.code == 404:
                message = "The URL for Twitter was not found"
            if e.code == 408:
                message = "The request to Twitter timed out.  Try again later."
            n = pynotify.Notification("Twitter Results", message)
            n.set_icon_from_pixbuf(ICON)
            n.show()

    def get_verb(self):
        return _("Send <b>%(name)s</b> to Twitter")


class TwitterMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, user=None, password=None, **kwargs):
        deskbar.interfaces.Match.__init__(self, name=name, user=user, password=password, category="actions",  **kwargs)
        self.user = user
        self.password = password
        self.name = name
        self.add_action( TwitterAction(self.name))

    def get_hash(self, text=None):
        return True

    def get_icon(self):
        return ICON

class TwitterHandler(deskbar.interfaces.Module):
    INFOS = {'icon': ICON,
             "name": _("Twitter"),
             "description": _("What are you doing?"),
             "version": "1.1",
            }

    def __init__(self):
        deskbar.interfaces.Module.__init__(self)

    def query(self, query): 
        self._emit_query_ready(query, [TwitterMatch(query)])

    def has_config(self):
        return True

    def show_config(self, parent):
        dialog = gtk.Dialog(_("Twitter Account"), parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        table = gtk.Table(rows=3, columns=2)

        table.attach(gtk.Label(_("Enter your Twitter account information")), 0, 2, 0, 1)

        user_entry = gtk.Entry()
        u = GconfStore.get_instance().get_client().get_string(GCONF_TWITTER_USER)
        if u != None:
            user_entry.set_text(u)
        table.attach(gtk.Label(_("Username: ")), 0, 1, 1, 2)
        table.attach(user_entry, 1, 2, 1, 2)

        password_entry = gtk.Entry()
        password_entry.set_visibility(True) #this should be false, but the value disappears when set as false
        p = GconfStore.get_instance().get_client().get_string(GCONF_TWITTER_PASSWORD)
        if p != None:
            password_entry.set_text(p)
        table.attach(gtk.Label(_("Password: ")), 0, 1, 2, 3)
        table.attach(password_entry, 1, 2, 2, 3)
        table.show_all()
        dialog.vbox.add(table)

        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_ACCEPT:
            GconfStore.get_instance().get_client().set_string(GCONF_TWITTER_USER, user_entry.get_text())
            GconfStore.get_instance().get_client().set_string(GCONF_TWITTER_PASSWORD, password_entry.get_text())

    @staticmethod
    def has_requirements():
        #We need user and password
        if not GconfStore.get_instance().get_client().get_string(GCONF_TWITTER_USER) or not GconfStore.get_instance().get_client().get_string(GCONF_TWITTER_PASSWORD):
            TwitterHandler.INSTRUCTIONS = _("You need to configure your Twitter account.")
            return True
        else:
            TwitterHandler.INSTRUCTIONS = _("You can modify your Twitter account.")
            return True

