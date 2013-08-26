#!/usr/bin/python
# -*- coding: utf-8 -*-
import _addoncompat
import _common
import _connection
import os
import simplejson
import sys
import urllib
import xbmc
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup, SoupStrainer

pluginHandle=int(sys.argv[1])

SITE = 'thecw'
SHOWS = 'http://www.cwtv.com/feed/mobileapp/shows?pagesize=100&api_version=3'
VIDEOLIST = 'http://www.cwtv.com/feed/mobileapp/videos?show=%s&api_version=3'
VIDEOURL = 'http://metaframe.digitalsmiths.tv/v2/CWtv/assets/%s/partner/132?format=json'
RTMPURL = 'rtmpe://wbworldtv.fcod.llnwd.net/a2246/o23/'
SWFURL = 'http://pdl.warnerbros.com/cwtv/digital-smiths/production_player/vsplayer.swf'
CLOSEDCAPTION = 'http://api.digitalsmiths.tv/metaframe/200f2a4d/asset/%s/filter'
SUBTITLE = os.path.join(_common.CACHEPATH,'subtitle.srt')

def masterlist():
	master_db = []
	master_data = _connection.getURL(SHOWS)
	master_menu = simplejson.loads(master_data)['items']
	for master_item in master_menu:
		master_name = master_item['title']
		season_url = master_item['slug']
		master_db.append((master_name, SITE, 'seasons', season_url))
	return master_db

def rootlist():
	root_data = _connection.getURL(SHOWS)
	root_menu = simplejson.loads(root_data)['items']
	for root_item in root_menu:
		root_name = root_item['title']
		season_url = root_item['slug']
		_common.add_show(root_name,  SITE, 'seasons', season_url)
	_common.set_view('tvshows')

def seasons(season_url = _common.args.url):
	fullepisodes = 0
	clips = 0
	season_data = _connection.getURL(VIDEOLIST % season_url)
	season_menu = simplejson.loads(season_data)['videos']
	for season_item in season_menu:
		if int(season_item['fullep']) == 1:
			fullepisodes = 1
		else:
			clips = 1
	if fullepisodes == 1:
		_common.add_directory('Full Episodes',  SITE, 'episodes', season_url + '#1')
	if clips == 1:
		_common.add_directory('Clips',  SITE, 'episodes', season_url + '#0')
	_common.set_view('seasons')

def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(VIDEOLIST % episode_url.split('#')[0])
	episode_menu = simplejson.loads(episode_data)['videos']
	for episode_item in episode_menu:
		if int(episode_item['fullep']) == int(episode_url.split('#')[1]):
			show_name = episode_item['series_name']
			url = episode_item['guid']
			episode_duration = int(episode_item['duration_secs'])/60
			episode_plot = episode_item['description_long']
			episode_name = episode_item['title']
			season_number = int(episode_item['season'])
			episode_thumb = episode_item['large_thumbnail'].replace('media.cwtv.com', 'pdl.warnerbros.com')
			try:
				episode_number = int(episode_item['episode'][len(str(season_number)):])
			except:
				episode_number = None
			try:
				episode_airdate = _common.format_date(episode_item['airdate'],'%Y-%b-%d', '%d.%m.%Y')
			except:
				episode_airdate = None
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
	_common.set_view('episodes')

def play_video(video_url = _common.args.url):
	hbitrate=-1
	if _addoncompat.get_setting('enablesubtitles') == 'true':
		convert_subtitles(video_url)
	sbitrate = int(_addoncompat.get_setting('quality'))
	video_data = _connection.getURL(VIDEOURL % video_url)
	video_tree = simplejson.loads(video_data)
	for video_key in video_tree['videos']:
		video_index = video_tree['videos'][video_key]
		bitrate = int(video_index['bitrate'])
		if bitrate > hbitrate and bitrate <= sbitrate:
			hbitrate = bitrate
			playpath_url = video_index['uri'].split('mp4:')[1].replace('Level3', '') 
	finalurl = RTMPURL + ' playpath=mp4:' + playpath_url + ' swfurl=' + SWFURL + ' swfvfy=true'
	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))
	if _addoncompat.get_setting('enablesubtitles') == 'true':
		while not xbmc.Player().isPlaying():
			xbmc.sleep(100)
		xbmc.Player().setSubtitles(SUBTITLE)
		
def convert_subtitles(video_guid):
	str_output = ''
	subtitle_data = _connection.getURL(CLOSEDCAPTION % video_guid, connectiontype = 0)
	subtitle_data = simplejson.loads(subtitle_data)
	for i, subtitle_line in enumerate(subtitle_data):
		if subtitle_line is not None:
			sub = _common.smart_utf8(subtitle_line['metadata']['Text'])
			start_time = _common.smart_utf8(str(subtitle_line['startTime'])).split('.')
			start_minutes, start_seconds = divmod(int(start_time[0]), 60)
			start_hours, start_minutes = divmod(start_minutes, 60)
			start_time = '%02d:%02d:%02d,%02d' % (start_hours, start_minutes, start_seconds, int(start_time[1][0:2]))
			end_time = _common.smart_utf8(str(subtitle_line['endTime'])).split('.')
			end_minutes, end_seconds = divmod(int(end_time[0]), 60)
			end_hours, end_minutes = divmod(end_minutes, 60)
			end_time = '%02d:%02d:%02d,%02d' % (end_hours, end_minutes, end_seconds, int(end_time[1][0:2]))
			str_output += str(i + 1) + '\n' + start_time + ' --> ' + end_time + '\n' + sub + '\n\n'
	file = open(SUBTITLE, 'w')
	file.write(str_output)
	file.close()
	return True