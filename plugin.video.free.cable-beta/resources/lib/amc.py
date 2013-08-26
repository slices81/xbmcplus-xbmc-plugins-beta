#!/usr/bin/python
# -*- coding: utf-8 -*-
import _common
import _connection
import pyamf
import re
import simplejson
import sys
import urllib
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup
from pyamf import remoting

pluginHandle = int(sys.argv[1])

SITE = 'amc'
SHOWS = 'http://www.amctv.com/videos'
VIDEOURL = 'http://www.amctv.com/index.php'
CONST = '353d86e482b6e9ad425cfd0fbac5d21174cb0d55'

def masterlist():
	master_db = []
	master_data = _connection.getURL(SHOWS)
	master_menu = BeautifulSoup(master_data).find('select', id = 'rb-video-browser-show').find_all('option', title = True)
	for master_item in master_menu:
		master_name = master_item.text
		season_url = master_item['value']
		master_db.append((master_name, SITE, 'seasons', season_url))
	return master_db

def rootlist():
	root_data = _connection.getURL(SHOWS)
	root_menu = BeautifulSoup(root_data).find('select', id = 'rb-video-browser-show').find_all('option', title = True)
	for root_item in root_menu:
		root_name = root_item.text
		season_url = root_item['value']
		_common.add_show(root_name,  SITE, 'seasons', season_url)
	_common.set_view('tvshows')

def seasons():
	season_data = _connection.getURL(SHOWS)
	season_tree = BeautifulSoup(season_data)
	season_videotypes = season_tree.find('select', id = 'rb-video-browser-content_type').find_all('option')
	season_shows = season_tree.find('select', id = 'rb-video-browser-show').find_all('option')
	for season_item in season_shows:
		if season_item['value'] == _common.args.url:
			season_category = season_item['title'].replace('[','').replace(']','').replace('"','').split(',')
			for season_videoitem in season_videotypes:
				if season_videoitem['value'] in season_category:
					season_name = season_videoitem.string
					season_url = 'rb-video-browser-num_items=100&module_id_base=rb-video-browser'
					season_url += '&rb-video-browser-show='+season_item['value']
					season_url += '&rb-video-browser-content_type='+season_videoitem['value']
					_common.add_directory(season_name, SITE, 'episodes', season_url)
	_common.set_view('seasons')

def episodes():
	episode_values = {	'video_browser_action' : 'filter',
						'params[type]' : 'all',
						'params[filter]' : _common.args.url,
						'params[page]' : '1',
						'params[post_id]' : '71306',      
						'module_id_base' : 'rb-video-browser' }
	episode_data = _connection.getURL(VIDEOURL, episode_values)
	episode_tree = simplejson.loads(episode_data)['html']['date']
	episode_menu = BeautifulSoup(episode_tree).find_all('li')
	for episode_item in episode_menu:
		episode_name = episode_item.a.img['title']
		episode_plot = episode_item.a.img['alt'].replace('/n',' ')
		episode_thumb = episode_item.a.img['src']
		url = episode_item.a['href']		
		u = sys.argv[0]
		u += '?url="' + urllib.quote_plus(url) + '"'
		u += '&mode="' + SITE + '"'
		u += '&sitemode="play_video"'
		infoLabels={	'title' : episode_name,
						'plot' : episode_plot }
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
	video_url2 = renditions['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']
	for item in sorted(renditions['programmedContent']['videoPlayer']['mediaDTO']['renditions'], key = lambda item:item['frameHeight'], reverse = False):
		stream_size = item['size']
		if (int(stream_size) > stored_size):
			video_url2 = item['defaultURL']
			stored_size = stream_size
	try:
		finalurl = video_url2.split('&', 2)[0] + '?' + video_url2.split('&', 2)[2] + ' playpath=' + video_url2.split('&', 2)[1]
	except:
		finalurl = video_url2.split('&', 1)[0] + ' playpath=' + video_url2.split('&', 1)[1]
	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))

def get_episode_info(video_player_key, video_content_id, video_url, video_player_id):
	envelope = build_amf_request(video_player_key, video_content_id, video_url, video_player_id)
	connection_url = "http://c.brightcove.com/services/messagebroker/amf?playerKey=" + video_player_key
	values = bytes(remoting.encode(envelope).read())
	header = {'Content-Type' : 'application/x-amf'}
	response = remoting.decode(_connection.getAMF(connection_url, values,  header)).bodies[0][1].body
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
			body = [CONST, viewer_exp_req],
			envelope = env
		)
	)
	)
	return env