Sheer
===================

Sheer will contain:

- tools for loading appropriately structured, on-disk content (HTML and Markdown, with Jekyll-style metadata) into elasticsearch
- a web server that combines on-disk configuration and templates with data in elasticsearch
- scripts for pre-generating HTML from said configuration and elasticsearch data.

Why Sheer? Why not Jekyll?
---------

Jekyll is pretty darn compelling, for a number of reasons:

- Ease of management
- Ease of breaking out of the CMS (the "snowfall" problem)
- Serving static files is fast
- Bring your own version control
- On the whole, less mysterious than CMS's.

We want those advantages, but we also dont' want to have to anticipate every way our editorial team might wish to slice and serve content. 
We don't want to have to anticipate what developers will want to do with our API, or which content third party publishers will want to syndicate on their site
, or which collection of content people will want to subscribe to with RSS. 
We want to pre-generate (Jekyll-style) the common pages, without precluding the stuff we haven't thought of yet.

Our hypothesis is that we can get the benefits of Jekyll and all the flexibility we want by building sites around a full-featured search engine (like elasticsearch).
