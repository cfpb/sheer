import sys
import json
import requests

def posts_at_url(url):
    
    current_page = 1
    max_page = sys.maxint

    while current_page <= max_page:

        resp = requests.get(url, params={'json':1,'page':current_page})
        results = json.loads(resp.content) 
        current_page += 1
        max_page = results['pages']
        for p in results['posts']:
            yield p
     


def documents(name, url):
    
    for post in posts_at_url(url):
        yield process_post(post)

def process_post(post):
    post['_id'] = post['slug']
    # remove fields we're not interested in
    for cat in post['categories']:
        del cat['id']
        del cat['parent']
        del cat['post_count']
    del post['author']['id']
    del post['id']
    return post
