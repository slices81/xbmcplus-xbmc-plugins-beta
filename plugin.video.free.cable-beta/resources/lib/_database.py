#!/usr/bin/python
# -*- coding: utf-8 -*-
import _addoncompat
import os
import sys
import urllib
import xbmc
from sqlite3 import dbapi2 as sqlite

DBVERSION = 1
PLUGINPATH = _addoncompat.get_path()
DBPATH = os.path.join(xbmc.translatePath(PLUGINPATH), 'resources', 'database')
DBFILE = os.path.join(DBPATH, 'shows.db')
OLDDBPATH = 'special://home/addons/script.module.free.cable.database/lib/'
OLDDBFILE = os.path.join(xbmc.translatePath(OLDDBPATH), 'shows.db')

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

def execute_command(command, values = [], commit = False, fetchone = False, fetchall = False):
	conn = sqlite.connect(DBFILE)
	conn.text_factory = str
	c = conn.cursor()
	data = c.execute(command, values)
	if commit is True:
		conn.commit()
	if (fetchone is False) and (fetchall is False):
		c.close()
		return data
	elif fetchone is True:
		return data.fetchone()
	elif fetchall is True:
		return data.fetchall()

def create_db():
	if os.path.exists(OLDDBFILE):
		print "OLDD"
		if not os.path.exists(DBPATH):
			os.mkdir(DBPATH)
		os.rename(OLDDBFILE, DBFILE)
	else:
		command = ('''CREATE TABLE shows(
					series_title TEXT,
					mode TEXT,
					submode TEXT,
					url TEXT,
					TVDB_ID TEXT,
					IMDB_ID TEXT,
					TVDBbanner TEXT,
					TVDBposter TEXT,
					TVDBfanart TEXT,
					first_aired TEXT,
					date TEXT,
					year INTEGER,
					actors TEXT,
					genres TEXT,
					network TEXT,
					plot TEXT,
					runtime TEXT,
					rating REAL,
					Airs_DayOfWeek TEXT,
					Airs_Time TEXT,
					status TEXT,
					has_full_episodes INTEGER,
					favor INTEGER,
					hide INTEGER,
					tvdb_series_title TEXT,
					PRIMARY KEY(series_title,mode,submode)
					);''')
		execute_command(command, commit = True)
		command = 'pragma user_version = 1'
		execute_command(command)

def check_db_version():
	command = 'pragma user_version;'
	current = int(execute_command(command, fetchone = True)[0])
	if current < DBVERSION:
		for v in range(current, DBVERSION):
			new_version = v + 1
			upgrade_db_to_version(new_version)

def upgrade_db_to_version(db_version):
	if db_version == 1:
		command = 'alter table shows add tvdb_series_title TEXT;'
	try:
		execute_command(command, commit = True)
		command = 'pragma user_version = %i' % db_version
		execute_command(command)
	except:
		print '_database :: DB-Version = %i' % db_version