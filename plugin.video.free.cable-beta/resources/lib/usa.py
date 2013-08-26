#!/usr/bin/python
# -*- coding: utf-8 -*-
import _addoncompat
import _common
import _connection
import _m3u8
import os
import re
import simplejson
import sys
import urllib
import xbmc
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup, SoupStrainer

pluginHandle = int(sys.argv[1])

SITE = 'usa'
SHOWS = 'http://feed.theplatform.com/f/OyMl-B/PleQEkKucpUm/categories?form=json&sort=order'
CLIPS = 'http://feed.theplatform.com/f/OyMl-B/8IyhuVgUXDd_?count=true&form=json&byCustomValue={fullEpisode}{false}&byCategories=%s'
FULLEPISODES = 'http://feed.theplatform.com/f/OyMl-B/8IyhuVgUXDd_?count=true&form=json&byCustomValue={fullEpisode}{true}&byCategories=%s'
SWFURL = 'http://www.usanetwork.com/videos/pdk/swf/flvPlayer.swf'
SUBTITLE = os.path.join(_common.CACHEPATH,'subtitle.srt')

def masterlist():
	master_db = []
	master_data = _connection.getURL(SHOWS)
	master_menu = simplejson.loads(master_data)['entries']
	for master_item in master_menu:
		master_name = master_item['title']
		season_url = master_item['plcategory$fullTitle']
		master_db.append((master_name, SITE, 'seasons', season_url))
	return master_db

def rootlist():
	root_data = _connection.getURL(SHOWS)
	root_menu = simplejson.loads(root_data)['entries']
	for root_item in root_menu:
		root_name = root_item['title']
		season_url = root_item['plcategory$fullTitle']
		_common.add_show(root_name,  SITE, 'seasons', season_url)
	_common.set_view('tvshows')

def seasons(season_url = _common.args.url):
	season_data = _connection.getURL(FULLEPISODES % urllib.quote_plus(season_url) + '&range=0-1')
	try:
		season_menu = int(simplejson.loads(season_data)['totalResults'])
	except:
		season_menu = 0
	if season_menu > 0:
		season_url2 = FULLEPISODES % urllib.quote_plus(season_url) + '&range=0-' + str(season_menu)
		_common.add_directory('Full Episodes',  SITE, 'episodes', season_url2)
	season_data2 = _connection.getURL(CLIPS % urllib.quote_plus(season_url) + '&range=0-1')
	try:
		season_menu2 = int(simplejson.loads(season_data2)['totalResults'])
	except:
		season_menu2 = 0
	if season_menu2 > 0:
		season_url3 = CLIPS % urllib.quote_plus(season_url) + '&range=0-' + str(season_menu2)
		_common.add_directory('Clips',  SITE, 'episodes', season_url3)
	_common.set_view('seasons')

def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(episode_url)
	episode_menu = simplejson.loads(episode_data)['entries']
	for i, episode_item in enumerate(episode_menu):
		url = episode_item['media$content'][0]['plfile$url']
		episode_duration = int(episode_item['media$content'][0]['plfile$duration']/60)
		episode_plot = episode_item['description']
		episode_airdate = _common.format_date(epoch = episode_item['pubDate']/1000)
		episode_name = episode_item['title']
		try:
			season_number = int(episode_item['pl' + str(i + 1) + '$season'][0])
		except:
			season_number = None
		try:
			episode_number = int(episode_item['pl' + str(i + 1) + '$episode'][0])
		except:
			episode_number = None
		try:
			episode_thumb = episode_item['plmedia$defaultThumbnailUrl']
		except:
			episode_thumb = None
		u = sys.argv[0]
		u += '?url="' + urllib.quote_plus(url) + '"'
		u += '&mode="' + SITE + '"'
		u += '&sitemode="play_video"'
		infoLabels={	'title' : episode_name,
						'duration' : episode_duration,
						'season' : season_number,
						'episode' : episode_number,
						'plot' : episode_plot,
						'premiered' : episode_airdate }
		_common.add_video(u, episode_name, episode_thumb, infoLabels = infoLabels)
	_common.set_view('episodes')

def play_video(video_url = _common.args.url):
	hbitrate = -1
	sbitrate = int(_addoncompat.get_setting('quality')) * 1024
	closedcaption = None
	video_data = _connection.getURL(video_url)
	video_tree = BeautifulSoup(video_data, 'html.parser')
	video_rtmp = video_tree.meta
	if video_rtmp is not None:
		base_url = video_rtmp['base']
		video_url2 = video_tree.switch.find_all('video')
		for video_index in video_url2:
			bitrate = int(video_index['system-bitrate'])
			if bitrate > hbitrate and bitrate <= sbitrate:
				hbitrate = bitrate
				playpath_url = video_index['src']	
				if '.mp4' in playpath_url:
					playpath_url = 'mp4:'+ playpath_url
				else:
					playpath_url = playpath_url.replace('.flv','')
				finalurl = base_url +' playpath=' + playpath_url + ' swfurl=' + SWFURL + ' swfvfy=true'
	else:
		video_data = _connection.getURL(video_url + '&manifest=m3u')
		video_tree = BeautifulSoup(video_data)
		try:
			closedcaption = video_tree.textstream['src']
		except:
			pass
		if (_addoncompat.get_setting('enablesubtitles') == 'true') and (closedcaption is not None):
				convert_subtitles(closedcaption)
		video_url2 = video_tree.seq.find_all('video')[0]
		video_url3 = video_url2['src'].replace('bravohls-f.','bravohls-i.')
		video_url4 = video_url3.split('/')[-1]
		video_data2 = _connection.getURL(video_url3)
		video_url5 = _m3u8.parse(video_data2)
		for video_index in video_url5.get('playlists'):
			bitrate = int(video_index.get('stream_info')['bandwidth'])
			if bitrate > hbitrate and bitrate <= sbitrate:
				hbitrate = bitrate
				finalurl = video_url3.replace(video_url4, video_index.get('uri'))
	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))
	if (_addoncompat.get_setting('enablesubtitles') == 'true') and (closedcaption is not None):
		while not xbmc.Player().isPlaying():
			xbmc.sleep(100)
		xbmc.Player().setSubtitles(SUBTITLE)

def clean_subs(data):
	br = re.compile(r'<br.*?>')
	tag = re.compile(r'<.*?>')
	space = re.compile(r'\s\s\s+')
	apos = re.compile(r'&amp;apos;')
	sub = br.sub('\n', data)
	sub = tag.sub(' ', sub)
	sub = space.sub(' ', sub)
	sub = apos.sub('\'', sub)
	return sub

def convert_subtitles(closedcaption):
	str_output = ''
	subtitle_data = _connection.getURL(closedcaption, connectiontype = 0)
	subtitle_data = BeautifulSoup(subtitle_data, 'html.parser', parse_only = SoupStrainer('div'))
	lines = subtitle_data.find_all('p')
	for i, line in enumerate(lines):
		if line is not None:
			sub = clean_subs(_common.smart_utf8(line))
			start_time_rest, start_time_msec = line['begin'].rsplit(':',1)
			start_time = _common.smart_utf8(start_time_rest + ',' + start_time_msec)
			try:
				end_time_rest, end_time_msec = line['end'].rsplit(':',1)
				end_time = _common.smart_utf8(end_time_rest + ',' + end_time_msec)
			except:
				continue
			str_output += str(i + 1) + '\n' + start_time + ' --> ' + end_time + '\n' + sub + '\n\n'
	file = open(SUBTITLE, 'w')
	file.write(str_output)
	file.close()