Sheer
===================

Sheer will contain:

- Tools for loading arbitrary content into elasticsearch
- A WSGI server for mixing that content with Jinja2 templates
- scripts for pre-generating HTML from said configuration and elasticsearch data.

Why Sheer? Why not Jekyll?
---------

Jekyll is pretty darn compelling, for a number of reasons:

- Ease of management
- Ease of breaking out of the CMS (the "snowfall" problem)
- Serving static files is fast
- Bring your own version control
- On the whole, less mysterious than CMS's.

We want those advantages, but we dont' want to have to anticipate every way our editorial team might wish to slice and serve content. 
We don't want to have to anticipate what developers will want to do with our API, or which content third party publishers will want to syndicate on their site
, or which collection of content people will want to subscribe to with RSS. 
We want to pre-generate (Jekyll-style) the common pages, without precluding the stuff we haven't thought of yet.

Our hypothesis is that we can combine some of Jekyll's ideas with a full-featured search engine, and get something powerful, flexible, productive, and fun.

Status
------------

Parts of it work!

sheer index -l *directory* will pull a sites content into Elasticsearch

sheer serve -l *directory* launches the web server

With both commands, you can ommit the -l option to act on the current directory.

Usage
--------------

```
sheer --help
usage: sheer [-h] [--debug] [--location LOCATION]
             [--elasticsearch ELASTICSEARCH] [--index INDEX]
             {index,serve} ...

document loader and dev server for Sheer, a content publishing system

positional arguments:
  {index,serve}
    index               load content into Elasticsearch
    serve               serve content from elasticsearch, using configuration
                        and templates at location

optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging output to the console
  --location LOCATION, -l LOCATION
                        Directory you want to operate on. You can also set the
                        SHEER_LOCATION environment variable.
  --elasticsearch ELASTICSEARCH, -e ELASTICSEARCH
                        elasticsearch host:port pairs. Seperate hosts with
                        commas. Default is localhost:9200. You can also set
                        the SHEER_ELASTICSEARCH_HOSTS environment variable.
  --index INDEX, -i INDEX
                        elasticsearch index name. Default is 'content'. You
                        can also set the SHEER_ELASTICSEARCH_INDEX environment
                        variable.
```
