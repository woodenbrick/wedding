import webbrowser
import md5
import urllib
import urllib2
import time
import os
from errorcodes import Lastfm_Api_Error
import xmlparser
#currently implemented in the set_method function:
#user.getrecenttracks
#this may be reimplemented as a class if it becomes too unwieldy

class Lastfm_Stats:
    def __init__(self):
        self.get_values = {'api_key' : '2d21a4ab6f049a413eb27dbf9af10579'}
        self.base_url = "http://ws.audioscrobbler.com/2.0/?"
        self.xml_dir = os.path.join(os.getcwd(), "xml")
        self.create_xml_dir()
    
        
    def set_user(self, user):
        self.get_values['user'] = user
        
    def set_method(self, method, limit=10):
        self.get_values['method'] = method
        self.filename = os.path.join(self.xml_dir, method + '.xml')

    def encode_url_values(self):
        values = urllib.urlencode(self.get_values)
        return values
    
    def create_xml_dir(self):
        try:
            os.mkdir(self.xml_dir)
        except:
            pass
        
    def request_data(self):
        values = self.encode_url_values()
        urllib.urlretrieve(url = self.base_url + values, filename = self.filename)
        
        
    def parse_data(self):
        """Checks that data is correct, deletes otherwise and shows error"""
        parser = xmlparser(self.filename)
        parser.parse()
        
    def add_get_data(self, datadic):
        """Adds any extra get data that may be required"""
        self.get_values.update(datadic)
  
if __name__ == '__main__':
    lastfm = Lastfm_Stats()
    lastfm.set_user('woodenbrick')
    wanted_data = ['user.getrecenttracks', 'artist.getTopAlbums', 'user.getLovedTracks']
    for method in wanted_data:
        lastfm.set_method(method)
        print 'Getting', method
        lastfm.request_data()
        lastfm.parse_data()
        time.sleep(1)
    print 'Complete'
