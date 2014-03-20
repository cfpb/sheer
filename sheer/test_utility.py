from .utility import build_search_path_for_request, build_search_path


class testSearchpaths:
    def test_simple_searchpath(self):
        paths = build_search_path('/var/sheer', '/my/site/is/cool/index.html')
        assert('/var/sheer/my/site/is/cool/' in paths)
        assert('/var/sheer/my/site/is/' in paths)
        assert('/var/sheer/my/site/' in paths)
        assert('/var/sheer/my/' in paths)
        assert('/var/sheer/' in paths)
        assert('/var/' not in paths)

    def test_searchpath_with_append(self):
        paths = build_search_path('/var/sheer', '/my/site/is/cool/foo.html', append='_layouts')
        assert('/var/sheer/my/site/_layouts' in paths)
        assert('/var/sheer/my/_layouts' in paths)
        assert('/var/sheer/_layouts' in paths)
        assert('/var/_layouts' not in paths)
        assert paths[0] == '/var/sheer/my/site/is/cool/_layouts'

    def test_searchpath_with_append_including_start(self):
        paths = build_search_path('/var/sheer',
                                  '/my/site/is/cool/foo.html',
                                   append='_layouts',
                                   include_start_directory=True)

        assert('/var/sheer/my/site/is/cool/_layouts' in paths)
        assert('/var/sheer/my/site/_layouts' in paths)
        assert('/var/sheer/my/_layouts' in paths)
        assert('/var/sheer/_layouts' in paths)
        assert('/var/_layouts' not in paths)
        assert paths[0] == '/var/sheer/my/site/is/cool/'
