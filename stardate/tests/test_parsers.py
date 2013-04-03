import datetime

from django.test import TestCase
from django.utils import timezone

from stardate.parsers import SingleFileParser


class SingleFileParserTestCase(TestCase):
    def setUp(self):
        self.parser = SingleFileParser()
        self.test_string = "publish: 2012-01-02 12:00 AM\ntitle: Tingling of the spine\n\n\nExtraordinary claims require extraordinary evidence!"

    def test_parse(self):
        parsed = self.parser.parse(self.test_string)

        self.assertEqual(parsed['title'], 'Tingling of the spine')
        self.assertEqual(parsed['publish'], datetime.datetime(2012, 1, 2, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(parsed['body'], 'Extraordinary claims require extraordinary evidence!')

    def test_unpack(self):
        content = self.test_string
        post_list = self.parser.unpack(content)

        #The file has one post to unpack
        self.assertEqual(len(post_list), 1)
        self.assertEqual(post_list[0].get('title'), 'Tingling of the spine')
        self.assertEqual(post_list[0].get('publish'), datetime.datetime(2012, 1, 2, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(post_list[0].get('body'), 'Extraordinary claims require extraordinary evidence!')

    # def test_get_post_objects(self):
    #     posts = self.parser.get_post_objects()

    #     self.assertEqual(len(posts), 2)
    #     self.assertEqual(posts, [
    #         {
    #             'body': 'Extraordinary claims require extraordinary evidence!\n',
    #             'publish': datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc),
    #             'title': 'Tingling of the spine'},
    #         {
    #             'body': "With pretty stories for which there's little good evidence.\n",
    #             'publish': datetime.datetime(2012, 1, 1, 14, 0, tzinfo=timezone.utc),
    #             'title': 'Great turbulent clouds'}])
