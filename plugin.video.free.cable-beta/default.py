#!/usr/bin/python
# -*- coding: utf-8 -*-
import resources.lib._addoncompat as _addoncompat
import resources.lib._common as _common
import resources.lib._contextmenu as _contextmenu
import operator
import os
import sys
import xbmcaddon
import xbmcplugin

pluginHandle = int(sys.argv[1])

__plugin__ = 'FREE CABLE'
__authors__ = 'BlueCop'
__credits__ = 'moneymaker, slices, zero'
__version__ = '0.7.1'

print '\n\n\n start of FREE CABLE plugin'

def modes():
	if sys.argv[2] == '':
		all_description = ''
		for network, name in sorted(_common.site_dict.iteritems(), key = operator.itemgetter(1)):
			if _addoncompat.get_setting(network) == 'true':
				if name.endswith(', The'):
					name = 'The ' + name.replace(', The', '')
				all_description += name + ', '
		count = 0
		_common.add_directory(xbmcaddon.Addon(id = _common.ADDONID).getLocalizedString(39000), 'Favorlist', 'NoUrl', thumb = _common.FAVICON, count = count, description = xbmcaddon.Addon(id = _common.ADDONID).getLocalizedString(39001) + '\n' + all_description)
		count += 1
		_common.add_directory(xbmcaddon.Addon(id = _common.ADDONID).getLocalizedString(39002), 'Masterlist', 'NoUrl', thumb = _common.ALLICON, count = count, description = xbmcaddon.Addon(id = _common.ADDONID).getLocalizedString(39003) + '\n' + all_description)
		count += 1
		for network, name in sorted(_common.site_dict.iteritems(), key = operator.itemgetter(1)):
			station_icon = os.path.join(_common.IMAGEPATH, network + '.png')
			if name.endswith(', The'):
				name = 'The ' + name.replace(', The', '')
			if _addoncompat.get_setting(network) == 'true':
				_common.add_directory(name, network, 'rootlist', thumb = station_icon, fanart = _common.PLUGINFANART, description = _common.site_descriptions[network], count = count)
			count += 1
		xbmcplugin.addSortMethod(pluginHandle, xbmcplugin.SORT_METHOD_PLAYLIST_ORDER)
		_common.set_view()
		xbmcplugin.endOfDirectory(pluginHandle)
	elif _common.args.mode == 'Masterlist':
		xbmcplugin.addSortMethod(pluginHandle, xbmcplugin.SORT_METHOD_LABEL)
		_common.load_showlist()
		_common.set_view('tvshows')
		xbmcplugin.endOfDirectory(pluginHandle)
	elif _common.args.mode == 'Favorlist':   
		xbmcplugin.addSortMethod(pluginHandle, xbmcplugin.SORT_METHOD_LABEL)
		_common.load_showlist(favored = 1)
		_common.set_view('tvshows')
		xbmcplugin.endOfDirectory(pluginHandle)
	elif _common.args.mode == '_contextmenu':
		exec '_contextmenu.%s()' % _common.args.sitemode
	elif _common.args.mode == '_common':
		exec '_common.%s()' % _common.args.sitemode
	elif _common.args.mode in _common.site_dict.keys():
		exec 'import resources.lib.%s as sitemodule' % _common.args.mode
		exec 'sitemodule.%s()' % _common.args.sitemode
		if not _common.args.sitemode.startswith('play'):
			xbmcplugin.endOfDirectory(pluginHandle)
modes()
sys.modules.clear()
