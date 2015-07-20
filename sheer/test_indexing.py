# -*- coding: utf-8 -*-

import sys
import mock
from StringIO import StringIO
from .indexer import ContentProcessor, index_location
from elasticsearch.exceptions import TransportError


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class TestIndexing(object):
    """
    Test Sheer content indexing.
    """

    def setup(self):
        # Sheer indexing tries to load three JSON files. For testing purposes,
        # `settings.json` and `mappings.json` are not necessary, but we do need
        # a content processor to test with. The contents of `processors.json` is
        # mocked here.
        self.mock_processors = {'posts':
            {'url': 'http://test/api/get_posts/',
             'processor': 'post_processor',
             'mappings': '_settings/posts_mappings.json'}}
        self.mock_processor_mappings = '''{}'''
        self.mock_document = {
            '_id': u'a-great-post-slug',
            '_index': 'content',
            '_type': 'posts'
        }

        self.config = {'location': '.',
                       'elasticsearch': None,
                       'index': 'content'}

        # This is our mock ContentProcessor. It will return mappings and
        # documents for a particular document type, 'posts' in our mock
        # scenario. documents() returns a generator, which requires us to mock
        # its iterator.
        self.mock_processor = mock.Mock(spec=ContentProcessor)
        self.mock_processor.name = 'posts'
        self.mock_processor.processor_name = 'posts_processor'
        self.mock_processor.mapping.return_value = {}
        self.mock_processor.documents.return_value = iter([self.mock_document])

    @mock.patch('sheer.indexer.bulk')
    @mock.patch('sheer.indexer.Elasticsearch')
    @mock.patch('sheer.indexer.ContentProcessor')
    @mock.patch('sheer.indexer.read_json_file')
    @mock.patch('os.path.exists')
    def test_indexing(self, mock_exists, mock_read_json_file,
                      mock_ContentProcessor, mock_Elasticsearch, mock_bulk):
        """
        `sheer index`

        Test the creation of indexes by Sheer. For a given index, if it
        does not exist, it should be created and the documents yeilded
        by a given set of content processors should be created.
        """
        # Mock file existing/opening/reading
        # os.path.exists is only called directly for settings.json and
        # mappings.json, which are not necessary for our tests.
        mock_exists.return_value = False
        mock_read_json_file.side_effect = [self.mock_processors, {}]

        # Wire-up our mock content processor
        mock_ContentProcessor.return_value = self.mock_processor

        # Here we want to test:
        #   * Index doesn't exist -> should be created
        #   * Mappings don't exist for processor -> should be created
        #   * Documents don't exist for processor -> should be created
        mock_es = mock_Elasticsearch.return_value
        mock_es.indices.exists.return_value = False
        mock_es.indices.get_mapping.return_value = None

        test_args = AttrDict(processors=[], reindex=False)
        index_location(test_args, self.config)

        mock_es.indices.create.assert_called_with(index=self.config['index'])
        mock_bulk.assert_called_with(mock_es,
                                     self.mock_processor.documents(),
                                     index='content')

    @mock.patch('sheer.indexer.bulk')
    @mock.patch('sheer.indexer.Elasticsearch')
    @mock.patch('sheer.indexer.ContentProcessor')
    @mock.patch('sheer.indexer.read_json_file')
    @mock.patch('os.path.exists')
    def test_reindexing(self, mock_exists, mock_read_json_file,
                        mock_ContentProcessor, mock_Elasticsearch, mock_bulk):
        """
        `sheer index --reindex`

        Test the re-creation of existing indexes by Sheer. For a given
        index, if it already exists, it should be removed and recreated.
        """
        # Mock file existing/opening/reading
        # os.path.exists is only called directly for settings.json and
        # mappings.json, which are not necessary for our tests.
        mock_exists.return_value = False
        mock_read_json_file.side_effect = [self.mock_processors, {}]

        # Wire-up our mock content processor
        mock_ContentProcessor.return_value = self.mock_processor

        # Here we want to test:
        #   * Index exists -> should be deleted and recreated.
        #   ... therefore ...
        #   * Mappings don't exist for processor -> should be created
        #   * Documents don't exist for processor -> should be created
        mock_es = mock_Elasticsearch.return_value
        mock_es.indices.exists.side_effect = [True, False]
        mock_es.indices.get_mapping.return_value = None

        test_args = AttrDict(processors=[], reindex=True)
        index_location(test_args, self.config)

        mock_es.indices.delete.assert_called_with(self.config['index'])
        mock_es.indices.create.assert_called_with(index=self.config['index'])
        mock_bulk.assert_called_with(mock_es,
                                     self.mock_processor.documents(),
                                     index='content')

    @mock.patch('sheer.indexer.bulk')
    @mock.patch('sheer.indexer.Elasticsearch')
    @mock.patch('sheer.indexer.ContentProcessor')
    @mock.patch('sheer.indexer.read_json_file')
    @mock.patch('os.path.exists')
    def test_partial_indexing(self, mock_exists, mock_read_json_file,
                              mock_ContentProcessor, mock_Elasticsearch,
                              mock_bulk):
        """
        `sheer index --processors posts`

        Test partial indexing of the document type associated with a
        content processor.
        """
        # Mock file existing/opening/reading
        # os.path.exists is only called directly for settings.json and
        # mappings.json, which are not necessary for our tests.
        mock_exists.return_value = False
        mock_read_json_file.side_effect = [self.mock_processors, {}]

        # Wire-up our mock content processor
        mock_ContentProcessor.return_value = self.mock_processor

        # Here we want to test:
        #   * Index exists -> should be left alone
        #   * Mappings exist for processor -> should be deleted and recreated
        #   * Documents don't exist for processor -> should be created

        mock_es = mock_Elasticsearch.return_value
        mock_es.indices.exists.return_value = True
        # The tests for the get_mapping return value simply need to evaluate to
        # True in indexer.py.
        mock_es.indices.get_mapping.return_value = True
        mock_create_exception = TransportError(409)
        mock_es.create.side_effect = mock_create_exception

        test_args = AttrDict(processors=['posts'], reindex=False)
        index_location(test_args, self.config)
        mock_bulk.assert_called_with(mock_es,
                                     self.mock_processor.documents(),
                                     index='content')

    @mock.patch('sheer.indexer.bulk')
    @mock.patch('sheer.indexer.Elasticsearch')
    @mock.patch('sheer.indexer.ContentProcessor')
    @mock.patch('sheer.indexer.read_json_file')
    @mock.patch('os.path.exists')
    def test_partial_reindexing(self, mock_exists, mock_read_json_file,
                                mock_ContentProcessor, mock_Elasticsearch,
                                mock_bulk):
        """
        `sheer index --processors posts --reindex`

        Test the re-creation of mappings associated with content processor
        and the updating of its documents.
        """
        # Mock file existing/opening/reading
        # os.path.exists is only called directly for settings.json and
        # mappings.json, which are not necessary for our tests.
        mock_exists.return_value = False
        mock_read_json_file.side_effect = [self.mock_processors, {}]

        # Wire-up our mock content processor
        mock_ContentProcessor.return_value = self.mock_processor

        # Here we want to test:
        #   * Index exists and we're given processors -> should be left alone.
        #   * Mappings exist for processor -> should be deleted and recreated
        #   * Documents no longer exist for processor -> should be created
        mock_es = mock_Elasticsearch.return_value
        mock_es.indices.exists.side_effect = [True, False]
        mock_es.indices.get_mapping.return_value = True

        test_args = AttrDict(processors=['posts'], reindex=True)
        index_location(test_args, self.config)

        mock_es.indices.delete_mapping.assert_called_with(
            index=self.config['index'],
            doc_type='posts')
        mock_bulk.assert_called_with(mock_es,
                                     self.mock_processor.documents(),
                                     index='content')

    @mock.patch('sheer.indexer.bulk')
    @mock.patch('sheer.indexer.Elasticsearch')
    @mock.patch('sheer.indexer.ContentProcessor')
    @mock.patch('sheer.indexer.read_json_file')
    @mock.patch('os.path.exists')
    def test_indexing_failure_ioerr(self, mock_exists, mock_read_json_file,
                              mock_ContentProcessor, mock_Elasticsearch,
                              mock_bulk):
        """
        `sheer index`

        Test the failure of indexing by Sheer via an IOError, and make sure it
        fails gracefully. This simulates the unavailability and timeout of the
        upstream source of information.
        """
        # We want to capture stderr
        sys.stderr = StringIO()

        # Add mock error processors to the mock_processor json. This will let us
        # have two processors total. Because we're mocking ContentProcessor()
        # below we don't have to worry about the actual contents of this
        # dictionary.
        self.mock_processors['ioerrs'] = {
            'url': 'http://test/api/get_posts/',
            'processor': 'post_processor',
            'mappings': '_settings/posts_mappings.json'}

        # Mock file existing/opening/reading
        # os.path.exists is only called directly for settings.json and
        # mappings.json, which are not necessary for our tests.
        mock_exists.return_value = False
        mock_read_json_file.side_effect = [self.mock_processors, {}]

        # A context processor that will raise an IOError to simulate a
        # connection failure in requests.
        mock_ioerr_processor = mock.Mock(spec=ContentProcessor)
        mock_ioerr_processor.name = 'ioerrs'
        mock_ioerr_processor.processor_name = 'posts_processor'
        mock_ioerr_processor.mapping.return_io = {}
        mock_ioerr_processor.documents.side_effect = IOError("Connection aborted.")

        # Make sure ContentProcessor returns the processors
        mock_ContentProcessor.side_effect = [mock_ioerr_processor,
                                             self.mock_processor]

        # Here we assume:
        #   * Index doesn't exist -> should be created
        #   * Mappings don't exist for processor -> should be created
        #   * Documents don't exist for processor -> should be created
        #       * An exception is raised when trying to fetch documents from the
        #         context processor.
        mock_es = mock_Elasticsearch.return_value
        mock_es.indices.exists.return_value = False
        mock_es.indices.get_mapping.return_value = None

        test_args = AttrDict(processors=[], reindex=False)
        try:
            index_location(test_args, self.config)
        except SystemExit, s:
            assert s.code == \
                'Indexing the following processor(s) failed: ioerrs'

        # Ensure that we got the right error message.
        assert 'error making connection' in sys.stderr.getvalue()

        mock_bulk.assert_called_with(mock_es,
                                     self.mock_processor.documents(),
                                     index='content')

    @mock.patch('sheer.indexer.bulk')
    @mock.patch('sheer.indexer.Elasticsearch')
    @mock.patch('sheer.indexer.ContentProcessor')
    @mock.patch('sheer.indexer.read_json_file')
    @mock.patch('os.path.exists')
    def test_indexing_failure_valueerr(self, mock_exists, mock_read_json_file,
                              mock_ContentProcessor, mock_Elasticsearch,
                              mock_bulk):
        """
        `sheer index`

        Test the failure of indexing by Sheer via a ValueError, and make sure it
        fails gracefully. This simulates the unavailability and timeout of the
        upstream source of information.
        """
        # We want to capture stderr
        sys.stderr = StringIO()

        # Add a mock error processor to the mock_processor json. This will let us
        # have three processors total. Because we're mocking ContentProcessor()
        # below we don't have to worry about the actual contents of these
        # dictionaries.
        valueerr_mock_processor = {'valueerrs': {
            'url': 'http://test/api/get_posts/',
            'processor': 'post_processor',
            'mappings': '_settings/posts_mappings.json'}
            }

        # Mock file existing/opening/reading
        # os.path.exists is only called directly for settings.json and
        # mappings.json, which are not necessary for our tests.
        mock_exists.return_value = False
        mock_read_json_file.side_effect = [valueerr_mock_processor, {}]

        # A context processor that will raise a ValueError to simulate bad json
        # being provided by the upstream source.
        mock_bulk.side_effect = ValueError("No JSON object could be decoded")
        mock_valueerr_processor = mock.Mock(spec=ContentProcessor)
        mock_valueerr_processor.name = 'valueerrs'
        mock_valueerr_processor.processor_name = 'posts_processor'
        mock_valueerr_processor.mapping.return_value = {}

        # Make sure ContentProcessor returns the err processor
        mock_ContentProcessor.side_effect = [mock_valueerr_processor]

        # Here we assume:
        #   * Index doesn't exist -> should be created
        #   * Mappings don't exist for processor -> should be created
        #   * Documents don't exist for processor -> should be created
        #       * An exception is raised when trying to fetch documents from the
        #         context processor.
        mock_es = mock_Elasticsearch.return_value
        mock_es.indices.exists.return_value = False
        mock_es.indices.get_mapping.return_value = None

        test_args = AttrDict(processors=[], reindex=False)
        try:
            index_location(test_args, self.config)
        except SystemExit, s:
            assert s.code == \
                'Indexing the following processor(s) failed: valueerrs'

        # Ensure that we got the right error message.
        assert 'error reading documents' in sys.stderr.getvalue()
