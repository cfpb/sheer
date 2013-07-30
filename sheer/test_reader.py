import os.path

from sheer import reader
from sheer.utility import get_case_contents


class testReader:

    def test_frontmatter_extraction(self):
        data = get_case_contents('simple_frontmatter.txt')
        frontmatter, text = reader.extract_frontmatter(data)
        assert(frontmatter == "\nHi, I'm Frontmatter\n")
        assert("I'm a unicorn!" in text)

    def test_no_frontmatter(self):
        data = get_case_contents('no_frontmatter.txt')
        frontmatter, text = reader.extract_frontmatter(data)
        assert(frontmatter == None)
        assert("I don't have frontmatter at all" in text)

    def test_document_builder(self):
        data = get_case_contents('post.md')
        document = reader.document_from_str(data)
        assert('Website' in document['categories'])
        assert('level playing field' in document['text'])
