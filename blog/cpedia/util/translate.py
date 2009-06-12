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


"""
translate.py

Translates strings using Google Translate

All input and output is in unicode.
"""

__all__ = ('source_languages', 'target_languages', 'translate')

import sys
import urllib
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup

def translate(sl, tl, text):

    assert type(text) == type(u''), "Expects input to be unicode."

    # Do a POST to google

    # I suspect "ie" to be Input Encoding.
    # I have no idea what "hl" is.

    translated_page = urlfetch.fetch(
        url="http://translate.google.com/translate_t?" + urllib.urlencode({'sl': sl, 'tl': tl}),
        payload=urllib.urlencode({'hl': 'en',
                               'ie': 'UTF8',
                               'text': text.encode('utf-8'),
                               'sl': sl, 'tl': tl}),
        method=urlfetch.POST,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    if translated_page.status_code == 200:
        translated_soup = BeautifulSoup(translated_page.content)
        return translated_soup('div', id='result_box')[0].string
    else:
        return ""
