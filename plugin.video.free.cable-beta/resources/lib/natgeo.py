#!/usr/bin/python
# -*- coding: utf-8 -*-
import _addoncompat
import _common
import _connection
import _m3u8
import re
import sys
import urllib
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup, SoupStrainer

pluginHandle = int(sys.argv[1])

SITE = 'natgeo'
BASE = 'http://video.nationalgeographic.com'
SHOWS = 'http://video.nationalgeographic.com/video/national-geographic-channel/shows/'
SPECIALS = 'http://video.nationalgeographic.com/video/national-geographic-channel/specials-1/'

def masterlist():
	master_dict = {}
	master_db = []
	for master_url in (SHOWS, SPECIALS):
		master_data = _connection.getURL(master_url)
		master_tree = BeautifulSoup(master_data, 'html.parser', parse_only = SoupStrainer('div', id = 'content'))
		master_menu = master_tree.find_all('div', class_ = 'natgeov-cat-group')
		for master_item in master_menu:
			master_name = master_item.h3.text.split('(')[0].strip()
			season_url = BASE + master_item.a['href']
			master_dict[master_name] = season_url
	for master_name, season_url in master_dict.iteritems():
		master_db.append((master_name, SITE, 'episodes', season_url))
	return master_db

def rootlist():
	root_dict = {}
	for root_url in (SHOWS, SPECIALS):
		root_data = _connection.getURL(root_url)
		root_tree = BeautifulSoup(root_data, 'html.parser', parse_only = SoupStrainer('div', id = 'content'))
		root_menu = root_tree.find_all('div', class_ = 'natgeov-cat-group')
		for root_item in root_menu:
			root_name = root_item.h3.text.split('(')[0].strip()
			season_url = BASE + root_item.a['href']
			root_dict[root_name] = season_url
	for root_name, season_url in root_dict.iteritems():
		_common.add_show(root_name, SITE, 'episodes', season_url)
	_common.set_view('tvshows')

def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(episode_url)
	episode_tree = BeautifulSoup(episode_data)
	add_videos(episode_tree)
	pagedata = re.compile('new Paginator\((.+?),(.+?)\)').findall(episode_data)
	if pagedata:
		total   = int(pagedata[0][0])
		current = int(pagedata[0][1])
		if total > 1:
			for page in range(1,total):
				episode_data = _connection.getURL(episode_url + '/' + str(page) + '/')
				episode_tree = BeautifulSoup(episode_data)
				add_videos(episode_tree)
	_common.set_view('episodes')

def add_videos(episode_tree):
	episode_menu = episode_tree.find_all('div', class_ = 'vidthumb')
	show_name = episode_tree.find('h3', id = 'natgeov-section-title').text
	for episode_item in episode_menu:
		episode_name = episode_item.a['title']
		episode_thumb = episode_item.img['src'].split('url=')[1]
		episode_duration = episode_item.span.text
		url = BASE + episode_item.a['href']
		u = sys.argv[0]
		u += '?url="'+urllib.quote_plus(url)+'"'
		u += '&mode="' + SITE + '"'
		u += '&sitemode="play_video"'
		infoLabels = {	'title' : episode_name,
						'duration' : episode_duration,
						'tvshowtitle' : show_name }
		_common.add_video(u, episode_name, episode_thumb, infoLabels = infoLabels)

def play_video(video_url = _common.args.url):
	hbitrate = -1
	sbitrate = int(_addoncompat.get_setting('quality'))
	video_data = _connection.getURL(video_url)
	video_tree = BeautifulSoup(video_data)
	video_url2 = video_tree.find('video', id = 'ngs_player')('source')[0]['src']
	video_data2 = _connection.getURL(video_url2.replace('&format=redirect', ''))
	video_tree2 = BeautifulSoup(video_data2)
	video_url3 = video_tree2.video['src']
	video_data3 = _connection.getURL(video_url3)
	video_url4 = _m3u8.parse(video_data3)
	for video_index in video_url4.get('playlists'):
		bitrate = int(video_index.get('stream_info')['bandwidth'])
		if bitrate > hbitrate and bitrate <= (sbitrate * 1000):
			hbitrate = bitrate
			finalurl = video_url3.rsplit('/',1)[0] + '/' + video_index.get('uri')
	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))