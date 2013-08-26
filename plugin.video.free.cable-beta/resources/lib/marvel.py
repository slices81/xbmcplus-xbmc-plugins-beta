#!/usr/bin/python
# -*- coding: utf-8 -*-
import _common
import _connection
import pyamf
import re
import sys
import urllib
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup, SoupStrainer
from pyamf import remoting

pluginHandle = int (sys.argv[1])

SITE = 'marvel'
BASE = 'http://marvel.com'
SHOWS = 'http://marvel.com/connect/dynamic_list?id=video_index&type=video&sort_order=alpha_asc'

def masterlist():
	master_db = []
	master_data = _connection.getURL(SHOWS)
	master_menu = BeautifulSoup(master_data, 'html5lib').find_all('li')
	for master_item in master_menu:
		master_name = master_item.a.string.rsplit(' ',1)[0].strip()
		season_url = BASE + master_item.a['href'] + '?limit=100'
		master_db.append((master_name, SITE, 'episodes', season_url))
	return master_db

def rootlist():
	root_data = _connection.getURL(SHOWS)
	root_menu = BeautifulSoup(root_data, 'html5lib').find_all('li')
	for root_item in root_menu:
		root_name = root_item.a.string.rsplit(' ',1)[0].strip()
		season_url = BASE + root_item.a['href'] + '?limit=100'
		_common.add_show(root_name,  SITE, 'episodes', season_url)
	_common.set_view('tvshows')
        
def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(episode_url)
	episode_tree = BeautifulSoup(episode_data, 'html5lib')
	episode_menu = episode_tree.find('ul', id = 'browse_results').find_all('li', recursive = False)
	for episode_item in episode_menu:
		episode_name = episode_item.a['title']
		episode_thumb = episode_item.img['src']
		episode_plot = episode_item.find('div', class_ = 'browse_result_description').string.strip()
		show_name = _common.args.name
		url = BASE + episode_item.a['href']
		try:
			episode_duration = episode_item.find('span', class_ = 'duration').string.strip('()')
		except:
			episode_duration = 0
		try:
			episode_airdate = episode_item.find('p', class_ = 'browse_result_sale grid-visible').string.replace('Available: ','')
			episode_airdate = _common.format_date(episode_airdate, inputFormat = '%b %d, %Y')
		except:
			episode_airdate = None
		u = sys.argv[0]
		u += '?url="' + urllib.quote_plus(url) + '"'
		u += '&mode="' + SITE + '"'
		u += '&sitemode="play_video"'
		infoLabels={	'title' : episode_name,
						'duration' : episode_duration,
						'plot' : episode_plot,
						'premiered' : episode_airdate,
						'tvshowtitle': show_name }
		_common.add_video(u, episode_name, episode_thumb, infoLabels = infoLabels)
	_common.set_view('episodes')
    
def play_video(video_url = _common.args.url):
	stored_size = 0
	video_data = _connection.getURL(video_url)
	video_tree = BeautifulSoup(video_data, 'html5lib')
	video_player_key = video_tree.find('param', attrs = {'name' : 'playerKey'})['value']
	video_content_id = video_tree.find('param', attrs = {'name' : '@videoPlayer'})['value']
	video_player_id = video_tree.find('param', attrs = {'name' : 'playerID'})['value']
	renditions = get_episode_info(video_player_key, video_content_id, video_url, video_player_id)
	finalurl = renditions['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']
	for item in sorted(renditions['programmedContent']['videoPlayer']['mediaDTO']['renditions'], key = lambda item:item['frameHeight'], reverse = False):
		stream_size = item['size']
		if (int(stream_size) > stored_size):
			finalurl = item['defaultURL']
			stored_size = stream_size
	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))

def get_episode_info(video_player_key, video_content_id, video_url, video_player_id):
	envelope = build_amf_request(video_player_key, video_content_id, video_url, video_player_id)
	connection_url = "http://c.brightcove.com/services/messagebroker/amf?playerKey=" + video_player_key
	values = bytes(remoting.encode(envelope).read())
	header = {'Content-Type' : 'application/x-amf'}
	response = remoting.decode(_connection.getAMF(connection_url, values,  header)).bodies[0][1].body
	print response
	return response

class ViewerExperienceRequest(object):
	def __init__(self, URL, contentOverrides, experienceId, playerKey, TTLToken = ''):
		self.TTLToken = TTLToken
		self.URL = URL
		self.deliveryType = float(0)
		self.contentOverrides = contentOverrides
		self.experienceId = experienceId
		self.playerKey = playerKey

class ContentOverride(object):
	def __init__(self, contentId, contentType = 0, target = 'videoPlayer'):
		self.contentType = contentType
		self.contentId = contentId
		self.target = target
		self.contentIds = None
		self.contentRefId = None
		self.contentRefIds = None
		self.contentType = 0
		self.featureId = float(0)
		self.featuredRefId = None

def build_amf_request(video_player_key, video_content_id, video_url, video_player_id):
	const = '4c1b306cc23230173e7dfc04e68329d3c0c354cb'
	pyamf.register_class(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')
	pyamf.register_class(ContentOverride, 'com.brightcove.experience.ContentOverride')
	content_override = ContentOverride(int(video_content_id))
	viewer_exp_req = ViewerExperienceRequest(video_url, [content_override], int(video_player_id), video_player_key)
	env = remoting.Envelope(amfVersion=3)
	env.bodies.append(
	(
		"/1",
		remoting.Request(
			target = "com.brightcove.experience.ExperienceRuntimeFacade.getDataForExperience",
			body = [const, viewer_exp_req],
			envelope = env
		)
	)
	)
	return env
