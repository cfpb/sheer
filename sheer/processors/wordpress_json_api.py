import urllib2
import json

def read_url(url):
    try:
        response = json.loads(urllib2.urlopen(url).read())
        return response['posts']
    except Exception as e:
        print "Exception: %s" % e

    return []
