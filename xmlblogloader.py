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


from google.appengine.api import urlfetch
from xml.etree import ElementTree

WEATHER_URL = 'http://xml.weather.yahoo.com/forecastrss?p=%s'
WEATHER_NS = 'http://xml.weather.yahoo.com/ns/rss/1.0'


def parse( url ) :
   result = urlfetch.fetch(url)
   if result.status_code == 200:
           parser = ElementTree.XMLTreeBuilder()
           parser.feed(result.content)
           return parser.close()


def weather_for_zip(zip_code):
    url = WEATHER_URL % zip_code
    rss = parse(url)
    forecasts = []
    for element in rss.findall('channel/item/{%s}forecast' %WEATHER_NS):
        forecasts.append({
            'date': element.get('date'),
            'low': element.get('low'),
            'high': element.get('high'),
            'condition': element.get('text')
        })
    ycondition = rss.find('channel/item/{%s}condition' % WEATHER_NS)
    return {
        'current_condition': ycondition.get('text'),
        'current_temp': ycondition.get('temp'),
        'forecasts': forecasts,
        'title': rss.findtext('channel/title')
    }


#print 'Content-Type: text/plain'
#print ''
#print weather_for_zip('94089')



def get_blog_list(xmlfile):
    root = ElementTree.parse(xmlfile).getroot()
    bloglist = []
    for element in root.findall('weblog'):
        bloglist.append({
            'id': element.findtext('id'),
            'title': element.findtext('title'),
            'text': element.findtext('text'),
            'date': element.findtext('date')
        })
    return bloglist

def get_blog_reaction_list(xmlfile):
    root = ElementTree.parse(xmlfile).getroot()
    reactionlist = []
    for element in root.findall('weblog_reactions'):
        reactionlist.append({
            'id': element.findtext('weblog'),
            'user': element.findtext('user'),
            'text': element.findtext('text'),
            'ip': element.findtext('ip'),
            'date': element.findtext('date')
        })
    return reactionlist

