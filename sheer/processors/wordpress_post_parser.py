import sys
import json
import requests
from string import Template

import dateutil.parser

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
    del post['comments']
    post['_id'] = post['slug']
    # remove fields we're not interested in
    post['categories'] = [cat['slug'] for cat in post['categories']]
    post['tags'] = [tag['slug'] for tag in post['tags']]
    author_template = Template("$first_name $last_name")
    post['author'] = author_template.substitute(**post['author'])
    dt = dateutil.parser.parse(post['date'])
    dt_string = dt.strftime('%Y-%m-%d %H:%M:%S')
    post['date'] = dt_string
    return post
