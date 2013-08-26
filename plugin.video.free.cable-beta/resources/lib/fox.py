#!/usr/bin/python
# -*- coding: utf-8 -*-
import _addoncompat
import _common
import _connection
import _m3u8
import binascii
import hashlib
import hmac
import os
import re
import simplejson
import sys
import time
import urllib
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup, SoupStrainer
from pyamf import remoting
import httplib

pluginHandle=int(sys.argv[1])

SITE = 'fox'
SHOWS = 'http://assets.fox.com/apps/FEA/v1.7/allshows.json'
CLIPS = 'http://feed.theplatform.com/f/fox.com/metadata?count=true&byCustomValue={fullEpisode}{false}&byCategories=Series/%s'
FULLEPISODES = 'http://feed.theplatform.com/f/fox.com/metadata?count=true&byCustomValue={fullEpisode}{true}&byCategories=Series/%s'

def masterlist():
	master_db = []
	master_data = _connection.getURL(SHOWS)
	master_menu = simplejson.loads(master_data)['shows']
	for master_item in master_menu:
		if master_item['external_link'] == '':
			master_name = master_item['title']
			master_db.append((master_name, SITE, 'seasons', master_name))
	return master_db

def rootlist():
	root_data = _connection.getURL(SHOWS)
	root_menu = simplejson.loads(root_data)['shows']
	for root_item in root_menu:
		if root_item['external_link'] == '':
			root_name = root_item['title']
			_common.add_show(root_name,  SITE, 'seasons', root_name)
	_common.set_view('tvshows')

def seasons(season_url = _common.args.url):
	season_data = _connection.getURL(FULLEPISODES % urllib.quote_plus(season_url) + '&range=0-1')
	try:
		season_menu = int(simplejson.loads(season_data)['total_count'])
	except:
		season_menu = 0
	if season_menu > 0:
		season_url2 = FULLEPISODES % urllib.quote_plus(season_url) + '&range=0-' + str(season_menu)
		_common.add_directory('Full Episodes',  SITE, 'episodes', season_url2)
	season_data2 = _connection.getURL(CLIPS % urllib.quote_plus(season_url) + '&range=0-1')
	try:
		season_menu2 = int(simplejson.loads(season_data2)['total_count'])
	except:
		season_menu2 = 0
	if season_menu2 > 0:
		season_url3 = CLIPS % urllib.quote_plus(season_url) + '&range=0-' + str(season_menu2)
		_common.add_directory('Clips',  SITE, 'episodes', season_url3)
	_common.set_view('seasons')

def episodes(episode_url = _common.args.url):
	episode_data = _connection.getURL(episode_url)
	episode_menu = simplejson.loads(episode_data.replace('}{', '},{'))['results']
	for episode_item in episode_menu:
		show_name = _common.args.name
		url = episode_item['videoURL']
		episode_duration = int(episode_item['length']/60)
		episode_plot = episode_item['shortDescription']
		episode_airdate = _common.format_date(episode_item['airdate'],'%Y-%m-%d', '%d.%m.%Y')
		episode_name = episode_item['name']
		try:
			season_number = episode_item['season']
		except:
			season_number = None
		try:
			episode_number = episode_item['episode']
		except:
			episode_number = None
		try:
			episode_thumb = episode_item['videoStillURL']
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
						'premiered' : episode_airdate,
						'tvshowtitle': show_name }
		_common.add_video(u, episode_name, episode_thumb, infoLabels = infoLabels)
	_common.set_view('episodes')

def play_video(video_url = _common.args.url):
	hbitrate = -1
	sbitrate = int(_addoncompat.get_setting('quality')) * 1000
	finalurl = ''
	video_data = _connection.getURL(video_url + '&manifest=m3u')
	video_tree = BeautifulSoup(video_data)

	video_url2 = video_tree.find('video', src = True)['src']
	signature = FOXsig(_common.args.url)
	print signature
	video_data2 = _connection.getFox(video_url2, header = {'Cookie' : signature}, referer = 'http://player.foxfdm.com/shared/1.4.522/pdk/swf/akamaiHD.swf')
	print video_data2
	video_menu = _m3u8.parse(video_data2)
	for video_index in video_menu.get('playlists'):
		bitrate = int(video_index.get('stream_info')['bandwidth'])
		if bitrate > hbitrate and bitrate <= sbitrate:
			hbitrate = bitrate
			video_url3 = video_index.get('uri').replace('%2f', '')
	video_data3 = re.sub(r"\#EXT-X-DISCONTINUITY\n","", _connection.getURL(video_url3))
	keyurl = re.compile('URI="(.*?)"').findall(video_data3)[0]
	key_data = _connection.getURL(keyurl)		
	keyfile = open(KEYPATH, 'w')
	keyfile.write(key_data)
	keyfile.close()
	localhttpserver = True
	filestring = 'XBMC.RunScript(' + os.path.join(_common.LIBPATH,'_proxy.py') + ',' + KEYPATH + ', 12345)'
	xbmc.executebuiltin(filestring)
	time.sleep(2)
	newkeyurl = 'http://127.0.0.1:12345'
	video_data4 = video_data4.replace(keyurl, newkeyurl)
	playfile = open(PLAYPATH, 'w')
	playfile.write(video_data4)
	playfile.close()
	finalurl = PLAYPATH
	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))
	if localhttpserver is True:
		_connection.getURL('http://localhost:12345/stop', connectiontype = 0)

#def play_video(video_url = _common.args.url):
#	hbitrate = -1
#	sbitrate = int(_addoncompat.get_setting('quality')) * 1000
#	finalurl = ''
#	smil_url = video_url
#	smil_url += '&policy=19938&policy=19938'
#	smil_url += '&sig=' + FOXsig(video_url)
#	smil_url += '&format=SMIL&Tracking=true&Embedded=true'
#	smil_url += '&manifest=m3u'
#	data = _connection.getURL(smil_url)
#	video_tree = BeautifulSoup(data)
#	video_url2 = video_tree.find('video', src = True)['src'].split('?', 1)[1]
#	print data
#	smil_url2 = _common.args.url
#	smil_url2 += '&manifest=m3u&format=redirect'
#	data2 = _connection.getURL(smil_url2)
#	video_url4 = _m3u8.parse(data2)	
#	video_url5 = video_url4.get('playlists')[0].get('uri').split('/index')[0].replace('https', 'http')
#	print video_url5
#	
#	video_url6 = video_url5 + '/manifest.f4m?' + video_url2
#	finalurl = video_url6
	

#	for video_index in video_url4.get('playlists'):
#		bitrate = int(video_index.get('stream_info')['bandwidth'])
#		if bitrate > hbitrate and bitrate <= (sbitrate * 1000):
#			hbitrate = bitrate
#			finalurl = video_index.get('uri')
#	filenames=BeautifulSoup(data).find_all('video')
#	hbitrate = -1
#	sbitrate = int(_addoncompat.get_setting('quality'))
#	for filename in filenames:
#		bitrate = int(filename['system-bitrate'])/1024
#		if bitrate > hbitrate and bitrate <= sbitrate:
#			hbitrate = bitrate
#			finalurl = filename['src']
#	xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path = finalurl))  

def FOXsig(smil_url):
	relative_path = smil_url.split('theplatform.com/s/')[1].split('?')[0]
	sha1_key = "#100FoxLock"
	secret_name = "FoxKey"
	final_sig = '00' #00 or 10 for parameter signing
	final_sig += str(hex(int(time.time()+60))).split('x')[1]
	hmacdata = final_sig+relative_path
	final_sig += binascii.hexlify(hmac.new(sha1_key, hmacdata, hashlib.sha1).digest())
	final_sig += binascii.hexlify(secret_name)
	return final_sig

def play_old():
	videoPlayer = int(common.args.url)
	const = '17e0633e86a5bc4dd47877ce3e556304d0a3e7ca'
	playerID = 644436256001
	publisherID = 51296410001
	rtmpdata = get_clip_info(const, playerID, videoPlayer, publisherID)
	print rtmpdata
	rtmpdata = rtmpdata['renditions']
	hbitrate = -1
	sbitrate = int(_addoncompat.get_setting('quality')) * 1024
	for item in rtmpdata:
		bitrate = int(item['encodingRate'])
		if bitrate > hbitrate and bitrate <= sbitrate:
			hbitrate = bitrate
			urldata = item['defaultURL']
			auth = urldata.split('?')[1]
			urldata = urldata.split('&')
			rtmp = urldata[0]+'?'+auth
			playpath = urldata[1].split('?')[0]+'?'+auth
	swfUrl = 'http://admin.brightcove.com/viewer/us1.25.03.01.2011-05-12131832/federatedVideo/BrightcovePlayer.swf'
	rtmpurl = rtmp+' playpath='+playpath + " swfurl=" + swfUrl + " swfvfy=true"
	item = xbmcgui.ListItem(path=rtmpurl)
	xbmcplugin.setResolvedUrl(pluginHandle, True, item)
       
def build_amf_request(const, playerID, videoPlayer, publisherID):
	env = remoting.Envelope(amfVersion=3)
	env.bodies.append(
		(
			"/1", 
			remoting.Request(
				target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", 
				body=[const, playerID, videoPlayer, publisherID],
				envelope=env
			)
		)
	)
	return env

def get_clip_info(const, playerID, videoPlayer, publisherID):
	conn = httplib.HTTPConnection("c.brightcove.com")
	envelope = build_amf_request(const, playerID, videoPlayer, publisherID)
	conn.request("POST", "/services/messagebroker/amf?playerKey=AQ~~,AAAAC_GBGZE~,q40QbnxHunHkwKuAvWxESNjERBgcAQY8", str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
	response = conn.getresponse().read()
	response = remoting.decode(response).bodies[0][1].body
	return response  

