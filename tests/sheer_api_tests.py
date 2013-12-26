import unittest
from sheer.sheer_api import SheerAPI

class SheerAPITest(unittest.TestCase):

    def setUp(self):
        self.sapi = SheerAPI('./sample_data/', [])

    def test_initialization(self):
        """ Testing SheerAPI initialization """
        self.assertTrue( './sample_data/' == self.sapi.site_root )
        self.assertTrue( [] == self.sapi.permalink_map )
        self.assertTrue( 'events' in self.sapi.allowed_content )
        self.assertFalse( 'bugs' in self.sapi.allowed_content )
        self.assertTrue( None == self.sapi.errors )

    def test_handle_wsgi(self):
        pass

    def test_check_errors(self):
        """ Testing check_errors function """
        self.assertFalse( True == self.sapi.check_errors() )
        self.sapi.errors = ''
        self.assertTrue( True == self.sapi.check_errors() )

    def test_return_results(self):
        pass

    def test_calculate_results(self):
        pass

    def test_add_2q(self):
        """ Testing add_2q function """
        result = self.sapi.add_2q('', ['keyword', 'SEARCH'])
        self.assertTrue( ' _all:(SEARCH)' == result )
        result = self.sapi.add_2q('', ['keyword', 'SEARCH,KEY'])
        self.assertTrue( ' _all:(SEARCH KEY)' == result )
        result = self.sapi.add_2q('AND', ['keyword', 'SEARCH'])
        self.assertTrue( 'AND _all:(SEARCH)' == result )
        result = self.sapi.add_2q('', ['item1', 'item2'])
        self.assertTrue( ' item1:"item2"' == result )
        result = self.sapi.add_2q('', ['item1', 'item2,item3'])
        self.assertTrue( ' item1:"item2" AND item1:"item3"' == result )
        result = self.sapi.add_2q('OR', ['item1', 'item2,item3'])
        self.assertTrue( 'OR item1:"item2" AND item1:"item3"' == result )

    def test_process_arguments(self):
        """ Testing process_arguments function """
        pass
