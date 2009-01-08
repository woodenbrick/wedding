# !/usr/bin/env python
#
# Copyright 2008 CPedia.com.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'Ping Chen'


import gdata.photos.service
import gdata.media
import gdata.geo
import atom

import cgi
import wsgiref.handlers
import os
import re
import datetime
import calendar
import logging
import string

from xml.etree import ElementTree

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache

import authorized
import view
import util

from model import Album

import gdata.urlfetch
gdata.service.http_request_handler = gdata.urlfetch



class BaseRequestHandler(webapp.RequestHandler):
  def generate(self, template_name, template_values={}):
    values = {
      'request': self.request,
    }
    values.update(template_values)
    directory = os.path.dirname(__file__)
    view.ViewPage(cache_time=0).render(self, template_name,values)

  def getAlbumFeedEntry(self,album_username):
      key_albums = "albums_"+ album_username
      try:
          feed = memcache.get(key_albums)
      except Exception:
          feed = None
      if not feed:
          gd_client = gdata.photos.service.PhotosService()
          try:
              feed = gd_client.GetUserFeed(user= album_username)
          except Exception:
              return None
          memcache.add(key=key_albums, value=feed, time=3600)
      return feed

  def validatorFeedAndReturnTemplate(self,feed,album_username,usernames):
      if feed == None:
          template_values ={
              'error':"Can not retrieve the picasaweb album(s) of user '"+album_username+"', please " +
              "make sure you set the correct picasaweb account."
          }
      else:
          template_values = {
            'username':album_username,
            'usernames':usernames,
            'albums':feed.entry,
             }
      return template_values

class MainPage(BaseRequestHandler):
  def get(self):
    usernames = util.getAlbumList()
    if usernames:
        defaultAlbum = usernames[0]
        album_username = defaultAlbum.album_username
        feed = self.getAlbumFeedEntry(defaultAlbum.album_username)
        template_values = self.validatorFeedAndReturnTemplate(feed,album_username,usernames)
    else:
        template_values ={
            'error':"Please set picasaweb album(s) in the system configuration."
        }
    self.generate('album_main.html',template_values)

        
class UserHandler(BaseRequestHandler):
  def get(self, username):
    usernames = util.getAlbumList()
    album = db.Query(Album).filter('album_username =',username).get()
    if album is None:
        self.redirect("/albums")
    feed = self.getAlbumFeedEntry(album.album_username)
    template_values = self.validatorFeedAndReturnTemplate(feed,album.album_username,usernames)
    self.generate('album_main.html',template_values)

class UserPrivateHandler(BaseRequestHandler):
  @authorized.authSub("albums")
  def get(self, username):
    usernames = util.getAlbumList()
    album = db.Query(Album).filter('album_username =',username).get()
    if album is None:
        self.redirect("/albums")
    feed = self.getAlbumFeedEntry(album.album_username)
    template_values = self.validatorFeedAndReturnTemplate(feed,album.album_username,usernames)
    self.generate('album_main.html',template_values)


class AlbumHandler(BaseRequestHandler):
    #@authorized.authSub('albums')
    def get(self, username, album_name):
        gd_client = gdata.photos.service.PhotosService()

        key_photos = "photos_"+username+"_"+album_name
        try:
            feed_photos = memcache.get(key_photos)
        except Exception:
            feed_photos = None
        if not feed_photos:
            feed_photos = gd_client.GetFeed(
                '/data/feed/api/user/%s/album/%s?kind=photo' % (
                    username, album_name))
            memcache.add(key=key_photos, value=feed_photos, time=3600)

        key_albums = "albums_"+ username
        try:
            feed_albums = memcache.get(key_albums)
        except Exception:
            feed_albums = None    
        if not feed_albums:
            feed_albums = gd_client.GetUserFeed(user=username)
            memcache.add(key=key_albums, value=feed_albums, time=3600)

        album = None
        for album_ in feed_albums.entry:
            if album_.name.text == album_name:
                album = album_
                break

        template_values = {
          'photos': feed_photos.entry,
          'album': album,
          'username':username,
          'album_name':album_name,
          }
        self.generate('album_view.html',template_values)

#deprecated
class PhotoHandler(BaseRequestHandler):
    def get(self, username, album_name, photoId):
        gd_client = gdata.photos.service.PhotosService()
        feed = gd_client.GetFeed(
            '/data/feed/api/user/%s/album/%s?kind=photo' % (
                username, album_name))
        i=0
        for photo in feed.entry:
            if photo.gphoto_id.text == photoId:
                break
            i=i+1
        cur_photo = feed.entry[i]
        if(i==0):
            next_photo = feed.entry[i+1]
            pre_photo = None
        else:
          pre_photo = feed.entry[i-1]
          if i==len(feed.entry)-1:
              next_photo = None
          else:
              next_photo = feed.entry[i+1]
            
        template_values = {
          'cur_photo': cur_photo,
          'pre_photo': pre_photo,
          'next_photo': next_photo,
          'username':username,
          'album_name':album_name,
          }
        self.generate('album_photo_view.html',template_values)
