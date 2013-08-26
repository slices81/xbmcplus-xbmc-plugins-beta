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
from bs4 import BeautifulSoup
from pyamf import remoting

pluginHandle = int (sys.argv[1])

SITE = 'marvelkids'
BASE = 'http://marvelkids.marvel.com'
SHOWS = 'http://marvelkids.marvel.com/shows'
CONST = '4c1b306cc23230173e7dfc04e68329d3c0c354cb'

def masterlist():
	master_db = []
	master_data = _connection.getURL(SHOWS)
	master_menu = BeautifulSoup(master_data, 'html5lib').find_all(href = re.compile('/shows/'))
	for master_item in master_menu:
		master_name = master_item['title']
		season_url = BASE + master_item['href']
		master_db.append((master_name, SITE, 'seasons', season_url))
	return master_db

def rootlist():
	root_data = _connection.getURL(SHOWS)
	root_menu = BeautifulSoup(root_data, 'html5lib').find_all(href = re.compile('/shows/'))
	for root_item in root_menu:
		root_name = root_item['title']
		season_url = BASE + root_item['href']
		_common.add_show(root_name,  SITE, 'seasons', season_url)
	_common.set_view('tvshows')

def seasons(season_url = _common.args.url):
	season_data = _connection.getURL(season_url)
	season_tree = BeautifulSoup(season_data)
	season_menu = season_tree.find_all('div', class_ = 'tab-wrap')
	for season_item in season_menu:
		season_name = season_item.h2.text
		_common.add_directory(season_name, SITE, 'episodes', season_url)
	_common.set_view('seasons')

def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(episode_url)
	episode_tree = BeautifulSoup(episode_data)
	episode_carousel = episode_tree.find_all('div', class_ = 'tab-wrap')
	for episode in episode_carousel:
		if _common.args.name == episode.h2.text:
			episode_menu = episode.find_all('li', class_ = 'result-item')
			for episode_item in episode_menu:
				episode_name = episode_item.img['title']
				episode_thumb = episode_item.img['src']
				episode_exp_id = episode_item.a['data-video']
				episode_plot = episode_item.find('p', class_ = 'description').text.strip()
				url = episode_url
				u = sys.argv[0]
				u += '?url="' + urllib.quote_plus(url) + '#' + urllib.quote_plus(episode_exp_id) + '"'
				u += '&mode="' + SITE + '"'
				u += '&sitemode="play_video"'
				infoLabels={	'title' : episode_name,
								'plot' : episode_plot }
				_common.add_video(u, episode_name, episode_thumb, infoLabels = infoLabels)
	_common.set_view('episodes')

def play_video(video_url = _common.args.url):
	stored_size = 0
	video_url, video_content_id = video_url.split('#')
	video_data = _connection.getURL(video_url)
	video_tree = BeautifulSoup(video_data, 'html5lib')
	video_player_key = video_tree.find('param', attrs = {'name' : 'playerKey'})['value']
	video_player_id = video_tree.find('param', attrs = {'name' : 'publisherID'})['value']
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