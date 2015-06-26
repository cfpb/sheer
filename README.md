# Sheer

Sheer is a tool for [loading arbitrary content](#indexing) into [Elasticsearch](http://www.elasticsearch.org) and [serving that content](#serving) on the web using [Jinja2 templates](http://jinja.pocoo.org/). 

If you're not familiar with Elasticsearch, it is highly recommended that you read the Elasticsearch Definitive Guide's [Finding Your Feet](http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/_finding_your_feet.html).

* [Requirements](#requirements)
* [Installation](#installation)
* [General Usage](#general-usage)
* [Testing](#testing)
* [Quick Start](#quick-start)
* [Indexing](#indexing)
    * [Reindexing](#reindexing)
    * [Partial Indexing](#partial-indexing)
	* [Sheer Index Settings](#sheer-index-settings)
	* [Content Processors](#content-processors)
	* [Mappings](#mappings)
* [Serving](#serving)
	* [Templates](#templates)
		* [Context](#context)
			* [`selected_filters_for_field`](#selected_filters_for_fieldfieldname)
			* [`is_filter_selected`](#is_filter_selectedfieldname-value)
			* [`queries`](#queries)
			* [`more_like_this`](#more_like_thishit)
			* [`get_document`](#get_documentdoctype-docid)
	* [Elasticsearch Lookup URLs](#elasticsearch-lookup-urls)
	* [Blueprints](#blueprints)
	* [Query API](#query-api)
		* [`QueryFinder`](#queryfinder)
		* [`Query`](#query)
		* [`QueryResult`](#queryresult)
		* [`QueryHit`](#queryhit)
- [Licensing](#licensing)


## Requirements

Sheer is a Python application that requires:

- [Elasticsearch](http://www.elasticsearch.org/)
- [Flask](http://flask.pocoo.org/)

Recommended for installing and running Sheer:

- [virtualenv](https://virtualenv.pypa.io/en/latest/)
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.org)

Running tests requires:

- [nose](https://nose.readthedocs.org/en/latest/)
- [mock](http://www.voidspace.org.uk/python/mock/)

## Installation

### Elasticsearch

To run Sheer you will first need to install 
[Elasticsearch](http://www.elasticsearch.org/). This can be acomplished 
a number of ways, many of which are detailed in 
[in the Elasticsearch documentation](http://www.elastic.co/guide/en/elasticsearch/reference/current/setup.html). 
On Mac OS X it can be installed using [Homebrew](http://brew.sh/):

```
brew install elasticsearch
```

There are also [Elasticsearch apt and Yum repositories](http://www.elastic.co/guide/en/elasticsearch/reference/current/setup-repositories.html).

Before running Sheer, you will also need to ensure that Elasticsearch is
running. When installing Elasticsearch on Mac OS X installed via
Homebrew, Homebrew will provide some guidance like:

```shell
To have launchd start elasticsearch at login:
    ln -sfv <homebrew location>/elasticsearch/*.plist ~/Library/LaunchAgents
Then to load elasticsearch now:
    launchctl load ~/Library/LaunchAgents/homebrew.mxcl.elasticsearch.plist
```

### Sheer

To install Sheer itself, it is recommended to create a 
[`virtualenv`](https://virtualenv.pypa.io/en/latest/) using 
[`virtualenvwrapper`](https://virtualenvwrapper.readthedocs.org).

```
mkvirtualenv sheer
workon sheer
```

Then you can clone the Sheer repository and install the Python 
requirements using `pip`:

```shell
git clone https://github.com/cfpb/sheer
pip install -r sheer/requirements.txt
```

You can then install Sheer with `pip`. `pip -e` installs Sheer in
"editable" mode, which means it runs from the path where you've cloned
it, and any changes you `git pull` from upstream won't have to be
installed again.

```shell
pip install -e sheer
```

## General Usage

The `sheer` command takes the following general arguments:

* `-h`: Show help message and exit.
* `--debug`: Print debugging output to the console.
* `--location`: The directory you want to operate on. You can also set
  the `SHEER_LOCATION` environment variable.
* `--elasticsearch ELASTICSEARCH, -e ELASTICSEARCH`: Elasticsearch
  host:port pairs. Seperate hosts with commas. Default is
  `localhost:9200` You can also set the `SHEER_ELASTICSEARCH_HOSTS`
  environment variable.
* `--index INDEX, -i INDEX`: Elasticsearch index name. Default is
  `content`. You can also set the `SHEER_ELASTICSEARCH_INDEX`
  environment variable.

The `sheer` command also takes one of two positional arguments:

* `index`: Load content into Elasticsearch.
* `serve`: Serve content from Elasticsearch using configuration and
  templates at location.

These are covered in more detail below.

## Testing

To run the Sheer tests, you'll need the Python packages 
[nose](https://nose.readthedocs.org/en/latest/) and 
[mock](http://www.voidspace.org.uk/python/mock/) installed. Both can be
installed via `pip`:

```shell
pip install nose mock
```

Both are also installed by the Sheer [`requirements.txt` file](#installation).

To run the tests, simply run:

```shell
nosetest sheer
```

## Quick Start

This quick start assumes you have an existing Sheer site you want to
load content for and serve.

```shell
cd path/to/my/sheer/site
```

Index the site's content in Elasticsearch:

```shell
sheer index
```

Serve the site at [http://localhost:7000](http://localhost:7000):

```shell
sheer serve
```

The site can also be served in "debug" mode:

```shell
sheer serve --debug
```

## Indexing 

```shell
sheer index
```

Sheer indexing allows configurable loading of content into  [Elasticsearch](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/docs-index_.html).

`sheer index` takes the following arguments:

* `--reindex, -r`: Recreate the index and reindex all content.
* `--processors [PROCESSORS [PROCESSORS ...]], -p [PROCESSORS
  [PROCESSORS ...]]`: Content processors to index.

These are covered in more detail below.


Sheer *does not index*:

* `_settings/` 
* `_layouts/` 
* `_queries/` 
* `_defaults/` 
* `_lib/`
* `_tests/`

These are hard-coded in `indexer.py`.

The basic indexing process:

1. Creates the index with the given [settings](#sheer-index-settings) if it does not exist
2. Creates the [mappings](#mappings) for each [content processor](#content-processors) if they do not exist
3. Enumerates the documents to be loaded into Elasticsearch that are yeilded by the [content processor's `documents()` function](#content-processors). If the documents already exist they are updated.

### Reindexing

```shell
sheer index --reindex
```

Destroys the index in Elasticsearch and recreates it, recreating the mappings and reloading all documents.

### Partial Indexing

```shell
sheer index --processors posts
```

Reindex only content provided by the given [content processors](#content-processors). The documents provided by the given processor will be updated in Elasticsearch.

```shell
sheer index --processors posts --reindex
```

This will destroy the [mappings](#mappings) for the given [content processor](#content-processors) and recreate them, then load the documents provided by the given processor into Elasticsearch.

### Sheer Index Settings

Sheer reads settings from `_settings/settings.json`. These settings are passed as a document containing index settings to [`Elasticsearch.create`](https://elasticsearch-py.readthedocs.org/en/master/api.html#elasticsearch.Elasticsearch.create). Existing Sheer sites use this file to configure [Elasticsearch analyzers](http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/analysis-intro.html). 

Analyzers tokenize both document fields during indexing and query strings for searching, that way there is consistency between terms being searched for and terms indexed.

For example:

```json
{
    "settings" : {
        "analysis" : {
            "analyzer" : {
                "my_edge_ngram_analyzer" : {
                    "tokenizer" : "my_edge_ngram_tokenizer"
                }
            },
            "tokenizer" : {
                "my_edge_ngram_tokenizer" : {
                    "type" : "edgeNGram",
                    "min_gram" : "2",
                    "max_gram" : "5",
                    "token_chars": [ "letter", "digit" ]
                }
            }
        }
    }
}
```

This will use Elasticsearch's `edgeNGram` tokenizer (which only keeps n-grams, a sequence of text characters, from the beginning of a token) to build an analyzer

See [Elasticsearch's Configuring Analyzers](http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/configuring-analyzers.html) for more information about configuration.


### Content Processors

Sheer reads Content Processors from `_settings/processors.json`. 

Content Processors are configured with a unique name and a JSON object including at least the following fields:

* `processor`: The name of a Python module within the Sheer site's `_lib` directory.
* `mappings` (*optional*): The mappings file (within the Sheer site directory) for this content.

The `processor` module must provide a `documents` [generator](https://wiki.python.org/moin/Generators) which takes the processor's `name` and the remaining keyword arguments from the JSON object and yields documents suitable for indexing in Elasticsearch. 

```python
def documents(name, **kwargs):
	...
		yield document
```

For example, a content processor might be configured like this in `processors.json`:

```json
{
  "posts": {
    "url": "$WORDPRESS/api/get_posts/",
    "processor": "wordpress_post_processor",
    "mappings": "_settings/posts_mappings.json"
  }
}
```

And may have the following corresponding `_lib/wordpress_post_processor.py`:

```python
def posts_at_url(url):
	"""
	Yield WordPress posts from the given URL
	"""
	...
	
def process_post(post):
	"""
	Process a post for indexing in Elasticsearch
	"""
	...

def documents(name, url, **kwargs):
	"""
	Yield a document for indexing in Elasticsearch
	"""
    for post in posts_at_url(url):
        yield process_post(post)
```

### Mappings

Mappings are described in great detail in the [Elasticsearch mappings documentation](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping.html). Mapping defines the searchable characteristics of a document, such as which fields are searchable and how they're tokenized.

Each [content processor](#content-processor) provides a mappings file path relative to the Sheer site directory. This file contains the `properties` JSON object for the mapping (as described in Elasticsearch's [PUT mapping API reference](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/indices-put-mapping.html)). This is passed directly to Elasticsearch.

For example: 

```json
{ "properties" :
  {
    "title" : {"type" : "string", "store" : "yes"},
    "text" : {"type" : "string", "store" : "yes"},
    "date" : {"type" : "date", "store": "yes"},
    "category" : {"type":"string", "index": "not_analyzed"},
    "author" : {"type":"string", "index":"not_analyzed"},
    "tags" : {"type":"string", "store": "yes", "index":"not_analyzed"},
    "excerpt" : {"type":"string", "store": "yes"},
    "custom_fields": {
            "properties": {
                "display_in_newsroom": {"type":"string", "index":"not_analyzed"}
            }
    }
  }
}
```

A default `_settings/mappings.json`, if it exists, is also passed to Elasticsearch.


## Serving

```shell
sheer serve
```

Sheer can serve the content it indexes in Elasticsearch via command-line in the foreground or via WSGI. Sheer serves its content using a [Flask](http://flask.pocoo.org/) application. 

`sheer serve` takes the following arguments:

* `--port PORT, -p PORT`: Port to run the web server on.
* `--addr ADDR, -a ADDR`: Address to run the web server on.

Sheer does not serve any paths beginning with an underscore. They are considered private.

Sheer will serve the following content in order:

1. `index.html` template from a directory containing it
2. An Elasticsearch document from a [lookup URL](#elasticsearch-lookup-urls) 
3. A [Flask Blueprint](#blueprints)

## Templates

Sheer will serve the `index.html` template from any directory under the site root not beginning with an underscore. So, given a `<site root>/blog/index.html`, Sheer will serve the template at `/blog/` and `/blog/index.html`. Sheer will also redirect `/blog` to `/blog/`.

Sheer always adds two search paths beyond the request directory for [Jinja2 templates](http://jinja.pocoo.org/):

* `_layouts`
* `_includes`

There are no specific rules within Sheer that dictate what templates go in either location, but they provide for some logical separation. These search paths include parent directories up to the root of the site.

### Context

Sheer provides convenient access to  query tools for use in templates using the following context variables:

#### `selected_filters_for_field(fieldname)`

Returns the selected filter values contained in the request query string for a given `fieldname`.

#### `is_filter_selected(fieldname, value)`

Returns whether or not the given filter `value` is selected in the request query string for the given `fieldname`. 

#### `queries`

A [`QueryFinder`](#queryfinder) object for lookup of pre-defined Elasticsearch queries stored as JSON files in `<site_root>/_queries/<query_name>.json`. This context variable exposes the Sheer [query API](#query-api) to templates.

For example, within a [Jinja2 template](http://jinja.pocoo.org/), one might do the following:

```jinja
{% set query = queries.posts %}
{% set posts = query.search(size=10) %}
{%- for post in posts %}
	...
{% endfor %}
```

#### `more_like_this(hit)`

Performs an [Elasticsearch "more like this" (mlt)](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-more-like-this.html) search for documents that are "like" the document described by the given [`QueryHit`](#queryhit) object. 

Returns a [`QueryResult`](#queryresult) object. 

Optionally takes additional keyword arguments corrosponding to the "mlt" parameters [described in the Elasticsearch documentation](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-more-like-this.html).

```jinja
{% set query = queries.posts %}
{% set posts = query.search(size=10) %}
{%- for post in posts %}
	...
    {% for similar in more_like_this(post) %}
    	...
	{% endfor %}
	...
{% endfor %}
```

#### `get_document(doctype, docid)`

Performs an [Elasticsearch "get"](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/docs-get.html) for a document of the given `doctype` with the given `docid`. Returns a single [`QueryHit`](#queryhit) object.

## Elasticsearch Lookup URLS

Lookup URLs in Sheer are URLs at which Elasticsearch lookups will be performed. Lookup URLs are defined in `_settings/lookups.json`. For example:

```json
{
  "post": {
    "url":       "/blog/<id>/",
    "type":      "posts",
    "permalink": true
  },
}
```

This will add a URL pattern where the `<id>` in the URL pattern is the Elasticsearch id of a document of the given `type`. These documents are then templated using either an `index.html` file at their full path (include `<id>`) or the first `_single.html` template that is found in the search path.

In this case, documents in Elasticsearch with the type `posts` will be served at the URL `/blog/<id>` and templated with either:

1. `<site root>/blog/<id>/index.html`
2. `<site root>/blog/_single.html`
3. `<site root>/_single.html`.


## Blueprints

Sheer locals Flask Blueprints from `_settings/blueprints.json`. This a JSON file that includes the Python `package` which contains each blueprint, and the blueprint itself as `module`. 

For example, the following blueprint:

```pyhton
myblueprint = Blueprint("myblueprint", __name__, url_prefix="")
```

Defined in the Python package and module `ablueprint.controllers` would be configured like this:

```json
{
  "myblueprint": {
    "package": "ablueprint.controllers",
    "module":  "myblueprint"
  }
}
```

## Query API

Sheer includes some wrappers around Elasticsearch queries that allow for queries to be pre-defined in JSON files in `<site_root>/_queries/<query_name>.json`, run, and results of those queries to be easily accessed. 

#### `QueryFinder`

`QueryFinder` provides a simple attribute-lookup of [Elasticsearch JSON queries](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl.html) defined in `<site_root>/_queries/<query_name>.json` and will return a [`Query`](#query) object.  

For example, given the following query defined in `<site root>/_queries/posts.json`:

```json
{
  "name": "Blog Posts",
  "query": {
    "doc_type": "posts",
    "size": 10,
    "sort": "date:desc"
  }
}
```

From within the Sheer Flask application:

```python
>>> queries = QueryFinder()
>>> posts_query = queries.posts
```

A [`Query`](#query) object for the archive query is available at `queries.posts`. 

File lookups are done on the fly and a new `Query` instance is created every time the `posts` attribute is accessed. 

#### `Query`

`Query` wraps an [Elasticsearch search](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-search.html) fetched via [`QueryFinder`](#queryfinder).

```python
>>> queries = QueryFinder()
>>> posts_query = queries.posts
>>> posts_results = queries.posts.search(size=10)
```

##### `search(aggregations=None, **kwargs)`

Perform the search with the given keyword arguments, returning a [`QueryResult`](#queryresult) object.

Keyword arguments should be [Elasticsearch request body parameters](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-request-body.html)

If `aggregations` are given, an [Elasticsearch terms aggregation](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html) is used to return counts and possible values for the given fields.

##### `possible_values_for(field, **kwargs)`

Return possible values for the field. This performs a search using [Elasticsearch terms aggregation](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html). Keyword arguments are [Elasticsearch request body parameters](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-request-body.html). 

For example, `possible_values_for('category', doc_type='posts')` would return the counts and existing values of the field `category` on all `posts` documents.

#### `QueryResult`

`QueryResult` objects wrap [Elasticsearch search results](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/_the_search_api.html). `QueryResult` objects are [iterables](https://docs.python.org/2/glossary.html#term-iterable) that yield   [`QueryHit`](#queryhit) objects for each result.

```python
>>> queries = QueryFinder()
>>> posts_query = queries.posts
>>> posts_results = queries.posts.search(size=10)
>>> for result_hit in post_results:
>>>		...
```

`QueryResult` objects provide several properties to aid in pagination of results:

* `total`: the total number of results
* `size`: the number of results included in this query
* `from_`: the number of results skipped in this query
* `pages`: the total number of pages given the above `size`
* `current_page`: the current page given the above `size` and `from_` values

##### `aggregations(fieldname)`

Returns the [terms aggregation](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html) dictionary that resulted from the query for the given `fieldname`.

##### `json_compatible()`

Returns a JSON-compatible (but *not* JSON-encoded) dictionary of the query results, including the above properties and the resulting hits.

##### `url_for_page(pagenum)`

Returns a URL for the given page number within the query.

#### `QueryHit`

A `QueryHit` object is the result of an Elasticsearch query. `QueryHit` objects provide the query result's fields as attributes. Given the following blog post document stored in Elasticsearch:

```json
{  
    "id": 12345,
    "title": "An Example Blog Post",
    "date": "2015-01-11T09:34:40Z",
    "slug": "an-example-blog-post",
    "author": [  
        "Hugh Man"
    ],
    "content": "...",
    "excerpt": "...",
    "category": [  
        "Announcements"
    ]
}
```

Each of the JSON object's properties would be accessible as a `QueryHit` object's attributes:

```python
>>> queries = QueryFinder()
>>> posts_query = queries.posts
>>> posts_results = queries.posts.search(size=10)
>>> for result_hit in post_results:
>>>		print result_hit.title, result_hit.author
```

##### `permalink()`

Returns the permanent link to this Elasticsearch document *if* the type of this query hit (for our blog example, "posts") corropsonds to one of the [lookup URLs](#elasticsearch-lookup-urls) configured in a Sheer site.

##### `json_compatible()`

Returns a JSON-compatible (but *not* JSON-encoded) dictionary of a query hit.


## Licensing 

Public Domain/CC0 1.0

1. [Terms](TERMS.md)
2. [License](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)


