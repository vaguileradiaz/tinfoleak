#!/usr/bin/env python
# -*- coding: utf-8 -*-

# License:
# This work is licensed under a Creative Commons Attribution Share-Alike v4.0 License.
# https://creativecommons.org/licenses/by-sa/4.0/

"""
Tinfoleak - The most complete open-source tool for Twitter intelligence analysis
	:author: 	Vicente Aguilera Diaz
	:version: 	2.3

	License:
	This work is licensed under a Creative Commons Attribution Share-Alike v4.0 License.
	https://creativecommons.org/licenses/by-sa/4.0/

"""

# Classes
#	Configuration
#	User
#	Sources
#	Social_Networks
#	Geolocation
#	Search_GeoTweets
#	Hashtags
#	Mentions
#	User_Tweets
#	User_Images
# 	User_Conversations
#	Parameters
# 	Followers
# 	Friends
# 	Lists
#	Collections
#	Favorites


import argparse
import tweepy
import sys
import ConfigParser
import datetime
import errno
import os
import urllib2
from PIL import Image, ExifTags, ImageCms
import exifread
import struct
import time
from datetime import date, timedelta
import pyexiv2
from collections import OrderedDict
from operator import itemgetter
from OpenSSL import SSL
from jinja2 import Template, Environment, FileSystemLoader
from urlparse import urlparse
import re
import csv
import json
import oauth2 as oauth
import operator
import random

from PyQt4 import QtGui, QtCore
import main_window
import users_window
import relations_window
import lists_window
import collections_window
import followers_window
import friends_window


reload(sys)
sys.setdefaultencoding('utf8')


# ==========================================================================
class Configuration():
	"""Configuration information"""

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			# Read tinfoleak configuration file ("tinfoleak.conf")
			config = ConfigParser.RawConfigParser()
			config_path = os.path.abspath(os.path.dirname(sys.argv[0])) + '/tinfoleak.conf'
			config.read(config_path)

			CONSUMER_KEY = config.get('Twitter OAuth', 'CONSUMER_KEY')
			CONSUMER_SECRET = config.get('Twitter OAuth', 'CONSUMER_SECRET')
			ACCESS_TOKEN = config.get('Twitter OAuth', 'ACCESS_TOKEN')
			ACCESS_TOKEN_SECRET = config.get('Twitter OAuth', 'ACCESS_TOKEN_SECRET')

			# User authentication
			auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
			auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

			# Tweepy (a Python library for accessing the Twitter API)
			self.api = tweepy.API(auth)

			consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
			access_token = oauth.Token(key=ACCESS_TOKEN, secret=ACCESS_TOKEN_SECRET)

			# Twitter API
			self.client = oauth.Client(consumer, access_token)

		except Exception as e:
			show_error(e)
			sys.exit(1)


# ==========================================================================
class User:
	"""Information about a Twitter user"""

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.screen_name = ""
			self.name = ""
			self.id = ""
			self.created_at = ""
			self.followers_count = ""
			self.statuses_count = ""
			self.location = ""
			self.geo_enabled = ""
			self.description = ""
			self.expanded_description = ""
			self.url = ""
			self.expanded_url = ""
			self.profile_image_url = ""
			self.profile_banner_url = ""
			self.tweets_average = ""
			self.likes_average = ""
			self.meta = ""
			self.protected = ""

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_user_information(self, api):
		try:

			self.screen_name = api.screen_name
			self.name = api.name
			self.id = api.id
			self.created_at = api.created_at
			self.followers_count = api.followers_count
			self.friends_count = api.friends_count
			self.statuses_count = api.statuses_count
			self.location = api.location
			self.geo_enabled = api.geo_enabled
			self.time_zone = api.time_zone
			self.favourites_count = str(api.favourites_count)
			self.protected = api.protected

			td = datetime.datetime.today() - self.created_at
			if td.days > 0:
				self.tweets_average = round(float(self.statuses_count / (td.days * 1.0)),2)
				self.likes_average = round(float(api.favourites_count / (td.days * 1.0)),2)
			else:
				self.tweets_average = self.statuses_count
				self.likes_average = self.favourites_count

			self.url = api.url

			if len(api.entities) > 1:
				if api.entities['url']['urls']:
					self.expanded_url = api.entities['url']['urls'][0]['expanded_url']
				else:
					self.expanded_url = ""
			else:
				self.expanded_url = ""

			try:
				self.description = api.description
				if api.entities['description']['urls']:
					tmp_expanded_description = api.description
					url = api.entities['description']['urls'][0]['url']
					expanded_url = api.entities['description']['urls'][0]['expanded_url']
					self.expanded_description = tmp_expanded_description.replace(url, expanded_url)
				else:
					self.expanded_description= ""
			except:
				self.expanded_description= ""

			self.profile_image_url = str(api.profile_image_url).replace("_normal","")

			try:
				if api.profile_banner_url:
					self.profile_banner_url = str(api.profile_banner_url).replace("_normal","")
				else:
					self.profile_banner_url = ""
			except:
				self.profile_banner_url = ""

			self.verified = str(api.verified)
			self.listed_count = str(api.listed_count)
			self.lang = str(api.lang)

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Sources:
	"""Get apps used to publish tweets"""

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			# source = [source1, source2, ... ]
			# sources_firstdate = {source1: first_date1, source2: first_date2, ... ]
			# sources_lastdate = {source1: last_date1, source2: last_date2, ... ]
			# sources_count = {source1: tweets_number1, source2: tweets_number2, ... ]
			# sources_lasttweet = {source1: tweet_id1, source2: tweet_id2, ...}
			self.sources = []
			self.sources_firstdate = {}
			self.sources_lastdate = {}
			self.sources_count = {}
			self.sources_total_count = 0
			self.sources_percent = {}
			self.sources_firsttweet = {}
			self.sources_lasttweet = {}

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_sources_information(self, tweet):
		try:

			add = 1
			for index, item in enumerate(self.sources):
				if tweet.source == item[0]:
					add = 0
					self.sources_count[tweet.source] += 1
					self.sources_total_count += 1
					if tweet.created_at < self.sources_firstdate[tweet.source]:
						self.sources_firstdate[tweet.source] = tweet.created_at
					if tweet.created_at > self.sources_lastdate[tweet.source]:
						self.sources_lastdate[tweet.source] = tweet.created_at
					self.sources_firsttweet[tweet.source] = tweet.id

			if add:
				self.sources.append([tweet.source])
				self.sources_count[tweet.source] = 1
				self.sources_firstdate[tweet.source] = tweet.created_at
				self.sources_lastdate[tweet.source] = tweet.created_at
				self.sources_total_count += 1
				self.sources_lasttweet[tweet.source] = tweet.id

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_global_information(self):
		try:

			for s in self.sources:
				self.sources_percent[s[0]] = round((self.sources_count[s[0]] * 100.0) / self.sources_total_count, 1)

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Lists:
	"""Get info about the lists the authenticated user has been added to or is owner"""

	# ----------------------------------------------------------------------
	def get_memberships(self, client, listed_count, screen_name):
		try:

			memberships_file = screen_name + "_memberships.txt"

			username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
			if not os.path.isdir(username_directory):
				os.mkdir(username_directory)

			csvFile = open(username_directory + "/" + memberships_file, "wb")
			csvWriter = csv.writer(csvFile)
			csvWriter.writerow(["", "TINFOLEAK Report"])
			csvWriter.writerow(["", "Vicente Aguilera Díaz"])
			csvWriter.writerow(["", "@VAguileraDiaz"])
			csvWriter.writerow(["", "www.isecauditors.com"])
			csvWriter.writerow([""])
			csvWriter.writerow(["", ">>> Date:", datetime.datetime.now().strftime('%Y-%m-%d')])
			csvWriter.writerow(["", ">>> Time:", datetime.datetime.now().strftime('%H:%M')])
			csvWriter.writerow(["", ">>> Analyzed user:", screen_name])
			csvWriter.writerow(["", ">>> Information:", "Membership Lists"])
			csvWriter.writerow([""])
			csvWriter.writerow(["#", "ID", "LIST NAME", "LIST DESCRIPTION", "LIST MEMBER COUNT", "LIST SUBSCRIBER COUNT", "LIST URI", "USER SCREEN NAME", "USER CREATED AT", "USER NAME", "USER DESCRIPTION", "USER FOLLOWERS", "USER FRIENDS"])

			cursor = -1
			api_path = "https://api.twitter.com/1.1/lists/memberships.json?screen_name=" + screen_name

			public_lists = 0

			while cursor != 0:
				try:
					url_with_cursor = api_path + "&cursor=" + str(cursor)
					response, data = client.request(url_with_cursor)
					if response['status'] != "404":
						response_dictionary = json.loads(data)
						if "Rate limit exceeded" in str(response_dictionary):
							show_ui_message("Waiting...", "INFO", br=1)
							time.sleep(60)
							continue
						else:
							for public_list in response_dictionary['lists']:
								if public_lists < int(str(ui.tb_lists_number.text())):
									public_lists += 1
									show_ui_message(str(public_lists) + " public lists analyzed", "INFO", br=0)

									cursor = ui.tb_messages.textCursor()
									cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
									cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
									cursor.removeSelectedText()

									csvWriter.writerow([public_lists, public_list['id_str'], public_list['name'], public_list['description'], public_list['member_count'], public_list['subscriber_count'], public_list['uri'], public_list['user']['screen_name'], public_list['user']['created_at'], public_list['user']['name'], public_list['user']['description'], public_list['user']['followers_count'], public_list['user']['friends_count']])
									csvFile.flush()
								else:
									cursor = 0
									break

							if cursor != 0:
								cursor = response_dictionary['next_cursor']
					else:
						cursor = 0
				except Exception as e:
					rate_limit = show_error(e)
					if rate_limit:
						show_ui_message("Waiting...", "INFO", br=1)
						time.sleep(60)
						continue

			private_lists = listed_count - public_lists
			show_ui_message("The user has been added to " + str(listed_count) + " lists (private: " + str(private_lists) + ", public: " + str(public_lists) + ")", "INFO", br=1)
			show_ui_message("Output file: " + username_directory + "/" + memberships_file, "INFO", br=1)

			csvFile.close()

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def get_ownerships(self, client, screen_name):
		try:

			ownerships_file = screen_name + "_ownerships.txt"

			username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
			if not os.path.isdir(username_directory):
				os.mkdir(username_directory)

			csvFile = open(username_directory + "/" + ownerships_file, "wb")
			csvWriter = csv.writer(csvFile)
			csvWriter.writerow(["", "TINFOLEAK Report"])
			csvWriter.writerow(["", "Vicente Aguilera Díaz"])
			csvWriter.writerow(["", "@VAguileraDiaz"])
			csvWriter.writerow(["", "www.isecauditors.com"])
			csvWriter.writerow([""])
			csvWriter.writerow(["", ">>> Date:", datetime.datetime.now().strftime('%Y-%m-%d')])
			csvWriter.writerow(["", ">>> Time:", datetime.datetime.now().strftime('%H:%M')])
			csvWriter.writerow(["", ">>> Analyzed user:", screen_name])
			csvWriter.writerow(["", ">>> Information:", "Ownership Lists"])
			csvWriter.writerow([""])
			csvWriter.writerow(["#", "ID", "LIST NAME", "LIST DESCRIPTION", "LIST MEMBER COUNT", "LIST SUBSCRIBER COUNT", "LIST URI", "USER SCREEN NAME", "USER CREATED AT", "USER NAME", "USER DESCRIPTION", "USER FOLLOWERS", "USER FRIENDS"])

			cursor = -1
			api_path = "https://api.twitter.com/1.1/lists/ownerships.json?screen_name=" + screen_name

			owner_lists = 0

			while cursor != 0:
				try:
					url_with_cursor = api_path + "&cursor=" + str(cursor)
					response, data = client.request(url_with_cursor)
					if response['status'] != "404":
						response_dictionary = json.loads(data)
						if "Rate limit exceeded" in str(response_dictionary):
							show_ui_message("Waiting...", "INFO", br=1)
							time.sleep(60)
							continue
						else:
							for owner_list in response_dictionary['lists']:
								owner_lists += 1

								csvWriter.writerow([owner_lists, owner_list['id_str'], owner_list['name'], owner_list['description'], owner_list['member_count'], owner_list['subscriber_count'], owner_list['uri'], owner_list['user']['screen_name'], owner_list['user']['created_at'], owner_list['user']['name'], owner_list['user']['description'], owner_list['user']['followers_count'], owner_list['user']['friends_count']])
								csvFile.flush()

							cursor = response_dictionary['next_cursor']
					else:
						cursor = 0
				except Exception as e:
					rate_limit = show_error(e)
					if rate_limit:
						show_ui_message("Waiting...", "INFO", br=1)
						time.sleep(60)
						continue

			show_ui_message(str(owner_lists) + " public lists owned by the user", "INFO", br=1)
			show_ui_message("Output file: " + username_directory + "/" + ownerships_file, "INFO", br=1)

			csvFile.close()

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def get_lists(self, client, screen_name):
		try:

			lists_file = screen_name + "_lists.txt"

			username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
			if not os.path.isdir(username_directory):
				os.mkdir(username_directory)

			csvFile = open(username_directory + "/" + lists_file, "wb")
			csvWriter = csv.writer(csvFile)
			csvWriter.writerow(["", "TINFOLEAK Report"])
			csvWriter.writerow(["", "Vicente Aguilera Díaz"])
			csvWriter.writerow(["", "@VAguileraDiaz"])
			csvWriter.writerow(["", "www.isecauditors.com"])
			csvWriter.writerow([""])
			csvWriter.writerow(["", ">>> Date:", datetime.datetime.now().strftime('%Y-%m-%d')])
			csvWriter.writerow(["", ">>> Time:", datetime.datetime.now().strftime('%H:%M')])
			csvWriter.writerow(["", ">>> Analyzed user:", screen_name])
			csvWriter.writerow(["", ">>> Information:", "Subscribed to Lists"])
			csvWriter.writerow([""])
			csvWriter.writerow(["#", "ID", "LIST NAME", "LIST DESCRIPTION", "LIST MEMBER COUNT", "LIST SUBSCRIBER COUNT", "LIST URI", "USER SCREEN NAME", "USER CREATED AT", "USER NAME", "USER DESCRIPTION", "USER FOLLOWERS", "USER FRIENDS"])

			cursor = -1
			api_path = "https://api.twitter.com/1.1/lists/list.json?screen_name=" + screen_name

			user_lists = 0

			url_with_cursor = api_path + "&cursor=" + str(cursor)
			response, data = client.request(url_with_cursor)

			if response['status'] != "404":
				rate_limit = 0
				while not rate_limit:
					response_dictionary = json.loads(data)
					if "Rate limit exceeded" in str(response_dictionary):
						show_ui_message("Waiting...", "INFO", br=1)
						time.sleep(60)
					else:
						rate_limit = 1

				for user_list in response_dictionary:
					try:
						user_lists += 1
						csvWriter.writerow([user_lists, user_list['id_str'], user_list['name'], user_list['description'], user_list['member_count'], user_list['subscriber_count'], user_list['uri'], user_list['user']['screen_name'], user_list['user']['created_at'], user_list['user']['name'], user_list['user']['description'], user_list['user']['followers_count'], user_list['user']['friends_count']])
						csvFile.flush()
					except Exception as e:
						rate_limit = show_error(e)
						if rate_limit:
							show_ui_message("Waiting...", "INFO", br=1)
							time.sleep(60)
							continue

			show_ui_message("User subscribed to " + str(user_lists) + " lists", "INFO", br=1)
			show_ui_message("Output file: " + username_directory + "/" + lists_file, "INFO", br=1)

			csvFile.close()

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Collections:
	"""Get info about the colletions created by the specified user"""

	# ----------------------------------------------------------------------
	def get_collections(self, client, screen_name):
		try:

			collections_file = screen_name + "_collections.txt"

			username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
			if not os.path.isdir(username_directory):
				os.mkdir(username_directory)

			csvFile = open(username_directory + "/" + collections_file, "wb")
			csvWriter = csv.writer(csvFile)
			csvWriter.writerow(["", "TINFOLEAK Report"])
			csvWriter.writerow(["", "Vicente Aguilera Díaz"])
			csvWriter.writerow(["", "@VAguileraDiaz"])
			csvWriter.writerow(["", "www.isecauditors.com"])
			csvWriter.writerow([""])
			csvWriter.writerow(["", ">>> Date:", datetime.datetime.now().strftime('%Y-%m-%d')])
			csvWriter.writerow(["", ">>> Time:", datetime.datetime.now().strftime('%H:%M')])
			csvWriter.writerow(["", ">>> Analyzed user:", screen_name])
			csvWriter.writerow(["", ">>> Information:", "Collections"])
			csvWriter.writerow([""])
			csvWriter.writerow(["#", "ID", "COLLECTION NAME", "COLLECTION DESCRIPTION", "COLLECTION URL"])

			cursor = -1
			api_path = "https://api.twitter.com/1.1/collections/list.json?screen_name=" + screen_name

			collections = 0

			while cursor != 0:
				try:
					url_with_cursor = api_path + "&cursor=" + str(cursor)
					response, data = client.request(url_with_cursor)
					response_dictionary = json.loads(data)
					if "Rate limit exceeded" in str(response_dictionary):
						show_ui_message("Waiting...", "INFO", br=1)
						time.sleep(60)
						continue
					else:
						if response_dictionary['objects']:
							for timeline in response_dictionary['objects']['timelines']:
								collections += 1
								name = response_dictionary['objects']['timelines'][str(timeline)]['name']
								try:
									description = response_dictionary['objects']['timelines'][str(timeline)]['description']
								except Exception as e:
									description = ""
								url = response_dictionary['objects']['timelines'][str(timeline)]['collection_url']

								csvWriter.writerow([collections, timeline, name, description, url])
								csvFile.flush()

						if len(response_dictionary['objects']) > 0:
							cursor = response_dictionary['response']['cursors']['next_cursor']
						else:
							cursor = 0

				except Exception as e:
					rate_limit = show_error(e)
					if rate_limit:
						show_ui_message("Waiting...", "INFO", br=1)
						time.sleep(60)
						continue

			show_ui_message(str(collections) + " public collections owned by the user", "INFO", br=1)
			show_ui_message("Output file: " + username_directory + "/" + collections_file, "INFO", br=1)

			csvFile.close()

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Activity:
	"""Get statistics about the timeline activity"""

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.activity_count = 0
			self.activity_tweet = 0
			self.activity_tweet_retweets = 0
			self.activity_tweet_likes = 0
			self.activity_retweet = 0
			self.activity_reply = 0
			self.activity_url = 0
			self.activity_expanded_url = []
			self.activity_media = 0
			self.activity_tweet_percent = 0
			self.activity_retweet_percent = 0
			self.activity_reply_percent = 0
			self.activity_url_percent = 0
			self.activity_media_percent = 0
			self.activity_hours = {}
			self.activity_hours["00"] = 0
			self.activity_hours["01"] = 0
			self.activity_hours["02"] = 0
			self.activity_hours["03"] = 0
			self.activity_hours["04"] = 0
			self.activity_hours["05"] = 0
			self.activity_hours["06"] = 0
			self.activity_hours["07"] = 0
			self.activity_hours["08"] = 0
			self.activity_hours["09"] = 0
			self.activity_hours["10"] = 0
			self.activity_hours["11"] = 0
			self.activity_hours["12"] = 0
			self.activity_hours["13"] = 0
			self.activity_hours["14"] = 0
			self.activity_hours["15"] = 0
			self.activity_hours["16"] = 0
			self.activity_hours["17"] = 0
			self.activity_hours["18"] = 0
			self.activity_hours["19"] = 0
			self.activity_hours["20"] = 0
			self.activity_hours["21"] = 0
			self.activity_hours["22"] = 0
			self.activity_hours["23"] = 0

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_activity(self, tweet):
		try:

			self.activity_count += 1

			if hasattr(tweet, 'retweeted_status'):
				self.activity_retweet += 1
			else:
				self.activity_tweet += 1
				self.activity_tweet_retweets += tweet.retweet_count
				self.activity_tweet_likes += tweet.favorite_count

			if hasattr(tweet, 'in_reply_to_screen_name'):
				self.activity_reply += 1

			if tweet.entities['urls']:
				medias = tweet.entities['urls']
				for m in medias:
					try:
						url = m['expanded_url']
						if url:
							expanded_url = urllib2.urlopen(url)
							if "https://twitter.com/i/web/status/" not in expanded_url.url:
								self.activity_expanded_url.append(expanded_url.url)
							if "instagram" in url:
								self.activity_media += 1
							else:
								self.activity_url += 1
					except Exception as e:
						pass
			if tweet.entities.has_key('media') :
				self.activity_media += 1

			self.activity_hours[str(tweet.created_at.time().strftime('%H'))] += 1

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_global_information(self):
		try:

			self.activity_tweet_percent = round((self.activity_tweet * 100.0) / self.activity_count, 1)
			self.activity_retweet_percent = round((self.activity_retweet * 100.0) / self.activity_count, 1)
			self.activity_url_percent = round((self.activity_url * 100.0) / self.activity_count, 1)
			self.activity_media_percent = round((self.activity_media * 100.0) / self.activity_count, 1)

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Followers:
	"""Get followers for the specified user"""
	users = []

	# ----------------------------------------------------------------------
	def get_followers(self, username, api, limit):
		try:

			followers_file = username + "_followers.txt"

			username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + username
			if not os.path.isdir(username_directory):
				os.mkdir(username_directory)

			pics_directory = username_directory + "/followers-" + datetime.datetime.now().strftime('%Y%m%d')
			if not os.path.isdir(pics_directory):
				os.mkdir(pics_directory)

			csvFile = open(pics_directory + "/" + followers_file, "wb")
			csvWriter = csv.writer(csvFile)
			csvWriter.writerow(["", "TINFOLEAK Report"])
			csvWriter.writerow(["", "Vicente Aguilera Díaz"])
			csvWriter.writerow(["", "@VAguileraDiaz"])
			csvWriter.writerow(["", "www.isecauditors.com"])
			csvWriter.writerow([""])
			csvWriter.writerow(["", ">>> Date:", datetime.datetime.now().strftime('%Y-%m-%d')])
			csvWriter.writerow(["", ">>> Time:", datetime.datetime.now().strftime('%H:%M')])
			csvWriter.writerow(["", ">>> Analyzed user:", username])
			csvWriter.writerow(["", ">>> Information:", "Followers"])
			csvWriter.writerow([""])
			csvWriter.writerow(["#", "ID", "USERNAME", "SCREEN NAME", "DESCRIPTION", "PROFILE IMAGE URL", "PROFILE BANNER URL", "CREATED AT", "LOCATION", "TIME_ZONE", "GEO ENABLED", "FOLLOWERS COUNT", "FRIENDS COUNT", "STATUSES COUNT", "LISTED COUNT", "FAVOURITES COUNT", "USER VERIFIED", "USER LANG"])

			analyzed_user = 0
			for userid in tweepy.Cursor(api.followers_ids, screen_name=username).items():
				try:
					if int(analyzed_user) < int(limit):
						user = api.get_user(userid)
						self.users.append(user)
						analyzed_user += 1
						csvWriter.writerow([analyzed_user, user.id, user.name.encode('utf-8'), user.screen_name, user.description.encode('utf-8'), user.profile_image_url, user.profile_background_image_url, user.created_at, user.location, user.time_zone, user.geo_enabled, user.followers_count, user.friends_count, user.statuses_count, user.listed_count, user.favourites_count, user.verified, user.lang])
						csvFile.flush()

						show_ui_message(str(analyzed_user) +"/" + str(limit) + " users analyzed", "INFO", br=0)

						cursor = ui.tb_messages.textCursor()
						cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
						cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
						cursor.removeSelectedText()

						try:
							img = urllib2.urlopen(user.profile_image_url.replace("_normal.", ".")).read()
							filename = str(user.id) + ".jpg"
							image = pics_directory + "/" +filename
							if not os.path.exists(image):
								f = open(image, 'wb')
								f.write(img)
								f.close()

						except Exception as e:
							pass
					else:
						break

				except Exception as e:
					rate_limit = show_error(e)
					if rate_limit:
						show_ui_message("Waiting...", "INFO", br=1)
						time.sleep(60)
						continue

			show_ui_message("Output file: " + pics_directory + "/" + followers_file, "INFO", br=1)

			csvFile.close()

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Friends:
	"""Get friends for the specified user"""

	# ----------------------------------------------------------------------
	def get_friends(self, username, api, limit):
		try:
			friends_file = username + "_friends.txt"

			username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + username
			if not os.path.isdir(username_directory):
				os.mkdir(username_directory)

			pics_directory = username_directory + "/friends-" + datetime.datetime.now().strftime('%Y%m%d')
			if not os.path.isdir(pics_directory):
				os.mkdir(pics_directory)

			csvFile = open(pics_directory + "/" + friends_file, "wb")
			csvWriter = csv.writer(csvFile)
			csvWriter.writerow(["", "TINFOLEAK Report"])
			csvWriter.writerow(["", "Vicente Aguilera Díaz"])
			csvWriter.writerow(["", "@VAguileraDiaz"])
			csvWriter.writerow(["", "www.isecauditors.com"])
			csvWriter.writerow([""])
			csvWriter.writerow(["", ">>> Date:", datetime.datetime.now().strftime('%Y-%m-%d')])
			csvWriter.writerow(["", ">>> Time:", datetime.datetime.now().strftime('%H:%M')])
			csvWriter.writerow(["", ">>> Analyzed user:", username])
			csvWriter.writerow(["", ">>> Information:", "Friends"])
			csvWriter.writerow([""])
			csvWriter.writerow(["#", "ID", "USERNAME", "SCREEN NAME", "DESCRIPTION", "PROFILE IMAGE URL", "PROFILE BANNER URL", "CREATED AT", "LOCATION", "TIME_ZONE", "GEO ENABLED", "FOLLOWERS COUNT", "FRIENDS COUNT", "STATUSES COUNT", "LISTED COUNT", "FAVOURITES COUNT", "USER VERIFIED", "USER LANG"])

			analyzed_user = 0
			for userid in tweepy.Cursor(api.friends_ids, screen_name=username).items():
				try:
					if int(analyzed_user) < int(limit):
						user = api.get_user(userid)
						analyzed_user += 1
						csvWriter.writerow([analyzed_user, user.id, user.name.encode('utf-8'), user.screen_name, user.description.encode('utf-8'), user.profile_image_url, user.profile_background_image_url, user.created_at, user.location, user.time_zone, user.geo_enabled, user.followers_count, user.friends_count, user.statuses_count, user.listed_count, user.favourites_count, user.verified, user.lang])
						csvFile.flush()

						try:
							img = urllib2.urlopen(user.profile_image_url.replace("_normal.", ".")).read()
							filename = str(user.id) + ".jpg"
							image = pics_directory + "/" +filename
							if not os.path.exists(image):
								f = open(image, 'wb')
								f.write(img)
								f.close()
						except Exception as e:
							pass
					else:
						break

				except Exception as e:
					rate_limit = show_error(e)
					if rate_limit:
						show_ui_message("Waiting...", "INFO", br=1)
						time.sleep(60)
						continue

			show_ui_message("Output file: " + pics_directory + "/" + friends_file, "INFO", br=1)

			csvFile.close()

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Social_Networks:
	"""Identify social networks identities for a user"""

	#: social networks used by a Twitter user:
	#: {'twitteruser': [[Instagram_user, Instagram_profile],
	#:					[Foursquare_user, Foursquare_profile],
	#:					[Facebook_user, Facebook_profile],
	#:					[LinkedIn_user, LinkedIn_profile],
	#:					[Runkeeper_user, Runkeeper_profile],
	#:					[Flickr_user, Flickr_profile],
	#:					[Vine_user, Vine_profile],
	#:					[Periscope_user, Periscope_profile],
	#:					[Kindle_user, Kindle_profile],
	#:					[Youtube_user, Youtube_profile],
	#:					[Google+_user, Google+_profile],
	#:					[Frontback_user, Frontback_profile]
	#:					]}

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.user_sn = {}
			self.see_again = 1

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def get_socialnetwork_userinfo(self, status, socialnetwork):
		try:

			#: username used in the social network
			username = ""
			#: link to the user profile in the social network
			link = ""
			#: user picture in the social network
			pic = "?"
			#: real user name
			name = ""
			#: additional info
			info = ""
			#: html page
			html = ""

			medias = status.entities['urls']
			for m in medias:
				url = m['expanded_url']
				try:
					response = urllib2.urlopen(url)
					html = response.read()
				except Exception as e:
					pass
				if socialnetwork.lower().find("instagram") >= 0:
					#: Instagram
					#: ----------------------------------------------
					urls = re.search('"viewer_has_saved_to_collection":(.*)"profile_pic_url":"(.*)","username":"(.*)","blocked_by_viewer"', html)

					if urls:
						username = urls.group(3)
						pic = urls.group(2)

					urls = re.search('<meta property="og:title" content="(.*) on Instagram:(.*)', html)

					if urls:
						name = urls.group(1)

					if username:
						link = "https://instagram.com/" + username
						# Stop after the first result
						break
				else:
					if socialnetwork.lower().find("foursquare") >= 0:
						#: Foursquare
						#: ----------------------------------------------
						urls = re.search('https://www.swarmapp.com/(.*)/checkin/', html)
						if urls:
							username = urls.group(1)
							link = "https://foursquare.com/" + username
						else:
							urls = re.search('canonicalPath":"..(\w*)","canonicalUrl"', html)
							if urls:
								username = urls.group(1)
								link = "https://foursquare.com/" + username
						tmp = re.search('<div class="venue push"><h1><strong>(.*)</strong> at ', html)
						if tmp:
							name = tmp.group(1).decode('utf-8')

						tmp = re.search('<div id="mapContainer"><img src="(.*)" alt="(.*)" class="avatar mainUser"width="86"', html)
						if tmp:
							pic = tmp.group(1).decode('unicode-escape')

						if username:
							# Stop after the first result
							break
					else:
						if socialnetwork.lower().find("facebook") >= 0:
							#: Facebook
							#: ----------------------------------------------
							if status.source.lower().find("facebook") >= 0:
							# Identify Faceboook acount from Facebook page
								if not html:
									# Identify Faceboook acount from 404 not found facebook page
									try:
										response = urllib2.urlopen(url)
										html = response.read()
									except Exception as e:
										pass
									urls = re.search(';id=(.*)">', html)
									if urls:
										try:
											response = urllib2.urlopen("https://facebook.com/profile.php?id=" + urls.group(1))
											html = response.read()
										except Exception as e:
											pass
										urls = re.search('0; URL=/(.*)\/\?_fb_noscript=1', html)
										if urls:
											username = urls.group(1)
											link = "https://facebook.com/" + username
											try:
												response = urllib2.urlopen(link)
												html = response.read()
											except Exception as e:
												pass
											tmp = re.search('<img class="profilePic img" alt="(.*)" src="(.*)" /></a></div></div><div class="_58gk">', html)
											if tmp:
												pic = tmp.group(2).replace("&amp;", "&")
											tmp = re.search('<span itemprop="name">(.*)</span><span class="_5rqt">', html)
											if tmp:
												info = tmp.group(1).decode('utf-8')
								else:
									urls = re.search('autocomplete="off" name="next" value="https://www.facebook.com/(.*)/posts/[0-9]*"', html)
									if urls:
										if str(urls.group(1)).find("profile.php") < 0:
											username = urls.group(1)
											link = "https://facebook.com/" + username
									else:
										try:
											response = urllib2.urlopen("http://longurl.org/expand?url="+url)
											html2 = response.read()
											urls = re.search('<a href="https://www.facebook.com/(.*)/posts/[0-9]*">https://', html2)
										except Exception as e:
											pass
										if urls:
											username = urls.group(1)
											link = "https://facebook.com/" + username
											try:
												response = urllib2.urlopen(link)
												html = response.read()
											except Exception as e:
												pass
											tmp = re.search('<img class="profilePic img" alt="(.*)" src="(.*)" /></a></div></div><div class="_58gk">', html)
											if tmp:
												pic = tmp.group(2).replace("&amp;", "&")
											tmp = re.search('<span itemprop="name">(.*)</span><span class="_5rqt">', html)
											if tmp:
												info = tmp.group(1).decode('utf-8')

							else:
								if self.see_again == 0:
									username = ""
								if (self.user_sn[status.user.screen_name][1][0] and self.user_sn[status.user.screen_name][1][0].find("Unknown") < 0 and self.see_again > 0):
									# Identify Faceboook acount from Fourquare page
									self.see_again = 0
									username = ""
									try:
										response = urllib2.urlopen("https://foursquare.com/"+self.user_sn[status.user.screen_name][1][0])
										html = response.read()
									except Exception as e:
										pass
									urls = re.search('<ul class="social"><li><a href="http://www.facebook.com/profile.php\?id=(.*)" rel="nofollow" target="_blank" class="fbLink"', html)
									if urls:
										username = urls.group(1)
										link = "http://www.facebook.com/profile.php?id=" + username
										try:
											response = urllib2.urlopen(link)
											html = response.read()
										except Exception as e:
											pass
										tmp = re.search('<img class="profilePic img" alt="(.*)" src="(.*)" /></div></div><meta itemprop="image"', html)
										if tmp:
											pic = tmp.group(2).replace("&amp;", "&")
										tmp = re.search('autocomplete="off" name="next" value="https://www.facebook.com/(.*)" /></form>', html)
										if tmp:
											username = tmp.group(1)
											link = "https://facebook.com/" + username
										tmp = re.search('<span id="fb-timeline-cover-name">(.*)</span></a><span class="_1xim">', html)
										if tmp:
											name = tmp.group(1)
										try:
											response = urllib2.urlopen(link)
											html = response.read()
										except Exception as e:
											pass
										tmp = re.search('<img class="profilePic img" alt="(.*)" src="(.*)" /></a></div></div><div class="_58gk">', html)
										if tmp:
											pic = tmp.group(2).replace("&amp;", "&")
										tmp = re.search('<span itemprop="name">(.*)</span><span class="_5rqt">', html)
										if tmp:
											info = tmp.group(1).decode('utf-8')
							if username:
								# Stop after the first result
								break
						else:
							if socialnetwork.lower().find("linkedin") >= 0:
								#: LinkedIn
								#: ----------------------------------------------
								if not html:
									try:
										req = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
										html = urllib2.urlopen(req).read()

										tmp = re.search('linkedin.com/in/(.*)"/><link rel="stylesheet"', html)
										if tmp:
											username = tmp.group(1).decode('utf-8')
											link = "https://www.linkedin.com/in/" + username

										tmp = re.search('<meta property="og:image" content="(.*)"/>', html)
										if tmp:
											pic = tmp.group(1).decode('utf-8')

										tmp = re.search('<title>(.*) \| LinkedIn</title>', html)
										if tmp:
											name = tmp.group(1).decode('utf-8')

									except Exception as e:
										pass

								if username:
									# Stop after the first result
									break

							else:
								if socialnetwork.lower().find("runkeeper") >= 0:
									# Runkeeper
									#: ----------------------------------------------
									urls = re.search('"https://runkeeper.com/user/(.*)/activity/', html)
									if urls:
										username = urls.group(1)
										link = "https://runkeeper.com/user/" + username
										try:
											response = urllib2.urlopen(link)
											html = response.read()
										except Exception as e:
											pass
										tmp = re.search('https://graph.facebook.com(.*)" title', html)
										if tmp:
											pic = "https://graph.facebook.com" + tmp.group(1)
										tmp = re.search('<h1 id="userStatementHead"><b>(.*) is using Runkeeper</b>', html)
										if tmp:
											name = tmp.group(1).decode('utf-8')
										tmp = re.search('<meta name="description" content="(.*)"/>', html)
										if tmp:
											info = tmp.group(1)[tmp.group(1).find("joined"):].decode('utf-8')
									if username:
										# Stop after the first result
										break
								else:
									if socialnetwork.lower().find("flickr") >= 0:
										# Flickr
										#: ----------------------------------------------
										urls = re.search('"og:url" content="https://www.flickr.com/photos/(.*)/[0-9]*/"', html)
										if urls:
												username = urls.group(1)
												link = "https://www.flickr.com/" + username

										tmp = re.search('"image": "(.*).jpg?', html)
										if tmp:
											pic = tmp.group(1).decode('unicode-escape') + ".jpg"

										tmp = html.find('"name": ')
										if tmp:
											html = html[tmp+5:]
											tmp = html.find('"name": ')
											if tmp:
												html = html[tmp+5:]
											tmp = re.search('"name": "(.*)",', html)
											if tmp:
												name = tmp.group(1).decode('utf-8')
										if username:
											# Stop after the first result
											break
									else:
										if socialnetwork.lower().find("vine") >= 0:
											# Vine
											#: ----------------------------------------------
											urls = re.search('"name": "(.*)",', html)
											if urls:
													username = urls.group(1)
											urls = re.search('"url": "https://vine.co/u/(.*)"', html)
											if urls:
													link = "https://vine.co/u/" + urls.group(1)
											if username:
												# Stop after the first result
												break
										else:
											if socialnetwork.lower().find("periscope") >= 0:
												# Periscope
												#: ----------------------------------------------
												urls = re.search('pscp://user/(.*)&quot;,&quot;inAppUrl', html)
												if urls:
														username = urls.group(1)
														link = "https://www.periscope.tv/" + username

												tmp = re.search('avatarUrl&quot;:&quot;(.*)&quot;}}},&quot;usernames', html)
												if tmp:
														pic = tmp.group(1)

												if username:
													# Stop after the first result
													break
											else:
												if socialnetwork.lower().find("kindle") >= 0:
													# Kindle
													#: ----------------------------------------------
													urls = re.search('customerId":"(.*)","howLongAgo', html)
													if urls:
														tmp = urls.group(1)
														try:
															url = "https://kindle.amazon.com/profile/redirect/" + tmp
															response = urllib2.urlopen(str(url))
															html = response.read()
														except Exception as e:
															pass
														urls = re.search('"/profile/(.*)"', html)
														if urls:
															tmp = re.search('(.*)/[0-9]*', urls.group(1))
															if tmp:
																username = tmp.group(1)
																link = "https://kindle.amazon.com/profile/" + urls.group(1)
																try:
																	response = urllib2.urlopen(link)
																	html = response.read()
																except Exception as e:
																	pass
																urls = re.search('<img alt="(.*)" class="profilePhoto" src="(.*).jpg" />', html)
																if urls:
																	name = urls.group(1).decode('utf-8')
																	pic = urls.group(2).decode('utf-8')
																tmp = re.search('<span id="numFollowers(.*)">(.*)</span></a>', html)
																if tmp:
																	info = "Followers: " + tmp.group(2)
																tmp = re.search('<span id="numFollowing(.*)">(.*)</span></a>', html)
																if tmp:
																	info += " Following: " + tmp.group(2)
													if username:
														# Stop after the first result
														break
												else:
													if socialnetwork.lower().find("youtube") >= 0:
														# Youtube
														#: ----------------------------------------------
														urls = re.search('/channel/(.*)" class', html)
														if urls:
															tmp = urls.group(1)
															try:
																url = "http://www.youtube.com/channel/" + tmp
																response = urllib2.urlopen(str(url))
																html = response.read()
															except Exception as e:
																pass
															urls = re.search('href="http://www.youtube.com/user/(.*)"', html)
															if urls:
																username = urls.group(1)
																link = "http://www.youtube.com/user/" + username
															else:
																urls = re.search('<meta property="og:title" content="(.*)">', html)
																if urls:
																	username = urls.group(1)
																	link = "http://www.youtube.com/user/" + username
															try:
																url = "http://www.youtube.com/user/" + username
																response = urllib2.urlopen(url)
																html = response.read()
															except Exception as e:
																pass
															tmp = re.search(' <img class="appbar-nav-avatar" src="(.*)" title="(.*)" alt="', html)
															if urls:
																pic = tmp.group(1)
																name = tmp.group(2).decode('utf-8')
															tmp = re.search('<meta name="keywords" content="(.*)">', html)
															if urls:
																info = tmp.group(1).decode('utf-8').replace("&quot;", "")
														else:
															# Identify Youtube acount from Google+ page
															urls = re.search('<link itemprop="url" href="http://www.youtube.com/user/(.*)">', html)
															if urls:
																username = urls.group(1)
																link = "http://www.youtube.com/user/" + username
														if username:
															# Stop after the first result
															break
													else:
														if socialnetwork.lower().find("google") >= 0:
															# Google+
															#: ----------------------------------------------
															urls = re.search('"url" href="https://plus.google.com/(.*)">', html)
															if urls:
																tmp = urls.group(1)
																username = tmp
																link = "https://plus.google.com/" + username
																try:
																	url = "https://plus.google.com/" + tmp
																	response = urllib2.urlopen(url)
																	html = response.read()
																except Exception as e:
																	pass
																urls = re.search('href="https://plus.google.com/(.*)"><meta itemprop="name" content=', html)
																if urls:
																	username = urls.group(1)
																	link = "https://plus.google.com/" + username
																tmp = re.search('<meta itemprop="image" content="(.*)"><meta itemprop="url"', html)
																if tmp:
																	pic = "https:" + tmp.group(1)
																tmp = re.search('<meta property="og:title" content="(.*): Google\+"><meta name="twitter:title"', html)
																if tmp:
																	name = tmp.group(1).decode('utf-8')
																tmp = re.search('<meta itemprop="description" content="(.*)"><meta itemprop="image" content="', html)
																if tmp:
																	info = tmp.group(1).decode('utf-8')
															if username:
																# Stop after the first result
																break
														else:
															if socialnetwork.lower().find("frontback") >= 0:
																# Frontback
																#: ----------------------------------------------
																urls = re.search('<h1 class="post-info-username"><a class="no-ui" href="http://www.frontback.me/(.*)">(.*)</a></h1>', html)
																if urls:
																	username = urls.group(1)
																	link = "http://www.frontback.me/" + username
																try:
																	response = urllib2.urlopen(link)
																	html = response.read()
																except Exception as e:
																	pass
																tmp = re.search('data-image-url="(.*)"></span></header><div class="pp-usercard"><h2>(.*)</h2><strong>(.*)</strong><p>(.*)</p><span class="pp-location"><i></i>(.*)</span><a class="button button-label-big button-green" data-deeplink=', html)
																if tmp:
																	pic = tmp.group(1)
																	name = tmp.group(3)
																	info = tmp.group(5)


			return username, link, pic, name, info

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_social_networks(self, status):
		try:

			# Twitter user
			owner = status.user.screen_name
			status.user.screen_name = status.user.screen_name.lower()
			if not hasattr(status, 'retweeted_status'):
				# The user is the original source of this tweet
				if status.source.lower().find("instagram") >= 0 and (self.user_sn[status.user.screen_name][0][0] == "" or self.user_sn[status.user.screen_name][0][0] == "Unknown"):
					# Instagram user.
					username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "instagram")
					self.user_sn[status.user.screen_name][0][0] = username
					self.user_sn[status.user.screen_name][0][1] = link
					self.user_sn[status.user.screen_name][0][2] = pic
					self.user_sn[status.user.screen_name][0][3] = name
					self.user_sn[status.user.screen_name][0][4] = info
				else:
					if status.source.lower().find("foursquare") >= 0 and (self.user_sn[status.user.screen_name][1][0] == "" or self.user_sn[status.user.screen_name][1][0] == "Unknown"):
						# Foursquare user
						username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "foursquare")
						self.user_sn[status.user.screen_name][1][0] = username
						self.user_sn[status.user.screen_name][1][1] = link
						self.user_sn[status.user.screen_name][1][2] = pic
						self.user_sn[status.user.screen_name][1][3] = name
						self.user_sn[status.user.screen_name][1][4] = info
					if status.source.lower().find("facebook") >= 0  and (self.user_sn[status.user.screen_name][2][0] == "" or self.user_sn[status.user.screen_name][2][0] == "Unknown"):
						# Facebook user
						username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "facebook")
						self.user_sn[status.user.screen_name][2][0] = username
						self.user_sn[status.user.screen_name][2][1] = link
						self.user_sn[status.user.screen_name][2][2] = pic
						self.user_sn[status.user.screen_name][2][3] = name
						self.user_sn[status.user.screen_name][2][4] = info
					else:
						if status.source.lower().find("linkedin") >= 0 and (self.user_sn[status.user.screen_name][3][0] == "" or self.user_sn[status.user.screen_name][3][0] == "Unknown"):
							# LinkedIn user
							username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "linkedin")
							self.user_sn[status.user.screen_name][3][0] = username
							self.user_sn[status.user.screen_name][3][1] = link
							self.user_sn[status.user.screen_name][3][2] = pic
							self.user_sn[status.user.screen_name][3][3] = name
							self.user_sn[status.user.screen_name][3][4] = info
						else:
							if status.source.lower().find("runkeeper") >= 0 and (self.user_sn[status.user.screen_name][4][0] == "" or self.user_sn[status.user.screen_name][4][0] == "Unknown"):
								# Runkeeper user
								username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "runkeeper")
								self.user_sn[status.user.screen_name][4][0] = username
								self.user_sn[status.user.screen_name][4][1] = link
								self.user_sn[status.user.screen_name][4][2] = pic
								self.user_sn[status.user.screen_name][4][3] = name
								self.user_sn[status.user.screen_name][4][4] = info
							else:
								if status.source.lower().find("flickr") >= 0 and (self.user_sn[status.user.screen_name][5][0] == "" or self.user_sn[status.user.screen_name][5][0] == "Unknown"):
									# Flickr user
									username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "flickr")
									self.user_sn[status.user.screen_name][5][0] = username
									self.user_sn[status.user.screen_name][5][1] = link
									self.user_sn[status.user.screen_name][5][2] = pic
									self.user_sn[status.user.screen_name][5][3] = name
									self.user_sn[status.user.screen_name][5][4] = info
								else:
									if status.source.lower().find("vine") >= 0 and (self.user_sn[status.user.screen_name][6][0] == "" or self.user_sn[status.user.screen_name][6][0] == "Unknown"):
										# Vine user
										username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "vine")
										self.user_sn[status.user.screen_name][6][0] = username
										self.user_sn[status.user.screen_name][6][1] = link
										self.user_sn[status.user.screen_name][6][2] = pic
										self.user_sn[status.user.screen_name][6][3] = name
										self.user_sn[status.user.screen_name][6][4] = info
									else:
										if status.source.lower().find("periscope") >= 0 and (self.user_sn[status.user.screen_name][7][0] == "" or self.user_sn[status.user.screen_name][7][0] == "Unknown"):
											# Periscope user
											username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "periscope")
											self.user_sn[status.user.screen_name][7][0] = username
											self.user_sn[status.user.screen_name][7][1] = link
											self.user_sn[status.user.screen_name][7][2] = pic
											self.user_sn[status.user.screen_name][7][3] = name
											self.user_sn[status.user.screen_name][7][4] = info
										else:
											if status.source.lower().find("kindle") >= 0 and (self.user_sn[status.user.screen_name][8][0] == "" or self.user_sn[status.user.screen_name][8][0] == "Unknown"):
												# Kindle user
												username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "kindle")
												self.user_sn[status.user.screen_name][8][0] = username
												self.user_sn[status.user.screen_name][8][1] = link
												self.user_sn[status.user.screen_name][8][2] = pic
												self.user_sn[status.user.screen_name][8][3] = name
												self.user_sn[status.user.screen_name][8][4] = info
											else:
												if status.source.lower().find("google") >= 0 and status.text.lower().find("a @youtube") >= 0 and (self.user_sn[status.user.screen_name][10][0] == "" or self.user_sn[status.user.screen_name][10][0] == "Unknown"):
													# Google+ user
													username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "google")
													self.user_sn[status.user.screen_name][10][0] = username
													self.user_sn[status.user.screen_name][10][1] = link
													self.user_sn[status.user.screen_name][10][2] = pic
													self.user_sn[status.user.screen_name][10][3] = name
													self.user_sn[status.user.screen_name][10][4] = info

												if ((status.source.lower().find("youtube") >= 0 and status.text.lower().find("a @youtube") >= 0) or (status.source.lower().find("google") >= 0 and status.text.lower().find("a @youtube") >= 0)) and (self.user_sn[status.user.screen_name][9][0] == "" or self.user_sn[status.user.screen_name][9][0] == "Unknown"):
													# Youtube user
													username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "youtube")
													self.user_sn[status.user.screen_name][9][0] = username
													self.user_sn[status.user.screen_name][9][1] = link
													self.user_sn[status.user.screen_name][9][2] = pic
													self.user_sn[status.user.screen_name][9][3] = name
													self.user_sn[status.user.screen_name][9][4] = info
												else:
													if status.source.lower().find("frontback") >= 0 and (self.user_sn[status.user.screen_name][11][0] == "" or self.user_sn[status.user.screen_name][11][0] == "Unknown"):
														# Frontback user
														username, link, pic, name, info = self.get_socialnetwork_userinfo(status, "frontback")
														self.user_sn[status.user.screen_name][11][0] = username
														self.user_sn[status.user.screen_name][11][1] = link
														self.user_sn[status.user.screen_name][11][2] = pic
														self.user_sn[status.user.screen_name][11][3] = name
														self.user_sn[status.user.screen_name][11][4] = info

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Geolocation:
	"""Get geolocation info included in tweets"""

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.toplocations = {}
			self.toplocationsstartdate = {}
			self.toplocatonsenddate = {}
			self.geoimg = 0  # tweets with images and geolocation (parameter: -p 0)
			self.toplocations = {}  # store the user most visited locations
			self.toplocationsdatetime = {}  # store date and time of the user most visited locations
			self.toplocationsstartdate = {}  # store initial date of the user most visited locations
			self.toplocationsenddate = {}  # store final date of the user most visited locations
			self.toplocationsstarttime = {}  # store initial time of the user most visited locations
			self.toplocationsdays = {}  # store week day of the user most visited locations
			self.toplocationsendtime = {}  # store final time of the user most visited locations
			self.toplocationsdaysmo = {}  # store week day of the user most visited locations
			self.toplocationsdaystu = {}  # store week day of the user most visited locations
			self.toplocationsdayswe = {}  # store week day of the user most visited locations
			self.toplocationsdaysth = {}  # store week day of the user most visited locations
			self.toplocationsdaysfr = {}  # store week day of the user most visited locations
			self.toplocationsdayssa = {}  # store week day of the user most visited locations
			self.toplocationsdayssu = {}  # store week day of the user most visited locations
			self.geo_info = []
			self.toplocations_tweets = {}
			self.toplocations_tweets_route = {}
			self.visited_locations = []
			self.visited_locations_startdate = []
			self.visited_locations_enddate = []
			self.visited_locations_starttime = []
			self.visited_locations_endtime = []
			self.visited_locations_days = []
			self.kml_info = []
			self.media_info = {}
			self.toploc = []

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_geolocation_information(self, tweet):
		try:

			add = 0
			splace = ""
			sgeo = ""
			in_reply_to_screen_name = ""
			source_app = ""
			lat = ""
			lon = ""

			if tweet.place:
				splace = tweet.place.name.encode('utf-8')
				add = 1
			if tweet.geo:
				reply = tweet.in_reply_to_screen_name
				if reply:
					in_reply_to_screen_name = reply

				source_app = tweet.source
				sgeo = tweet.geo['coordinates']
				add = 1
				lat = str(sgeo[0])[:str(sgeo[0]).find(".")+4]
				lon = str(sgeo[1])[:str(sgeo[1]).find(".")+4]
				location_coord = "[" + lat + ", " + lon + "]"
				for i in range (1, 20-len(location_coord)):
					location_coord += " "
				location = location_coord + "\t" + splace

				if location in self.toplocations.keys():
					self.toplocations[location] += 1
					if tweet.created_at < self.toplocationsstartdate[location]:
						self.toplocationsstartdate[location] = tweet.created_at
					if tweet.created_at > self.toplocationsenddate[location]:
						self.toplocationsenddate[location] = tweet.created_at
					if tweet.created_at.time() < self.toplocationsstarttime[location]:
						self.toplocationsstarttime[location] = tweet.created_at.time()
					if tweet.created_at.time() > self.toplocationsendtime[location]:
						self.toplocationsendtime[location] = tweet.created_at.time()
				else:
					self.toplocations[location] = 1
					self.toplocationsstartdate[location] = tweet.created_at
					self.toplocationsenddate[location] = tweet.created_at
					self.toplocationsstarttime[location] = tweet.created_at.time()
					self.toplocationsendtime[location] = tweet.created_at.time()
					self.toplocationsdaysmo[location] = 0
					self.toplocationsdaystu[location] = 0
					self.toplocationsdayswe[location] = 0
					self.toplocationsdaysth[location] = 0
					self.toplocationsdaysfr[location] = 0
					self.toplocationsdayssa[location] = 0
					self.toplocationsdayssu[location] = 0
				if tweet.created_at.weekday() == 0: # Monday
						self.toplocationsdaysmo[location] += 1
				elif tweet.created_at.weekday() == 1:   # Tuesday
						self.toplocationsdaystu[location] += 1
				elif tweet.created_at.weekday() == 2: # Wednesday
						self.toplocationsdayswe[location] += 1
				elif tweet.created_at.weekday() == 3: # Thursday
						self.toplocationsdaysth[location] += 1
				elif tweet.created_at.weekday() == 4: # Friday
						self.toplocationsdaysfr[location] += 1
				elif tweet.created_at.weekday() == 5: # Saturday
						self.toplocationsdayssa[location] += 1
				elif tweet.created_at.weekday() == 6: # Sunday
						self.toplocationsdayssu[location] += 1


			place = splace.decode('utf-8')
			if splace in self.toplocations_tweets:
				self.toplocations_tweets[place] += 1
			else:
				self.toplocations_tweets[place] = 1

			sinfo = ""
			media_url = ""
			keywords_instagram = []

			if tweet.entities.has_key('media') :
				medias = tweet.entities['media']
				for m in medias :
					media_url = m['media_url']

			else:
				if tweet.entities['urls']:
					media = str(tweet.entities['urls'][0]['expanded_url'])
					if media.find("instagram") > 0:
						# Instagram
						try:
							response = urllib2.urlopen(str(media))
							html = response.read()
							media_url = get_url_media_from_instagram(html)
							#tagged_users, owner = get_tagged_users_from_instagram(html)
							#keywords_instagram = get_hashtags_from_instagram(html)
							if media_url.find(".mp4") > 0:
								media_type = "Video"
						except Exception as e:
							pass
					else:
						media_url = ""

			if add:
				place = splace.decode('utf-8')
				sinfo = media_url + splace.decode('utf-8') + " " + str(sgeo).decode('utf-8')
				self.geo_info.append([media_url, place, str(sgeo).decode('utf-8'), str(tweet.created_at.strftime('%m/%d/%Y')), str(tweet.created_at.time()), str(tweet.id), source_app])

				if len(self.visited_locations)>0 and place in self.visited_locations[len(self.visited_locations)-1][0]:
					self.visited_locations[len(self.visited_locations)-1][1] = tweet.created_at
					self.visited_locations[len(self.visited_locations)-1][2] = tweet.created_at.time()
					delta = self.visited_locations[len(self.visited_locations)-1][3] - tweet.created_at
					self.visited_locations[len(self.visited_locations)-1][5] = delta.days+1
					self.visited_locations[len(self.visited_locations)-1][6] = self.toplocations_tweets[place]

				else:
					# [place, date (since), time (since), date (until), time (until), days, tweets]
					coord = lat + ", " + lon
					self.visited_locations.append([place, tweet.created_at,  tweet.created_at.time(), tweet.created_at, tweet.created_at.time(), 1, 1, coord])

			else:
				sinfo = ""

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_geofile_information(self, tweet, user):
		try:

			tweet_geo = 0
			place = ""
			geo = ""

			# Get place from tweet
			if tweet.place:
				place = tweet.place.name.encode('utf-8')

			# Get coordinates from tweet
			if tweet.geo:
				geo = tweet.geo['coordinates']
				tweet_geo = 1

			media_url = []
			# Get media content from tweet
			if tweet.entities.has_key('media') :
				medias = tweet.entities['media']
				for m in medias :
					media_url.append(m['media_url'])

			photo = ""
			if tweet_geo:
				# Tweet with coordinates
				content = "<table width=\"100%\"><tr><td width=\"48\"><img src=\""+user.profile_image_url.encode('utf-8') +"\"></td><td bgcolor=\"#cde4f3\"><b>" + user.name.encode('utf-8') + "</b> @" + user.screen_name.encode('utf-8') + "<br>" + tweet.text.encode('utf-8') + "</td></tr></table>"

				for media in media_url:
					photo = " [Media] "
					content += "<table width=\"100%\"><tr><td><img src=\"" + str(media) + "\"></td></tr></table>"

				date = tweet.created_at.strftime('%m/%d/%Y')
				time = tweet.created_at.time()
				self.kml_info.append([geo, content, photo, place, date, time])

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def generates_geofile(self, geofile, parameters):
		kml_file_content = ""
		kml_file_header = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<kml xmlns=\"http://earth.google.com/kml/2.2\">\n<Folder>\n"
		kml_file_body = ""
		kml_file_foot = "</Folder>\n</kml>"
		header = ""
		content = ""

		try:

			f = open(geofile, "w")

			header = "<table bgcolor=\"#000000\" width=\"100%\"><tr><td><font color=\"white\"><b>" + parameters.program_name + " " + parameters.program_version + "</b></font><td align=\"right\"><font color=\"white\">" + parameters.program_author_twitter + "</font></td></tr></table>"

			for info in self.kml_info:
				#INFO: [coordinates, content, photo, place, date, time]
				coord = str(info[0])
				lat = coord[1:coord.find(",")]
				lon = coord[coord.find(",")+2:coord.find("]")]

				cdata = ""
				cdata = "\t\t<![CDATA[" + header + str(info[1]) + "]]>\n"
				snippet = ""

				# Place + [Photo]
				snippet = info[3] + " " + str(info[2])
				kml_file_body += "\t<Placemark>\n"

				# Date + Time
				kml_file_body += "\t\t<name>" + str(info[4]) + " - " + str(info[5]) + "</name>\n"
				kml_file_body += "\t\t<Snippet>" + snippet + "</Snippet>\n"
				kml_file_body += "\t\t<description>\n" + cdata + "\t\t</description>\n"
				kml_file_body += "\t\t<Point>\n"
				kml_file_body += "\t\t\t<coordinates>" + lon + "," + lat + "</coordinates>\n"
				kml_file_body += "\t\t</Point>\n"
				kml_file_body += "\t</Placemark>\n"

			kml_file_content = kml_file_header + kml_file_body + kml_file_foot
			f.write(kml_file_content)
			f.close()

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_global_information(self, top):
		try:

			sort_loc = OrderedDict(sorted(self.toplocations.items(), key=itemgetter(1), reverse=True))
			sort_top = sort_loc.items()[0:int(top)]

			for place, value in sort_top:
				startdate = self.toplocationsstartdate[place]
				enddate = self.toplocationsenddate[place]
				starttime = self.toplocationsstarttime[place]
				endtime = self.toplocationsendtime[place]

				favorite = 1

				mo = self.toplocationsdaysmo[place]
				tu = self.toplocationsdaystu[place]
				we = self.toplocationsdayswe[place]
				th = self.toplocationsdaysth[place]
				fr = self.toplocationsdaysfr[place]
				sa = self.toplocationsdayssa[place]
				su = self.toplocationsdayssu[place]

				week = [mo, tu, we, th, fr, sa, su]
				week_sort = sorted(week, reverse = True)
				maxday = week_sort [0]

				if week_sort[0] > 0 and week_sort[1] == 0:
					favorite = 0
				else:
					while week_sort[0] == maxday:
						del week_sort[0]
					if len(week_sort) > 0:
						if week_sort[0] == 0:
							favorite = 0

				day = []
				fav = 0
				mo_day = "Mo"
				tu_day = "Tu"
				we_day = "We"
				th_day = "Th"
				fr_day = "Fr"
				sa_day = "Sa"
				su_day = "Su"

				if mo == 0:
						mo_day = ""
				else:
						if mo == maxday and favorite:
							fav = "1"
							day.append("Mo")
				if tu == 0:
						tu_day = ""
				else:
						if tu == maxday and favorite:
							fav = "2"
							day.append("Tu")
				if we == 0:
						we_day = ""
				else:
						if we == maxday and favorite:
							fav = "3"
							day.append("We")
				if th == 0:
						th_day = ""
				else:
						if th == maxday and favorite:
							fav = "4"
							day.append("Th")
				if fr == 0:
						fr_day = ""
				else:
						if fr == maxday and favorite:
							fav = "5"
							day.append("Fr")
				if sa == 0:
						sa_day = ""
				else:
						if sa == maxday and favorite:
							fav = "6"
							day.append("Sa")
				if su == 0:
						su_day = ""
				else:
						if su == maxday and favorite:
							fav = "7"
							day.append("Su")

				coordinates = place[1:place.find("]")]
				location = place[20:len(place)]

				values = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]
				tmp1 = random.choice(values)
				tmp2 = random.choice(values)
				tmp3 = random.choice(values)
				tmp4 = random.choice(values)
				tmp5 = random.choice(values)
				tmp6 = random.choice(values)

				color = "#" + tmp1 + tmp2 + tmp3 + tmp4 + tmp5 + tmp6

				self.toploc.append([str(value), str(startdate.strftime('%m/%d/%Y')), str(enddate.strftime('%m/%d/%Y')), str(starttime), str(endtime), mo_day, tu_day, we_day, th_day, fr_day, sa_day, su_day, coordinates, location, fav, day, mo, tu, we, th, fr, sa, su, color])

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Search_GeoTweets:
	"""Get tweets based in geolocation info"""

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.toplocations = {}
			self.toplocationsstartdate = {}
			self.toplocatonsenddate = {}
			self.geoimg = 0
			self.adv_geo_info = []
			self.kml_info = []
			self.adv_media_info = {}
			self.toploc = []
			self.user_sn = {}  # social networks used by this Twitter user:{'twitteruser': [[Image], [Instagram User, Image], [Foursquare user, Image], [Facebook user, Image]] }. Example: { 'jlopez', ['julian.lopez', 'julianl', 'ad23', 'http://www.facebook.com/profile.php?id=343844'] }
			self.user_taggeds = {}  # { 'user': ['by', 'media_url', 'tweet', 'author_image', 'date', 'time'] }
			self.user_keywords = {}  # { 'user': 'keywords' }
			self.adv_media_count = 0  # total images

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_search_information(self, hashtag, mentions, user_images, user_tweets, source, activity, top_words):
		# Search global timeline (without coordinates)
		try:

			splace = ""
			sgeo = ""
			tweets_found = 0
			tweets_count = 0
			searched_tweets = []
			last_id = -1
			results = 0

			search = "-thisisaimpossiblewordinatweet and -thisisnotpossibleinatweet"
			with_words = ui.tb_include_words.text().replace(" ", " and +")
			without_words = ui.tb_not_include_words.text().replace(" ", " and -")

			tmp_count = 0
			for status in tweepy.Cursor(api.search,
										q=search + " and +" + with_words + " and -" + without_words,
										count=int(ui.tb_tweets_number.text()),
										since=ui.tb_sdate.text(),
										until=ui.tb_edate.text(),
										result_type='recent').items():

				screen_name = ""
				profile_image_url = ""
				created_at = status.created_at

				tmp_count += 1
				tweets_count += 1
				if tmp_count == 10 or tweets_count == int(ui.tb_tweets_number.text()) or tmp_count == int(
						ui.tb_tweets_number.text()):
					cursor = ui.tb_messages.textCursor()
					cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
					cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
					cursor.removeSelectedText()

					br = 0
					if tweets_count == int(ui.tb_tweets_number.text()):
						br = 1
					show_ui_message("Processing tweet " + str(tweets_count) + "/" + str(ui.tb_tweets_number.text()), "INFO", br)

				if tmp_count == 10:
					tmp_count = 0

				app.processEvents()

				if is_valid(status):
					results = 1

					if len(ui.tb_include_words.text()) > 0 or len(ui.tb_not_include_words.text()) > 0:
						user_tweets.set_find_information(status)

					if ui.cb_source_apps.isChecked():
						source.set_sources_information(status)

					if ui.cb_hashtags.isChecked():
						hashtag.set_hashtags_information(status, "*")

					if ui.cb_mentions.isChecked():
						mentions.set_mentions_information(status, "*")

					if ui.cb_metadata.isChecked():
						# Get metadata information from user images
						user_images.set_metadata_information(status)

					if ui.cb_media.isChecked():
						# Get images included in tweets
						if not ui.cb_metadata.isChecked():
							user_images.set_metadata_information(status)
						user_images.username = status.user.screen_name
						user_images.set_images_information(status)

					if ui.cb_words_frequency.isChecked():
						top_words.set_words_information(status)

					if ui.cb_activity.isChecked():
						activity.set_activity(status)

					if ui.cb_show_tweets.isChecked():
						user_tweets.set_find_information(status)

					profile_image_url = status.user.profile_image_url_https.replace("_normal.", ".")
					self.user_sn[status.user.screen_name] = [[profile_image_url], '', '', '']
					coord = ""
					try:
						coord = str(status.geo['coordinates'])
					except:
						coord = ""

					if not status.source:
						status.source = ""

					media_url = ""
					media_type = ""
					videos = []
					keywords_instagram = []
					extended_entities = ""

					retweeted = 0
					media = 0

					# Identify RT and media content
					if hasattr(status, 'retweeted_status'):
						retweeted = 1
						if status.retweeted_status.entities.has_key('media'):
							media = 1

					else:
						retweeted = 0
						if status.entities.has_key('media'):
							media = 1

					if media:
						if retweeted:
							medias = status.retweeted_status.entities['media']
							try:
								extended_entities = \
									status.retweeted_status.extended_entities['media'][0]['video_info']['variants']
							except Exception as e:
								extended_entities = ""
						else:
							medias = status.entities['media']
							try:
								extended_entities = status.extended_entities['media'][0]['video_info']['variants']
							except Exception as e:
								extended_entities = ""

						for m in medias:
							media_url = m['media_url']
							if str(media_url).find("video_thumb") >= 0:
								if extended_entities:
									for content in extended_entities:  # status.extended_entities['media'][0]['video_info']['variants']:
										if str(content['url']).find(".mp4") >= 0:
											videos.append([str(content['url']), content['bitrate']])

									sort_vid = OrderedDict(sorted(videos, key=itemgetter(1), reverse=True))
									vid_top = sort_vid.items()[0:1]
									media_type = "Video"
									media_url = str(vid_top[0][0])

							if media_url.find("/media/") >= 0:
								media_type = "Image"

					else:
						media = ""
						if retweeted:
							if status.retweeted_status.entities['urls']:
								media = str(status.retweeted_status.entities['urls'][0]['expanded_url'])

						else:
							if status.entities['urls']:
								media = str(status.entities['urls'][0]['expanded_url'])

						if media.find("instagram") > 0:
							# Instagram
							try:

								response = urllib2.urlopen(str(media))
								html = response.read()
								media_url = get_url_media_from_instagram(html)
								tagged_users, owner, profile_image = get_tagged_users_from_instagram(html)
								keywords_instagram = get_hashtags_from_instagram(html)

								self.user_sn[status.user.screen_name][1] = [owner, profile_image]
								for u in tagged_users:
									if u in self.user_taggeds:
										pass
									else:
										self.user_taggeds[u] = [str(status.author.screen_name), str(media_url),
																status.id, profile_image_url,
																str(status.created_at.strftime('%m/%d/%Y')),
																str(status.created_at.time()), coord]

								if media_url.find(".mp4") > 0:
									media_type = "Video"
								else:
									media_type = "Image"

							except Exception as e:
								pass
						else:
							if media.find("swarmapp") > 0:
								# Foursquare
								media_url, owner, profile_image = get_url_media_from_foursquare(media)
								user_facebook = ""
								user_private_facebook = ""
								url_facebook = ""

								self.user_sn[status.user.screen_name][2] = [owner, profile_image]

								if media_url:
									url_facebook, user_facebook, profile_image = get_url_facebook_from_foursquare(
										"https://foursquare.com/" + owner)
									self.user_sn[status.user.screen_name][3] = [user_facebook, profile_image]

							else:
								media_url = ""

					url = ""
					owner = status.user.screen_name

					if media_url and not media_type:
						# GIF
						media_type = "Image"

					profile_image_url = status.user.profile_image_url_https.replace("_normal.", ".")
					self.adv_geo_info.append(
						[coord, status.user.screen_name, media_url, str(status.created_at.strftime('%m/%d/%Y')),
						 str(status.created_at.time()), status.id, url, str(status.source), media_type, screen_name,
						 profile_image_url, str(created_at.strftime('%m/%d/%Y')), str(created_at.time()),
						 status.user.profile_image_url_https.replace("_normal.", "."), status.text])
					tweets_found += 1
					keywords_list = []
					# Get keywords from twitter
					if status.entities.has_key('hashtags'):
						for h in status.entities['hashtags']:
							keywords_list.append(h['text'].lower())
					# List merge without dupe
					keywords_list = list(set(keywords_list + keywords_instagram))

				if tweets_count == int(ui.tb_tweets_number.text()):
					break

			return results

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_geolocation_information(self, coordinates, hashtag, mentions, social_networks, user_images, user_tweets, source, activity, top_words):
		# Search with coordinates
		try:

			results = 0
			self.adv_geo_info = []
			splace = ""
			sgeo = ""
			media = 0
			include_words = ""
			tweets_count = 0
			searched_tweets = []
			last_id = -1
			tweets_found = 0
			tmp_count = 0

			for status in tweepy.Cursor(api.search,
										q="",
										geocode=str(coordinates),
										count=int(ui.tb_tweets_number.text()),
										since=str(ui.tb_sdate.text()),
										until=str(ui.tb_edate.text()),
										result_type='recent').items():

				add = 1
				retweeted = 0

				# Media
				if status.entities.has_key('media'):
					media = 1
				else:
					media = 0

				# Retweeted
				screen_name = ""
				profile_image_url = ""
				created_at = status.created_at
				if hasattr(status, 'retweeted_status'):
					profile_image_url = status.retweeted_status.author.profile_image_url_https.replace("_normal.", ".")
					screen_name = status.retweeted_status.author.screen_name
					created_at = status.retweeted_status.created_at
					retweeted = 1
				else:
					profile_image_url = status.user.profile_image_url_https.replace("_normal.", ".")
					screen_name = status.user.screen_name

				if is_valid(status):
					results = 1
					if ui.cb_source_apps.isChecked():
						source.set_sources_information(status)

					if ui.cb_hashtags.isChecked():
						hashtag.set_hashtags_information(status, "*")

					if ui.cb_mentions.isChecked():
						mentions.set_mentions_information(status, "*")

					if ui.cb_metadata.isChecked():
						# Get metadata information from user images
						user_images.set_metadata_information(status)

					if ui.cb_media.isChecked():
						# Get images included in tweets
						if not ui.cb_metadata.isChecked():
							user_images.set_metadata_information(status)
						user_images.username = screen_name
						user_images.set_images_information(status)

					if ui.cb_words_frequency.isChecked():
						top_words.set_words_information(status)

					if ui.cb_activity.isChecked():
						activity.set_activity(status)

					if ui.cb_show_tweets.isChecked():
						user_tweets.set_find_information(status)

					profile_image_url = status.user.profile_image_url_https.replace("_normal.", ".")
					self.user_sn[status.user.screen_name] = [[profile_image_url], '', '', '']
					coord = ""
					try:
						coord = str(status.geo['coordinates'])
					except:
						coord = ""

					if not status.source:
						status.source = ""

					media_url = ""
					media_type = ""
					videos = []
					keywords_instagram = []

					if status.entities.has_key('media'):
						medias = status.entities['media']
						for m in medias:
							media_url = m['media_url']
							if str(media_url).find("video_thumb") >= 0:
								for content in status.extended_entities['media'][0]['video_info']['variants']:
									if str(content['url']).find(".mp4") >= 0:
										videos.append([str(content['url']), content['bitrate']])

								sort_vid = OrderedDict(sorted(videos, key=itemgetter(1), reverse=True))
								vid_top = sort_vid.items()[0:1]

								media_type = "Video"
								media_url = str(vid_top[0][0])

							if media_url.find("/media/") >= 0:
								media_type = "Image"

					if status.entities['urls']:
						media = str(status.entities['urls'][0]['expanded_url'])
						if media.find("instagram") > 0:
							# Instagram
							try:
								self.user_sn[status.user.screen_name][1] = ["?", "?"]
								response = urllib2.urlopen(str(media))
								html = response.read()

								media_url = get_url_media_from_instagram(html)
								tagged_users, owner, profile_image = get_tagged_users_from_instagram(html)
								keywords_instagram = get_hashtags_from_instagram(html)

								if owner and profile_image:
									self.user_sn[status.user.screen_name][1] = [owner, profile_image]

								for u in tagged_users:
									if u in self.user_taggeds:
										pass
									else:
										self.user_taggeds[u] = [str(status.author.screen_name),
																str(media_url), status.id,
																profile_image_url,
																str(status.created_at.strftime('%m/%d/%Y')),
																str(status.created_at.time()), coord]
								if media_url.find(".mp4") > 0:
									media_type = "Video"
								else:
									media_type = "Image"
							except Exception as e:
								pass

						else:
							if media.find("swarmapp") > 0:
								# Foursquare
								self.user_sn[status.user.screen_name][2] = ["?", "?"]
								tmp_media_url = ""
								if media_url:
									tmp_media_url = media_url
								media_url, owner, profile_image = get_url_media_from_foursquare(media)
								if tmp_media_url:
									media_url = tmp_media_url
								user_facebook = ""
								user_private_facebook = ""
								url_facebook = ""

								if owner and profile_image:
									self.user_sn[status.user.screen_name][2] = [owner, profile_image]

								if media_url:
									url_facebook, user_facebook, profile_image = get_url_facebook_from_foursquare(
										"https://foursquare.com/" + owner)
									self.user_sn[status.user.screen_name][3] = [user_facebook, profile_image]
							else:
								media_url = ""

					url = ""
					owner = status.user.screen_name
					if media_url and not media_type:
						# GIF
						media_type = "Image"

					profile_image_url = status.user.profile_image_url_https.replace("_normal.", ".")
					self.adv_geo_info.append(
						[coord, status.user.screen_name, media_url, str(status.created_at.strftime('%m/%d/%Y')),
						 str(status.created_at.time()), status.id, url, str(status.source), media_type, screen_name,
						 profile_image_url, str(created_at.strftime('%m/%d/%Y')), str(created_at.time()),
						 status.user.profile_image_url_https.replace("_normal.", ".")])
					tweets_found += 1

					keywords_list = []
					# Get keywords from twitter
					if status.entities.has_key('hashtags'):
						for h in status.entities['hashtags']:
							keywords_list.append(h['text'].lower())

					# List merge without dupe
					keywords_list = list(set(keywords_list + keywords_instagram))

					keywords_tmp = ""
					if self.user_keywords:
						if self.user_keywords.has_key(status.user.screen_name):
							keywords_tmp = self.user_keywords[status.user.screen_name]
							# List merge without dupe
							keywords_list = list(set(keywords_list + keywords_tmp))

					self.user_keywords[status.user.screen_name] = keywords_list

				tmp_count += 1
				tweets_count += 1
				if tmp_count == 10 or tweets_count == int(ui.tb_tweets_number.text()) or tmp_count == int(ui.tb_tweets_number.text()):
					cursor = ui.tb_messages.textCursor()
					cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
					cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
					cursor.removeSelectedText()

					br = 0
					if tweets_count == int(ui.tb_tweets_number.text()):
						br = 1
					show_ui_message("Processing tweet " + str(tweets_count) + "/" + str(ui.tb_tweets_number.text()), "INFO", br)

				if tmp_count == 10:
					tmp_count = 0

				app.processEvents()

				if tweets_count == int(ui.tb_tweets_number.text()):
					break

			return results

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Hashtags:
	"""Get hashtags included in tweets"""

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			# hashtag = [hashtag1, hashtag2, ... ]
			# hashtags_firstdate = {hashtag1: first_date1, hashtag2: first_date2, ... ]
			# hashtags_lastdate = {hashtag1: last_date1, hashtag2: last_date2, ... ]
			# hashtags_count = {hashtag1: tweets_number1, hashtag2: tweets_number2, ... ]
			self.hashtags = []
			self.hashtags_owner = {}
			self.hashtags_firstdate = {}
			self.hashtags_lastdate = {}
			self.hashtags_count = {}
			self.hashtags_tweet = []
			self.hashtags_rt = {}
			self.hashtags_fv = {}
			self.hashtags_results1 = 0
			self.hashtags_results2 = 0
			self.hashtags_results3 = 0
			self.hashtags_top = {}
			self.hashtags_list = []
			self.hashtags_users = {}

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_hashtags_information(self, tweet, from_username):
		try:

			tmp = ""
			self.hashtags_list = []

			# Identify the tweet author
			if hasattr (tweet, 'retweeted_status'):
				screen_name = tweet.retweeted_status.author.screen_name.encode('utf-8')
			else:
				screen_name = tweet.user.screen_name.encode('utf-8')

			if from_username == "*" or screen_name.upper() in (from_username.upper()):

				try:
					fav_count = tweet.retweeted_status.favorite_count
				except Exception as e:
					fav_count = tweet.favorite_count

				for i in tweet.entities['hashtags']:

					if i['text']:
						tmp = tmp + "#" + i['text'] + " "
						self.hashtags_list.append(i['text'])

					if i['text'].upper() in (name.upper() for name in self.hashtags_rt):
						self.hashtags_rt[i['text'].upper()] += tweet.retweet_count
					else:
						self.hashtags_rt[i['text'].upper()] = tweet.retweet_count

					if i['text'].upper() in (name.upper() for name in self.hashtags_fv):
						self.hashtags_fv[i['text'].upper()] += fav_count
					else:
						self.hashtags_fv[i['text'].upper()] = fav_count

				screen_name = ""
				if len(tmp):
					if hasattr (tweet, 'retweeted_status'):
						screen_name = tweet.retweeted_status.author.screen_name
						profile_image_url = tweet.retweeted_status.author.profile_image_url.replace("_normal.", ".")
						#profile_image_url = tweet.retweeted_status.author.profile_image_url
						location = tweet.retweeted_status.author.location
					else:
						screen_name = tweet.user.screen_name
						profile_image_url = tweet.user.profile_image_url.replace("_normal.", ".")
						#profile_image_url = tweet.user.profile_image_url
						location = tweet.user.location

					self.hashtags_tweet.append([str(tweet.created_at.strftime('%m/%d/%Y')), str(tweet.created_at.time()), str(tweet.retweet_count), str(fav_count), tmp, str(tweet.id), screen_name, profile_image_url, location])
					self.hashtags_results1 += 1

				try:
					# Hashtags tweeted by a user
					if len (self.hashtags_users[screen_name]):
						self.hashtags_users[screen_name].extend(self.hashtags_list)
					else:
						self.hashtags_users[screen_name] = self.hashtags_list
				except Exception as e:
					self.hashtags_users[screen_name] = self.hashtags_list

				for h in tweet.entities['hashtags']:
					orig = h['text']
					upper = h['text'].upper()

					if upper in (name.upper() for name in self.hashtags):
						self.hashtags_count[upper] += 1
						if tweet.created_at < self.hashtags_firstdate[upper]:
							self.hashtags_firstdate[upper] = tweet.created_at
						if tweet.created_at > self.hashtags_lastdate[upper]:
							self.hashtags_lastdate[upper] = tweet.created_at

					else:
						self.hashtags.append(orig)
						self.hashtags_count[upper] = 1
						self.hashtags_firstdate[upper] = tweet.created_at
						self.hashtags_lastdate[upper] = tweet.created_at
						self.hashtags_results2 += 1
						self.hashtags_owner[upper] = screen_name

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_global_information(self):
		try:

			for h in self.hashtags:
				self.hashtags_top[h] = self.hashtags_count[h.upper()]

			sort_has = OrderedDict(sorted(self.hashtags_top.items(), key=itemgetter(1), reverse=True))
			self.hashtags_top = sort_has.items()[0:10]
			self.hashtags_results3 = len (self.hashtags_top)

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Mentions:
	""" Get mentions included in tweets """

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			# mention = [mention1, mention2, ... ]
			# mentions_count = {mention1: tweets_number1, mention2: tweets_number2, ... ]
			# mentions_firstdate = {mention1: first_date1, mention2: first_date2, ... ]
			# mentions_lastdate = {mention1: last_date1, mention2: last_date2, ... ]
			self.mentions = []
			self.mentions_firstdate = {}
			self.mentions_lastdate = {}
			self.mentions_name = {}
			self.mentions_count = {}
			self.mentions_tweet = []
			self.mentions_rt = {}
			self.mentions_fv = {}
			self.mentions_results3 = 0
			self.mentions_top = {}
			self.mentions_list = []
			self.mentions_users = {}
			self.mentions_profileimg = {}

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_mentions_information(self, tweet, from_username):
		try:

			tmp = ""
			self.mentions_list = []

			# Identify the tweet author
			if hasattr (tweet, 'retweeted_status'):
				screen_name = tweet.retweeted_status.author.screen_name.encode('utf-8')
			else:
				screen_name = tweet.user.screen_name.encode('utf-8')

			if from_username == "*" or screen_name.upper() in (from_username.upper()):

				try:
					fav_count = tweet.retweeted_status.favorite_count
				except Exception as e:
					fav_count = tweet.favorite_count

				for i in tweet.entities['user_mentions']:
					if i['screen_name'].encode('utf-8'):
						tmp = tmp + "@" + i['screen_name'].encode('utf-8') + " "
						self.mentions_list.append(i['screen_name'])

					if i['screen_name'].encode('utf-8').upper() in (name.upper() for name in self.mentions_rt):
						self.mentions_rt[i['screen_name'].encode('utf-8').upper()] += tweet.retweet_count
					else:
						self.mentions_rt[i['screen_name'].encode('utf-8').upper()] = tweet.retweet_count

					if i['screen_name'].encode('utf-8').upper() in (name.upper() for name in self.mentions_fv):
						self.mentions_fv[i['screen_name'].encode('utf-8').upper()] += fav_count
					else:
						self.mentions_fv[i['screen_name'].encode('utf-8').upper()] = fav_count

				screen_name = ""
				if len(tmp):
					if hasattr (tweet, 'retweeted_status'):
						screen_name = tweet.retweeted_status.author.screen_name.encode('utf-8')
						profile_image_url = tweet.retweeted_status.author.profile_image_url.replace("_normal.", ".")
						#profile_image_url = tweet.retweeted_status.author.profile_image_url
						location = tweet.retweeted_status.author.location.encode('utf-8')
					else:
						screen_name = tweet.user.screen_name.encode('utf-8')
						profile_image_url = tweet.user.profile_image_url.replace("_normal.", ".")
						#profile_image_url = tweet.user.profile_image_url
						location = tweet.user.location.encode('utf-8')

					self.mentions_tweet.append([str(tweet.created_at.strftime('%m/%d/%Y')), str(tweet.created_at.time()), str(tweet.retweet_count), str(fav_count), tmp, str(tweet.id), screen_name, profile_image_url, location])

				try:
					# Mentions tweeted by a user
					if len (self.mentions_users[screen_name]):
						self.mentions_users[screen_name].extend(self.mentions_list)
					else:
						self.mentions_users[screen_name] = self.mentions_list
				except Exception as e:
					self.mentions_users[screen_name] = self.mentions_list


				for m in tweet.entities['user_mentions']:
					orig = m['screen_name'].encode('utf-8')
					upper = m['screen_name'].encode('utf-8').upper()
					if upper in (name.upper() for name in self.mentions):
						self.mentions_count[upper] += 1
						if tweet.created_at < self.mentions_firstdate[upper]:
							self.mentions_firstdate[upper] = tweet.created_at
						if tweet.created_at > self.mentions_lastdate[upper]:
							self.mentions_lastdate[upper] = tweet.created_at

					else:
						self.mentions.append(orig)
						self.mentions_count[upper] = 1
						self.mentions_firstdate[upper] = tweet.created_at
						self.mentions_lastdate[upper] = tweet.created_at
						self.mentions_name[upper] = str(m['name'].encode('utf-8'))

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_global_information(self):
		try:

			for h in self.mentions:
				self.mentions_top[h] = self.mentions_count[h.upper()]

			sort_has = OrderedDict(sorted(self.mentions_top.items(), key=itemgetter(1), reverse=True))
			self.mentions_top = sort_has.items()[0:10]
			self.mentions_results3 = len (self.mentions_top)

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class User_Tweets:
	""" Handle user tweets """

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.tweets_find = []  # [[text, date, time, ID, screen_name, profile_image_url, location, name], ...]

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_find_information(self, tweet):
		try:

			# Identify a tweet with all user criteria
			retweeted = 0
			media = 0
			media_url = ""
			media_type = ""
			videos = []
			source_app = ""

			if tweet.entities.has_key('media') :
				medias = tweet.entities['media']
				for m in medias :
					media_url = m['media_url']
					if str(media_url).find("video_thumb") >= 0:
						for content in tweet.extended_entities['media'][0]['video_info']['variants']:
							if str(content['url']).find(".mp4") >= 0:
								videos.append([str(content['url']), content['bitrate']])

						sort_vid = OrderedDict(sorted(videos, key=itemgetter(1), reverse=True))
						vid_top = sort_vid.items()[0:1]

						media_type = "Video"
						media_url = str(vid_top[0][0])

					if media_url.find("/media/") >= 0:
						media_type = "Image"

			else:
				if tweet.entities['urls']:
					media = str(tweet.entities['urls'][0]['expanded_url'])
					if media.find("instagram") > 0:
						# Instagram
						try:
							response = urllib2.urlopen(str(media))
							html = response.read()
							media_url = get_url_media_from_instagram(html)
							media = 1
							if media_url.find(".mp4") > 0:
								media_type = "Video"
							else:
								media_type = "Image"
						except Exception as e:
							pass
					else:
						if media.find("swarmapp") > 0:
							# Foursquare
							media_url, owner, profile_image = get_url_media_from_foursquare(media)
							media = 1
							if media_url.find(".mp4") > 0:
								media_type = "Video"
							else:
								media_type = "Image"
						else:
							media_url = ""

			if hasattr (tweet, 'retweeted_status'):
				screen_name = tweet.retweeted_status.author.screen_name
				profile_image_url = tweet.retweeted_status.author.profile_image_url.replace("_normal.", ".")
				#profile_image_url = tweet.retweeted_status.author.profile_image_url
				location = tweet.retweeted_status.author.location
				name = tweet.retweeted_status.author.name
				source_app = tweet.retweeted_status.source
				retweeted = 1
				if tweet.retweeted_status.entities.has_key('media'):
					media = 1
			else:
				screen_name = tweet.user.screen_name
				profile_image_url = tweet.user.profile_image_url.replace("_normal.", ".")
				#profile_image_url = tweet.user.profile_image_url
				location = tweet.user.location
				name = tweet.user.name
				source_app = tweet.source

			self.tweets_find.append([tweet.text, tweet.created_at.strftime('%m/%d/%Y'), tweet.created_at.time(), tweet.id, screen_name, profile_image_url, location, name, media_url, media_type])

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Words_Tweets:
	""" Handle words in tweets """

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.top_words = {}  # Most used words
			self.ordered_words = {}
			self.top_dates = {}
			self.total_occurrences = 0

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_words_information(self, tweet):
		try:

			if not hasattr (tweet, 'retweeted_status'):
				# Identify words in a tweet
				english_words = ['a', 'about', 'above', 'across', 'after', 'afterwards']
				english_words += ['again', 'against', 'all', 'almost', 'alone', 'along']
				english_words += ['already', 'also', 'although', 'always', 'am', 'among']
				english_words += ['amongst', 'amoungst', 'amount', 'an', 'and', 'another']
				english_words += ['any', 'anyhow', 'anyone', 'anything', 'anyway', 'anywhere']
				english_words += ['are', 'around', 'as', 'at', 'back', 'be', 'became']
				english_words += ['because', 'become', 'becomes', 'becoming', 'been']
				english_words += ['before', 'beforehand', 'behind', 'being', 'below']
				english_words += ['beside', 'besides', 'between', 'beyond', 'bill', 'both']
				english_words += ['bottom', 'but', 'by', 'call', 'can', 'cannot', 'cant']
				english_words += ['co', 'computer', 'con', 'could', 'couldnt', 'cry', 'de']
				english_words += ['describe', 'detail', 'did', 'do', 'done', 'down', 'due']
				english_words += ['during', 'each', 'eg', 'eight', 'either', 'eleven', 'else']
				english_words += ['elsewhere', 'empty', 'enough', 'etc', 'even', 'ever']
				english_words += ['every', 'everyone', 'everything', 'everywhere', 'except']
				english_words += ['few', 'fifteen', 'fifty', 'fill', 'find', 'fire', 'first']
				english_words += ['five', 'for', 'former', 'formerly', 'forty', 'found']
				english_words += ['four', 'from', 'front', 'full', 'further', 'get', 'give']
				english_words += ['go', 'had', 'has', 'hasnt', 'have', 'he', 'hence', 'her']
				english_words += ['here', 'hereafter', 'hereby', 'herein', 'hereupon', 'hers']
				english_words += ['herself', 'him', 'himself', 'his', 'how', 'however']
				english_words += ['hundred', 'i', 'ie', 'if', 'in', 'inc', 'indeed']
				english_words += ['interest', 'into', 'is', 'it', 'its', 'itself', 'keep']
				english_words += ['last', 'latter', 'latterly', 'least', 'less', 'ltd', 'made']
				english_words += ['many', 'may', 'me', 'meanwhile', 'might', 'mill', 'mine']
				english_words += ['more', 'moreover', 'most', 'mostly', 'move', 'much']
				english_words += ['must', 'my', 'myself', 'name', 'namely', 'neither', 'never']
				english_words += ['nevertheless', 'next', 'nine', 'no', 'nobody', 'none']
				english_words += ['noone', 'nor', 'not', 'nothing', 'now', 'nowhere', 'of']
				english_words += ['off', 'often', 'on','once', 'one', 'only', 'onto', 'or']
				english_words += ['other', 'others', 'otherwise', 'our', 'ours', 'ourselves']
				english_words += ['out', 'over', 'own', 'part', 'per', 'perhaps', 'please']
				english_words += ['put', 'rather', 're', 's', 'same', 'see', 'seem', 'seemed']
				english_words += ['seeming', 'seems', 'serious', 'several', 'she', 'should']
				english_words += ['show', 'side', 'since', 'sincere', 'six', 'sixty', 'so']
				english_words += ['some', 'somehow', 'someone', 'something', 'sometime']
				english_words += ['sometimes', 'somewhere', 'still', 'such', 'system', 'take']
				english_words += ['ten', 'than', 'that', 'the', 'their', 'them', 'themselves']
				english_words += ['then', 'thence', 'there', 'thereafter', 'thereby']
				english_words += ['therefore', 'therein', 'thereupon', 'these', 'they']
				english_words += ['thick', 'thin', 'third', 'this', 'those', 'though', 'three']
				english_words += ['three', 'through', 'throughout', 'thru', 'thus', 'to']
				english_words += ['together', 'too', 'top', 'toward', 'towards', 'twelve']
				english_words += ['twenty', 'two', 'un', 'under', 'until', 'up', 'upon']
				english_words += ['us', 'very', 'via', 'was', 'we', 'well', 'were', 'what']
				english_words += ['whatever', 'when', 'whence', 'whenever', 'where']
				english_words += ['whereafter', 'whereas', 'whereby', 'wherein', 'whereupon']
				english_words += ['wherever', 'whether', 'which', 'while', 'whither', 'who']
				english_words += ['whoever', 'whole', 'whom', 'whose', 'why', 'will', 'with']
				english_words += ['within', 'without', 'would', 'yet', 'you', 'your']
				english_words += ['yours', 'yourself', 'yourselves']


				spanish_words = ['a', 'acuerdo', 'adelante', 'ademas', 'además', 'adrede', 'ahi', 'ahí', 'ahora', 'al', 'alli', 'allí', 'alrededor', 'antano', 'antaño', 'ante', 'antes', 'apenas', 'aproximadamente', 'aquel', 'aquél', 'aquella', 'aquélla', 'aquellas', 'aquéllas', 'aquello', 'aquellos', 'aquéllos', 'aqui', 'aquí', 'arriba', 'abajo', 'asi', 'así', 'aun', 'aún', 'aunque', 'b', 'bajo', 'bastante', 'bien', 'breve', 'c', 'casi', 'cerca', 'claro', 'como', 'cómo', 'con', 'conmigo', 'contigo', 'contra', 'cual', 'cuál', 'cuales', 'cuáles', 'cuando', 'cuándo', 'cuanta', 'cuánta', 'cuantas', 'cuántas', 'cuanto', 'cuánto', 'cuantos', 'cuántos', 'd', 'de', 'debajo', 'del', 'delante', 'demasiado', 'dentro', 'deprisa', 'desde', 'despacio', 'despues', 'después', 'detras', 'detrás', 'dia', 'día', 'dias', 'días', 'donde', 'dónde', 'dos', 'durante', 'e', 'el', 'él', 'ella', 'ellas', 'ellos', 'en', 'encima', 'enfrente', 'enseguida', 'entre', 'es', 'esa', 'ésa', 'esas', 'ésas', 'ese', 'ése', 'eso', 'esos', 'ésos', 'esta', 'está', 'ésta', 'estado', 'estados', 'estan', 'están', 'estar', 'estas', 'éstas', 'este', 'éste', 'esto', 'estos', 'éstos', 'ex', 'excepto', 'f', 'final', 'fue', 'fuera', 'fueron', 'g', 'general', 'gran', 'h', 'ha', 'habia', 'había', 'habla', 'hablan', 'hace', 'hacia', 'han', 'hasta', 'hay', 'horas', 'hoy', 'i', 'incluso', 'informo', 'informó', 'j', 'junto', 'k', 'l', 'la', 'lado', 'las', 'le', 'lejos', 'lo', 'los', 'luego', 'm', 'mal', 'mas', 'más', 'mayor', 'me', 'medio', 'mejor', 'menos', 'menudo', 'mi', 'mí', 'mia', 'mía', 'mias', 'mías', 'mientras', 'mio', 'mío', 'mios', 'míos', 'mis', 'mismo', 'mucho', 'muy', 'n', 'nada', 'nadie', 'ninguna', 'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'nueva', 'nuevo', 'nunca', 'o', 'os', 'otra', 'otros', 'p', 'pais', 'paìs', 'para', 'parte', 'pasado', 'peor', 'pero', 'poco', 'por', 'porque', 'pronto', 'proximo', 'próximo', 'puede', 'q', 'qeu', 'que', 'qué', 'quien', 'quién', 'quienes', 'quiénes', 'quiza', 'quizá', 'quizas', 'quizás', 'r', 'raras', 'repente', 's', 'salvo', 'se', 'sé', 'segun', 'según', 'ser', 'sera', 'será', 'si', 'sí', 'sido', 'siempre', 'sin', 'sobre', 'solamente', 'solo', 'sólo', 'son', 'soyos', 'su', 'supuesto', 'sus', 'suya', 'suyas', 'suyo', 't', 'tal', 'tambien', 'también', 'tampoco', 'tarde', 'te', 'temprano', 'ti', 'tiene', 'todavia', 'todavía', 'todo', 'todos', 'tras', 'tu', 'tú', 'tus', 'tuya', 'tuyas', 'tuyo', 'tuyos', 'u', 'un', 'una', 'unas', 'uno', 'unos', 'usted', 'ustedes', 'v', 'veces', 'vez', 'vosotras', 'vosotros', 'vuestra', 'vuestras', 'vuestro', 'vuestros', 'w', 'x', 'y', 'ya', 'yo', 'z']

				catalan_words = ["a", "abans", "abans-d'ahir", "abintestat", "ací", "adesiara", "adés", "adéu", "adàgio", "ah", "ahir", "ai", "aitambé", "aitampoc", "aitan", "aitant", "aitantost", "aixà", "això", "així", "aleshores", "algun", "alguna", "algunes", "alguns", "algú", "alhora", "allà", "allèn", "allò", "allí", "almenys", "alto", "altra", "altre", "altres", "altresí", "altri", "alça", "al·legro", "amargament", "amb", "ambdues", "ambdós", "amunt", "amén", "anc", "andante", "andantino", "anit", "ans", "antany", "apa", "aprés", "aqueix", "aqueixa", "aqueixes", "aqueixos", "aqueixs", "aquell", "aquella", "aquelles", "aquells", "aquest", "aquesta", "aquestes", "aquests", "aquèn", "aquí", "ara", "arran", "arrera", "arrere", "arreu", "arri", "arruix", "atxim", "au", "avall", "avant", "aviat", "avui", "açò", "bah", "baix", "baldament", "ballmanetes", "banzim-banzam", "bastant", "bastants", "ben", "bis", "bitllo-bitllo", "bo", "bé", "ca", "cada", "cal", "cap", "car", "caram", "catorze", "cent", "centes", "cents", "cerca", "cert", "certa", "certes", "certs", "cinc", "cinquanta", "cinquena", "cinquenes", "cinquens", "cinquè", "com", "comsevulla", "contra", "cordons", "corrents", "cric-crac", "d", "daixonses", "daixò", "dallonses", "dallò", "dalt", "daltabaix", "damunt", "darrera", "darrere", "davall", "davant", "de", "debades", "dedins", "defora", "dejorn", "dejús", "dellà", "dementre", "dempeus", "demés", "demà", "des", "desena", "desenes", "desens", "després", "dessobre", "dessota", "dessús", "desè", "deu", "devers", "devora", "deçà", "diferents", "dinou", "dins", "dintre", "disset", "divers", "diversa", "diverses", "diversos", "divuit", "doncs", "dos", "dotze", "dues", "durant", "ecs", "eh", "el", "ela", "elis", "ell", "ella", "elles", "ells", "els", "em", "emperò", "en", "enans", "enant", "encara", "encontinent", "endalt", "endarrera", "endarrere", "endavant", "endebades", "endemig", "endemés", "endemà", "endins", "endintre", "enfora", "engir", "enguany", "enguanyasses", "enjús", "enlaire", "enlloc", "enllà", "enrera", "enrere", "ens", "ensems", "ensota", "ensús", "entorn", "entre", "entremig", "entretant", "entrò", "envers", "envides", "environs", "enviró", "ençà", "ep", "ep", "era", "eren", "eres", "ergo", "es", "escar", "essent", "esser", "est", "esta", "estada", "estades", "estan", "estant", "estar", "estaran", "estarem", "estareu", "estaria", "estarien", "estaries", "estaré", "estarà", "estaràs", "estaríem", "estaríeu", "estat", "estats", "estava", "estaven", "estaves", "estem", "estes", "esteu", "estic", "estiguem", "estigueren", "estigueres", "estigues", "estiguessis", "estigueu", "estigui", "estiguin", "estiguis", "estigué", "estiguérem", "estiguéreu", "estigués", "estiguí", "estos", "està", "estàs", "estàvem", "estàveu", "et", "etc", "etcètera", "ets", "excepte", "fins", "fora", "foren", "fores", "força", "fos", "fossin", "fossis", "fou", "fra", "fui", "fóra", "fórem", "fóreu", "fóreu", "fóssim", "fóssiu", "gaire", "gairebé", "gaires", "gens", "girientorn", "gratis", "ha", "hagi", "hagin", "hagis", "haguda", "hagudes", "hagueren", "hagueres", "haguessin", "haguessis", "hagut", "haguts", "hagué", "haguérem", "haguéreu", "hagués", "haguéssim", "haguéssiu", "haguí", "hala", "han", "has", "hauran", "haurem", "haureu", "hauria", "haurien", "hauries", "hauré", "haurà", "hauràs", "hauríem", "hauríeu", "havem", "havent", "haver", "haveu", "havia", "havien", "havies", "havíem", "havíeu", "he", "hem", "heu", "hi", "ho", "hom", "hui", "hàgim", "hàgiu", "i", "igual", "iguals", "inclusive", "ja", "jamai", "jo", "l", "la", "leri-leri", "les", "li", "lla", "llavors", "llevat", "lluny", "llur", "llurs", "lo", "los", "ls", "m", "ma", "mai", "mal", "malament", "malgrat", "manco", "mant", "manta", "mantes", "mantinent", "mants", "massa", "mateix", "mateixa", "mateixes", "mateixos", "me", "mentre", "mentrestant", "menys", "mes", "meu", "meua", "meues", "meus", "meva", "meves", "mi", "mig", "mil", "mitges", "mitja", "mitjançant", "mitjos", "moixoni", "molt", "molta", "moltes", "molts", "mon", "mos", "més", "n", "na", "ne", "ni", "ningú", "no", "nogensmenys", "només", "noranta", "nos", "nosaltres", "nostra", "nostre", "nostres", "nou", "novena", "novenes", "novens", "novè", "ns", "nòs", "nós", "o", "oh", "oi", "oidà", "on", "onsevulga", "onsevulla", "onze", "pas", "pengim-penjam", "per", "perquè", "pertot", "però", "piano", "pla", "poc", "poca", "pocs", "poques", "potser", "prest", "primer", "primera", "primeres", "primers", "pro", "prompte", "prop", "prou", "puix", "pus", "pàssim", "qual", "quals", "qualsevol", "qualsevulla", "qualssevol", "qualssevulla", "quan", "quant", "quanta", "quantes", "quants", "quaranta", "quart", "quarta", "quartes", "quarts", "quasi", "quatre", "que", "quelcom", "qui", "quin", "quina", "quines", "quins", "quinze", "quisvulla", "què", "ran", "re", "rebé", "renoi", "rera", "rere", "res", "retruc", "s", "sa", "salvament", "salvant", "salvat", "se", "segon", "segona", "segones", "segons", "seguida", "seixanta", "sempre", "sengles", "sens", "sense", "ser", "seran", "serem", "sereu", "seria", "serien", "series", "seré", "serà", "seràs", "seríem", "seríeu", "ses", "set", "setanta", "setena", "setenes", "setens", "setze", "setè", "seu", "seua", "seues", "seus", "seva", "seves", "si", "sia", "siau", "sic", "siguem", "sigues", "sigueu", "sigui", "siguin", "siguis", "sinó", "sis", "sisena", "sisenes", "sisens", "sisè", "sobre", "sobretot", "sol", "sola", "solament", "soles", "sols", "som", "son", "sos", "sota", "sots", "sou", "sovint", "suara", "sí", "sóc", "són", "t", "ta", "tal", "tals", "també", "tampoc", "tan", "tanmateix", "tant", "tanta", "tantes", "tantost", "tants", "te", "tercer", "tercera", "terceres", "tercers", "tes", "teu", "teua", "teues", "teus", "teva", "teves", "ton", "tos", "tost", "tostemps", "tot", "tota", "total", "totes", "tothom", "tothora", "tots", "trenta", "tres", "tret", "tretze", "tu", "tururut", "u", "uf", "ui", "uix", "ultra", "un", "una", "unes", "uns", "up", "upa", "us", "va", "vagi", "vagin", "vagis", "vaig", "vair", "vam", "van", "vares", "vas", "vau", "vem", "verbigràcia", "vers", "vet", "veu", "vint", "vora", "vos", "vosaltres", "vostra", "vostre", "vostres", "vostè", "vostès", "vuit", "vuitanta", "vuitena", "vuitenes", "vuitens", "vuitè", "vés", "vàreig", "vàrem", "vàreu", "vós", "xano-xano", "xau-xau", "xec", "érem", "éreu", "és", "ésser", "àdhuc", "àlies", "ça", "ço", "òlim", "ídem", "últim", "última", "últimes", "últims", "únic", "única", "únics", "úniques"]

				symbols = ['!', '"', '·', '$', '%', '&', '/', '(', ')', '=', '?', '¿', '^', '*', ',', '.', '-', ';', ':', '_', '[', ']', '@', '#', '~', '¡']

				empty_words = english_words + spanish_words + catalan_words + symbols

				words = tweet.text.split()
				words = [w for w in words if w.lower() not in empty_words]
				words = [w for w in words if w[0] not in ['@', '#']]

				for word in words:
					freq = words.count(word)

					if self.top_words.has_key(word):
						freq = self.top_words[word] + freq
						datefrom = self.top_dates[word][0]
						dateto = self.top_dates[word][1]

						if tweet.created_at < datefrom:
							datefrom = tweet.created_at
						if tweet.created_at > dateto:
							dateto = tweet.created_at

						self.top_words[word] = freq
						self.top_dates[word] = [datefrom, dateto]

					else:
						# First occurrence
						self.top_words[word] = freq
						self.top_dates[word] = [tweet.created_at, tweet.created_at]

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


#==========================================================================
class Favorites:
	""" Handle favorite tweets """

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.favorites_tweets = []

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_favorites_information(self, api, username, total_favs):
		try:

			favorites_count = 0
			page = 1
			end = 0
			while not end:
				try:

					favorites = api.favorites(id=username, page=page)
					if favorites:
						for tweet in favorites:
							favorites_count += 1
							if favorites_count > total_favs:
								end = 1
							else:
								tweet_date = tweet.created_at.strftime('%m/%d/%Y')
								tweet_time = tweet.created_at.time()
								media_url=""

								if tweet.entities.has_key('media') :
									medias = tweet.entities['media']
									for m in medias :
										media_url = m['media_url']

								profile_image_url = tweet.user.profile_image_url_https.replace("_normal.", ".")
								self.favorites_tweets.append([tweet.id, tweet_date, tweet_time, tweet.user.screen_name, profile_image_url, tweet.user.name, media_url, tweet.text])
					page += 1

				except Exception as e:
					rate_limit = show_error(e)
					if rate_limit:
						show_ui_message("Waiting...", "INFO", br=1)
						time.sleep(60)
						continue

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class User_Conversations:
	""" Show conversations between two users """

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.conversations = {}  # {'tweet1_id1': '[[tweet1], [tweet2], ..., [tweet_n]], 'tweet2_id2': '[[tweet1], [tweet2], ..., [tweet_n]], ...}
			self.processed_tweets = []

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def make_tweet_to_append(self, tweet, position):
		try:
			tweet_to_append = []

			user_screen_name = tweet.user.screen_name
			user_profile_image_url = tweet.user.profile_image_url
			user_location = tweet.user.location
			user_name = tweet.user.name
			tweet_date = tweet.created_at.strftime('%m/%d/%Y')
			tweet_time = tweet.created_at.time()
			tweet_datetime = tweet.created_at.strftime('%Y/%m/%d') + "-" + str(tweet_time)

			tweet_to_append = [tweet.id, tweet.text, tweet_date, tweet_time, user_screen_name, user_profile_image_url, user_location, user_name, position, tweet_datetime, "", tweet.in_reply_to_status_id]

			return tweet_to_append

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_tweets_conversations(self, tweet):
		try:

			add_tweet_conversation = 1
			conversation_id = 0

			while add_tweet_conversation > 0:
				if tweet.id not in self.processed_tweets:
					self.processed_tweets.append(tweet.id)

					if tweet.in_reply_to_status_id:
						# Reply
						try:

							if conversation_id == 0:
								conversation_id = tweet.in_reply_to_status_id

							tweet_in_reply = api.get_status(tweet.in_reply_to_status_id)

							tweet_to_append_in_reply = self.make_tweet_to_append(tweet_in_reply, "")
							tweet_to_append_reply = self.make_tweet_to_append(tweet, "")

							conversation_to_append = tweet_to_append_in_reply
							conversation = self.conversations.get(conversation_id)

							if conversation:

								for conv in conversation:
									if conv[0] == tweet_to_append_in_reply[0]:
										# Already exist
										break
									else:
										self.conversations[conversation_id].append(conversation_to_append)
										break
							else:
								self.conversations[conversation_id] = [conversation_to_append]

							conversation_to_append = tweet_to_append_reply
							self.conversations[conversation_id].append(conversation_to_append)


							search_user_screen_name = tweet.user.screen_name
							search_tweet_id = tweet.id
							search_since = tweet.created_at.strftime('%Y-%m-%d')
							tmp = tweet.created_at + datetime.timedelta(days=1)
							search_until = tmp.strftime('%Y-%m-%d')

							# Find others replies
							for status in tweepy.Cursor(api.search,
														q="@" + search_user_screen_name,
														since_id=search_tweet_id,
														count=100,
														since=search_since,
														until=search_until,
														result_type='recent').items():

								if status.in_reply_to_status_id == search_tweet_id:
									tweet_to_append = self.make_tweet_to_append(status, "")
									self.conversations[conversation_id].append(tweet_to_append)

							tweet = tweet_in_reply

						except Exception as e:
							show_error(e)
							add_tweet_conversation = 0

					else:
						add_tweet_conversation = 0
				else:
					add_tweet_conversation = 0

		except Exception as e:
			show_ui_message(str(e), "ERROR", br=1)


# ==========================================================================
class User_Relations:
	""" Show relations from protected profiles """

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.followedby_users = []  # Followers
			self.following_users = []  # Friends
			self.protected_tweets = []  # Tweets

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_relations(self, username):
		try:

			show_ui_message("Identifying relations...", "INFO", 1)

			self.followedby_users = []  # Followers
			self.following_users = []  # Friends
			self.protected_tweets = []  # Tweets
			url = "https://mobile.twitter.com/search?f=tweets&q=to:" + username

			response = urllib2.urlopen(url)
			html = response.read()

			followed = []
			following = []
			hashtags = []
			mentions = []
			status = []

			if html:
				screenname = re.findall('<a href="/(.*)\?p=s">', html)
				status = re.findall('<a name="tweet_(.*)" href=', html)
				screenname = list(set(screenname))
				n = 0
				followedby_count = 0
				following_count = 0
				for sname in screenname:
					if not (sname.lower() in username.lower()):
						try:
							b = api.show_friendship(source_screen_name=username, target_screen_name=sname)
							if b[1].followed_by:
								followed.append(sname)
								followedby_count += 1
								followedby_user = User()
								api_followedby = api.get_user(sname)
								followedby_user.set_user_information(api_followedby)
								self.followedby_users.append(followedby_user)

							if b[1].following:
								following.append(sname)
								following_count += 1
								following_user = User()
								api_following = api.get_user(sname)
								following_user.set_user_information(api_following)
								self.following_users.append(following_user)

						except Exception as e:
							pass

					n+=1
					show_ui_message(str(n) + " identified relations. Followed by: " + str(followedby_count) + " users. Following: " + str(following_count) + " users", "INFO", 0)

					cursor = ui.tb_messages.textCursor()
					cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
					cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
					cursor.removeSelectedText()

				n = 0

				for content in status:
					try:

						n += 1
						show_ui_message(str(n) + " identified tweets. Followed by: " + str(followedby_count) + " users. Following: " + str(following_count) + " users", "INFO", 0)

						cursor = ui.tb_messages.textCursor()
						cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
						cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
						cursor.removeSelectedText()

						tweet = api.get_status(content)
						self.protected_tweets.append(tweet)

						for i in tweet.entities['hashtags']:
							if i['text'] and (i['text'].lower() not in str(hashtags).lower()):
								hashtags.append(str(i['text']))

						for i in tweet.entities['user_mentions']:

							if i['screen_name'] and (i['screen_name'].lower() not in username.lower()) and (i['screen_name'].lower() not in str(mentions).lower()):
								mentions.append(str(i['screen_name']))
								b = api.show_friendship(source_screen_name=username, target_screen_name=i['screen_name'])
								if b[1].followed_by:
									followed.append(str(i['screen_name']))
									followedby_count += 1
									followedby_user = User()
									api_followedby = api.get_user(str(i['screen_name']))
									followedby_user.set_user_information(api_followedby)
									self.followedby_users.append(followedby_user)

								if b[1].following:
									following.append(str(i['screen_name']))
									following_count += 1
									following_user = User()
									api_following = api.get_user(str(i['screen_name']))
									following_user.set_user_information(api_following)
									self.following_users.append(following_user)

					except Exception as e:
						pass

				for sname in followed:
					if not (sname.lower() in username.lower()) and (sname not in following):
						try:
							b = api.show_friendship(source_screen_name=username, target_screen_name=sname)
							if b[1].following:
								following.append(sname)
								following_count += 1
								following_user = User()
								api_following = api.get_user(sname)
								following_user.set_user_information(api_following)
								self.following_users.append(following_user)
						except Exception as e:
							pass

					n+=1
					show_ui_message("Followed by: " + str(followedby_count) + " users. Following: " + str(following_count) + " users", "INFO", 0)

					cursor = ui.tb_messages.textCursor()
					cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
					cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
					cursor.removeSelectedText()

				for sname in following:
					if not (sname.lower() in username.lower()) and (sname not in followed):
						try:
							b = api.show_friendship(source_screen_name=username, target_screen_name=sname)
							if b[1].followed_by:
								followed.append(sname)
								followedby_count += 1
								followedby_user = User()
								api_followedby = api.get_user(sname)
								followedby_user.set_user_information(api_followedby)
								self.followedby_users.append(followedby_user)
						except Exception as e:
							pass

					n+=1
					show_ui_message("Followed by: " + str(followedby_count) + " users. Following: " + str(following_count) + " users", "INFO", 0)

					cursor = ui.tb_messages.textCursor()
					cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
					cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
					cursor.removeSelectedText()

			show_ui_message("Relations: OK", "INFO", 1)

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class User_Images:
	""" Handle user images and metadata information """

	# ----------------------------------------------------------------------
	def __init__(self):
		try:

			self.metadata = 0
			self.profile_image_url = ""
			self.profile_banner_url = ""
			self.screen_name = ""
			self.pic = []
			self.pics_directory = ""
			self.pics_result = 0
			self.username = ""
			self.images = ""
			self.meta = ""
			self.meta_description = {}
			self.meta_copyright = {}
			self.meta_date = {}
			self.meta_make = {}
			self.meta_model = {}
			self.meta_software = {}
			self.meta_distance = {}
			self.meta_size = {}
			self.meta_platform = {}
			self.meta_iccdate = {}
			self.meta_GPSLatitude = {}
			self.meta_coordinates = {}
			self.meta_thumb = {}
			self.meta_profile_image = []
			self.meta_profile_banner = []
			self.platforms = {
				"APPL": "Apple Computer Inc.",
				"MSFT": "Microsoft Corporation",
				"SGI ": "Silicon Graphics Inc.",
				"SUNW": "Sun Microsystems Inc.",
				"TGNT": "Taligent Inc.",
			}

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_images_information(self, tweet):
		try:

			media_url = ""
			image = ""
			media_type = "Image"
			in_reply_to_screen_name = ""

			reply = tweet.in_reply_to_screen_name
			if reply:
				in_reply_to_screen_name = reply

			if tweet.entities.has_key('media') :
				medias = tweet.entities['media']
				for m in medias :
					media_url = m['media_url']
					if str(media_url).find("video") >= 0:
						media_type = "Video"
						videos = []
						for content in tweet.extended_entities['media'][0]['video_info']['variants']:
							if str(content['url']).find(".mp4") >= 0:
								videos.append([str(content['url']), content['bitrate']])

						sort_vid = OrderedDict(sorted(videos, key=itemgetter(1), reverse=True))
						vid_top = sort_vid.items()[0:1]
						media_url = str(vid_top[0][0])

					else:
						if ui.cb_media_download.isChecked() or ui.cb_metadata.isChecked():
							if not os.path.isdir(self.username):
								os.mkdir(self.username)
							img = urllib2.urlopen(media_url).read()
							filename = media_url.split('/')[-1]
							self.pics_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + self.username
							image = self.pics_directory + "/" +filename
							if not os.path.exists(self.username+"/"+filename):
								f = open(self.username+"/"+filename, 'wb')
								f.write(img)
								f.close()

			else:
				if tweet.entities['urls']:
					media = str(tweet.entities['urls'][0]['expanded_url'])
					if media.find("instagram") > 0:
						# Instagram
						try:
							response = urllib2.urlopen(str(media))
							html = response.read()
							media_url = get_url_media_from_instagram(html)
							if media_url.find(".mp4") > 0:
								media_type = "Video"
						except Exception as e:
							pass
					else:
						media_url = ""

			if media_url:
				screen_name = ""
				profile_image_url_orig = ""
				created_at = tweet.created_at
				screen_name = tweet.user.screen_name
				screen_name_orig = ""
				profile_image_url = tweet.user.profile_image_url_https.replace("_normal.", ".")
				if hasattr (tweet, 'retweeted_status'):
					source_app = str(tweet.retweeted_status.source)
					source_likes = str(tweet.retweeted_status.favorite_count)
					source_rt = str(tweet.retweeted_status.retweet_count)
					profile_image_url_orig = tweet.retweeted_status.author.profile_image_url_https.replace("_normal.", ".")
					screen_name_orig = tweet.retweeted_status.author.screen_name
					created_at = tweet.retweeted_status.created_at
				else:
					source_app = tweet.source
					source_likes = str(tweet.favorite_count)
					source_rt = str(tweet.retweet_count)

				self.pic.append([media_url, image, str(tweet.created_at.strftime('%m/%d/%Y')), str(tweet.created_at.time()), str(tweet.id), screen_name_orig, profile_image_url_orig, str(created_at.strftime('%m/%d/%Y')), str(created_at.time()), media_type, screen_name, profile_image_url, source_app, source_rt, source_likes, in_reply_to_screen_name])

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

	# ----------------------------------------------------------------------
	def set_metadata_information(self, tweet):
		try:

			for p in self.pic:
				path = p[1]
				self.meta_description[p[0]] = ""
				self.meta_copyright[p[0]] = ""
				self.meta_date[p[0]] = ""
				self.meta_make[p[0]] = ""
				self.meta_model[p[0]] = ""
				self.meta_software[p[0]] = ""
				self.meta_distance[p[0]] = ""
				self.meta_platform[p[0]] = ""
				self.meta_iccdate[p[0]] = ""
				self.meta_coordinates[p[0]] = ""
				self.meta_thumb[p[0]] = ""

				fileName, fileExtension = os.path.splitext(path)

				if os.path.exists(path):
					img = Image.open(path)
					if fileExtension in (".jpg", ".jpeg"):
						if img._getexif():
							metadata = 1
							exif = { ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS }
							self.meta_description[p[0]] = unicode(exif['ImageDescription'])
							self.meta_copyright[p[0]] = unicode(exif['Copyright'])
							self.meta_date[p[0]] = unicode(exif['ImageDescription'])
							self.meta_make[p[0]] = unicode(exif['Make'])
							self.meta_model[p[0]] = unicode(exif['Model'])
							self.meta_software[p[0]] = unicode(exif['Software'])
							self.meta_distance[p[0]] = unicode(exif['SubjectDistance'][0]/float(exif['SubjectDistance'][1])) + " meters"

					self.meta_size[p[0]] = str(img.size[0]) + "x" + str(img.size[1]) + " px"
					if 'icc_profile' in img.info:
						icc_profile = img.info.get("icc_profile")
						if icc_profile:
							platform = icc_profile[40:44]
							metadata = 1
							if platform in ('APPL', 'MSFT', 'SGI ', 'SUNW', 'TGNT'):
								self.meta_platform[p[0]] = self.platforms[platform]
							datetime = struct.unpack('>hhhhhh',icc_profile[24:36])
							tmp_tuple = (0, 0, 0)
							final_tuple = datetime + tmp_tuple
							self.meta_iccdate[p[0]] = unicode(time.strftime('%Y/%m/%d %H:%M:%S', final_tuple))

					# Checkf for GPS information
					try:
						latitude = metadata.__getitem__("Exif.GPSInfo.GPSLatitude")
						latitudeRef = metadata.__getitem__("Exif.GPSInfo.GPSLatitudeRef")
						longitude = metadata.__getitem__("Exif.GPSInfo.GPSLongitude")
						longitudeRef = metadata.__getitem__("Exif.GPSInfo.GPSLongitudeRef")

						latitude = str(latitude).split("=")[1][1:-1].split(" ");
						latitude = map(lambda f: str(float(Fraction(f))), latitude)
						latitude = latitude[0] + u"\u00b0" + latitude[1] + "'" + latitude[2] + '"' + " " + str(latitudeRef).split("=")[1][1:-1]

						longitude = str(longitude).split("=")[1][1:-1].split(" ");
						longitude = map(lambda f: str(float(Fraction(f))), longitude)
						longitude = longitude[0] + u"\u00b0" + longitude[1] + "'" + longitude[2] + '"' + " " + str(longitudeRef).split("=")[1][1:-1]

						latitude_value = dms_to_decimal(*metadata.__getitem__("Exif.GPSInfo.GPSLatitude").value + [metadata.__getitem__("Exif.GPSInfo.GPSLatitudeRef").value]);
						longitude_value = dms_to_decimal(*metadata.__getitem__("Exif.GPSInfo.GPSLongitude").value + [metadata.__getitem__("Exif.GPSInfo.GPSLongitudeRef").value]);

						self.meta_coordinates[p[0]] = str(latitude_value) + ", " + str(longitude_value)
					except Exception as e:
						# No GPS information
						pass

		except Exception as e:
			show_ui_message(str(e), "ERROR", br=1)

	# ----------------------------------------------------------------------
	def get_metadata(self, filename, save, username):
		try:

			metadata = 0
			platforms = {
				"APPL" : "Apple Computer Inc.",
				"MSFT" : "Microsoft Corporation",
				"SGI " : "Silicon Graphics Inc.",
				"SUNW" : "Sun Microsystems Inc.",
				"TGNT" : "Taligent Inc.",
			}

			self.profile_image_url = filename

			if save:
				save_image(filename, username)

			pics_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + username

			filename = filename.split('/')[-1]
			path = pics_directory + "/" + filename
			fileName, fileExtension = os.path.splitext(path)

			if os.path.exists(path):

				img = Image.open(path)
				if fileExtension in (".jpg", ".jpeg"):
					if img._getexif():
						metadata = 1
						exif = { ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS }
						self.meta_profile_image.append(unicode(exif['ImageDescription']))
						self.meta_profile_image.append(unicode(exif['Copyright']))
						self.meta_profile_image.append(unicode(exif['DateTimeOriginal']))
						self.meta_profile_image.append(unicode(exif['Make']))
						self.meta_profile_image.append(unicode(exif['Model']))
						self.meta_profile_image.append(unicode(exif['Software']))
						self.meta_profile_image.append(unicode(exif['SubjectDistance'][0]/float(exif['SubjectDistance'][1])) + " meters")

					else:
						self.meta_profile_image.append("")
						self.meta_profile_image.append("")
						self.meta_profile_image.append("")
						self.meta_profile_image.append("")
						self.meta_profile_image.append("")
						self.meta_profile_image.append("")
						self.meta_profile_image.append("")

				if 'icc_profile' in img.info:
					icc_profile = img.info.get("icc_profile")
					if icc_profile:
						platform = icc_profile[40:44]
						metadata = 1
						if platform in ('APPL', 'MSFT', 'SGI ', 'SUNW', 'TGNT'):
							self.meta_profile_image.append(platforms[platform])

						datetime = struct.unpack('>hhhhhh',icc_profile[24:36])
						tmp_tuple = (0, 0, 0)
						final_tuple = datetime + tmp_tuple
						self.meta_profile_image.append(time.strftime('%Y/%m/%d %H:%M:%S', final_tuple))

				try:
					latitude = metadata.__getitem__("Exif.GPSInfo.GPSLatitude")
					latitudeRef = metadata.__getitem__("Exif.GPSInfo.GPSLatitudeRef")
					longitude = metadata.__getitem__("Exif.GPSInfo.GPSLongitude")
					longitudeRef = metadata.__getitem__("Exif.GPSInfo.GPSLongitudeRef")

					latitude = str(latitude).split("=")[1][1:-1].split(" ");
					latitude = map(lambda f: str(float(Fraction(f))), latitude)
					latitude = latitude[0] + u"\u00b0" + latitude[1] + "'" + latitude[2] + '"' + " " + str(latitudeRef).split("=")[1][1:-1]

					longitude = str(longitude).split("=")[1][1:-1].split(" ");
					longitude = map(lambda f: str(float(Fraction(f))), longitude)
					longitude = longitude[0] + u"\u00b0" + longitude[1] + "'" + longitude[2] + '"' + " " + str(longitudeRef).split("=")[1][1:-1]

					latitude_value = dms_to_decimal(*metadata.__getitem__("Exif.GPSInfo.GPSLatitude").value + [metadata.__getitem__("Exif.GPSInfo.GPSLatitudeRef").value]);
					longitude_value = dms_to_decimal(*metadata.__getitem__("Exif.GPSInfo.GPSLongitude").value + [metadata.__getitem__("Exif.GPSInfo.GPSLongitudeRef").value]);

				except Exception as e:
					pass

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)


# ==========================================================================
class Parameters:
	"""Global program parameters"""
	# ----------------------------------------------------------------------
	def __init__(self, **kwargs):
		try:

			self.program_name ="Tinfoleak"
			self.program_version = "v2.3"
			self.program_date = "01/27/2018"
			self.program_author_name = "Vicente Aguilera Diaz"
			self.program_author_twitter = "@VAguileraDiaz"
			self.program_author_companyname = "Internet Security Auditors"
			self.html_output_directory = "Output_Reports"

		except Exception as e:
			show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def is_valid(tweet):
	"""Verify if a tweet meets all requirements"""
	try:

		valid = 1
		retweeted = 0
		media = 0

		# Identify RT and media content
		if hasattr(tweet, 'retweeted_status'):
			retweeted = 1
			if tweet.retweeted_status.entities.has_key('media'):
				media = 1

		else:
			retweeted = 0
			if tweet.entities.has_key('media'):
				media = 1

		# Verify "Start date" and "End date" filter
		date = str(tweet.created_at.strftime('%Y-%m-%d'))
		if date < str(ui.tb_sdate.text()) or date > str(ui.tb_edate.text()):
			valid = 0

		# Verify "Start time" and "End time" filter
		if valid:
			time = str(tweet.created_at.strftime('%H:%M:%S'))
			if time < str(ui.tb_stime.text()) or time > str(ui.tb_etime.text()):
				valid = 0

		if valid:
			# Verify "Retweet" filter
			if retweeted and ui.rb_RT_no.isChecked():
				valid = 0
			if not retweeted and ui.rb_RT_yes.isChecked():
				valid = 0

		if valid:
			# Verify "Multimedia" filter
			if media and ui.rb_media_no.isChecked():
				valid = 0
			if not media and ui.rb_media_yes.isChecked():
				valid = 0

		if valid and len(ui.tb_source_app.text())>0:
			# Verify "Source application" filter
			source_app = str(ui.tb_source_app.text()).lower()
			if (source_app in tweet.source.lower()) and ui.rb_sourceapp_no.isChecked():
				valid = 0
			if (source_app not in tweet.source.lower()) and ui.rb_sourceapp_yes.isChecked():
				valid = 0

		if valid and ui.tb_include_words.text():
			# Verify "Include words" filter
			with_words = str(ui.tb_include_words.text()).lower().split()
			for word in with_words:
				if word not in tweet.text.lower():
					valid = 0
					break

		if valid and ui.tb_not_include_words.text():
			# Verify "Don't include words" filter
			without_words = str(ui.tb_not_include_words.text()).lower().split()
			for word in without_words:
				if word in tweet.text.lower():
					valid = 0
					break

		return valid

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def get_video_url(url):
	"""Get video URL from a tweet media URL"""
	try:

		video_url = ""
		response = urllib2.urlopen(str(url))
		html = response.read()
		if html.find(".mp4") >= 0:
			begin = html.index('video-src="')
			end = html.index('.mp4"')
			video_url = html[begin+11:end+4]

		return video_url

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def getKey(item):
	return item[9]

# ----------------------------------------------------------------------
def generates_HTML_file(parameters, user, source, social, hashtag, mention, geolocation, user_images, user_tweets, search, user_conversations, favorites, top_words, activity, user_relations):
	"""Generates a HTML output file"""
	try:

		tinfoleak_dir = os.path.dirname(os.path.abspath(__file__))
		jinja2_env = Environment(loader=FileSystemLoader(tinfoleak_dir), autoescape=True, trim_blocks=True)

		desc = user.description
		if user.expanded_description:
			desc = user.expanded_description

		url = user.url
		if user.expanded_url and len(user.expanded_url) < 50:
			url = user.expanded_url

		all_conv = {}
		conversations_number = 0
		conversations_users = {}
		conversations_messages = {}

		for tid, conv in user_conversations.conversations.items():
			# Order conversations by datetime
			tmp = sorted(conv, key=getKey)
			user_conversations.conversations[tid] = tmp

			# Remove duplicates
			tmplist = []
			res = []
			index = 0
			for n in tmp:
				if n[0] not in tmplist:
					tmplist.append(n[0])
					res.append(n)
				index += 1

			user_conversations.conversations[tid] = res

			# Make some updates
			index = 0
			for n in res:
				if res[index][11]:
					# In reply ID
					res[index][10] = "replied"
				else:
					# First tweet of this conversation
					res[index][10] = "tweeted"

				if index > 0:
					size = len(res)
					while size >= 0:
						if n[11] == res[size-1][0]:
							# If tweet.in_reply_to_status_id == tweet.id => change chat position
							if res[size-1][8] == "left":
								res[index][8] = "right"
							else:
								res[index][8] = "left"

						size -= 1

				else:
					res[index][8] = "left"
				index += 1

			user_conversations.conversations[tid] = res

			try:
				for r in res:
					all_conv[res[0][0]].append(r)
			except Exception as e:
				all_conv[res[0][0]] = res

		user_conversations.conversations = all_conv

		for tid, conv in user_conversations.conversations.items():
			conversations_number += 1

			# Order conversations by datetime
			tmp = sorted(conv, key=getKey)
			user_conversations.conversations[tid] = tmp

			# Remove duplicates
			tmplist = []
			res = []
			index = 0
			users = []
			for n in tmp:

				if n[0] not in tmplist:
					tmplist.append(n[0])
					res.append(n)

				value = [n[4], n[7]]
				if value not in users:
					users.append(value)

				index += 1

			conversations_users[tid] = users
			conversations_messages[tid] = len(conv)
			user_conversations.conversations[tid] = res

		template_values = {
			'program': parameters.program_name,
			'version': parameters.program_version,
			'author_name': parameters.program_author_name,
			'author_twitter': parameters.program_author_twitter,
			'author_company': parameters.program_author_companyname,
			'profile_image': user.profile_image_url.replace("_normal.", "."),
			'screen_name': user.screen_name,
			'user_name': user.name,
			'twitter_id': user.id,
			'date': user.created_at.strftime('%m/%d/%Y'),
			'followers': '{:,}'.format(user.followers_count),
			'friends': '{:,}'.format(user.friends_count),
			'geo': user.geo_enabled,
			'tweets': '{:,}'.format(user.statuses_count),
			'location': user.location,
			'timezone': user.time_zone,
			'description': desc,
			'protected': user.protected,
			'url': url,
			'tweets_average': user.tweets_average,
			'likes_average': user.likes_average,
			'favourites_count': user.favourites_count,
			'verified': user.verified,
			'listed_count': user.listed_count,
			'lang': user.lang,
			'user_color': "DDDDDD",
			'argv': str(sys.argv),
			'os_name': os.name,
			'os_platform': sys.platform,

			# source
			'output_source': (ui.cb_source_apps.isChecked() and ui.cb_source_apps.isEnabled()),
			'source': source.sources,
			'sources_count': source.sources_count,
			'sources_percent': source.sources_percent,
			'sources_firstdate': source.sources_firstdate,
			'sources_lastdate': source.sources_lastdate,
			'sources_results': len(source.sources),
			'sources_firsttweet': source.sources_firsttweet,
			'sources_lasttweet': source.sources_lasttweet,

			# social networks
			'output_social': (ui.cb_social_networks.isChecked() and ui.cb_social_networks.isEnabled()),
			'social_tweet': social.user_sn,
			'social_results': len(social.user_sn),

			# hashtag
			'output_hashtag': (ui.cb_hashtags.isChecked() and ui.cb_hashtags.isEnabled()),
			'hashtags_tweet': hashtag.hashtags_tweet,
			'hashtags_results1': hashtag.hashtags_results1,
			'hashtags_results2': hashtag.hashtags_results2,
			'hashtags_results3': hashtag.hashtags_results3,
			'hashtags_firstdate': hashtag.hashtags_firstdate,
			'hashtags_lastdate': hashtag.hashtags_lastdate,
			'hashtag': hashtag.hashtags,
			'hashtags_rt': hashtag.hashtags_rt,
			'hashtags_fv': hashtag.hashtags_fv,
			'hashtags_count': hashtag.hashtags_count,
			'hashtags_top': hashtag.hashtags_top,
			'hashtags_owner': hashtag.hashtags_owner,
			'hashtags_users': hashtag.hashtags_users,

			# mention
			'output_mention': (ui.cb_mentions.isChecked() and ui.cb_mentions.isEnabled()),
			'mentions_tweet': mention.mentions_tweet,
			'mentions_results1': len(mention.mentions_tweet),
			'mentions_results2': len(mention.mentions_count),
			'mentions_results3': mention.mentions_results3,
			'mentions_firstdate': mention.mentions_firstdate,
			'mentions_lastdate': mention.mentions_lastdate,
			'mentions_name': mention.mentions_name,
			'mention': mention.mentions,
			'mentions_rt': mention.mentions_rt,
			'mentions_fv': mention.mentions_fv,
			'mentions_count': mention.mentions_count,
			'mentions_top': mention.mentions_top,
			'mentions_users': mention.mentions_users,
			'mentions_profileimg': mention.mentions_profileimg,

			# find text
			'output_tweet': (ui.cb_show_tweets.isChecked() and ui.cb_show_tweets.isEnabled()),
			'find': "",
			'tweet_find': user_tweets.tweets_find,
			'find_count': len(user_tweets.tweets_find),

			# media
			'output_media': (ui.cb_media.isChecked() and ui.cb_media.isEnabled()),
			'media': user_images.pic,
			'media_directory': user_images.pics_directory,
			'media_count': len(user_images.pic),

			#meta
			'output_metadata': (ui.cb_metadata.isChecked() and ui.cb_metadata.isEnabled()),
			'meta_size': user_images.meta_size,
			'meta_description': user_images.meta_description,
			'meta_copyright': user_images.meta_copyright,
			'meta_date': user_images.meta_date,
			'meta_make': user_images.meta_make,
			'meta_model': user_images.meta_model,
			'meta_software': user_images.meta_software,
			'meta_distance': user_images.meta_distance,
			'meta_platform': user_images.meta_platform,
			'meta_iccdate': user_images.meta_iccdate,
			'meta_coordinates': user_images.meta_coordinates,
			'meta_thumb': user_images.meta_thumb,
			'meta_profile_image': user_images.meta_profile_image,
			'meta_profile_banner': user_images.meta_profile_banner,
			'meta_profile_image_url': user_images.profile_image_url,
			'meta_profile_banner_url': user_images.profile_banner_url,

			# geolocation
			'output_geolocation': (ui.cb_visited_locations.isChecked() and ui.cb_visited_locations.isEnabled()),
			'geo_info': geolocation.geo_info,
			'geo_count': len(geolocation.geo_info),
			'geo_media': geolocation.media_info,
			'geo_info_count': len(geolocation.geo_info),
			'geo_visited_locations': geolocation.visited_locations,
			'geo_visited_locations_count': len(geolocation.visited_locations),
			'geo_toplocations_tweets': geolocation.toplocations_tweets,
			'geo_toplocations': geolocation.toploc,
			'geo_toplocations_count': len(geolocation.toploc),
			'geo_toplocationsdaysmo': geolocation.toplocationsdaysmo,
			'geo_toplocationsdaystu': geolocation.toplocationsdaystu,
			'geo_toplocationsdayswe': geolocation.toplocationsdayswe,
			'geo_toplocationsdaysth': geolocation.toplocationsdaysth,
			'geo_toplocationsdaysfr': geolocation.toplocationsdaysfr,
			'geo_toplocationsdayssa': geolocation.toplocationsdayssa,
			'geo_toplocationsdayssu': geolocation.toplocationsdayssu,

			# advanced search
			'output_search': ui.rb_place.isChecked(),
			'output_search_nocoord': ui.rb_global_timeline.isChecked(),
			'adv_geo_info': search.adv_geo_info,
			'adv_geo_count': len(search.adv_geo_info),
			'adv_geo_media': search.adv_media_info,
			'adv_media_count': search.adv_media_count,
			'user_sn': search.user_sn,
			'user_sn_count': len(search.user_sn),
			'user_taggeds': search.user_taggeds,
			'user_taggeds_count': len(search.user_taggeds),
			'user_keywords': search.user_keywords,

			# conversations
			'output_conversation': (ui.cb_conversations.isChecked() and ui.cb_conversations.isEnabled()),
			'conversations': user_conversations.conversations.items(),
			'conversations_number': conversations_number,
			'conversations_users': conversations_users,
			'conversations_messages': conversations_messages,

			# favorites
			'output_favorites': (ui.cb_likes.isChecked() and ui.cb_likes.isEnabled()),
			'favourites_tweets': favorites.favorites_tweets,
			'fav_count': len(favorites.favorites_tweets),

			# top words
			'output_words': (ui.cb_words_frequency.isChecked() and ui.cb_words_frequency.isEnabled()),
			'top_words': top_words.ordered_words,
			'top_dates': top_words.top_dates,
			'total_occurrences': top_words.total_occurrences,
			'words_count': len(top_words.ordered_words),

			# activity
			'output_activity': (ui.cb_activity.isChecked() and ui.cb_activity.isEnabled()),
			'activity_count': activity.activity_count,
			'activity_tweet': activity.activity_tweet,
			'activity_tweet_retweets': activity.activity_tweet_retweets,
			'activity_tweet_likes': activity.activity_tweet_likes,
			'activity_retweet': activity.activity_retweet,
			'activity_reply': activity.activity_reply,
			'activity_url': activity.activity_url,
			'activity_media': activity.activity_media,
			'activity_hours': activity.activity_hours,
			'activity_tweet_percent': activity.activity_tweet_percent,
			'activity_retweet_percent': activity.activity_retweet_percent,
			'activity_url_percent': activity.activity_url_percent,
			'activity_media_percent': activity.activity_media_percent,
			'activity_expanded_url': activity.activity_expanded_url,
			'activity_expanded_url_count': len(activity.activity_expanded_url),

			# protected account
			'output_protected': (ui.cb_protected_account.isChecked() and ui.cb_protected_account.isEnabled()),
			'followedby_users': user_relations.followedby_users,
			'followedby_count': len(user_relations.followedby_users),
			'following_users': user_relations.following_users,
			'following_count': len(user_relations.following_users),
			'protected_tweets': user_relations.protected_tweets,
			'protected_tweets_count': len(user_relations.protected_tweets)

		}

		html_content = jinja2_env.get_template('ReportTemplate/tinfoleak-theme.html').render(template_values)

		if not os.path.exists(parameters.html_output_directory) :
			os.makedirs(parameters.html_output_directory)

		output_report_filename = parameters.html_output_directory + "/" + str(ui.tb_report_filename.text())
		if os.path.exists(output_report_filename):
			os.remove(output_report_filename)
		f = open(output_report_filename, "w")
		f.write(html_content.encode('utf-8'))
		f.close()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def save_image(url, username):
	try:

		if not os.path.isdir(username):
			os.mkdir(username)

		img = urllib2.urlopen(url).read()
		filename = url.split('/')[-1]
		pics_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + username
		image = pics_directory + "/" +filename
		if not os.path.exists(username+"/"+filename):
			f = open(username+"/"+filename, 'wb')
			f.write(img)
			f.close()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def get_information_for_user_target():
	try:

		source = Sources()
		hashtag = Hashtags()
		mentions = Mentions()
		user_images = User_Images()
		geolocation = Geolocation()
		user = User()
		search = Search_GeoTweets()
		user_tweets = User_Tweets()
		user_conversations = User_Conversations()
		user_relations = User_Relations()
		social_networks = Social_Networks()
		followers = Followers()
		friends = Friends()
		lists = Lists()
		collections = Collections()
		favorites = Favorites()
		top_words = Words_Tweets()
		activity = Activity()

		#  Get information about a USER
		username = str(ui.tb_username.text())
		tweets_number = int(ui.tb_tweets_number.text())
		show_ui_message("Looking info for <b>@" + username + "</b>:", "INFO", 1)
		show_ui_message("Getting account information...", "INFO", 1)
		userapi = api.get_user(username)
		user.set_user_information(userapi)

		user_conversations.conversations = {}
		user_images.pic = []
		#: [username, link, picture, name, info]
		social_networks.user_sn = {}

		social_networks.user_sn[username] = \
			[["", "", "", "", ""], # Instagram
			 ["", "", "", "", ""], # Foursquare
			 ["", "", "", "", ""], # Facebook
			 ["", "", "", "", ""], # LinkedIn
			 ["", "", "", "", ""], # Runkeeper
			 ["", "", "", "", ""], # Flickr
			 ["", "", "", "", ""], # Vine
			 ["", "", "", "", ""], # Periscope
			 ["", "", "", "", ""], # Kindle
			 ["", "", "", "", ""], # Youtube
			 ["", "", "", "", ""], # Google+
			 ["", "", "", "", ""]] # Frontback

		img_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + user.screen_name
		if not os.path.isdir(img_directory):
			os.mkdir(img_directory)
		try:
			img = urllib2.urlopen(user.profile_image_url.replace("_normal.", ".")).read()
		except:
			img = urllib2.urlopen(user.profile_image_url.replace(".jpg", "_400x400.jpg")).read()
		filename = str(user.id) + ".jpg"
		imgFile = img_directory + "/" + filename
		if not os.path.exists(imgFile):
			f = open(imgFile, 'wb')
			f.write(img)
			f.close()

		datenow, timenow = show_ui_message("<img src=" + imgFile + " height=60 align=middle>", "INFO", 1)
		show_ui_message("Account information: OK", "INFO", 1)
		show_ui_message("Executing operations...", "INFO", 1)

		# Latest targets analyzed
		try:
			pixmap = QtGui.QPixmap(imgFile)
			icon_button_profile_image = QtGui.QToolButton(parent=window)
			icon_button_profile_image.setIcon(QtGui.QIcon(pixmap))
			icon_button_profile_image.setIconSize(QtCore.QSize(60, 60))
			icon_button_profile_image.setAutoRaise(True)

			ui.tbl_targets_analyzed.insertRow(0)
			ui.tbl_targets_analyzed.setItem(0, 0, QtGui.QTableWidgetItem(datenow + " " + timenow))
			ui.tbl_targets_analyzed.setCellWidget(0, 1, icon_button_profile_image)
			ui.tbl_targets_analyzed.setItem(0, 2, QtGui.QTableWidgetItem("@" + user.screen_name))
			ui.tbl_targets_analyzed.setItem(0, 3, QtGui.QTableWidgetItem(user.name.decode('utf-8')))
			ui.tbl_targets_analyzed.resizeColumnsToContents()
			ui.tbl_targets_analyzed.setRowHeight(0, 60)

		except Exception as e:
			show_ui_message(str(e), "INFO", 1)

		results = 0
		# if the user select some operation
		if ui.cb_source_apps.isChecked() or ui.cb_activity.isChecked() or ui.cb_hashtags.isChecked() or ui.cb_mentions.isChecked() or ui.cb_words_frequency.isChecked() or ui.cb_social_networks.isChecked() or ui.cb_visited_locations.isChecked() or ui.cb_metadata.isChecked() or ui.cb_media.isChecked() or ui.cb_conversations.isChecked() or ui.cb_show_tweets.isChecked():
			page = 1
			tweets_count = 0
			tmp_count = 0
			while True:
				timeline = api.user_timeline(screen_name=username, include_rts=True, count=10, page=page)
				if timeline:
					for tweet in timeline:
						tweets_count += 1
						tmp_count += 1
						if tweets_count == 1 or tmp_count == 10 or tweets_count == tweets_number:
							cursor = ui.tb_messages.textCursor()
							cursor.movePosition(QtGui.QTextCursor.StartOfLine, 0)
							cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
							cursor.removeSelectedText()
							br = 0
							if tweets_count == tweets_number:
								br = 1
							show_ui_message("Processing tweet " + str(tweets_count) + "/" + str(ui.tb_tweets_number.text()), "INFO", br)
						if tmp_count == 10:
							tmp_count = 0
						app.processEvents()
						if is_valid(tweet):
							results = 1
							if ui.cb_source_apps.isChecked():
								# Get information about the sources applications used to publish tweets
								source.set_sources_information(tweet)

							if ui.cb_activity.isChecked():
								# Get statistics
								activity.set_activity(tweet)

							if ui.cb_hashtags.isChecked():
								# Get hashtags included in tweets
								hashtag.set_hashtags_information(tweet, "*")

							if ui.cb_mentions.isChecked():
								# Get mentionsincluded in tweets
								mentions.set_mentions_information(tweet, "*")

							if ui.cb_words_frequency.isChecked():
								# Get words most used
								top_words.set_words_information(tweet)

							if ui.cb_social_networks.isChecked():
								# Identify social networks identities
								social_networks.set_social_networks(tweet)

							if ui.cb_visited_locations.isChecked():
								# Get geolocation information from user tweets
								geolocation.set_geolocation_information(tweet)
								if ui.tb_kml_filename.text():
									geolocation.set_geofile_information(tweet, user)

							if ui.cb_metadata.isChecked():
								# Get metadata information from user images
								user_images.set_metadata_information(tweet)

							if ui.cb_media.isChecked():
								# Get images included in tweets
								if not ui.cb_metadata.isChecked():
									user_images.set_metadata_information(tweet)
								user_images.username = username
								user_images.set_images_information(tweet)

							if ui.cb_conversations.isChecked():
								# Get conversations between two users
								user_conversations.set_tweets_conversations(tweet)

							if ui.cb_show_tweets.isChecked():
								user_tweets.set_find_information(tweet)

						if tweets_count >= tweets_number:
							break

				else:
					break
				page += 1
				if tweets_count >= tweets_number:
					break

		parameters = Parameters()

		if results:

			if ui.cb_hashtags.isChecked():
				hashtag.set_global_information()

			if ui.cb_mentions.isChecked():
				mentions.set_global_information()

			if ui.cb_activity.isChecked():
				# Get info about the user activity
				show_ui_message("Getting user activity...", "INFO", br=1)
				activity.set_global_information()
				show_ui_message("User activity: OK", "INFO", br=1)

			if ui.cb_source_apps.isChecked():
				# Get info about the source apps
				show_ui_message("Getting source apps...", "INFO", br=1)
				source.set_global_information()
				show_ui_message("Source apps: OK", "INFO", br=1)

			if ui.cb_lists.isChecked():
				# Get info about the lists the user has been added to
				show_ui_message("Getting lists...", "INFO", br = 1)
				lists.get_memberships(client, int(user.listed_count), username)
				lists.get_ownerships(client, username)
				lists.get_lists(client, username)
				show_ui_message("Lists: OK", "INFO", br=1)

			if ui.cb_collections.isChecked():
				# Get info about the collections created by the user
				show_ui_message("Getting collections...", "INFO", br=1)
				collections.get_collections(client, username)
				show_ui_message("Collections: OK", "INFO", br=1)

			if ui.cb_followers.isChecked():
				# Get followers for the user
				if not ui.tb_followers_number.text():
					show_alert_field(field = ui.tb_followers_number, message = "You need to specify a followers number", type = "WARNING", br = 1)
				else:
					show_ui_message("Getting followers...", "INFO", br=1)
					followers.get_followers(username, api, int(ui.tb_followers_number.text()))
					show_ui_message("Followers: OK", "INFO", br=1)

			if ui.cb_friends.isChecked():
				# Get friends for the user
				if not ui.tb_friends_number.text():
					show_alert_field(field = ui.tb_friends_number, message = "You need to specify a friends number", type = "WARNING", br = 1)
				else:
					show_ui_message("Getting friends...", "INFO", br=1)
					friends.get_friends(username, api, int(ui.tb_friends_number.text()))
					show_ui_message("Friends: OK", "INFO", br=1)

			if ui.cb_words_frequency.isChecked():
				# Get words most used
				if not ui.tb_words_frequency_number.text():
					show_alert_field(field=ui.tb_words_frequency_number, message="You need to specify a words number", type="WARNING", br=1)
				else:
					show_ui_message("Getting words...", "INFO", br=1)
					wordlist = sorted(top_words.top_words.items(), key=operator.itemgetter(1))
					wordlist.reverse()
					max = int(ui.tb_words_frequency_number.text())
					if max > len(wordlist) - 1:
						max = len(wordlist) - 1
					top_words.ordered_words = wordlist[0:max]
					for n in top_words.ordered_words:
						top_words.total_occurrences += n[1]
					show_ui_message("Words: OK", "INFO", br=1)

			if ui.cb_visited_locations.isChecked():
				# Generates file with geolocation information from user tweets
				if ui.tb_kml_filename.text():
					show_ui_message("Generating KML file...", "INFO", br=1)
					geolocation.generates_geofile(ui.tb_kml_filename.text(), parameters)
					show_ui_message("KML file: OK", "INFO", br=1)

				# Get global information about geolocation in tweets
				if not ui.tb_top_locations.text():
					show_alert_field(field=ui.tb_top_locations, message="You need to specify a locations number", type="WARNING", br=1)
				else:
					show_ui_message("Getting most visited locations...", "INFO", br=1)
					geolocation.set_global_information(int(ui.tb_top_locations.text()))
					show_ui_message("Most visited locations: OK", "INFO", br=1)

			if ui.cb_protected_account.isChecked():
				# Get information about protected accounts
				show_ui_message("Getting info from protected account...", "INFO", br=1)
				user_relations.set_relations(username)
				show_ui_message("Info from protected account: OK", "INFO", br=1)

			if ui.cb_metadata.isChecked():
				user_images.profile_image_url = user.profile_image_url
				user_images.profile_banner_url = user.profile_banner_url
				user_images.screen_name = username

				tmp_profile_image_url = user.profile_image_url
				if user.profile_image_url.find("_normal") < 0:
					tmp_profile_image_url = user.profile_image_url.replace(".jpg", "_400x400.jpg")
				else:
					tmp_profile_image_url = user.profile_image_url.replace("_normal.", ".")

				user_images.get_metadata(tmp_profile_image_url, 1, username)

		if ui.cb_likes.isChecked():
			# Get favorites tweets
			if user.favourites_count:
				if not ui.tb_likes_number.text():
					show_alert_field(field=ui.tb_likes_number, message="You need to specify a likes number", type="WARNING", br=1)
				else:
					show_ui_message("Getting likes...", "INFO", br=1)
					favorites.set_favorites_information(api, username, int(ui.tb_likes_number.text()))
					show_ui_message("Likes: OK", "INFO", br=1)
			else:
				show_ui_message("The user has not marked favorite tweets", "INFO", br=1)

		# All operations finished
		show_ui_message("Operations: OK", "INFO", 1)
		show_ui_message("Generating report...", "INFO", 1)

		# Generates HTML file
		generates_HTML_file(parameters, user, source, social_networks, hashtag, mentions, geolocation, user_images, user_tweets, search, user_conversations, favorites, top_words, activity, user_relations)

		strPath = os.path.dirname(os.path.abspath(__file__))
		strDir = parameters.html_output_directory
		strFile = str(ui.tb_report_filename.text())

		html_dir = strPath + "/" + strDir + "/" + strFile

		show_ui_message("Report: OK", "INFO", 1)
		show_ui_message("Your HTML report: <b>" + html_dir + "</b><br>", "INFO", 1)

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)


# ----------------------------------------------------------------------
def get_information_for_place():
	"""Search info about a PLACE"""
	try:

		source = Sources()
		hashtag = Hashtags()
		mentions = Mentions()
		user_images = User_Images()
		geolocation = Geolocation()
		user = User()
		search = Search_GeoTweets()
		user_tweets = User_Tweets()
		user_conversations = User_Conversations()
		user_relations = User_Relations()
		social_networks = Social_Networks()
		followers = Followers()
		friends = Friends()
		lists = Lists()
		collections = Collections()
		favorites = Favorites()
		top_words = Words_Tweets()
		activity = Activity()
		coordinates = ui.tb_place_lat.text() + "," + ui.tb_place_lon.text() + "," + ui.tb_place_km.text() + "km"

		show_ui_message("Looking info for <b>" + coordinates + "</b>:", "INFO", 1)
		show_ui_message("Getting place information...", "INFO", 1)

		tmp_api = api.get_user("vaguileradiaz")
		user.set_user_information(tmp_api)

		results = search.set_geolocation_information(coordinates, hashtag, mentions, social_networks, user_images, user_tweets, source, activity, top_words)

		show_ui_message("Place information: OK", "INFO", 1)

		if results:
			if ui.cb_hashtags.isChecked():
				hashtag.set_global_information()

			if ui.cb_mentions.isChecked():
				mentions.set_global_information()

			if ui.cb_source_apps.isChecked():
				# Get info about the source apps
				show_ui_message("Getting source apps...", "INFO", br=1)
				source.set_global_information()
				show_ui_message("Source apps: OK", "INFO", br=1)

			if ui.cb_activity.isChecked():
				# Get info about the user activity
				show_ui_message("Getting user activity...", "INFO", br=1)
				activity.set_global_information()
				show_ui_message("User activity: OK", "INFO", br=1)

			if ui.cb_words_frequency.isChecked():
				# Get words most used
				if not ui.tb_words_frequency_number.text():
					show_alert_field(field=ui.tb_words_frequency_number, message="You need to specify a words number",
									 type="WARNING", br=1)
				else:
					show_ui_message("Getting words...", "INFO", br=1)
					wordlist = sorted(top_words.top_words.items(), key=operator.itemgetter(1))
					wordlist.reverse()
					max = int(ui.tb_words_frequency_number.text())
					if max > len(wordlist) - 1:
						max = len(wordlist) - 1
					top_words.ordered_words = wordlist[0:max]
					for n in top_words.ordered_words:
						top_words.total_occurrences += n[1]
					show_ui_message("Words: OK", "INFO", br=1)

		parameters = Parameters()
		show_ui_message("Generating report...", "INFO", 1)

		# Generates HTML file
		generates_HTML_file(parameters, user, source, social_networks, hashtag, mentions, geolocation, user_images, user_tweets, search, user_conversations, favorites, top_words, activity, user_relations)

		strPath = os.path.dirname(os.path.abspath(__file__))
		strDir = parameters.html_output_directory
		strFile = str(ui.tb_report_filename.text())

		html_dir = strPath + "/" + strDir + "/" + strFile

		show_ui_message("Report: OK", "INFO", 1)
		show_ui_message("Your HTML report: <b>" + html_dir + "</b><br>", "INFO", 1)

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)


# ----------------------------------------------------------------------
def get_information_for_timeline():
	"""Search info about the global timeline"""
	try:

		source = Sources()
		hashtag = Hashtags()
		mentions = Mentions()
		user_images = User_Images()
		geolocation = Geolocation()
		user = User()
		search = Search_GeoTweets()
		user_tweets = User_Tweets()
		user_conversations = User_Conversations()
		user_relations = User_Relations()
		social_networks = Social_Networks()
		followers = Followers()
		friends = Friends()
		lists = Lists()
		collections = Collections()
		favorites = Favorites()
		top_words = Words_Tweets()
		activity = Activity()

		coordinates = ui.tb_place_lat.text() + "," + ui.tb_place_lon.text() + "," + ui.tb_place_km.text() + "km"
		show_ui_message("Looking info at <b>global timeline</b>:", "INFO", 1)
		show_ui_message("Getting timeline information...", "INFO", 1)

		tmp_api = api.get_user("vaguileradiaz")
		user.set_user_information(tmp_api)

		results = search.set_search_information(hashtag, mentions, user_images, user_tweets, source, activity, top_words)

		show_ui_message("Timeline information: OK", "INFO", 1)

		if results:
			if ui.cb_hashtags.isChecked():
				hashtag.set_global_information()

			if ui.cb_mentions.isChecked():
				mentions.set_global_information()

			if ui.cb_source_apps.isChecked():
				# Get info about the source apps
				show_ui_message("Getting source apps...", "INFO", br=1)
				source.set_global_information()
				show_ui_message("Source apps: OK", "INFO", br=1)

			if ui.cb_activity.isChecked():
				# Get info about the user activity
				show_ui_message("Getting user activity...", "INFO", br=1)
				activity.set_global_information()
				show_ui_message("User activity: OK", "INFO", br=1)

			if ui.cb_words_frequency.isChecked():
				# Get words most used
				if not ui.tb_words_frequency_number.text():
					show_alert_field(field=ui.tb_words_frequency_number, message="You need to specify a words number",
									 type="WARNING", br=1)
				else:
					show_ui_message("Getting words...", "INFO", br=1)
					wordlist = sorted(top_words.top_words.items(), key=operator.itemgetter(1))
					wordlist.reverse()
					max = int(ui.tb_words_frequency_number.text())
					if max > len(wordlist) - 1:
						max = len(wordlist) - 1
					top_words.ordered_words = wordlist[0:max]
					for n in top_words.ordered_words:
						top_words.total_occurrences += n[1]
					show_ui_message("Words: OK", "INFO", br=1)

		parameters = Parameters()
		show_ui_message("Generating report...", "INFO", 1)

		# Generates HTML file
		generates_HTML_file(parameters, user, source, social_networks, hashtag, mentions, geolocation, user_images, user_tweets, search, user_conversations, favorites, top_words, activity, user_relations)

		strPath = os.path.dirname(os.path.abspath(__file__))
		strDir = parameters.html_output_directory
		strFile = str(ui.tb_report_filename.text())

		html_dir = strPath + "/" + strDir + "/" + strFile

		show_ui_message("Report: OK", "INFO", 1)
		show_ui_message("Your HTML report: <b>" + html_dir + "</b><br>", "INFO", 1)

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def get_information_from_interface():
    """Get information about a Twitter user"""
    try:

        if ui.rb_user.isChecked():
            # Target of Analysis: User
            if ui.tb_username.text() == "":
                show_alert_field(field = ui.tb_username, message = "You need to specify a username", type = "WARNING", br = 1)
            else:
                # Get information for a USER
                get_information_for_user_target()
        else:
            if ui.rb_place.isChecked():
                # Target of Analysis: Place
                if ui.tb_place_lat.text() == "":
                    show_alert_field(field=ui.tb_place_lat, message="You need to specify a latitude", type="WARNING", br=1)
                else:
                    if ui.tb_place_lon.text() == "":
                        show_alert_field(field=ui.tb_place_lon, message="You need to specify a longitude", type="WARNING", br=1)
                    else:
                        if ui.tb_place_km.text() == "":
                            show_alert_field(field=ui.tb_place_km, message="You need to specify a distance", type="WARNING", br=1)
                        else:
                            # Get information for a PLACE
                            get_information_for_place()
            else:
                if ui.rb_global_timeline.isChecked():
                    # Target of Analysis: Global timeline
					get_information_for_timeline()

    except Exception as e:
        show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def show_ui_message(message, type, br):
	""" Show message in user interface"""
	try:

		app.processEvents()
		datenow = datetime.datetime.now().strftime('%Y-%m-%d')
		timenow = datetime.datetime.now().strftime('%H:%M:%S')
		ui.tb_messages.insertHtml("[ " + datenow + " " + timenow + " ] ")

		color = "black"
		if type == "ERROR":
			color = "red"
		else:
			if type == "INFO":
				color = "blue"
			else:
				if type == "WARNING":
					color = "orange"

		ui.tb_messages.insertHtml("<font color=" + color + ">" + type + "</font> : ")
		ui.tb_messages.insertHtml(message)
		if br:
			ui.tb_messages.insertHtml("<br>")
		sb = ui.tb_messages.verticalScrollBar()
		sb.setValue(sb.maximum())
		app.processEvents()

		return datenow, timenow

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def show_alert_field(field, message, type, br):
	""" Show alert in form field """
	try:

		field.setStyleSheet("background-color: rgb(0, 0, 255);")
		show_ui_message(message, type, br)
		time.sleep(0.05)
		field.setStyleSheet("background-color: rgb(255, 255, 255);")
		field.setFocus()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def show_error(error):
	""" Show error message """
	try:

		rate_limit = 0
		print "\n\n\t\tOops! Something went wrong:"

		if str(error).find("Name or service not known") >= 0:
			print "\t\tDo you have Internet connection?"
		else:
			if str(error).find("Could not authenticate you") >= 0:
				print "\t\tYou need to assign value to OAuth tokens. Please, read the README.txt file for more information."
			else:
				print "\t\t" + str(sys.exc_info()[1][0][0]['message'])
				if "Rate limit exceeded" in str(sys.exc_info()[1][0][0]['message']):
					rate_limit = 1
		print

		return rate_limit

	except Exception as e:
		print "\t\t" + str(error) + "\n"
		sys.exit(1)

# ----------------------------------------------------------------------
def get_url_media_from_instagram(html):
	""" Return a URL with the instagram photo or video """
	try:

		url_instagram = ""
		urls = re.search('og:video:secure_url" content="(.*)"', html)
		if urls:
			url_instagram = urls.group(1)
		else:
			urls = re.search('og:image" content="(.*)"', html)
			if urls:
				url_instagram = urls.group(1)

		return url_instagram

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_tagged_users_from_instagram(html):
	""" Return the tagged users in the instagram image """
	try:

		tagged_users = []
		owner = ""
		profile_image = ""

		urls = re.findall('{"user":{"username":"[^}]*"},"x":', html)

		for users in urls:
			user = users[23:len(users)-8]
			tagged_users.append(user)

		urls = re.search('"viewer_has_saved_to_collection":(.*)"profile_pic_url":"(.*)","username":"(.*)","blocked_by_viewer"', html)
		if urls:
			owner = urls.group(3)
			profile_image = urls.group(2)

		return tagged_users, owner, profile_image

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_hashtags_from_instagram(html):
	""" Return the hashtags in the instagram message """
	try:

		hashtags = []

		hash = re.findall('<meta content="(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+" property="instapp:hashtags"', html)
		for h in hash:
			hashtags.append(h[15:len(h)-29] .lower())

		return hashtags

	except Exception as e:
		pass


# ----------------------------------------------------------------------
def get_url_media_from_foursquare(url):
	""" Return a URL with the foursquare photo or video """
	try:

		url_foursquare = ""
		owner = ""
		profile_image = ""

		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			return url_foursquare, owner, profile_image

		urls = re.search('<div id="mapContainer"><img src="(.*)" alt="(.*)" class="avatar mainUser"', html)
		if urls:
			profile_image = urls.group(1)

		urls = re.search('","canonicalUrl":"https:(.*),"venue":{"name":"', html)

		if urls:
			urls = re.search('foursquare.com(.*)/checkin', str(urls.group(1)))
			if urls:
				owner = urls.group(1)[2:len(urls.group(1))-1]
				urls = re.search('"canonicalPath":(.*)checkin', str(urls.group(1)))
				if urls:

					last_position = 0
					try:
						while True:
							last_position = urls.group(1).index('"', last_position+1)
					except ValueError:
						owner = urls.group(1)[last_position+3:len(urls.group(1))-2]

				url_foursquare = ""

		return url_foursquare, owner, profile_image

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_url_facebook_from_foursquare(url):
	""" Return a URL with the facebook url from a foursquare user """

	try:
		url_facebook = ""
		user_facebook = ""
		profile_image = ""

		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			return url_facebook, user_facebook, profile_image
		urls = re.search('<a href="http://www.facebook.com/(.*)" rel="nofollow" target="_blank" class="fbLink iconLink"', html)
		if urls:
			url_facebook = urls.group(1)

			url = "https://www.facebook.com/" + url_facebook

			request_headers = {
				'User-agent': 'Mozilla/5.0',
				'Cookie': 'c_user=100010863996105; xs=64%3AeKa4GH5PF-pZpw%3A2%3A1474823721',
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
				}

			try:
				request = urllib2.Request(url, headers=request_headers)
				html = urllib2.urlopen(request.read())
				urls = re.search('content="0; URL=/(.*)?_fb_noscript=1"', html)
				if urls:
					user_facebook = str(urls.group(1))
			except Exception as e:
				pass

		return url_facebook, user_facebook, profile_image

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_user_from_facebook_url(url):
	""" Return a URL with the facebook url from a foursquare user """
	try:

		user_facebook = ""
		html = ""
		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('autocomplete="off" name="next" value="https://www.facebook.com/(.*)/posts/[0-9]*"', html)
		if urls:
			if str(urls.group(1)).find("profile.php") < 0:
				user_facebook = urls.group(1)
		else:
			try:
				response = urllib2.urlopen("http://longurl.org/expand?url="+url)
				html = response.read()
				urls = re.search('<a href="https://www.facebook.com/(.*)/posts/[0-9]*">https://', html)
				if urls:
					user_facebook = urls.group(1)
			except Exception as e:
				pass

		return user_facebook

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_user_from_flickr_url(url):
	""" Return the username of a flickr user """
	try:

		user_flickr = ""
		html = ""
		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('"og:url" content="https://www.flickr.com/photos/(.*)/[0-9]*/"', html)
		if urls:
			user_flickr = urls.group(1)

		return user_flickr

	except Exception as e:
		pass


# ----------------------------------------------------------------------
def get_user_from_runkeeper_url(url):
	""" Return the username of a Runkeeper user """
	try:

		user_runkeeper = ""
		html = ""
		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('"https://runkeeper.com/user/(.*)/activity/', html)
		if urls:
			user_runkeeper = urls.group(1)

		return user_runkeeper

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_user_from_vine_url(url):
	""" Return the username of a Vine user """
	try:

		user = ""
		html = ""

		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('"name": "(.*)",', html)
		if urls:
			tmp = urls.group(1)
			id = re.search('"url": "https://vine.co/u/(.*)"', html)
			if id:
				user = id.group(1)
				user = id.group(1) + "/" + str(tmp)

		return user

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_user_from_periscope_url(url):
	""" Return the username of a Periscope user """
	try:

		user_periscope = ""
		html = ""
		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('pscp://user/(.*)&quot;,&quot;inAppUrl', html)
		if urls:
			user_periscope = urls.group(1)

		return user_periscope

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_user_from_kindle_url(url):
	""" Return the username of a Kindle user """
	try:

		user_kindle = ""
		html = ""
		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('customerId":"(.*)","howLongAgo', html)
		if urls:
			tmp = urls.group(1)
			try:
				url = "https://kindle.amazon.com/profile/redirect/" + tmp
				response = urllib2.urlopen(str(url))
				html = response.read()
			except Exception as e:
				pass

			urls = re.search('"/profile/(.*)"', html)
			if urls:
				user_kindle = urls.group(1)

		return user_kindle

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_user_from_youtube_url(url):
	""" Return the username of a Youtube user """
	try:

		user = ""
		html = ""

		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('/channel/(.*)" class', html)
		if urls:
			tmp = urls.group(1)
			try:
				url = "http://www.youtube.com/channel/" + tmp
				response = urllib2.urlopen(str(url))
				html = response.read()
			except Exception as e:
				pass

			urls = re.search('href="http://www.youtube.com/user/(.*)"', html)
			if urls:
				user = tmp + "/" + urls.group(1)
			else:
				urls = re.search('<meta property="og:title" content="(.*)">', html)
				if urls:
						user = tmp + "/" + urls.group(1)

		return user

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_user_from_googleplus_url(url):
	""" Return the username of a Google+ user """
	try:
		user =\
			""
		html = ""
		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('"https://plus.google.com/(.*)">', html)
		if urls:
			tmp = urls.group(1)
			try:
				url = "https://plus.google.com/" + tmp
				response = urllib2.urlopen(str(url))
				html = response.read()
			except Exception as e:
				pass

			urls = re.search('<meta itemprop="url" content="https://plus.google.com/(.*)"><link rel="alternate" href="android-app:', html)
			if urls:
					user = tmp + "/" + urls.group(1)

		return user

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_user_from_frontback_url(url):
	""" Return the username of a Frontback user """
	try:

		user = ""
		html = ""
		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			pass

		urls = re.search('post-info-username"><a class="no-ui" href="http://www.frontback.me/(.*)">(.*)</a></h1><h2 class="post-info-caption', html)
		if urls:
				user = urls.group(1)

		return user

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def get_url_media_from_youtube(url):
	""" Return a URL with the foursquare photo or video """
	try:

		url_youtube = ""

		try:
			response = urllib2.urlopen(str(url))
			html = response.read()
		except Exception as e:
			return url_youtube

		urls = re.findall('data-expanded-url="http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', html)

		if urls:
			url_youtube = urls[0][19:]

		return url_youtube

	except Exception as e:
		pass

# ----------------------------------------------------------------------
def selectUser(table, checkbox_column, screen_name_column):
	try:

		selection = 0
		rowCount = table.rowCount()
		rowPosition = 0
		while rowPosition < rowCount:
			if table.cellWidget(rowPosition, checkbox_column):
				if table.cellWidget(rowPosition, checkbox_column).findChild(type(QtGui.QCheckBox())).isChecked():
					ui.tb_username.setText(table.item(rowPosition, screen_name_column).text().replace("@",""))
					ui.tb_username.setFocus()
					selection = 1
					break
			rowPosition += 1
		return selection

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)


# ----------------------------------------------------------------------
def selectFile():
	try:

		tmp_user = User()

		# Clean previous results
		users_window_ui.tbl_users.setRowCount(0)

		# Select file
		filename = QtGui.QFileDialog.getOpenFileName()
		if filename:
			users_window_ui.lb_file.setText(filename)

			# Read file
			row = 0
			valid_users = 0
			invalid_users = 0

			if ui.tb_users_number.text() != "":
				users_limit = int(ui.tb_users_number.text())
			else:
				users_limit = 10

			with open(filename) as f:
				show_ui_message("Analyzing file: " + str(filename), "INFO", 1)
				for line in f.readlines():
					try:
						if row < users_limit:
							tmp_user = api.get_user(line.strip("\n"))
							rowPosition = users_window_ui.tbl_users.rowCount()
							users_window_ui.tbl_users.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
							users_window_ui.tbl_users.insertRow(rowPosition)

							img_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + tmp_user.screen_name
							if not os.path.isdir(img_directory):
								os.mkdir(img_directory)

							img = ""
							# Profile image
							if len(tmp_user.profile_image_url)>0:
								img = urllib2.urlopen(tmp_user.profile_image_url.replace("_normal.", ".")).read()
							else:
								img = urllib2.urlopen("https://abs.twimg.com/sticky/default_profile_images/default_profile_400x400.png")
							filename = str(tmp_user.id) + "-profile-image.jpg"
							imgFile = img_directory + "/" + filename
							if not os.path.exists(imgFile):
								fd = open(imgFile, 'wb')
								fd.write(img)
								fd.close()

							pixmap = QtGui.QPixmap(imgFile)
							icon_button_profile_image = QtGui.QToolButton(parent=w)
							icon_button_profile_image.setIcon(QtGui.QIcon(pixmap))
							icon_button_profile_image.setIconSize(QtCore.QSize(100,100))
							icon_button_profile_image.setAutoRaise(True)

							# Profile background image
							try:
								img = urllib2.urlopen(tmp_user.profile_banner_url.replace("_normal.", ".")).read()
							except Exception as e:
								if tmp_user.profile_background_image_url:
									img = urllib2.urlopen(tmp_user.profile_background_image_url.replace("_normal.", ".")).read()

							filename = str(tmp_user.id) + "-profile-banner-image.jpg"
							imgFile = img_directory + "/" + filename
							if not os.path.exists(imgFile):
								fd = open(imgFile, 'wb')
								fd.write(img)
								fd.close()

							pixmap = QtGui.QPixmap(imgFile)
							icon_button_profile_background_image = QtGui.QToolButton(parent=w)
							icon_button_profile_background_image.setIcon(QtGui.QIcon(pixmap))
							icon_button_profile_background_image.setIconSize(QtCore.QSize(300,100))
							icon_button_profile_background_image.setAutoRaise(True)

							checkbox = QtGui.QCheckBox()
							checkbox.setText("")

							cell_widget = QtGui.QWidget()
							layout_widget = QtGui.QHBoxLayout(cell_widget)
							layout_widget.addWidget(checkbox)
							layout_widget.setAlignment(QtCore.Qt.AlignCenter)
							layout_widget.setContentsMargins(0, 0, 0, 0)
							cell_widget.setLayout(layout_widget)

							users_window_ui.tbl_users.setCellWidget(row, 0, cell_widget)
							users_window_ui.tbl_users.setCellWidget(row, 1, icon_button_profile_image)
							users_window_ui.tbl_users.setCellWidget(row, 2, icon_button_profile_background_image)
							users_window_ui.tbl_users.setItem(row, 3, QtGui.QTableWidgetItem(str(tmp_user.created_at)))
							users_window_ui.tbl_users.setItem(row, 4, QtGui.QTableWidgetItem("@" + tmp_user.screen_name))
							users_window_ui.tbl_users.setItem(row, 5, QtGui.QTableWidgetItem(tmp_user.name.decode('utf-8')))
							users_window_ui.tbl_users.setItem(row, 6, QtGui.QTableWidgetItem(str(tmp_user.protected)))
							users_window_ui.tbl_users.setItem(row, 7, QtGui.QTableWidgetItem(str(tmp_user.description).decode('utf-8')))
							users_window_ui.tbl_users.setItem(row, 8, QtGui.QTableWidgetItem(str(tmp_user.followers_count)))
							users_window_ui.tbl_users.setItem(row, 9, QtGui.QTableWidgetItem(str(tmp_user.friends_count)))
							users_window_ui.tbl_users.resizeColumnsToContents()
							users_window_ui.tbl_users.setRowHeight(row, 100)

							row += 1
							valid_users += 1
							show_ui_message("User identified: <b>@" + str(tmp_user.screen_name) + "</b>", "INFO", 1)
					except Exception as e:
						invalid_users += 1
						show_ui_message(str(e), "WARNING", 1)

			users_window_ui.tbl_users.removeRow(row)
			f.close()

			users_window_ui.lb_valid_users.setText(str(valid_users))
			users_window_ui.lb_invalid_users.setText(str(invalid_users))

			# Show window
			w.show()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def selectLastFile():
	try:

		if w.isHidden():
			w.show()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def setKMLOutputFile():
	try:

		if ui.cb_kml_file_screen_name.isChecked():
			if ui.tb_username.text():
				ui.tb_kml_filename.setText(ui.tb_username.text() + ".kml")
		else:
			ui.tb_kml_filename.setText("tinfoleak.kml")

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def setHTMLOutputFile():
	try:

		if ui.cb_file_screen_name.isChecked():
			if ui.tb_username.text():
				ui.tb_report_filename.setText(ui.tb_username.text() + ".html")
		else:
			ui.tb_report_filename.setText("tinfoleak.html")

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def enableOperations():
	try:

		boolEnabled = False
		boolChecked = False

		if ui.rb_user.isChecked():
			# Target of Analysis = User
			boolEnabled = True
		else:
			# Target of Analysis = Place | Timeline
			boolChecked = True

		# Likes
		ui.cb_likes.setEnabled(boolEnabled)
		ui.cb_likes.setChecked(boolChecked)
		ui.tb_likes_number.setEnabled(boolEnabled)

		# Lists
		ui.cb_lists.setEnabled(boolEnabled)
		ui.cb_lists.setChecked(boolChecked)
		ui.tb_lists_number.setEnabled(boolEnabled)
		ui.pb_lists_view.setEnabled(boolEnabled)

		# Collections
		ui.cb_collections.setEnabled(boolEnabled)
		ui.cb_collections.setChecked(boolChecked)
		ui.tb_collections_number.setEnabled(boolEnabled)
		ui.pb_collections_view.setEnabled(boolEnabled)

		# Followers
		ui.cb_followers.setEnabled(boolEnabled)
		ui.cb_followers.setChecked(boolChecked)
		ui.tb_followers_number.setEnabled(boolEnabled)
		ui.pb_followers_view.setEnabled(boolEnabled)

		# Friends
		ui.cb_friends.setEnabled(boolEnabled)
		ui.cb_friends.setChecked(boolChecked)
		ui.tb_friends_number.setEnabled(boolEnabled)
		ui.pb_friends_view.setEnabled(boolEnabled)

		# Locations
		ui.cb_visited_locations.setEnabled(boolEnabled)
		ui.cb_visited_locations.setChecked(boolChecked)
		ui.tb_top_locations.setEnabled(boolEnabled)
		ui.tb_kml_filename.setEnabled(boolEnabled)
		ui.cb_kml_file_screen_name.setEnabled(boolEnabled)
		ui.cb_kml_file_screen_name.setChecked(boolChecked)

		# Protected account
		ui.cb_protected_account.setEnabled(boolEnabled)
		ui.cb_protected_account.setChecked(boolChecked)

		# Conversations
		ui.cb_conversations.setEnabled(boolEnabled)
		ui.cb_conversations.setChecked(boolChecked)

		# Social networks
		ui.cb_social_networks.setEnabled(boolEnabled)
		ui.cb_social_networks.setChecked(boolChecked)

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def setUnsetAllUsers(table, checkbox_all, column):
	try:

		rowCount = table.rowCount()
		rowPosition = 0
		while rowPosition < rowCount:
			if checkbox_all.isChecked():
				# Select all users
				table.cellWidget(rowPosition, column).findChild(type(QtGui.QCheckBox())).setChecked(True)
			else:
				# Unselect all users
				table.cellWidget(rowPosition, column).findChild(type(QtGui.QCheckBox())).setChecked(False)
			rowPosition += 1

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def setUnsetUserRelations(table, relation_column, checkbox_relation):
	try:

		rowCount = table.rowCount()
		rowPosition = 0
		while rowPosition < rowCount:
			if checkbox_relation.isChecked():
				if table.item(rowPosition, relation_column).text() == "0":
					table.hideRow(rowPosition)
			else:
				table.showRow(rowPosition)

			rowPosition += 1

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def selectUsersFile(lbl_file):
	try:

		# Select file
		filename = QtGui.QFileDialog.getOpenFileName()
		lbl_file.setText(filename)

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def showUserRelations():
	try:

		# Connect pushButton
		user_relations_ui.pb_select_file_user2.clicked.connect(lambda: selectUsersFile(user_relations_ui.lb_file_user2))
		user_relations_ui.tbl_relations.hideColumn(9)

		# Show window
		user_relations_window.show()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def get_icon_button_profile_image(tmp_user, tmp_window):
    try:

        img_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + tmp_user.screen_name
        if not os.path.isdir(img_directory):
            os.mkdir(img_directory)

        # Profile image
        img = urllib2.urlopen(tmp_user.profile_image_url.replace("_normal.", ".")).read()
        filename = str(tmp_user.id) + "-profile-image.jpg"
        imgFile = img_directory + "/" + filename
        if not os.path.exists(imgFile):
            fd = open(imgFile, 'wb')
            fd.write(img)
            fd.close()

        pixmap = QtGui.QPixmap(imgFile)
        icon_button_profile_image = QtGui.QToolButton(parent=tmp_window)
        icon_button_profile_image.setIcon(QtGui.QIcon(pixmap))
        icon_button_profile_image.setIconSize(QtCore.QSize(100, 100))
        icon_button_profile_image.setAutoRaise(True)

        return icon_button_profile_image

    except Exception as e:
        show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def get_icon_button_relations_image(user1, user2, tmp_window):
	try:

		relation_code = 0
		friendship = api.show_friendship(source_screen_name=user1, target_screen_name=user2)

		# Arrow directory
		img_directory = os.path.dirname(os.path.abspath(__file__)) + "/Output_Reports/img"

		# Arrow left
		filename = "arrow-left.png"
		imgFile = img_directory + "/" + filename
		pixmap = QtGui.QPixmap(imgFile)
		icon_button_arrow_left_image = QtGui.QToolButton(parent=tmp_window)
		icon_button_arrow_left_image.setIcon(QtGui.QIcon(pixmap))
		icon_button_arrow_left_image.setIconSize(QtCore.QSize(100, 100))
		icon_button_arrow_left_image.setAutoRaise(True)

		# Arrow right
		filename = "arrow-right.png"
		imgFile = img_directory + "/" + filename
		pixmap = QtGui.QPixmap(imgFile)
		icon_button_arrow_right_image = QtGui.QToolButton(parent=tmp_window)
		icon_button_arrow_right_image.setIcon(QtGui.QIcon(pixmap))
		icon_button_arrow_right_image.setIconSize(QtCore.QSize(100, 100))
		icon_button_arrow_right_image.setAutoRaise(True)

		# Arrow left-right
		filename = "arrow-left-right.png"
		imgFile = img_directory + "/" + filename
		pixmap = QtGui.QPixmap(imgFile)
		icon_button_arrow_left_right_image = QtGui.QToolButton(parent=tmp_window)
		icon_button_arrow_left_right_image.setIcon(QtGui.QIcon(pixmap))
		icon_button_arrow_left_right_image.setIconSize(QtCore.QSize(100, 100))
		icon_button_arrow_left_right_image.setAutoRaise(True)

		# No arrow
		filename = "no-relations.png"
		imgFile = img_directory + "/" + filename
		pixmap = QtGui.QPixmap(imgFile)
		icon_button_no_relations_image = QtGui.QToolButton(parent=tmp_window)
		icon_button_no_relations_image.setIcon(QtGui.QIcon(pixmap))
		icon_button_no_relations_image.setIconSize(QtCore.QSize(100, 100))
		icon_button_no_relations_image.setAutoRaise(True)

		if friendship[0].following and friendship[0].followed_by:
			icon_button_relations_image = icon_button_arrow_left_right_image
			relation_code = 3
		else:
			if friendship[0].following:
				icon_button_relations_image = icon_button_arrow_right_image
				relation_code = 1
			else:
				if friendship[0].followed_by:
					icon_button_relations_image = icon_button_arrow_left_image
					relation_code = 2
				else:
					icon_button_relations_image = icon_button_no_relations_image
					relation_code = 0


		return icon_button_relations_image, relation_code

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def get_checkbox_widget(checkbox_label):
    try:

		checkbox = QtGui.QCheckBox()
		checkbox.setText(checkbox_label)

		cell_widget = QtGui.QWidget()
		layout_widget = QtGui.QHBoxLayout(cell_widget)
		layout_widget.addWidget(checkbox)
		layout_widget.setAlignment(QtCore.Qt.AlignCenter)
		layout_widget.setContentsMargins(0, 0, 0, 0)
		cell_widget.setLayout(layout_widget)

		return cell_widget

    except Exception as e:
        show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def show_relation_from_user_to_file(username, filename, table):
	try:
		tmp_user1 = User()
		tmp_user2 = User()

		# Clean previous results
		table.setRowCount(0)

		tmp_user1 = api.get_user(username)

		# Read file
		row = 0

		with open(filename) as f:
			show_ui_message("Analyzing file: " + str(filename), "INFO", 1)
			for line in f.readlines():
				try:
					if row < int(ui.tb_users_number.text()):
						tmp_user2 = api.get_user(line.strip("\n"))

						if str(tmp_user1.screen_name).lower() != str(tmp_user2.screen_name).lower():

							rowPosition = table.rowCount()
							table.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
							table.insertRow(rowPosition)

							icon_button_profile_image_user1 = get_icon_button_profile_image(tmp_user1, user_relations_window)
							icon_button_profile_image_user2 = get_icon_button_profile_image(tmp_user2, user_relations_window)

							cell_widget1 = get_checkbox_widget("")
							cell_widget2 = get_checkbox_widget("")

							icon_button_relations_image, relation_code = get_icon_button_relations_image(username, tmp_user2.screen_name, user_relations_window)

							table.setCellWidget(row, 0, cell_widget1)
							table.setCellWidget(row, 1, icon_button_profile_image_user1)
							table.setItem(row, 2, QtGui.QTableWidgetItem("@" + tmp_user1.screen_name))
							table.setItem(row, 3, QtGui.QTableWidgetItem(tmp_user1.name.decode('utf-8')))
							table.setCellWidget(row, 4, icon_button_relations_image)
							table.setCellWidget(row, 5, cell_widget2)
							table.setCellWidget(row, 6, icon_button_profile_image_user2)
							table.setItem(row, 7, QtGui.QTableWidgetItem("@" + tmp_user2.screen_name))
							table.setItem(row, 8, QtGui.QTableWidgetItem(tmp_user2.name.decode('utf-8')))
							table.setItem(row, 9, QtGui.QTableWidgetItem(str(relation_code)))

							table.setRowHeight(row, 100)
							table.resizeColumnsToContents()

							table.verticalScrollBar().setValue(table.verticalScrollBar().maximum())

							row += 1
							show_ui_message("User identified: <b>@" + str(tmp_user2.screen_name) + "</b>", "INFO", 1)
				except Exception as e:
					show_ui_message(str(e), "WARNING", 1)

		table.removeRow(row)
		f.close()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def show_lists():
	try:
		# Clean previous results
		user_lists_ui.tbl_header.setRowCount(0)
		user_lists_ui.tbl_subscribed.setRowCount(0)
		user_lists_ui.tbl_ownership.setRowCount(0)
		user_lists_ui.tbl_membership.setRowCount(0)

		screen_name = ui.tb_username.text()
		tmp_user = User()
		tmp_user = api.get_user(screen_name)
		icon_button_profile_image_user = get_icon_button_profile_image(tmp_user, user_lists_window)

		user_lists_ui.tbl_header.insertRow(0)
		user_lists_ui.tbl_header.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		user_lists_ui.tbl_header.setCellWidget(0, 0, icon_button_profile_image_user)
		user_lists_ui.tbl_header.setItem(0, 1, QtGui.QTableWidgetItem(screen_name))
		user_lists_ui.tbl_header.setItem(0, 2, QtGui.QTableWidgetItem(tmp_user.description))
		user_lists_ui.tbl_header.setRowHeight(0, 100)
		user_lists_ui.tbl_header.resizeColumnsToContents()

		# Subscribed lists
		subscribed_file = screen_name + "_lists.txt"
		username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
		csvFile = open(username_directory + "/" + subscribed_file, "rb")
		list_reader = csv.reader(csvFile)

		rowCount = 0
		for row in list_reader:
			if rowCount > 10:
				rowPosition = user_lists_ui.tbl_subscribed.rowCount()
				user_lists_ui.tbl_subscribed.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
				user_lists_ui.tbl_subscribed.insertRow(rowPosition)
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 0, QtGui.QTableWidgetItem(str(row[1])))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 1, QtGui.QTableWidgetItem(str(row[2]).decode('utf-8')))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 2, QtGui.QTableWidgetItem(str(row[3]).decode('utf-8')))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 3, QtGui.QTableWidgetItem(str(row[4])))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 4, QtGui.QTableWidgetItem(str(row[5])))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 5, QtGui.QTableWidgetItem(str(row[6])))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 6, QtGui.QTableWidgetItem(str(row[7])))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 7, QtGui.QTableWidgetItem(str(row[8])))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 8, QtGui.QTableWidgetItem(str(row[9]).decode('utf-8')))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 9, QtGui.QTableWidgetItem(str(row[10]).decode('utf-8')))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 10, QtGui.QTableWidgetItem(str(row[11])))
				user_lists_ui.tbl_subscribed.setItem(rowPosition, 11, QtGui.QTableWidgetItem(str(row[12])))
			rowCount += 1

		user_lists_ui.tbl_subscribed.resizeColumnsToContents()
		csvFile.close()

		# Ownerships lists
		ownerships_file = screen_name + "_ownerships.txt"
		username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
		csvFile = open(username_directory + "/" + ownerships_file, "rb")
		list_reader = csv.reader(csvFile)

		rowCount = 0
		for row in list_reader:
			if rowCount > 10:
				rowPosition = user_lists_ui.tbl_ownership.rowCount()
				user_lists_ui.tbl_ownership.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
				user_lists_ui.tbl_ownership.insertRow(rowPosition)
				user_lists_ui.tbl_ownership.setItem(rowPosition, 0, QtGui.QTableWidgetItem(str(row[1])))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 1, QtGui.QTableWidgetItem(str(row[2]).decode('utf-8')))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 2, QtGui.QTableWidgetItem(str(row[3]).decode('utf-8')))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 3, QtGui.QTableWidgetItem(str(row[4])))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 4, QtGui.QTableWidgetItem(str(row[5])))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 5, QtGui.QTableWidgetItem(str(row[6])))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 6, QtGui.QTableWidgetItem(str(row[7])))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 7, QtGui.QTableWidgetItem(str(row[8])))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 8, QtGui.QTableWidgetItem(str(row[9]).decode('utf-8')))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 9, QtGui.QTableWidgetItem(str(row[10]).decode('utf-8')))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 10, QtGui.QTableWidgetItem(str(row[11])))
				user_lists_ui.tbl_ownership.setItem(rowPosition, 11, QtGui.QTableWidgetItem(str(row[12])))
			rowCount += 1

		user_lists_ui.tbl_ownership.resizeColumnsToContents()
		csvFile.close()

		# Ownerships lists
		memberships_file = screen_name + "_memberships.txt"
		username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
		csvFile = open(username_directory + "/" + memberships_file, "rb")
		list_reader = csv.reader(csvFile)

		rowCount = 0
		for row in list_reader:
			if rowCount > 10:
				rowPosition = user_lists_ui.tbl_membership.rowCount()
				user_lists_ui.tbl_membership.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
				user_lists_ui.tbl_membership.insertRow(rowPosition)
				user_lists_ui.tbl_membership.setItem(rowPosition, 0, QtGui.QTableWidgetItem(str(row[1])))
				user_lists_ui.tbl_membership.setItem(rowPosition, 1, QtGui.QTableWidgetItem(str(row[2]).decode('utf-8')))
				user_lists_ui.tbl_membership.setItem(rowPosition, 2, QtGui.QTableWidgetItem(str(row[3]).decode('utf-8')))
				user_lists_ui.tbl_membership.setItem(rowPosition, 3, QtGui.QTableWidgetItem(str(row[4])))
				user_lists_ui.tbl_membership.setItem(rowPosition, 4, QtGui.QTableWidgetItem(str(row[5])))
				user_lists_ui.tbl_membership.setItem(rowPosition, 5, QtGui.QTableWidgetItem(str(row[6])))
				user_lists_ui.tbl_membership.setItem(rowPosition, 6, QtGui.QTableWidgetItem(str(row[7])))
				user_lists_ui.tbl_membership.setItem(rowPosition, 7, QtGui.QTableWidgetItem(str(row[8])))
				user_lists_ui.tbl_membership.setItem(rowPosition, 8, QtGui.QTableWidgetItem(str(row[9]).decode('utf-8')))
				user_lists_ui.tbl_membership.setItem(rowPosition, 9, QtGui.QTableWidgetItem(str(row[10]).decode('utf-8')))
				user_lists_ui.tbl_membership.setItem(rowPosition, 10, QtGui.QTableWidgetItem(str(row[11])))
				user_lists_ui.tbl_membership.setItem(rowPosition, 11, QtGui.QTableWidgetItem(str(row[12])))
			rowCount += 1

		user_lists_ui.tbl_membership.resizeColumnsToContents()
		csvFile.close()

		# Show window
		user_lists_window.show()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def show_collections():
	try:
		# Clean previous results
		user_collections_ui.tbl_user.setRowCount(0)
		user_collections_ui.tbl_collections.setRowCount(0)

		# Get user data
		screen_name = ui.tb_username.text()
		tmp_user = User()
		tmp_user = api.get_user(screen_name)
		icon_button_profile_image_user = get_icon_button_profile_image(tmp_user, user_collections_window)

		# Header
		user_collections_ui.tbl_user.insertRow(0)
		user_collections_ui.tbl_user.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		user_collections_ui.tbl_user.setCellWidget(0, 0, icon_button_profile_image_user)
		user_collections_ui.tbl_user.setItem(0, 1, QtGui.QTableWidgetItem(screen_name))
		user_collections_ui.tbl_user.setItem(0, 2, QtGui.QTableWidgetItem(tmp_user.description))
		user_collections_ui.tbl_user.setRowHeight(0, 100)
		user_collections_ui.tbl_user.resizeColumnsToContents()

		# Collections
		collections_file = screen_name + "_collections.txt"
		username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
		csvFile = open(username_directory + "/" + collections_file, "rb")
		collection_reader = csv.reader(csvFile)

		rowCount = 0
		for row in collection_reader:
			if rowCount > 10:
				rowPosition = user_collections_ui.tbl_collections.rowCount()
				user_collections_ui.tbl_collections.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
				user_collections_ui.tbl_collections.insertRow(rowPosition)
				user_collections_ui.tbl_collections.setItem(rowPosition, 0, QtGui.QTableWidgetItem(str(row[1])))
				user_collections_ui.tbl_collections.setItem(rowPosition, 1, QtGui.QTableWidgetItem(str(row[2]).decode('utf-8')))
				user_collections_ui.tbl_collections.setItem(rowPosition, 2, QtGui.QTableWidgetItem(str(row[3]).decode('utf-8')))
				user_collections_ui.tbl_collections.setItem(rowPosition, 3, QtGui.QTableWidgetItem(str(row[4])))

			rowCount += 1

		user_collections_ui.tbl_collections.resizeColumnsToContents()
		csvFile.close()

		# Show window
		user_collections_window.show()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def show_followers():
	try:

		# Clean previous results
		user_followers_ui.tbl_header.setRowCount(0)
		user_followers_ui.tbl_followers.setRowCount(0)

		screen_name = ui.tb_username.text()
		tmp_user = User()
		tmp_user = api.get_user(screen_name)
		icon_button_profile_image_user = get_icon_button_profile_image(tmp_user, user_followers_window)

		user_followers_ui.tbl_header.insertRow(0)
		user_followers_ui.tbl_header.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		user_followers_ui.tbl_header.setCellWidget(0, 0, icon_button_profile_image_user)
		user_followers_ui.tbl_header.setItem(0, 1, QtGui.QTableWidgetItem(screen_name))
		user_followers_ui.tbl_header.setItem(0, 2, QtGui.QTableWidgetItem(tmp_user.description))
		user_followers_ui.tbl_header.setRowHeight(0, 100)
		user_followers_ui.tbl_header.resizeColumnsToContents()

		username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
		if not os.path.isdir(username_directory):
			show_ui_message("Resource <b>" + username_directory + "</b> not found", "ERROR", 1)

		else:
			# Followers file
			followers_file = "/followers-" + datetime.datetime.now().strftime('%Y%m%d') + "/" + screen_name + "_followers.txt"
			csvFile = open(username_directory + "/" + followers_file, "rb")
			followers_reader = csv.reader(csvFile)

			rowCount = 0
			for row in followers_reader:
				if rowCount > 10:
					rowPosition = user_followers_ui.tbl_followers.rowCount()
					user_followers_ui.tbl_followers.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
					user_followers_ui.tbl_followers.insertRow(rowPosition)
					n =0
					while n < 17:
						user_followers_ui.tbl_followers.setItem(rowPosition, n, QtGui.QTableWidgetItem(str(row[n+1]).decode('utf-8')))
						n += 1
				rowCount += 1

			user_followers_ui.tbl_followers.resizeColumnsToContents()
			csvFile.close()

			# Show window
			user_followers_window.show()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def show_friends():
	try:

		# Clean previous results
		user_friends_ui.tbl_header.setRowCount(0)
		user_friends_ui.tbl_friends.setRowCount(0)

		screen_name = ui.tb_username.text()
		tmp_user = api.get_user(screen_name)
		icon_button_profile_image_user = get_icon_button_profile_image(tmp_user, user_friends_window)

		user_friends_ui.tbl_header.insertRow(0)
		user_friends_ui.tbl_header.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		user_friends_ui.tbl_header.setCellWidget(0, 0, icon_button_profile_image_user)
		user_friends_ui.tbl_header.setItem(0, 1, QtGui.QTableWidgetItem(screen_name))
		user_friends_ui.tbl_header.setItem(0, 2, QtGui.QTableWidgetItem(tmp_user.description))
		user_friends_ui.tbl_header.setRowHeight(0, 100)
		user_friends_ui.tbl_header.resizeColumnsToContents()

		username_directory = os.path.dirname(os.path.abspath(__file__)) + "/" + screen_name
		if not os.path.isdir(username_directory):
			show_ui_message("Resource <b>" + username_directory + "</b> not found", "ERROR", 1)

		else:
			# Friends file
			friends_file = "/friends-" + datetime.datetime.now().strftime('%Y%m%d') + "/" + screen_name + "_friends.txt"
			csvFile = open(username_directory + "/" + friends_file, "rb")
			friends_reader = csv.reader(csvFile)

			rowCount = 0
			for row in friends_reader:
				if rowCount > 10:
					rowPosition = user_friends_ui.tbl_friends.rowCount()
					user_friends_ui.tbl_friends.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
					user_friends_ui.tbl_friends.insertRow(rowPosition)
					n =0
					while n < 17:
						user_friends_ui.tbl_friends.setItem(rowPosition, n, QtGui.QTableWidgetItem(str(row[n+1]).decode('utf-8')))
						n += 1
				rowCount += 1

			user_friends_ui.tbl_friends.resizeColumnsToContents()
			csvFile.close()

			# Show window
			user_friends_window.show()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def selectTargetFromUserRelations():
    try:

		selection = 0
		selection = selectUser(table=user_relations_ui.tbl_relations, checkbox_column=0, screen_name_column=2)
		if not selection:
			selectUser(table=user_relations_ui.tbl_relations, checkbox_column=5, screen_name_column=7)

    except Exception as e:
        show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def getUserRelations():
	try:
		tmp_user1 = User()
		tmp_user2 = User()

		# Clean previous results
		user_relations_ui.tbl_relations.setRowCount(0)

		user1 = user_relations_ui.tb_username.text()
		user2 = user_relations_ui.tb_username_2.text()
		file2 = user_relations_ui.lb_file_user2.text()

		if user1 != "" and user2 != "":
			tmp_user1 = api.get_user(user1)
			tmp_user2 = api.get_user(user2)
			user_relations_ui.lb_file_user2.setText("")

			friendship = api.show_friendship(source_screen_name=user1, target_screen_name=user2)

			user_relations_ui.tbl_relations.insertRow(0)
			user_relations_ui.tbl_relations.setRowHeight(0,100)

			if user_relations_ui.cb_profile_images.isChecked():
				# User 1
				icon_button_profile_image_user1 = get_icon_button_profile_image(tmp_user1, user_relations_window)

				# User 2
				icon_button_profile_image_user2 = get_icon_button_profile_image(tmp_user2, user_relations_window)

				user_relations_ui.tbl_relations.setCellWidget(0, 1, icon_button_profile_image_user1)
				user_relations_ui.tbl_relations.setCellWidget(0, 6, icon_button_profile_image_user2)

			# Checkbox User 1
			cell_widget_user1 = get_checkbox_widget("")

			# Checkbox User 2
			cell_widget_user2 = get_checkbox_widget("")

			icon_button_relations_image, relation_code = get_icon_button_relations_image(user1, user2, user_relations_window)

			user_relations_ui.tbl_relations.setCellWidget(0, 0, cell_widget_user1)
			user_relations_ui.tbl_relations.setCellWidget(0, 5, cell_widget_user2)
			user_relations_ui.tbl_relations.setItem(0, 2, QtGui.QTableWidgetItem("@" + tmp_user1.screen_name))
			user_relations_ui.tbl_relations.setItem(0, 3, QtGui.QTableWidgetItem(tmp_user1.name.decode('utf-8')))
			user_relations_ui.tbl_relations.setCellWidget(0, 4, icon_button_relations_image)
			user_relations_ui.tbl_relations.setItem(0, 7, QtGui.QTableWidgetItem("@" + tmp_user2.screen_name))
			user_relations_ui.tbl_relations.setItem(0, 8, QtGui.QTableWidgetItem(tmp_user2.name.decode('utf-8')))
			user_relations_ui.tbl_relations.resizeColumnsToContents()

		else:
			if user1 != "" and file2 != "":
				show_relation_from_user_to_file(user1, file2, user_relations_ui.tbl_relations)

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)

# ----------------------------------------------------------------------
def reset_filters():
	try:
		today = date.today()
		sdate = date.fromordinal(today.toordinal() - 14)
		edate = (datetime.datetime.now() + datetime.timedelta(days=1))

		ui.tb_sdate.setDate(QtCore.QDate(int(sdate.strftime('%Y')), int(sdate.strftime('%m')), int(sdate.strftime('%d'))))
		ui.tb_edate.setDate(QtCore.QDate(int(edate.strftime('%Y')), int(edate.strftime('%m')), int(edate.strftime('%d'))))

		ui.tb_stime.setTime(QtCore.QTime(0, 0, 0))
		ui.tb_etime.setTime(QtCore.QTime(23, 59, 59))

		ui.tb_include_words.setText("")
		ui.tb_not_include_words.setText("")
		ui.tb_source_app.setText("")

		ui.rb_RT_all.setChecked(True)
		ui.rb_media_all.setChecked(True)
		ui.rb_sourceapp_yes.setChecked(True)

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)


################################
# MAIN
################################
if __name__ == '__main__':
	try:

		vconfig = Configuration()
		api = vconfig.api
		client = vconfig.client

		# Graphical interface
		app = QtGui.QApplication(sys.argv)
		window = QtGui.QDialog()
		ui = main_window.Ui_Dialog()
		ui.setupUi(window)

		# Window to select users from file
		w = QtGui.QDialog(parent=window)
		users_window_ui = users_window.Ui_Dialog()
		users_window_ui.setupUi(w)
		# Connect buttonBox
		btn = users_window_ui.buttonBox.button(QtGui.QDialogButtonBox.Ok)
		btn.clicked.connect(lambda: selectUser(table = users_window_ui.tbl_users, checkbox_column = 0, screen_name_column = 4))
		# Connect checkbox : select all
		users_window_ui.cb_all.stateChanged.connect(lambda: setUnsetAllUsers(table = users_window_ui.tbl_users, checkbox_all = users_window_ui.cb_all, column = 0))

		# Window to identify user relations
		user_relations_window = QtGui.QDialog(parent=window)
		user_relations_ui = relations_window.Ui_Dialog()
		user_relations_ui.setupUi(user_relations_window)
		# Connect buttonBox
		btn = user_relations_ui.buttonBox.button(QtGui.QDialogButtonBox.Apply)
		btn.clicked.connect(getUserRelations)
		btnClose = user_relations_ui.buttonBox.button(QtGui.QDialogButtonBox.Ok)
		btnClose.clicked.connect(selectTargetFromUserRelations)
		# Connect checkbox : select all
		user_relations_ui.cb_all_user1.stateChanged.connect(lambda: setUnsetAllUsers(table = user_relations_ui.tbl_relations, checkbox_all = user_relations_ui.cb_all_user1, column = 0))
		user_relations_ui.cb_all_user2.stateChanged.connect(lambda: setUnsetAllUsers(table= user_relations_ui.tbl_relations, checkbox_all= user_relations_ui.cb_all_user2,column=5))
		user_relations_ui.cb_relations.stateChanged.connect(lambda: setUnsetUserRelations(table = user_relations_ui.tbl_relations, relation_column = 9, checkbox_relation = user_relations_ui.cb_relations))

		# Window to show user lists
		user_lists_window = QtGui.QDialog(parent=window)
		user_lists_ui = lists_window.Ui_Dialog()
		user_lists_ui.setupUi(user_lists_window)
		# Connect buttonBox
		ui.pb_lists_view.clicked.connect(show_lists)

		# Window to show user collections
		user_collections_window = QtGui.QDialog(parent=window)
		user_collections_ui = collections_window.Ui_Dialog()
		user_collections_ui.setupUi(user_collections_window)
		# Connect buttonBox
		ui.pb_collections_view.clicked.connect(show_collections)

		# Window to show followers
		user_followers_window = QtGui.QDialog(parent=window)
		user_followers_ui = followers_window.Ui_Dialog()
		user_followers_ui.setupUi(user_followers_window)
		# Connect buttonBox
		ui.pb_followers_view.clicked.connect(show_followers)

		# Window to show friends
		user_friends_window = QtGui.QDialog(parent=window)
		user_friends_ui = friends_window.Ui_Dialog()
		user_friends_ui.setupUi(user_friends_window)
		# Connect buttonBox
		ui.pb_friends_view.clicked.connect(show_friends)

		# Initialize search filters
		reset_filters()

		# Connect pushButton
		ui.pb_select_users_file.clicked.connect(selectFile)
		ui.pb_reset_filters.clicked.connect(reset_filters)
		ui.pb_last_results.clicked.connect(selectLastFile)
		ui.pb_relations.clicked.connect(showUserRelations)

		# Connect buttonBox
		btn = ui.buttonBox.button(QtGui.QDialogButtonBox.Apply)
		btn.clicked.connect(get_information_from_interface)

		# Connect checkbox : HTML output file
		ui.cb_file_screen_name.stateChanged.connect(setHTMLOutputFile)

		# Connect checkbox : KML output file
		ui.cb_kml_file_screen_name.stateChanged.connect(setKMLOutputFile)

		# Connect radio button (Target of Analysis): User
		ui.rb_user.toggled.connect(enableOperations)

		window.show()

		app.exec_()

	except Exception as e:
		show_ui_message(str(e) + "<br>", "ERROR", 1)
