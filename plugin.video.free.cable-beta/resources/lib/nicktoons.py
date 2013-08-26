#!/usr/bin/python
# -*- coding: utf-8 -*-
import _addoncompat
import _common
import _connection
import os
import re
import sys
import urllib
import xbmc
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup, SoupStrainer

pluginHandle = int(sys.argv[1])

SITE = 'nicktoons'
BASE = 'http://nicktoons.nick.com'
SHOWS = 'http://nicktoons.nick.com/ajax/videos/all-videos?sort=date+desc&start=0&page=1&updateDropdown=true&viewType=collectionAll'
CLIPS = 'http://nicktoons.nick.com/ajax/videos/all-videos/%s?type=videoItem'
FULLEPISODES = 'http://nicktoons.nick.com/ajax/videos/all-videos/%s?type=fullEpisodeItem'

def masterlist():
	master_db = []
	master_data = _connection.getURL(SHOWS)
	master_tree = BeautifulSoup(master_data, 'html.parser')
	master_menu = master_tree.find_all('option')
	master_menu.pop(0)
	for master_item in master_menu:
		master_name = master_item.string
		season_url = master_item['value']
		master_db.append((master_name, SITE, 'seasons', season_url))
	return master_db

def rootlist():
	root_data = _connection.getURL(SHOWS)
	root_tree = BeautifulSoup(root_data, 'html.parser')
	root_menu = root_tree.find_all('option')
	root_menu.pop(0)
	for root_item in root_menu:
		root_name = root_item.string
		season_url = root_item['value']
		_common.add_show(root_name, SITE, 'seasons', season_url)
	_common.set_view('tvshows')

def seasons(season_url = _common.args.url):
	season_data = _connection.getURL(FULLEPISODES % season_url)
	try:
		season_menu = int(BeautifulSoup(season_data).find('div', class_ = 'total-videos').text.split(' ')[0])
	except:
		season_menu = 0
	if season_menu > 0:
		season_url2 = FULLEPISODES % season_url
		_common.add_directory('Full Episodes',  SITE, 'episodes', season_url2)
	season_data2 = _connection.getURL(CLIPS % season_url)
	try:
		season_menu2 = int(BeautifulSoup(season_data2).find('div', class_ = 'total-videos').text.split(' ')[0])
	except:
		season_menu2 = 0
	if season_menu2 > 0:
		season_url3 = CLIPS % season_url
		_common.add_directory('Clips',  SITE, 'episodes', season_url3)
	_common.set_view('seasons')

def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(episode_url)
	episode_tree = BeautifulSoup(episode_data, 'html.parser')
	add_videos(episode_tree.find('ul', class_ = 'large-grid-list'))
	pagedata = episode_tree.find('span', class_ = 'pagination-next')
	if pagedata:
		try:
			episodes(episode_url.split('?')[0] + pagedata.a['href'] + '&type=' + episode_url.rsplit('=', 1)[1])
		except:
			pass
	_common.set_view('episodes')	

def add_videos(episode_tree):
	episode_menu = episode_tree.find_all('li', recursive = False)
	for episode_item in episode_menu:
		show_name = _common.args.name
		episode_link = episode_item.h4.a
		episode_name = episode_link.text
		url = BASE + episode_link['href']
		episode_thumb = episode_item.find('img')['src'].split('?')[0]
		episode_plot = episode_item.find('p', class_ = 'description').text
		u = sys.argv[0]
		u += '?url="' + urllib.quote_plus(url) + '"'
		u += '&mode="' + SITE + '"'
		u += '&sitemode="play_video"'
		infoLabels = {	'title' : episode_name,
						'plot' : episode_plot,
						'tvshowtitle' : show_name }
		_common.add_video(u, episode_name, episode_thumb, infoLabels = infoLabels)

def play_video(video_url = _common.args.url):
	video_url9 = 'stack://'
	sbitrate = int(_addoncompat.get_setting('quality'))
	closedcaption = None
	video_data = _connection.getURL(video_url, forwardHeader = True)
	try:
		video_url2 = re.compile('<meta content="http://media.nick.com/(.+?)" itemprop="embedURL"/>').findall(video_data)[0]
	except:
		video_url2 = re.compile("NICK.unlock.uri = '(.+?)';").findall(video_data)[0]
	video_url3 = _connection.getRedirect('http://media.nick.com/' + video_url2, referer = BASE, forwardHeader = True)
	video_url4 = urllib.unquote_plus(video_url3.split('CONFIG_URL=')[1].split('&')[0]).strip()
	video_data2 = _connection.getURL(video_url4, referer = 'http://media.nick.com/' + video_url2, forwardHeader = True)
	video_tree = BeautifulSoup(video_data2)
	video_url5 = video_tree.feed.string.replace('{uri}', video_url2).replace('&amp;', '&').replace('{type}', 'network').replace('mode=episode', 'mode=clip')
	video_data3 = _connection.getURL(video_url5,forwardHeader=True)
	video_tree2 = BeautifulSoup(video_data3)
	video_segments = video_tree2.find_all('media:content')
	for video_segment in video_segments:
		hbitrate = -1
		video_url6 = video_segment['url']
		video_data4 = _connection.getURL(video_url6, forwardHeader = True)
		video_menu = BeautifulSoup(video_data4).find_all('rendition')
		for video_index in video_menu:
			bitrate = int(video_index['bitrate'])
			if bitrate > hbitrate and bitrate <= sbitrate:
				hbitrate = bitrate
				video_url7 = video_index.find('src').string
				video_url8 = video_url7 + ' swfurl=' + video_url3.split('?')[0] + ' pageUrl=' + BASE + ' swfvfy=true'
		video_url9 += video_url8.replace(',',',,') + ' , '
	finalurl = video_url9[:-3]
	try:
		closedcaption = video_tree2.find_all('media:text')
	except:
		pass
	if (_addoncompat.get_setting('enablesubtitles') == 'true') and (closedcaption is not None):
		convert_subtitles(closedcaption)
	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))
	if (_addoncompat.get_setting('enablesubtitles') == 'true') and (closedcaption is not None):
		while not xbmc.Player().isPlaying():
			xbmc.sleep(100)
		for count in range(1, len(closedcaption)):
			xbmc.Player().setSubtitles(os.path.join(_common.CACHEPATH,'subtitle-%s.srt' % str(count)))
			while xbmc.Player().isPlaying():
				xbmc.sleep(10)

def clean_subs(data):
	br = re.compile(r'<br.*?>')
	tag = re.compile(r'<.*?>')
	space = re.compile(r'\s\s\s+')
	apos = re.compile(r'&amp;apos;')
	gt = re.compile(r'&gt;+')
	sub = br.sub('\n', data)
	sub = tag.sub(' ', sub)
	sub = space.sub(' ', sub)
	sub = apos.sub('\'', sub)
	sub = gt.sub('>', sub)
	return sub

def convert_subtitles(closedcaption,durations=[]):
	str_output = ''
	j = 0
	count = 0
	for closedcaption_url in closedcaption:
		count = count + 1
		subtitle_data = _connection.getURL(closedcaption_url['src'], connectiontype = 0)
		subtitle_data = BeautifulSoup(subtitle_data, 'html.parser', parse_only = SoupStrainer('div'))
		lines = subtitle_data.find_all('p')
		for i, line in enumerate(lines):
			if line is not None:
				sub = clean_subs(_common.smart_utf8(line))
				start_time = _common.smart_utf8(line['begin'][:-1].replace('.', ','))
				end_time = _common.smart_utf8(line['end'][:-1].replace('.', ','))
				str_output += str(j + i + 1) + '\n' + start_time + ' --> ' + end_time + '\n' + sub + '\n\n'
		j = j + i + 1
		file = open(os.path.join(_common.CACHEPATH,'subtitle-%s.srt' % int(count)), 'w')
		file.write(str_output)
		str_output=''
		file.close()