from collections import namedtuple
import os
import json
import codecs
from dateutil.parser import parse
import time
from glob import glob
import re

cgi_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.abspath(os.path.join(cgi_dir, os.path.pardir))
www_dir = os.path.join(app_dir, "WWW")

TheDish = namedtuple('TheDish', ['official_name', 'subtitle', 'long_name',
                     'blurb', 'description', 'url', 'logo_src'])

thedish = TheDish(official_name='The Dish on Science',
                  subtitle='as told by Stanford students',
                  long_name='The Dish on Science: as told by Stanford students',
                  blurb='A science blogging club for Stanford students.',
                  description='The Dish on Science (The Dish for short) is a science outreach group that aims to bring you quality, understandable coverage of cutting edge scientific research, stories of impactful moments in the history of science, and more. In short, we want to share how excited we are about all the amazing science that we read about on a daily basis!',
                  url='http://thedishonscience.stanford.edu/',
                  logo_src='/images/dish-logo.png')


# usused since Author is just a field of post for now
# Author = namedtuple('Author', ['name', 'headshot_src'])

Team = namedtuple('Team', ['url_name', 'name', 'blurb', 'description', 'logo_src'])
# load all the team information from a global file
team_data_file = os.path.join(www_dir, 'assets', 'info', 'blog-teams.json')
team_data = codecs.open(team_data_file, 'r', encoding='utf-8').read()
teams = json.loads(team_data, encoding='utf-8', object_hook=lambda d: namedtuple('Team', d.keys())(*d.values())).teams

default_post_dict_keys = ['title', 'url_title', 'blurb', 'description',
                          'publication_date', 'five_by_two_image_src',
                          'two_by_one_image_src',
                          'one_by_one_image_src' ]
num_keys = len(default_post_dict_keys)
default_post_dict = dict(zip(default_post_dict_keys, [None]*num_keys))
class Post(object):
    """Knows about a blog post for The Dish."""

    def __init__(self, post_directory):
        """ Read JSON into self.__dict__ and pull in HTML of post"""
        post_file = os.path.join(post_directory, 'post_info.json')
        post_data = codecs.open(post_file, 'r', encoding='utf-8').read()
        data = json.loads(post_data, object_hook=lambda d: namedtuple('Post', d.keys())(*d.values()))
        self.__dict__ = default_post_dict.copy()
        self.__dict__.update(data.__dict__)
        if not self.publication_date:
            self.publication_date = time.strftime("%Y-%m-%d")
        self.publication_date = parse(self.publication_date)
        self.url = '/posts/' + str(self.url_title)
        self.absolute_url = thedish.url + self.url
        self.teams = [team for team in teams if team.name in self.teams or team.url_name in self.teams]
        html_file = glob(os.path.join(post_directory, '*.html'))
        if html_file:
# glob returns a list of files, even if that list is of length 1
            self.html = codecs.open(html_file[0], encoding='utf-8').read()
        else:
            self.html = ''

# load posts from posts directory
post_directories = os.listdir(os.path.join(www_dir, 'posts'))
all_posts = [Post(os.path.join(www_dir, 'posts', post_directory))
             for post_directory in post_directories
             if not re.match('.*\.zip$', post_directory) ]
