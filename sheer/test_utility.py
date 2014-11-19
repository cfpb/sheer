from .utility import build_search_path, parse_es_host_port_pair, parse_es_hosts


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
        paths = build_search_path(
            '/var/sheer', '/my/site/is/cool/foo.html', append='_layouts', include_start_directory=False)
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

    def test_parse_host_port_pair(self):
        pairs = ["localhost", "localhost:9200", ":9200"]
        for p in pairs:
            result = parse_es_host_port_pair(p)
            assert(result.get('host') == 'localhost')
            assert(result.get('port') == 9200)

    def test_parse_es_hosts(self):
        packed_hosts = "ringo,foo:777,:9000"
        parsed = parse_es_hosts(packed_hosts)
        expected_hosts = ["ringo", "foo", "localhost"]
        expected_ports = [9200, 777, 9000]
        for result, host, port in zip(parsed, expected_hosts, expected_ports):
            assert(result['host'] == host)
            assert(result['port'] == port)
