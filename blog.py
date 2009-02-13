# !/usr/bin/env python
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

import cgi
import wsgiref.handlers
import os
import re
import datetime
import calendar
import logging
import string
import urllib

from xml.etree import ElementTree

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext import search

from cpedia.pagination.GqlQueryPaginator import GqlQueryPaginator,GqlPage
from cpedia.pagination.paginator import InvalidPage,Paginator
from cpedia.util import translate

from model import Song
import model
from model import Archive,Weblog,WeblogReactions
import authorized
import view
import util

from recaptcha.client import captcha

class BaseRequestHandler(webapp.RequestHandler):
  """Supplies a common template generation function.

  When you call generate(), we augment the template variables supplied with
  the current user in the 'user' variable and the current webapp request
  in the 'request' variable.
  """
  def generate(self, template_name, template_values={}):
    values = {
      'archiveList': util.getArchiveList(),
    }
    values.update(template_values)
    directory = os.path.dirname(__file__)
    view.ViewPage(cache_time=0).render(self, template_name,values)


class NotFoundHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        view.ViewPage(cache_time=36000).render(self)

class UnauthorizedHandler(webapp.RequestHandler):
    def get(self):
        self.error(403)
        view.ViewPage(cache_time=36000).render(self)
        
class MainPage(BaseRequestHandler):
  def get(self):
    pageStr = self.request.get('page')
    if pageStr:
        page = int(pageStr)
    else:
        page = 1;

    #get blog pagination from cache.
    obj_page = util.getBlogPagination(page)
    if obj_page is None:
        self.redirect('/')

    recentReactions = util.getRecentReactions()
    template_values = {
      'page':obj_page,
      'recentReactions':recentReactions,
      }
    self.generate('blog_main.html',template_values)

class PageHandle(BaseRequestHandler):
  def get(self,pagenum):
    page = int(pagenum)
    #get blog pagination from cache.
    obj_page = util.getBlogPagination(page)
    if obj_page is None:
        self.redirect('/')

    recentReactions = util.getRecentReactions()
    template_values = {
      'page':obj_page,
      'recentReactions':recentReactions,
      }
    self.generate('blog_main.html',template_values)

def SendMail(email='wodemoneke@gmail.com', subject='changes', body=''):
  """global function that will send email to me on certain events"""
  from google.appengine.api import mail
  body += """\n danborywedding"""
  mail.send_mail(sender='wodemoneke@gmail.com', to=email, subject=subject,
                 body=body)
  
class BridesMaidComment(BaseRequestHandler):
  def post(self):
    name = self.request.get('name')
    if name == '':
      name = 'Anonymous'
    comment = self.request.get('comment')
    if comment is not None:
      new_comment = model.BridesMaidComment(name=name, comment=comment)
      new_comment.put()
      memcache.delete("comment")
      SendMail(subject="New email from %s" % name, body="""%s left this comment:\n
               %s""" % (name, comment))
    self.redirect('/albums/boryana.daniel.wedding/BridesmaidDresses')

class UploadDress(BaseRequestHandler):
  """For uploading new images"""
  def get(self):
    self.generate('upload_dress.html')
  
  def post(self):
    import gdata.photos.service
    import gdata.media
    import gdata.geo
    import time
    filename = str(self.request.get('photo'))
    gd_client = gdata.photos.service.PhotosService()
    gd_client.email = 'boryana.daniel.wedding@gmail.com'
    gd_client.password = 'FReNZaL18'
    gd_client.source = 'danielboryanawedding'
    gd_client.ProgrammaticLogin()
    bridesmaid_dresses_id = "5292600333161189617"
    
    new_photo = model.NewPhoto()
    new_photo.photo = db.Blob(open(filename).read())
    new_photo.put()
    self.response.headers['content'] = 'image/jpeg'

    self.response.out.write(new_photo.photo)
    #album_url = '/data/feed/api/user/%s/albumid/%s' % ('default', bridesmaid_dresses_id)
    #photo = gd_client.InsertPhotoSimple(album_url, time.time(),
    #                                    'Uploaded using the API', new_photo.photo,
    #                                    content_type='image/jpeg')
    
    
    #self.redirect('/admin_upload_dress')


class BridesMaidVote(BaseRequestHandler):
  def post(self):
    voter = self.request.get('voter')
    vote = self.request.get('vote')
    url = self.request.get('photo_url')

    new_vote = model.BridesMaidVotes.all().filter('voter =', voter).filter('photo_url', url).get()    
    new_avg = model.BridesMaidRating.all().filter('photo_url', url).get()
    
    if new_vote is None:
      new_vote = model.BridesMaidVotes()
      new_vote.photo_url = url    
    new_vote.voter = voter
    new_vote.vote = int(vote)
    new_vote.put()
    
    if new_avg is None:
      new_avg = model.BridesMaidRating()
      new_avg.photo_url = url
      new_avg.rating = vote
      new_avg.put()
    else:
      num_votes = model.BridesMaidVotes.all().filter('photo_url', url)
      vot = 0.0
      t = 0.0
      for n in num_votes:
        self.response.out.write(str(n.vote))
        vot +=1
        t += n.vote
      
      new_avg.rating = str(round(t / vot, 2))
      new_avg.put()
    
    #redo the rankings
    photos = model.BridesMaidRating.all().order('-rating')
    #rank = 1
    #old_rating = None
    #for photo in photos:
    #  photo.current_rank = rank
    #  photo.put()
    #  if not old_rating == photo.rating:
    #    rank += 1
    #  old_rating = photo.rating

    old_rating = None
    rank = 0
    counter = 1
    for photo in photos:
      if float(photo.rating) == old_rating:
        counter += 1
      else:
        old_rating = float(photo.rating)
        rank += counter
        counter = 1
      photo.current_rank = rank
      photo.put()

    #delete the memcache
    memcache.delete("current_votes")
    memcache.delete("rating")
    last_voter = memcache.set("last_voter", voter)
    self.redirect('/albums/boryana.daniel.wedding/BridesmaidDresses')

class FullMusicList(BaseRequestHandler):
  def get(self):
    full_list = memcache.get("songs_full_list")
    if full_list is None:
      full_list = Song.all().order('artist')
    template_values = {'songs' : full_list}
    self.generate('full_music_list.html', template_values)

class MusicRequest(BaseRequestHandler):
  def get(self):
    # IMPLEMENT MEMCACHE HERE
    songlist = memcache.get("songs")
    ip = self.request.remote_addr
    previous_user = memcache.get(ip)
    if previous_user is None:
      previous_user = model.SongRequester.all().filter('ip=', ip).get()
    if songlist is None:
      songs = Song.all().order('-date')
      songlist = songs.fetch(20)
      memcache.add("songs", songlist)
    template_values = {'songs' : songlist, 'heading' : 'Song Request', 'previous_user' : previous_user}
    if self.request.get('error') == '1':
      template_values['error'] = 'At the very least, I need the title of the song, or an artist.'
    self.generate('music.html', template_values)
    
class NewMusicRequest(BaseRequestHandler):
  def post(self):
    artist = cgi.escape(self.request.get('artist'))
    title = cgi.escape(self.request.get('title'))
    requested_by = cgi.escape(self.request.get('requested_by'))
    ip = self.request.remote_addr
    old_user = memcache.get(ip)
    if old_user is None:
      new_user = model.SongRequester(ip=ip, username=requested_by)
      new_user.put()
      memcache.set(ip, new_user)
    elif old_user != requested_by:
      previous_user = model.SongRequester.all().filter('ip = ', ip).get()
      previous_user.username = requested_by
      previous_user.put()
      memcache.set(ip, previous_user)
     
    if title == '' and artist == '':
      self.redirect('/musicrequest?error=1')
    else:
      #lets check last.fm for this song
      search_lastfm = True
      if title == '':
        title = 'Any song'
        search_lastfm = False
      elif artist == '':
        artist = 'Unknown artist'
      if requested_by == '':
        requested_by = 'Anonymous'
        search_lastfm = False
      #if search_lastfm:
      #  song_url = self.get_song_url(title, artist)
      song = Song(artist=artist, title=title, requested_by = requested_by)#, url=song_url)
      song.put()
      memcache.delete("songs")
      self.redirect('/musicrequest')
      
  def get_song_url(self, title, artist):
    import BeautifulSoup
    import urllib
    import urllib2
    from google.appengine.api import urlfetch
    root_url = "http://ws.audioscrobbler.com/2.0/?"
    url_data = {'method' : 'track.search',
                'track' : title,
                'api_key' : '2d21a4ab6f049a413eb27dbf9af10579', 'artist' : artist}
    encoded_data = urllib.urlencode(url_data)
    search = root_url + encoded_data
    url = urlfetch.fetch(search)
    
    print url.content
    
    #handler = urlfetch.fetch(url=root_url, payload=url_data,
    #                         method = urlfetch.GET)
    handle = urllib.urlopen(root_url)
    #print handler.status_code
    #if handler.status_code == 200:
    if True:
      wanted = ['url']
      parser = xmlparser.XML_Parser(handler, wanted)
      parser.run_iterator()
      url = parser.collected[0]
      return url
    
class ClearMusic(BaseRequestHandler):
  def get(self):
    #the only purpose of this is to clear all music
    #should be disabled except when debugging
    songs = Song.all()
    for song in songs:
      song.delete()
    self.redirect('/musicrequest')
    
class AddBlog(BaseRequestHandler):
  @authorized.role("admin")
  def get(self,entrytype):
    template_values = {
      'entrytype': entrytype,
      'action': "addBlog",
      }
    self.generate('blog_add.html',template_values)

  @authorized.role("admin")
  def post(self,entrytype):
    preview = self.request.get('preview')
    submitted = self.request.get('submitted')
    user = users.get_current_user()
    blog = Weblog()
    blog.title = self.request.get('title_input')
    blog.content = self.request.get('text_input')
    blog.author = user
    blog.authorEmail = user.email()
    blog.tags_commas = self.request.get('tags')
    if entrytype == 'page':
        blog.entrytype = entrytype
    template_values = {
      'entrytype': entrytype,
      'blog': blog,
      'preview': preview,
      'submitted': submitted,
      'action': "addBlog",
      'tags': self.request.get('tags'),
      }
    if preview == '1' and submitted !='1':
        self.generate('blog_add.html',template_values)
    else:
      if submitted =='1':
        try:
            permalink =  util.get_permalink(blog.date,translate.translate('zh-CN','en', util.u(blog.title,'utf-8')))
            if not permalink:
                raise Exception
        except Exception:
            template_values.update({'error':'Generate permanent link for blog error, please retry it.'})
            self.generate('blog_add.html',template_values)
            return
        #check the permalink duplication problem.
        maxpermalinkBlog = db.GqlQuery("select * from Weblog where permalink >= :1 and permalink < :2 order by permalink desc",permalink, permalink+u"\xEF\xBF\xBD").get()
        if maxpermalinkBlog is not None:
            permalink = maxpermalinkBlog.permalink+"1"
        blog.permalink =  permalink
        blog.save()
        util.flushBlogMonthCache(blog)
        util.flushBlogPagesCache()
        util.flushTagList()
        self.redirect('/'+blog.relative_permalink())

class EditBlog(BaseRequestHandler):
    @authorized.role("admin")
    def get(self,entrytype,blogId):
        blog = Weblog.get_by_id(int(blogId))
        template_values = {
        'blog': blog,
        'action': "editBlog",
        }
        self.generate('blog_add.html',template_values)

    @authorized.role("admin")
    def post(self,entrytype,blogId):
        blog= Weblog.get_by_id(int(blogId))
        if(blog is None):
            self.redirect('/')
        if blog.entrytype == 'page':
            blog.permalink = self.request.get('permalink') 
        blog.title = self.request.get('title_input')
        blog.content = self.request.get('text_input')
        blog.tags_commas = self.request.get('tags')
        user = users.get_current_user()
        blog.lastModifiedDate = datetime.datetime.now()
        blog.lastModifiedBy = user
        blog.update()
        util.flushBlogMonthCache(blog)
        util.flushBlogPagesCache()
        self.redirect('/'+blog.relative_permalink())

class DeleteBlog(BaseRequestHandler):
  @authorized.role("admin")
  def get(self,entrytype,blogId):
      blog = Weblog.get_by_id(int(blogId))
      template_values = {
      'blog': blog,
      'action': "deleteBlog",
      }
      self.generate('blog_delete.html',template_values)

  @authorized.role("admin")
  def post(self,entrytype,blogId):
    blog= Weblog.get_by_id(int(blogId))
    if(blog is not None):
        blogReactions = blog.weblogreactions_set
        for reaction in blogReactions:
            reaction.delete()
        blog.delete()
        util.flushBlogMonthCache(blog)
        util.flushBlogPagesCache()
    self.redirect('/')

class AddBlogReaction(BaseRequestHandler):
  def post(self):
    blogId_ = self.request.get('blogId')
    blog= Weblog.get_by_id(int(blogId_))
    if(blog is None):
      self.redirect('/')
    blogReaction = WeblogReactions()
    blogReaction.weblog = blog
    blogReaction.content = self.request.get('text_input')
    blogReaction.authorWebsite = self.request.get('website')
    blogReaction.authorEmail = self.request.get('mail')
    blogReaction.user = self.request.get('name_input')

    cpedialog = util.getCPedialog()
    clientIp = self.request.remote_addr
    if(cpedialog.recaptcha_enable):
        challenge = self.request.get('recaptcha_challenge_field')
        response  = self.request.get('recaptcha_response_field')
        cResponse = captcha.submit(
                       challenge,
                       response,
                       cpedialog.recaptcha_private_key,
                       clientIp)
        if not cResponse.is_valid:
            captchahtml = None
            captchahtml = captcha.displayhtml(
                    public_key = cpedialog.recaptcha_public_key,
                    use_ssl = False,
                    error = cResponse.error_code)
            reactions = db.GqlQuery("select * from WeblogReactions where weblog =:1  order by date", blog)
            template_values = {
              'blog': blog,
              'reactions': reactions,
              'blogReaction': blogReaction,
              'captchahtml': captchahtml,
              }
            self.generate('blog_view.html',template_values)
            return True

    user = users.get_current_user()
    if user is not None:
        blogReaction.author = user
        blogReaction.authorEmail = str(user.email())
        blogReaction.user = str(user.nickname())
    blogReaction.userIp = clientIp
    blogReaction.save()
    util.flushRecentReactions()
    self.redirect('/'+blog.relative_permalink())

class EditBlogReaction(BaseRequestHandler):
    @authorized.role("user")
    def get(self,reactionId):
        blogReaction = WeblogReactions.get_by_id(int(reactionId))
        template_values = {
        'blogReaction': blogReaction,
        'action': "editBlogReaction",
        }
        self.generate('blog_add.html',template_values)

    @authorized.role("user")
    def post(self,reactionId):
        blogReaction= WeblogReactions.get_by_id(int(reactionId))
        if(blogReaction is None):
            self.redirect('/')
        blogReaction.content = self.request.get('text_input')
        blogReaction.authorWebsite = self.request.get('website')
        user = users.get_current_user()
        if user is not None:
            blogReaction.lastModifiedBy = user
            blogReaction.authorEmail = str(user.email())
            blogReaction.user = str(user.nickname())
        else:
            blogReaction.authorEmail = self.request.get('mail')
            blogReaction.user = self.request.get('name_input')
        blogReaction.lastModifiedDate = datetime.datetime.now()
        blogReaction.put()
        self.redirect('/'+blogReaction.weblog.relative_permalink())


class DeleteBlogReaction(BaseRequestHandler):
  @authorized.role("admin")
  def get(self,reactionId):
      blogReaction = WeblogReactions.get_by_id(int(reactionId))
      template_values = {
      'reaction': blogReaction,
      'action': "deleteBlogReaction",
      }
      self.generate('blog_delete.html',template_values)

  @authorized.role("admin")
  def post(self,reactionId):
    blogReaction= WeblogReactions.get_by_id(int(reactionId))
    if(blogReaction is not None):
        db.delete(blogReaction)
        util.flushRecentReactions()
    self.redirect('/'+blogReaction.weblog.relative_permalink())


class ArchiveHandler(BaseRequestHandler):
    def get(self, monthyear):
        #get blogs in month from cache.        
        blogs = util.getArchiveBlog(monthyear)
        recentReactions = util.getRecentReactions()
        template_values = {
          'blogs':blogs,
          'recentReactions':recentReactions,
          }
        self.generate('blog_main_month.html',template_values)


class ArticleHandler(BaseRequestHandler):
    def get(self,year,month, perm_stem):
        #for recaptcha.
        captchahtml = None
        cpedialog = util.getCPedialog()
        if(cpedialog.recaptcha_enable):
            captchahtml = captcha.displayhtml(
            public_key = cpedialog.recaptcha_public_key,
            use_ssl = False,
            error = None)
        blog = db.Query(Weblog).filter('permalink =',perm_stem).get()
        if(blog is None):
            self.redirect('/')
        reactions = db.GqlQuery("select * from WeblogReactions where weblog =:1  order by date", blog)
        template_values = {
          'blog': blog,
          'reactions': reactions,
          'captchahtml': captchahtml,
          }
        self.generate('blog_view.html',template_values)

class PageHandler(BaseRequestHandler):
    def get(self,perm_stem):
        blog = db.Query(Weblog).filter('permalink =',perm_stem).get()
        if(blog is None):
            self.redirect('/')
        reactions = db.GqlQuery("select * from WeblogReactions where weblog =:1  order by date", blog)
        template_values = {
          'blog': blog,
          'reactions': reactions,
          }
        self.generate('blog_view.html',template_values)

class SiteMapHandler(BaseRequestHandler):    #for live.com SEO
    def get(self):
        blogs = Weblog.all().order('-date')
        template_values = {
          'allblogs': blogs,
          }
        self.generate('site_map.html',template_values)


class TagHandler(BaseRequestHandler):
    def get(self, encoded_tag):
        #tag =  re.sub('(%25|%)(\d\d)', lambda cmatch: chr(string.atoi(cmatch.group(2), 16)), encoded_tag)   # No urllib.unquote in AppEngine?
        #tag =  urllib.unquote(encoded_tag.encode('utf8'))
        tag = encoded_tag
        blogs = Weblog.all().filter('tags', tag).order('-date')
        recentReactions = util.getRecentReactions()
        template_values = {
          'blogs':blogs,
          'tag':tag,
          'recentReactions':recentReactions,
          }
        self.generate('tag.html',template_values)


class DeliciousHandler(BaseRequestHandler):
    def get(self, encoded_tag):
        tag =  urllib.unquote(encoded_tag)
        cpedialog = util.getCPedialog()
        posts = util.getDeliciousPost(cpedialog.delicious_username,tag)
        recentReactions = util.getRecentReactions()
        template_values = {
          'posts':posts,
          'tag':tag,
          'recentReactions':recentReactions,
          }
        self.generate('tag_delicious.html',template_values)


class FeedHandler(BaseRequestHandler):
    def get(self,tags=None):
        blogs = Weblog.all().filter('entrytype =','post').order('-date').fetch(10)
        last_updated = datetime.datetime.now()
        if blogs and blogs[0]:
            last_updated = blogs[0].date
            last_updated = last_updated.strftime("%Y-%m-%dT%H:%M:%SZ")
        for blog in blogs:
            blog.formatted_date = blog.date.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.generate('atom.xml',{'blogs':blogs,'last_updated':last_updated})
    

class SearchHandler(BaseRequestHandler):
    def get(self,search_term):
        pageStr = self.request.get('page')
        if pageStr:
            page = int(pageStr)
        else:
            page = 1;
        #search_term = self.request.get("q")
        #query = search.SearchableQuery('Weblog')
        #query.Search(search_term)
        #result = query.Run()
        query = db.Query(Weblog).filter('tags =', search_term).order('-date')
        try:
            cpedialog = util.getCPedialog()
            obj_page  =  Paginator(query,1000)
        except InvalidPage:
            self.redirect('/')

        recentReactions = util.getRecentReactions()
        template_values = {
          'search_term':search_term,
          'page':obj_page,
          'recentReactions':recentReactions,
          }
        self.generate('blog_main.html',template_values)
