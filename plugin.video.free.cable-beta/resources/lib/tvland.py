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

SITE = 'tvland'
BASE = 'http://www.tvland.com'
SHOWS = 'http://www.tvland.com/full-episodes'
CLIPS = 'http://www.tvland.com/video-clips'
SEASONURL = 'http://www.tvland.com/fragments/search_results/related_episodes_seasons?showId=%s&seasonId=%s&episodeId=%s'
VIDEOURL = 'http://www.tvland.com/feeds/video_player/mrss?uri='
MP4URL = 'http://mtvnmobile.vo.llnwd.net/kip0/_pxn=0+_pxK=18639/44620/mtvnorigin'

def masterlist():
	master_dict = {}
	master_db = []
	for master_url in (CLIPS, SHOWS):
		master_data = _connection.getURL(master_url)
		master_tree = BeautifulSoup(master_data, 'html.parser', parse_only = SoupStrainer('div', class_ = 'showsList'))
		master_menu = master_tree.find_all('a')
		for master_item in master_menu:
			master_name = master_item.contents[0].strip()
			season_url = master_item['href'].rsplit('/', 1)[0]
			master_dict[master_name] = season_url
	for master_name, season_url in master_dict.iteritems():	
		master_db.append((master_name, SITE, 'seasons', season_url))
	return master_db
     
def rootlist():
	root_dict = {}
	for root_url in (CLIPS, SHOWS):
		root_data = _connection.getURL(root_url)
		root_tree = BeautifulSoup(root_data, 'html.parser', parse_only = SoupStrainer('div', class_ = 'showsList'))
		root_menu = root_tree.find_all('a')
		for root_item in root_menu:
			root_name = root_item.contents[0].strip()
			season_url = root_item['href'].rsplit('/', 1)[0]
			root_dict[root_name] = season_url
	for root_name, season_url in root_dict.iteritems():	
		_common.add_show(root_name, SITE, 'seasons', season_url)
	_common.set_view('tvshows')

def seasons(season_url = _common.args.url):
	season_data = _connection.getURL(season_url)
	season_menu = BeautifulSoup(season_data, 'html5lib').find('a', class_ = 'full_episodes')
	season_menu2 = BeautifulSoup(season_data, 'html5lib').find('a', class_ = 'video_clips')
	if season_menu is not None:
		season_url2 = BASE + season_menu['href']
		_common.add_directory('Full Episodes',  SITE, 'episodes', season_url2)
	if season_menu2 is not None:
		season_url3 = BASE + season_menu2['href']
		_common.add_directory('Clips',  SITE, 'episodes', season_url3)
	_common.set_view('seasons')

def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(episode_url)
	episode_tree = BeautifulSoup(episode_data.replace('\'+\'', ''), 'html.parser')
	if _common.args.name == 'Clips':
		if episode_tree.find('a', class_ = 'next') is not None:
			add_clips(episode_tree)
			try:
				episodes(episode_url.split('?')[0] + episode_tree.find('a', class_ = 'next')['href'])
			except:
				pass
		else:
			add_clips(episode_tree)
	else:
		if episode_tree.find('a', class_ = 'season_menu') is not None:
			show_id = re.compile('var showId = "(.+?)";').findall(episode_data)[0]
			episode_id = re.compile('var episodeId = "(.+?)";').findall(episode_data)[0]
			episode_menu = episode_tree.find_all('a', class_ = 'season')
			for episode_item in episode_menu:
				episode_data2 = _connection.getURL(SEASONURL %(show_id, episode_item['id'], episode_id))
				episode_tree2 = BeautifulSoup(episode_data2)
				add_fullepisodes(episode_tree2, episode_item.text.split(' ')[1])
		else:
			add_fullepisodes(episode_tree)
	_common.set_view('episodes')

def add_fullepisodes(episode_tree, season_number = None):
	try:
		episode_menu = episode_tree.find_all('div', class_ = 'episodeContainer')
		for episode_item in episode_menu:
			episode_name = episode_item.find('div', class_ = 'episodeTitle').a.text
			episode_airdate = _common.format_date(episode_item.find('div', class_ = 'episodeAirDate').contents[1].strip(), '%b %d, %Y', '%d.%m.%Y')
			episode_plot = episode_item.find('div', class_ = 'episodeDescription').contents[0].strip()
			episode_thumb = episode_item.find('div', class_ = 'episodeImage').img['src'].split('?')[0]
			url = episode_item.find('div', class_ = 'episodeTitle').a['href']
			try:
				episode_duration = episode_item.find('span', class_ = 'episodeDuration').text.replace(')', '').replace('(', '')
			except:
				episode_duration = None
			try:
				episode_number = int(episode_item.find('div', class_ = 'episodeIdentifier').text.split('#' + season_number)[1])
			except:
				episode_number = None
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
	except:
		pass

def add_clips(episode_tree, season_number = None):
	try:
		episode_menu = episode_tree.find_all('div', class_ = 'search_pad')
		for episode_item in episode_menu:
			show_name = episode_item.find('div', class_ = 'search_show').text
			episode_name = episode_item.find('div', class_ = 'search_text').a.text.strip()
			episode_plot = episode_item.find('div', class_ = 'search_text').contents[4].strip()
			url = episode_item.find('div', class_ = 'search_text').a['href']
			episode_thumb = episode_item.find('div', class_ = 'search_image').img['src'].split('?')[0]
			try:
				episode_airdate = episode_item.find('div', class_ = 'episode_meta').contents[5].text.replace('Aired: ', '').strip()
				episode_airdate = _common.format_date(episode_airdate, '%B %d, %Y', '%d.%m.%Y')
			except:
				episode_airdate = None
			try:
				episode_duration = episode_item.find('span', class_ = 'search_duration').text.replace(')', '').replace('(', '')
			except:
				episode_duration = None
			try:
				episode_number = int(episode_item.find('div', class_ = 'episode_meta').contents[1].text.split('#')[1])
			except:
				episode_number = None
			u = sys.argv[0]
			u += '?url="' + urllib.quote_plus(url) + '"'
			u += '&mode="' + SITE + '"'
			u += '&sitemode="play_video"'
			infoLabels={	'title' : episode_name,
							'duration' : episode_duration,
							'season' : season_number,
							'episode' : episode_number,
							'plot' : episode_plot,
							'premiered' : episode_airdate,
							'tvshowtitle': show_name }
			_common.add_video(u, episode_name, episode_thumb, infoLabels = infoLabels)
	except:
		pass

def play_video(video_url = _common.args.url):
	video_url6 = 'stack://'
	sbitrate = int(_addoncompat.get_setting('quality'))
	closedcaption = None
	video_data = _connection.getURL(video_url)
	video_url2 = BeautifulSoup(video_data, 'html5lib').find('div', class_ = 'videoShare')['data-unique-id']
	video_data2 = _connection.getURL(VIDEOURL + video_url2)
	video_tree = BeautifulSoup(video_data2, 'html5lib')
	video_segments = video_tree.find_all('media:content')
	for video_segment in video_segments:
		video_url3 = video_segment['url']
		video_data3 = _connection.getURL(video_url3)
		video_menu = BeautifulSoup(video_data3).findAll('rendition')
		hbitrate = -1
		for video_index in video_menu:
			bitrate = int(video_index['bitrate'])
			if bitrate > hbitrate and bitrate <= sbitrate:
				hbitrate = bitrate
				video_url4 = video_index.find('src').string
				video_url5 = MP4URL + video_url4.split('e20')[1]
		video_url6 += video_url5.replace(',',',,')+' , '
	finalurl = video_url6[:-3]
	try:
		closedcaption = video_tree.find_all('media:text')
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