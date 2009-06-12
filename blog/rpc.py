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


import os
import logging
import datetime
import simplejson
import wsgiref.handlers

from google.appengine.api import datastore
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.ext import db

from model import Archive,Weblog,WeblogReactions,AuthSubStoredToken,Album,Menu,Images,Tag,Greeting,Feeds

import authorized
import util

class Image (webapp.RequestHandler):
  def get(self):
    image = db.get(self.request.get("img_id"))
    if image.image:
      self.response.headers['Content-Type'] = "image/png"
      self.response.out.write(image.image)
    else:
      self.response.out.write("No image")

class UploadImage (webapp.RequestHandler):
    @authorized.role('admin')
    def post(self):
        images = Images()
        img = self.request.get("img")
        if not img:
            self.response.out.write( '{status:"Please select your image."}')
            return
        try:
            images.image = db.Blob(img)
            images.uploader = users.GetCurrentUser()
            key = images.put()
        except Exception, e:
            self.response.out.write( '{status:"An Error Occurred uploading the image."}')
            return
        self.response.out.write('{status:"UPLOADED",image_url:"/rpc/img?img_id=%s"}' % (key))


# This handler allows the functions defined in the RPCHandler class to
# be called automatically by remote code.
class RPCHandler(webapp.RequestHandler):
  def get(self):
    action = self.request.get('action')
    arg_counter = 0;
    args = []
    while True:
      arg = self.request.get('arg' + str(arg_counter))
      arg_counter += 1
      if arg:
        args += (simplejson.loads(arg),);
      else:
        break;
    result = getattr(self, action)(*args)
    self.response.out.write(simplejson.dumps((result)))

  def post(self):
    action = self.request.get('action')
    request_ = self.request
    result = getattr(self, action)(request_)
    self.response.out.write(simplejson.dumps(result))

# The RPCs exported to JavaScript follow here:
  
  @authorized.role('admin')
  def FlushAllMemcache(self,flush):
    if flush:
        status = memcache.flush_all()
    cache_stats = memcache.get_stats()
    return cache_stats

  @authorized.role('admin')
  def FlushMemcache(self,key):
    memcache.delete(key)
    return True


  @authorized.role('admin')
  def DeleteSessionToken(self,user_email,target_service):
      stored_token = AuthSubStoredToken.gql('WHERE user_email = :1 and target_service = :2',
          user_email, target_service).get()
      if stored_token:
          stored_token.delete()
      return True

  # for menu inline cell editable table
  @authorized.role('admin')
  def UpdateMenu(self,request):
      menu = Menu.get_by_id(int(request.get("id")))
      editColumn = request.get("editColumn")
      if menu and editColumn:
          newData = request.get("newData")
          if editColumn == "title":
            menu.title = newData
          if editColumn == "permalink":
            menu.permalink = newData
          if editColumn == "target":
            menu.target = newData
          if editColumn == "order":
            menu.order = simplejson.loads(newData)
          if editColumn == "valid":
            menu.valid = simplejson.loads(newData)
          menu.put()
          util.flushMenuList()
      return True
        
  @authorized.role('admin')
  def AddMenu(self,request):
      menu = datastore.Entity("Menu")
      menu["title"] = "New Menu"
      menu["permalink"] = "New permalink"
      menu["target"] = "_self"
      menu["order"] = 0
      menu["valid"] = False
      datastore.Put(menu)
      util.flushMenuList()
      menu['key'] = str(menu.key())
      menu['id'] = str(menu.key().id())
      return menu

  @authorized.role('admin')
  def DeleteMenu(self,request):
      menu = Menu.get_by_id(int(request.get("id")))
      menu.delete()
      util.flushMenuList()
      return True

  # for album inline cell editable table.
  @authorized.role('user')
  def UpdateAlbum(self,request):
      album = Album.get_by_id(int(request.get("id")))
      editColumn = request.get("editColumn")
      if album and editColumn:
          newData = request.get("newData")
          if editColumn == "album_username":
            album.album_username = newData
          if editColumn == "album_type":
            album.album_type = newData
          if editColumn == "access":
            album.access = newData
          if editColumn == "date":
            album.date = simplejson.loads(newData)
          if editColumn == "order":
            album.order = simplejson.loads(newData)
          if editColumn == "valid":
            album.valid = simplejson.loads(newData)
          album.put()
          util.flushAlbumList()
      return True

  @authorized.role('user')
  def AddAlbum(self,request):
      album = datastore.Entity("Album")
      album["album_username"] = "New Album"
      album["album_type"] = "public"
      album["access"] = "public"
      album["date"] = datetime.datetime.now()
      album["valid"] = False
      album["order"] = 0
      album["owner"] = users.GetCurrentUser()
      datastore.Put(album)
      util.flushAlbumList()
      album['key'] = str(album.key())
      album['id'] = str(album.key().id())
      album["date"] = album["date"].strftime('%m/%d/%y')
      album["owner"] = str(album["owner"].email())
      return album

  @authorized.role('user')
  def DeleteAlbum(self,request):
      album = Album.get_by_id(int(request.get("id")))
      album.delete()
      util.flushAlbumList()
      return True

  #for uploaded images files management.
  @authorized.role('admin')
  def GetImages(self,startIndex,results):
      query = datastore.Query('Images')
      query.Order(('date', datastore.Query.DESCENDING))
      cpedialog = util.getCPedialog()
      images = []
      for image in query.Get(results,startIndex):
          image['uploader'] = image['uploader'].email()
          image['image'] = "/rpc/img?img_id="+str(image.key())
          image['url'] =  "/rpc/img?img_id="+str(image.key())
          image['key'] = str(image.key())
          image["date"] = image["date"].strftime('%m/%d/%y')
          image['id'] = str(image.key().id())
          images+=[image]
      totalRecords = query.Count()
      returnValue = {"records":images,"totalRecords":totalRecords,"startIndex":startIndex}    
      return returnValue

  @authorized.role('admin')
  def DeleteImage(self,request):
      image = Images.get_by_id(int(request.get("id")))
      image.delete()
      return True


  #for tags management.
  @authorized.role('admin')
  def GetTags(self,startIndex,results):
      query = datastore.Query('Tag')
      tags = []
      for tag in query.Get(results,startIndex):
          tag['key'] = str(tag.key())
          tag['id'] = str(tag.key().id())
          tags+=[tag]
      totalRecords = query.Count()
      returnValue = {"records":tags,"totalRecords":totalRecords,"startIndex":startIndex}
      return returnValue

  @authorized.role('admin')
  def DeleteTag(self,request):
      tag = Tag.get_by_id(int(request.get("id")))
      tag.delete()
      return True

  @authorized.role('admin')
  def RefreshTag(self,request):
      tag = Tag.get_by_id(int(request.get("id")))
      query_weblog = Weblog.all().filter('tags', tag.tag)
      if query_weblog:
          tag.entrycount = query_weblog.count()
          tag.put()
      tagJson = {}    
      tagJson["id"] =  str(tag.key().id())
      tagJson["key"] = str(tag.key())
      tagJson["tag"] = str(tag.tag)
      tagJson["entrycount"] = tag.entrycount
      tagJson["valid"] = tag.valid
      return tagJson

  #for archive management.
  @authorized.role('admin')
  def GetArchives(self,startIndex,results):
      query = datastore.Query('Archive').Order(('date',datastore.Query.DESCENDING))  #the parameter must be list.
      archives = []
      for archive in query.Get(results,startIndex):
          archive['key'] = str(archive.key())
          archive['id'] = str(archive.key().id())
          archive["date"] = archive["date"].strftime('%m/%d/%y')
          archives+=[archive]
      totalRecords = query.Count()
      returnValue = {"records":archives,"totalRecords":totalRecords,"startIndex":startIndex}
      return returnValue

  @authorized.role('admin')
  def DeleteArchive(self,request):
      archive = Archive.get_by_id(int(request.get("id")))
      archive.delete()
      return True

  @authorized.role('admin')
  def RefreshArchive(self,request):
      archive = Archive.get_by_id(int(request.get("id")))
      query = db.GqlQuery("select * from Weblog where monthyear=:1 and entrytype = 'post'order by date desc",archive.monthyear)
      if query:
          archive.weblogcount = query.count()
          archive.put()
      archiveJson = {}
      archiveJson["id"] =  str(archive.key().id())
      archiveJson["key"] = str(archive.key())
      archiveJson["monthyear"] = str(archive.monthyear)
      archiveJson["weblogcount"] = archive.weblogcount
      archiveJson["date"] = archive.date.strftime('%m/%d/%y')
      return archiveJson

  #for greeting.
  def AddGreeting(self,request):
      refresh = simplejson.loads(request.get("refresh"))
      if refresh:
          greeting = Greeting()
          greeting.user = request.get("id")
          greeting.content = request.get("msg")
          currentUser = users.GetCurrentUser()
          if currentUser:
            greeting.author = currentUser
          greeting.put()
      query = datastore.Query('Greeting').Order(('date',datastore.Query.DESCENDING))  #the parameter must be list.
      greetings = []
      for greeting_ in query.Get(20):
          greeting_['key'] = str(greeting_.key())
          #greeting_['author'] = greeting_['user']
          if greeting_['author']:
            greeting_['email'] = greeting_['author'].email()
            greeting_['author'] = "\""+greeting_['email'].split('@')[0]+"\""
          else:
            greeting_['author'] = greeting_['user'].split('@')[0]   
          greeting_["date"] = greeting_["date"].strftime('%m/%d/%y')
          greetings+=[greeting_]
      return greetings


  # for feed inline cell editable table
  @authorized.role('admin')
  def UpdateFeed(self,request):
      feed = Feeds.get_by_id(int(request.get("id")))
      editColumn = request.get("editColumn")
      if feed and editColumn:
          newData = request.get("newData")
          if editColumn == "title":
            feed.title = newData
          if editColumn == "feed":
            feed.feed = newData
          if editColumn == "order":
            feed.order = simplejson.loads(newData)
          if editColumn == "valid":
            feed.valid = simplejson.loads(newData)
          feed.put()
          util.flushFeedList()
      return True

  @authorized.role('admin')
  def AddFeed(self,request):
      feed = datastore.Entity("Feeds")
      feed["title"] = "New feed"
      feed["feed"] = "New feed url"
      feed["order"] = 0
      feed["valid"] = False
      datastore.Put(feed)
      util.flushFeedList()
      feed['key'] = str(feed.key())
      feed['id'] = str(feed.key().id())
      return feed

  @authorized.role('admin')
  def DeleteFeed(self,request):
      feed = Feeds.get_by_id(int(request.get("id")))
      feed.delete()
      util.flushFeedList()
      return True
