#!/usr/bin/python
# -*- coding: utf-8 -*-
import _common
import _connection
import re
import simplejson
import sys
import urllib
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup, SoupStrainer

pluginHandle = int(sys.argv[1])

SITE = 'thewb'
BASE = 'http://www.thewb.com'
SHOWS = 'http://www.thewb.com/shows/full-episodes'
CLIPS = 'http://www.thewb.com/shows/clips'
VIDEOURL = 'http://metaframe.digitalsmiths.tv/v2/WBtv/assets/%s/partner/146?format=json'

def masterlist():
	master_dict = {}
	master_db = []
	for master_url in (CLIPS, SHOWS):
		master_data = _connection.getURL(master_url)
		master_tree = BeautifulSoup(master_data, 'html5lib').find('div', id = 'show-directory')
		master_menu = master_tree.find_all('li')
		for master_item in master_menu:
			master_name = _common.replace_signs(clean_title(master_item.a.text))
			season_url = BASE + master_item.a['href']
			master_dict[master_name] = season_url
	for master_name, season_url in master_dict.iteritems():	
		master_db.append((master_name, SITE, 'episodes', season_url))
	return master_db

def rootlist():
	root_dict = {}
	for root_url in (CLIPS, SHOWS):
		root_data = _connection.getURL(root_url)
		root_tree = BeautifulSoup(root_data, 'html5lib').find('div', id = 'show-directory')
		root_menu = root_tree.find_all('li')
		for root_item in root_menu:
			root_name = clean_title(root_item.a.text)
			season_url = BASE + root_item.a['href']
			root_dict[root_name] = season_url
	for root_name, season_url in root_dict.iteritems():	
		_common.add_show(root_name, SITE, 'episodes', season_url)
	_common.set_view('tvshows')

def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(episode_url)
	episode_tree = BeautifulSoup(episode_data, 'html5lib')
	episode_menu = episode_tree.find_all('div', id = re.compile('video_*'))
	for episode_item in episode_menu:
		show_name = episode_item.strong.string
		episode_name = _common.replace_signs(episode_item.a.img['title'].replace(show_name,''))
		episode_thumb = episode_item.a.img['src'].rsplit('_',1)[0] + '_640x360.jpg'
		episode_plot = _common.replace_signs(episode_item.find_all('p')[1].text)
		url = BASE + episode_item.a['href']
		try:
			seasonEpisode = episode_item.find('span', class_ = 'type').string
			seasonSplit = seasonEpisode.split(': Ep. ')
			season_number = int(seasonSplit[0].replace('Season', '').strip())
			episodeSplit = seasonSplit[1].split(' ')
			episode_number = int(episodeSplit[0])
			episode_duration = episodeSplit[1].replace('(', '').replace(')', '').strip()
		except:
			season_number = None
			episode_number = None
			episode_duration = None
		u = sys.argv[0]
		u += '?url="' + urllib.quote_plus(url) + '"'
		u += '&mode="' + SITE + '"'
		u += '&sitemode="play_video"'
		infoLabels={	'title' : episode_name,
						'duration' : episode_duration,
						'season' : season_number,
						'episode' : episode_number,
						'plot' : episode_plot,
						'tvshowtitle' : show_name }
		_common.add_video(u, episode_name, episode_thumb, infoLabels = infoLabels)
	_common.set_view('episodes')

def play_video(video_url = _common.args.url):
	video_data = _connection.getURL(VIDEOURL % video_url.split('/')[-1])
	video_tree = simplejson.loads(video_data)['videos']['limelight700']['uri']
	rtmpsplit = video_tree.split('mp4:')
	finalurl = rtmpsplit[0] + ' playpath=mp4:' + rtmpsplit[1]
	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))

def clean_title(data):
	first = re.compile(r'on (dvd|blu-ray)', re.IGNORECASE)
	second = re.compile(r'and dvd', re.IGNORECASE)
	third = re.compile(r'(tm)', re.IGNORECASE)
	sub = first.sub('', data)
	sub = second.sub('', sub)
	sub = third.sub('', sub)
	return sub.strip()