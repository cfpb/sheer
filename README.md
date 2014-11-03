Sheer
===================

Sheer provides:

- Tools for loading arbitrary content into elasticsearch
- A WSGI server for mixing that content with Jinja2 templates 

Additionally, we hope to provide
- scripts for pre-generating HTML from said configuration and elasticsearch data.
- A full-featured REST API
- Tools for building elasticsearch "mappings" for your data

The best place to start is with a demo site. Here's one:
https://github.com/rosskarchner/itspecialists

Sheer is a Python/Flask application. It requires Elastic Search.

Why Sheer? Why not Jekyll?
---------

Jekyll is pretty darn compelling, for a number of reasons:

- Ease of management
- Ease of breaking out of the CMS (the "snowfall" problem)
- Serving static files is fast
- Bring your own version control
- On the whole, less mysterious than CMS's.

We want those advantages, but we don't want to have to anticipate every way our editorial team might wish to slice and serve content. 
We don't want to have to anticipate what developers will want to do with our API, or which content third party publishers will want to syndicate on their site
, or which collection of content people will want to subscribe to with RSS. 
We want to pre-generate (Jekyll-style) the common pages, without precluding the stuff we haven't thought of yet.

Our hypothesis is that we can combine some of Jekyll's ideas with a full-featured search engine, and get something powerful, flexible, productive, and fun.

Installation
------------

To get started with Sheer:

Install [Elasticsearch](http://www.elasticsearch.org/) however you'd like. (we use [homebrew](http://brew.sh/))::

```
$ brew install elasticsearch
```

Check out the sheer Github project:
```
$ git clone https://github.com/cfpb/sheer.git
```

create a virtualenv for sheer:
```
$ mkvirtualenv sheer
```

The new virtualenv will activate right away. to activate it later on (say, in a new terminal session) use the command "workon sheer"

Install sheer into the virtualenv with the -e flag (which allows you to make changes to sheer itself):

```
$ pip install -e ~/path/to/sheer
```

Install sheer's python requirements:

```
$ pip install -r ~/path/to/sheer/requirements.txt
```

You should now be able to run the sheer command:
```
$ sheer

usage: sheer [-h] [--debug] {inspect,index,serve} ...
sheer: error: too few arguments
```

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
