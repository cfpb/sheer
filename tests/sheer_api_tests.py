import unittest
from mock import MagicMock, patch

from sheer.sheer_api import SheerAPI

class SheerAPITest(unittest.TestCase):

    def setUp(self):
        self.sapi = SheerAPI('tests/sample_data', [])
        
        self.sapi.results_sample = {'success':'Success'}
        self.sapi.errors_sample = ['500 Internal Error',{'Error':'Error message'}]
        self.sapi.start_response = MagicMock( return_value = 'ACK' )

    def test_initialization(self):
        """ Testing SheerAPI initialization """
        self.assertTrue( 'tests/sample_data' == self.sapi.site_root )
        self.assertTrue( [] == self.sapi.permalink_map )
        self.assertTrue( 'events' in self.sapi.allowed_content )
        self.assertFalse( 'bugs' in self.sapi.allowed_content )
        self.assertTrue( None == self.sapi.errors )

    def test_handle_wsgi(self):
        """ Testing handle_wsgi function """
        # not a big deal
        pass

    def test_check_errors__no_errors(self):
        """ Testing check_errors function, no errors """
        self.assertFalse( True == self.sapi.check_errors() )

    def test_check_errors__errors(self):
        """ Testing check_errors function, with errors """
        self.sapi.errors = ''
        self.assertTrue( True == self.sapi.check_errors() )

    def test_return_results__success(self):
        """ Testing return_results function, no errors """
        self.sapi.results = self.sapi.results_sample
        self.assertIn( 'Success', self.sapi.return_results() )

    def test_return_results__errors(self):
        """ Testing return_results function, with errors """
        self.sapi.errors = self.sapi.errors_sample
        self.assertIn( 'Error', self.sapi.return_results() )
        
    def test_calculate_results__errors(self):
        """ Testing calculate_results function, with errors """
        self.sapi.errors = ''
        self.assertTrue( self.sapi == self.sapi.calculate_results('') )
        self.assertTrue( self.sapi.errors == '' )

    def test_calculate_results__wrong_path(self):
        """ Testing calculate_results function, wrong path """
        self.sapi.content_type = 'bugs'
        returned = self.sapi.calculate_results( '' )
        self.assertTrue( self.sapi == returned )
        self.assertTrue( len( self.sapi.errors ) == 2 )
        self.assertTrue( self.sapi.errors[0] == '501 Not Implemented' )

    @patch( 'sheer.query.Query.search' )
    def test_calculate_results__no_errors(self, mock_query_search):
        """ Testing calculate_results function, no errors """
        mock_query_search.return_value = [{'success':'Success'}]
        self.sapi.content_type = 'events'
        returned = self.sapi.calculate_results( {'ELASTICSEARCH_INDEX': None} )
        self.assertTrue( self.sapi.errors == None )
        self.assertFalse( self.sapi.results == None )
        self.assertFalse( self.sapi.results == [] )

    def test_add_2q_1(self):
        """ Testing add_2q function, ?keyword=SEARCH """
        result = self.sapi.add_2q('', ['keyword', 'SEARCH'])
        self.assertTrue( ' _all:(SEARCH)' == result )
        
    def test_add_2q_2(self):
        """ Testing add_2q function, ?keyword=SEARCH,KEY """
        result = self.sapi.add_2q('', ['keyword', 'SEARCH,KEY'])
        self.assertTrue( ' _all:(SEARCH KEY)' == result )

    def test_add_2q_3(self):
        """ Testing add_2q function, ?SMTH&keyword=SEARCH """
        result = self.sapi.add_2q('AND', ['keyword', 'SEARCH'])
        self.assertTrue( 'AND _all:(SEARCH)' == result )

    def test_add_2q_4(self):
        """ Testing add_2q function, ?item1=item2 """
        result = self.sapi.add_2q('', ['item1', 'item2'])
        self.assertTrue( ' item1:"item2"' == result )

    def test_add_2q_5(self):
        """ Testing add_2q function, ?item1=item2,item3 """
        result = self.sapi.add_2q('', ['item1', 'item2,item3'])
        self.assertTrue( ' item1:"item2" AND item1:"item3"' == result )

    def test_add_2q_6(self):
        """ Testing add_2q function, ?SMTH&item1=item2,item3 """
        result = self.sapi.add_2q('OR', ['item1', 'item2,item3'])
        self.assertTrue( 'OR item1:"item2" AND item1:"item3"' == result )

    def test_process_arguments__no_arguments(self):
        """ Testing process_arguments function, no arguments """
        self.sapi.process_arguments( {'PATH_INFO': '/v2/events'}, {})
        self.assertTrue( self.sapi.api_version == 'v2' )
        self.assertTrue( self.sapi.content_type == 'events' )
        self.assertTrue( self.sapi.errors == None )
        self.assertTrue( self.sapi.args == {} )
        
    def test_process_arguments__wrong_argument(self):
        """ Testing process_arguments function, not_allowed:blog """
        self.sapi.process_arguments( {'PATH_INFO': '/v2/events'}, {'not_allowed':'blog'} )
        self.assertEqual( self.sapi.args, {'not_allowed':'blog'} )
        self.assertTrue( self.sapi.errors == None )

    def test_process_arguments__from_arg(self):
        """ Testing processing_arguments function, from:10 """
        self.sapi.process_arguments( {'PATH_INFO': '/v2/events'}, {'from':10} )
        self.assertTrue( self.sapi.errors == None )
        self.assertEqual( self.sapi.args, {'from_':10} )

    def test_process_arguments__type_arg(self):
        """ Testing processing_arguments function, type:blog """
        self.sapi.process_arguments( {'PATH_INFO': '/v2/events'}, {'type':'blog'} )
        self.assertTrue( self.sapi.errors == None )
        self.assertEqual( self.sapi.args, {'q':' _type:"blog"'} )

    def test_process_arguments__multiple_arg(self):
        """ Testing processing_arguments function, type:blog,from:20,title:title1,title2 """
        self.sapi.process_arguments( {'PATH_INFO': '/v2/events'}, {'type':'blog', 'from':20, 'title':'title1,title2'} )
        self.assertTrue( self.sapi.errors == None )
        self.assertEqual( self.sapi.args, {'q':' _type:"blog" AND  title:"title1" AND title:"title2"', 'from_':20} )
