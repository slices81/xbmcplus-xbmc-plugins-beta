#!/usr/bin/python
# -*- coding: utf-8 -*-
import _common
import _database
import urllib
import sys
import xbmc

class _Info:
	def __init__(self, s):
		args = urllib.unquote_plus(s).split(' , ')
		for x in args:
			try:
				(k, v) = x.split('=', 1)
				setattr(self, k, v.strip('"\''))
			except:
				pass

args = _Info(sys.argv[2][1:].replace('&', ' , '))

def delete_show():
	series_title, mode, submode, url = args.url.split('<join>')
	command = 'delete from shows where series_title = ? and mode = ? and submode = ?;'
	values = (series_title, mode, submode)
	_database.execute_command(command, values, commit = True)

def favor_show():
	series_title, mode, submode, url = args.url.split('<join>')
	command = 'update shows set favor = 1 where series_title = ? and mode = ? and submode = ?;'
	values = (series_title, mode, submode)
	_database.execute_command(command, values, commit = True)

def unfavor_show():
	series_title, mode, submode, url = args.url.split('<join>')
	command = 'update shows set favor = 0 where series_title = ? and mode = ? and submode = ?;'
	values = (series_title, mode, submode)
	_database.execute_command(command, values, commit = True)

def hide_show():
	series_title, mode, submode, url = args.url.split('<join>')
	command = 'update shows set hide = 1 where series_title = ? and mode = ? and submode = ?;'
	values = (series_title, mode, submode)
	_database.execute_command(command, values, commit = True)

def unhide_show():
	series_title, mode, submode, url = args.url.split('<join>')
	command = 'update shows set hide = 0 where series_title = ? and mode = ? and submode = ?;'
	values = (series_title, mode, submode)
	_database.execute_command(command, values, commit = True)
	_common.args.name=series_title
	refresh_menu(mode, submode)

def refresh_show():
	series_title, mode, submode, url = args.url.split('<join>')
	_common.get_serie(series_title, mode, submode, url, forceRefresh = True)
	_common.args.name = series_title
	refresh_menu(mode, submode)
	
def refresh_menu(mode, submode):
	exec 'import resources.lib.%s as sitemodule' % mode
	exec 'sitemodule.%s()' % submode
	xbmc.executebuiltin('Container.Refresh')