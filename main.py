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

import wsgiref.handlers

from google.appengine.ext import webapp

import rpc
import blog
import album
import admin
import logging
import util

from google.appengine.ext.webapp import template
template.register_template_library('cpedia.filter.replace')
template.register_template_library('cpedia.filter.gravatar')


def main():
    cpedialog = util.getCPedialog()
    application = webapp.WSGIApplication(
                                       [
                                        ('/create/(blog|page)/*$', blog.AddBlog),
                                        ('/addBlogReaction', blog.AddBlogReaction),
                                        ('/edit/(blog|page)/(.*)/*$', blog.EditBlog),
                                        ('/delete/(blog|page)/(.*)/*$', blog.DeleteBlog),
                                        ('/edit/comment/(.*)/*$', blog.EditBlogReaction),
                                        ('/delete/comment/(.*)/*$', blog.DeleteBlogReaction),

                                        ('/admin/*$', admin.MainPage),
                                        ('/admin/system/*$', admin.AdminSystemPage),
                                        ('/admin/authsub/*$', admin.AdminAuthsubPage),
                                        ('/admin/cache/*$', admin.AdminCachePage),
                                        ('/admin/pages/*$', admin.AdminPagesPage),
                                        ('/admin/albums/*$', admin.AdminAlbumsPage),
                                        ('/admin/feeds/*$', admin.AdminFeedsPage),
                                        ('/admin/images/*$', admin.AdminImagesPage),
                                        ('/admin/tags/*$', admin.AdminTagsPage),
                                        ('/admin/archives/*$', admin.AdminArchivesPage),

                                        ('/rpc', rpc.RPCHandler),
                                        ('/rpc/uploadImage', rpc.UploadImage),
                                        ('/rpc/img', rpc.Image),

                                        ('/*$', blog.MainPage),
                                        ('/page/(\d*)/*$', blog.PageHandle),
                                        ('/403.html', blog.UnauthorizedHandler),
                                        ('/404.html', blog.NotFoundHandler),
                                        ('/archive/(.*)/*$', blog.ArchiveHandler),
                                        ('/([12]\d\d\d)/(\d|[01]\d)/([-\w]+)/*$', blog.ArticleHandler),
                                        ('/search/(.*)/*$', blog.SearchHandler),
                                        ('/tag/(.*)', blog.TagHandler),
                                        ('/delicious/(.*)', blog.DeliciousHandler),
                                        ('/atom/*$', blog.FeedHandler),
                                        ('/sitemap/*$', blog.SiteMapHandler),  #for live.com SEO

                                        ('/albums/*$', album.MainPage),
                                        ('/albums/([-\w\.]+)/*$', album.UserHandler),
                                        ('/albums/([-\w\.]+)/private/*$', album.UserPrivateHandler),
                                        ('/albums/([-\w\.]+)/([-\w]+)/*$', album.AlbumHandler),
                                        ('/albums/([-\w\.]+)/([-\w]+)/([\d]+)/*$', album.PhotoHandler),

                                        ('/([-\w]+)/*$', blog.PageHandler),                                        
                                       ],
                                       debug=cpedialog.debug)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
