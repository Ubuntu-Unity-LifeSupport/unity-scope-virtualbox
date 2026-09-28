#! /usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (C) 2013 David Callé <davidc@framli.eu>
# Copyright (C) 2012 Christopher Wayne <cwayne@ubuntu.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Unity, UnityExtras
from gi.repository import Gio, GLib
import subprocess
import re
import shlex
import gettext
import datetime

APP_NAME = 'unity-scope-virtualbox'
LOCAL_PATH = '/usr/share/locale/'
gettext.bindtextdomain(APP_NAME, LOCAL_PATH)
gettext.textdomain(APP_NAME)
_ = gettext.gettext

GROUP_NAME = 'com.canonical.Unity.Scope.Boxes.Virtualbox'
UNIQUE_PATH = '/com/canonical/unity/scope/boxes/virtualbox'
SEARCH_URI = ''
SEARCH_HINT = _('Search Virtualbox')
NO_RESULTS_HINT = _('Sorry, there is no VirtualBox machine that matches your search.')
PROVIDER_CREDITS = _('Powered by VirtualBox')
SVG_DIR = '/usr/share/icons/unity-icon-theme/places/svg/'
PROVIDER_ICON = SVG_DIR+'service-virtualbox.svg'
DEFAULT_RESULT_ICON = 'virtualbox'
DEFAULT_RESULT_MIMETYPE = 'application/x-virtualbox-vbox'
DEFAULT_RESULT_TYPE = Unity.ResultType.DEFAULT
EXTRA_DATA = None

c1 = {'id'      :'boxes',
      'name'    :_('Virtual Machines'),
      'icon'    :SVG_DIR+'group-boxes.svg',
      'renderer':Unity.CategoryRenderer.VERTICAL_TILE}
CATEGORIES = [c1]

FILTERS = []

EXTRA_METADATA = []

def search(search, filters):
    '''
    Any search method returning results as a list of tuples.
    Available tuple fields:
    uri (string)
    icon (string)
    title (string)
    comment (string)
    dnd_uri (string)
    mimetype (string)
    category (int)
    result_type (Unity ResultType)
    extras metadata fields (variant)
    '''
    results = []
    try:
        if not EXTRA_DATA:
            vboxlist = subprocess.check_output(['vboxmanage', 'list', 'vms'])
        else:
            vboxlist = EXTRA_DATA
        for vbox in vboxlist.splitlines():
            if not re.match('\".*\"\s\{.*-.*\}', vbox.decode('utf-8')):
                continue
            vbox_name = re.sub('\{.*\}', '', vbox.decode('utf-8'))
            uuid = re.match(r'.*\{(.*)\}', vbox.decode('utf-8'))
            if uuid:
                uuid = uuid.group(1)
            else:
                uuid = shlex.split(vbox_name)[0]
            if search.lower() in vbox_name.lower():
                results.append({'uri':uuid,
                                'title':shlex.split(vbox_name)[0]})
    except Exception as error:
        print (error)
    return results


# Classes below this point establish communication
# with Unity, you probably shouldn't modify them.


class MySearch (Unity.ScopeSearchBase):
    def __init__(self, search_context):
        super (MySearch, self).__init__()
        self.set_search_context (search_context)

    def do_run (self):
        '''
        Adds results to the model
        '''
        try:
            result_set = self.search_context.result_set
            for i in search(self.search_context.search_query,
                            self.search_context.filter_state):
                if not 'uri' in i or not i['uri'] or i['uri'] == '':
                    continue
                if not 'icon' in i or not i['icon'] or i['icon'] == '':
                    i['icon'] = DEFAULT_RESULT_ICON
                if not 'mimetype' in i or not i['mimetype'] or i['mimetype'] == '':
                    i['mimetype'] = DEFAULT_RESULT_MIMETYPE
                if not 'result_type' in i or not i['result_type'] or i['result_type'] == '':
                    i['result_type'] = DEFAULT_RESULT_TYPE
                if not 'category' in i or not i['category'] or i['category'] == '':
                    i['category'] = 0
                if not 'title' in i or not i['title']:
                    i['title'] = ''
                if not 'comment' in i or not i['comment']:
                    i['comment'] = ''
                if not 'dnd_uri' in i or not i['dnd_uri'] or i['dnd_uri'] == '':
                    i['dnd_uri'] = i['uri']
                i['provider_credits'] = GLib.Variant('s', PROVIDER_CREDITS)
                result_set.add_result(**i)
        except Exception as error:
            print (error)

class Preview (Unity.ResultPreviewer):

    def do_run(self):
        preview = Unity.GenericPreview.new(self.result.title, self.result.comment, None)
        preview.props.image_source_uri = self.result.icon_hint
        vboxinfo = subprocess.check_output(['vboxmanage', 'showvminfo', self.result.uri])
        description_line = False
        for line in vboxinfo.splitlines():
            line = line.decode('utf-8')
            if line.startswith('Guest OS:'):
                os = re.match(r'.*:\s+([^\s].*)',line)
                if os:
                    os_text = os.group(1)
                    preview.add_info(Unity.InfoHint.new("os", _("Operating System"), None, os_text))
            if line.startswith('Memory size:'):
                memsize = re.match(r'.*:\s+([^\s].*)',line)
                if memsize:
                    memsize_text = memsize.group(1)
                    preview.add_info(Unity.InfoHint.new("memsize", _("Base Memory"), None, memsize_text))
            if line.startswith('VRAM size:'):
                vramsize = re.match(r'.*:\s+([^\s].*)',line)
                if vramsize:
                    vramsize_text = vramsize.group(1)
                    preview.add_info(Unity.InfoHint.new("vramsize", _("Video Memory"), None, vramsize_text))
            if line.startswith('Number of CPUs:'):
                numcpu = re.match(r'.*:\s+([^\s].*)',line)
                if numcpu:
                    numcpu_text = numcpu.group(1)
                    preview.add_info(Unity.InfoHint.new("numcpu", _("Processors"), None, numcpu_text))
            if line.startswith('State:'):
                state = re.match(r'.*:\s+([^\s].*)\(since\s(.*)\)',line)
                if state:
                    state_text = state.group(1)
                    date = state.group(2)
                    translated_date = datetime.datetime.strptime(date[:-3], '%Y-%m-%dT%H:%M:%S.%f')
                    preview.props.subtitle = state_text.title() + "(%s)" % translated_date.strftime('%c')
            if line.startswith('Description:'):
                description_line = True
                continue
            if description_line:
                preview.props.description_markup = line
                description_line = False

        icon = Gio.FileIcon.new (Gio.file_new_for_path(PROVIDER_ICON))
        view_action = Unity.PreviewAction.new("launch", _("Launch"), icon)
        preview.add_action(view_action)
        return preview

class Scope (Unity.AbstractScope):
    def __init__(self):
        Unity.AbstractScope.__init__(self)

    def do_get_search_hint (self):
        return SEARCH_HINT

    def do_get_schema (self):
        '''
        Adds specific metadata fields
        '''
        schema = Unity.Schema.new ()
        if EXTRA_METADATA:
            for m in EXTRA_METADATA:
                schema.add_field(m['id'], m['type'], m['field'])
        #FIXME should be REQUIRED for credits
        schema.add_field('provider_credits', 's', Unity.SchemaFieldType.OPTIONAL)
        return schema

    def do_get_categories (self):
        '''
        Adds categories
        '''
        cs = Unity.CategorySet.new ()
        if CATEGORIES:
            for c in CATEGORIES:
                cat = Unity.Category.new (c['id'], c['name'],
                                          Gio.ThemedIcon.new(c['icon']),
                                          c['renderer'])
                cs.add (cat)
        return cs

    def do_get_filters (self):
        '''
        Adds filters
        '''
        fs = Unity.FilterSet.new ()
#        if FILTERS:
#            
        return fs

    def do_get_group_name (self):
        return GROUP_NAME

    def do_get_unique_name (self):
        return UNIQUE_PATH

    def do_create_search_for_query (self, search_context):
        se = MySearch (search_context)
        return se

    def do_create_previewer(self, result, metadata):
        rp = Preview()
        rp.set_scope_result(result)
        rp.set_search_metadata(metadata)
        return rp

    def do_activate(self, result, metadata, id):
        GLib.spawn_async(["/usr/bin/vboxmanage", "startvm", result.uri])
        return Unity.ActivationResponse(handled=Unity.HandledType.HIDE_DASH, goto_uri=None)

def load_scope():
    return Scope()
