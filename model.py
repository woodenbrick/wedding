# !/usr/bin/env python
#
#
#THIS VERSION HAS BEEN MODIFED BY Daniel Woodhouse
#wodemoneke@gmail.com
#Source avaiable via git repo:
#git clone git://github.com/woodenbrick/cpe_wedding.git 
#Original is available at http://code.google.com/p/cpedialog/
#
#
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


import pickle

from google.appengine.ext import db
from google.appengine.ext import search
import logging
import datetime
import urllib
import cgi
import simplejson


class Archive(db.Model):
    monthyear = db.StringProperty(multiline=False)
    """July 2008"""
    weblogcount = db.IntegerProperty(default=0)
    date = db.DateTimeProperty(auto_now_add=True)

class Song(db.Model):
    title = db.StringProperty()
    artist = db.StringProperty()
    date = db.DateTimeProperty(auto_now=True)
    requested_by = db.StringProperty()
    #url = db.StringProperty()
    
class BridesMaidPhoto(db.Model):
    #id = db.IntegerProperty()
    photo_url = db.StringProperty()

class BridesMaidComment(db.Model):
    name = db.StringProperty()
    comment = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now = True)

class NewPhoto(db.Model):
    photo = db.BlobProperty()

class BridesMaidVotes(db.Model):
    voter = db.StringProperty()
    photo_url = db.StringProperty()
    vote = db.IntegerProperty()
    vote_date = db.DateTimeProperty(auto_now=True)
    
class BridesMaidRating(db.Model):
    photo_url = db.StringProperty()
    rating = db.StringProperty()
    current_rank = db.IntegerProperty()
    
class Tag(db.Model):
    tag = db.StringProperty(multiline=False)
    entrycount = db.IntegerProperty(default=0)
    valid = db.BooleanProperty(default = True)


class Weblog(db.Model):
    permalink = db.StringProperty()
    title = db.StringProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    author = db.UserProperty()
    authorEmail = db.EmailProperty()
    catalog = db.StringProperty()
    lastCommentedDate = db.DateTimeProperty()
    commentcount = db.IntegerProperty(default=0)
    lastModifiedDate = db.DateTimeProperty()
    lastModifiedBy = db.UserProperty()
    tags = db.ListProperty(db.Category)
    monthyear = db.StringProperty(multiline=False)
    entrytype = db.StringProperty(multiline=False,default='post',choices=[
        'post','page'])
    _weblogId = db.IntegerProperty()   ##for data migration from the mysql system
    assoc_dict = db.BlobProperty()     # Pickled dict for sidelinks, associated Amazon items, etc.

    def relative_permalink(self):
        if self.entrytype == 'post':
            return self.date.strftime('%Y/%m/')+ self.permalink
        else:
            return self.permalink

    def full_permalink(self):
        if self.entrytype == 'post':
            return '/' + self.date.strftime('%Y/%m/')+ self.permalink
        else:
            return '/'+ self.permalink

    def get_tags(self):
        '''comma delimted list of tags'''
        return ','.join([urllib.unquote(tag.encode('utf8')) for tag in self.tags])
  
    def set_tags(self, tags):
        if tags:
            self.tags = [db.Category(urllib.quote(tag.strip().encode('utf8'))) for tag in tags.split(',')]
  
    tags_commas = property(get_tags,set_tags)

    #for data migration
    def update_archive(self,update):
        """Checks to see if there is a month-year entry for the
        month of current blog, if not creates it and increments count"""
        my = self.date.strftime('%B %Y') # July 2008
        archive = Archive.all().filter('monthyear',my).fetch(10)
        if archive == []:
            archive = Archive(monthyear=my,date=self.date,weblogcount=1)
            archive.put()
        else:
            if not update:
                # ratchet up the count
                archive[0].weblogcount += 1
                archive[0].put()

    def update_tags(self,update):
        """Update Tag cloud info"""
        if self.tags: 
            for tag_ in self.tags:
                #tag_ = tag.encode('utf8')
                tags = Tag.all().filter('tag',tag_).fetch(10)
                if tags == []:
                    tagnew = Tag(tag=tag_,entrycount=1)
                    tagnew.put()
                else:
                    if not update:
                        tags[0].entrycount+=1
                        tags[0].put()

    def save(self):
        self.update_tags(False)
        if self.entrytype == "post":
            self.update_archive(False)
        my = self.date.strftime('%B %Y') # July 2008
        self.monthyear = my
        self.put()

    def update(self):
        self.update_tags(True)
        if self.entrytype == "post":
            self.update_archive(True)
        self.put()


class WeblogReactions(db.Model):
    weblog = db.ReferenceProperty(Weblog)
    user = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    author = db.UserProperty()
    authorEmail = db.EmailProperty()
    authorWebsite = db.StringProperty()
    userIp = db.StringProperty()
    content = db.TextProperty()
    lastModifiedDate = db.DateTimeProperty()
    lastModifiedBy = db.UserProperty()
    _weblogReactionId = db.IntegerProperty()   ##for data migration from the mysql system

    def save(self):
        self.put()
        if self.weblog is not None:
            self.weblog.lastCommentedDate = self.date
            self.weblog.commentcount += 1
            self.weblog.put()


class AuthSubStoredToken(db.Model):
    user_email = db.StringProperty(required=True)
    target_service = db.StringProperty(multiline=False,default='base',choices=[
          'apps','base','blogger','calendar','codesearch','contacts','docs',
          'albums','spreadsheet','youtube'])
    session_token = db.StringProperty(required=True)


class CPediaLog(db.Model):
    title = db.StringProperty(multiline=False, default='Your Blog Title')
    author = db.StringProperty(multiline=False, default='Your Blog Author')
    email = db.StringProperty(multiline=False, default='')
    description = db.StringProperty(default='Blog powered by cpedialog.')
    root_url = db.StringProperty(multiline=False,default='http://cpedialog.appspot.com')
    logo_images = db.ListProperty(db.Category)
    num_post_per_page = db.IntegerProperty(default=8)
    cache_time = db.IntegerProperty(default=0)
    debug = db.BooleanProperty(default = True)
 
    recaptcha_enable = db.BooleanProperty(default = False)
    recaptcha_public_key = db.StringProperty(multiline=False,default='')
    recaptcha_private_key = db.StringProperty(multiline=False,default='')
 
    delicious_enable = db.BooleanProperty(default = True)
    delicious_username = db.StringProperty(multiline=False, default='cpedia')
 
    google_ajax_feed_enable = db.BooleanProperty(default = True)
    google_ajax_feed_key = db.StringProperty(multiline=False,
       default='ABQIAAAAOY_c0tDeN-DKUM-NTZldZhQG0TqTy2vJ9mpRzeM1HVuOe9SdDRSieJccw-q7dBZF5aGxGJ-oZDyf5Q')  #this key only for support from google. It's optional.
    google_ajax_feed_result_num = db.IntegerProperty(default = 10)
    google_ajax_feed_title = db.StringProperty(multiline=False,default='Your feeds')
    
    host_ip = db.StringProperty()
    host_domain = db.StringProperty()
    default = db.BooleanProperty(default = True)
 
    def get_logo_images_list(self):
        '''space delimted list of tags'''
        if not self.logo_images:
            logog_images_ =  ["http://cpedialog.appspot.com/img/logo/logo1.gif",
                    "http://cpedialog.appspot.com/img/logo/logo2.gif"]
            return logog_images_
        else:
            return self.logo_images

    def get_logo_images(self):
        '''space delimted list of tags'''
        if not self.logo_images:
            logog_images_ =  ["http://cpedialog.appspot.com/img/logo/logo1.gif",
                    "http://cpedialog.appspot.com/img/logo/logo2.gif"]
            self.logo_images = [db.Category(logo_image.strip().encode('utf8')) for logo_image in logog_images_]
        return ' '.join([urllib.unquote(logo_image) for logo_image in self.logo_images])

    def set_logo_images(self, logo_images):
        if not logo_images:
            logo_images =  "http://cpedialog.appspot.com/img/logo/logo1.gif http://cpedialog.appspot.com/img/logo/logo2.gif"
        self.logo_images = [db.Category(logo_image.strip().encode('utf8')) for logo_image in logo_images.split(' ')]

    logo_images_space = property(get_logo_images,set_logo_images)



class Album(db.Model):
    album_username = db.StringProperty()
    owner = db.UserProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    access = db.StringProperty(multiline=False,default='public',choices=[
        'public','private','login'])     #public: all can access the album; private:only the owner can access;
                                         #login:login user can access.
    album_type = db.StringProperty(multiline=False,default='public',choices=[
        'public','private'])    #private album need to authorize by user and store the session token.
    order = db.IntegerProperty()
    valid = db.BooleanProperty(default = True)

class Menu(db.Model):
    title = db.StringProperty()
    permalink = db.StringProperty()          
    target = db.StringProperty(multiline=False,default='_self',choices=[
        '_self','_blank','_parent','_top'])
    order = db.IntegerProperty()
    valid = db.BooleanProperty(default = True)

    def full_permalink(self):
        return  '/' + self.permalink


class Images(db.Model):
    uploader = db.UserProperty()
    image = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)


class Greeting(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    user = db.StringProperty()
    author = db.UserProperty()
    content = db.StringProperty()
    valid = db.BooleanProperty(default = True)


class FavouriteSite(db.Model):
    title = db.StringProperty()
    permalink = db.StringProperty()
    target = db.StringProperty(multiline=False,default='_self',choices=[
        '_self','_blank','_parent','_top'])
    order = db.IntegerProperty()
    valid = db.BooleanProperty(default = True)

class Feeds(db.Model):
    title = db.StringProperty()
    feed = db.StringProperty()
    order = db.IntegerProperty()
    valid = db.BooleanProperty(default = True)


class DeliciousPost(object):
    def __init__(self, item):
        self.link = item["u"]
        self.title = item["d"]
        self.description = item.get("n", "")
        self.tags = item["t"]

