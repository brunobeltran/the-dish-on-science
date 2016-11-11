from collections import namedtuple
import os
import json
import codecs
from dateutil.parser import parse
import time
from glob import glob
import re
import random
import logging
logging.basicConfig()
logger = logging.Logger('thedish.py')


cgi_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.abspath(os.path.join(cgi_dir, os.path.pardir))
www_dir = os.path.join(app_dir, "WWW")
posts_dir = os.path.join(www_dir, 'posts')

# the dish information used to be hardcoded
# TheDish = namedtuple('TheDish', ['official_name', 'subtitle', 'long_name',
#                      'blurb', 'description', 'url', 'logo_src'])

# thedish = TheDish(official_name='The Dish on Science',
#                   subtitle='as told by Stanford students',
#                   long_name='The Dish on Science: as told by Stanford students',
#                   blurb='A science blogging club for Stanford students.',
#                   description='The Dish on Science (The Dish for short) is a science outreach group that aims to bring you quality, understandable coverage of cutting edge scientific research, stories of impactful moments in the history of science, and more. In short, we want to share how excited we are about all the amazing science that we read about on a daily basis!',
#                   url='http://thedishonscience.stanford.edu/',
#                   logo_src='/images/dish-logo.png')

# instead, we now load it in from a json file
#TODO remove the above lame comments after merge verified working
# load dish information from global file
dish_data_file = os.path.join(www_dir, 'assets', 'info', 'the-dish.json')
dish_data = codecs.open(dish_data_file, 'r', encoding='utf-8').read()


#TODO remove these eternally unused lines after merge verified working
# usused since Author is just a field of post for now
# Author = namedtuple('Author', ['name', 'headshot_src'])

#TODO get rid fo all the following code after merge verified working, it's all
# been moved to dishsql

# # load in the team information from dish only on demand
# def get_teams_from_disk()
#     Team = namedtuple('Team', ['url_name', 'name', 'blurb', 'description', 'logo_src'])
# # load all the team information from a global file
#     team_data_file = os.path.join(www_dir, 'assets', 'info', 'blog-teams.json')
#     team_data = codecs.open(team_data_file, 'r', encoding='utf-8').read()
#     all_teams = json.loads(team_data, encoding='utf-8', object_hook=lambda d: namedtuple('Team', d.keys())(*d.values())).teams
#     return all_teams

# Author = namedtuple('Author', ['name', 'nickname', 'headshot_src'])
# default_post_dict_keys = ['title', 'url_title', 'blurb', 'description',
#                           'publication_date', 'five_by_two_image_src',
#                           'two_by_one_image_src',
#                           'one_by_one_image_src' ]
# num_keys = len(default_post_dict_keys)
# default_post_dict = dict(zip(default_post_dict_keys, [None]*num_keys))
# class Post(object):
#     """Knows about a blog post for The Dish."""

#     @classmethod
#     def __init__(self, post_directory):
#         """ Read JSON into self.__dict__ and pull in HTML of post"""
#         post_file = os.path.join(post_directory, 'post_info.json')
#         post_data = codecs.open(post_file, 'r', encoding='utf-8').read()
#         data = json.loads(post_data)
#         self.__dict__ = default_post_dict.copy()
#         self.__dict__.update(data)
#         # error out immediately if no url_title, since even the logging
#         # messages from now on will assume that it's present
#         if 'url_title' not in self.__dict__:
#             raise CannotFixError("'url_title' not specified in info file: " + post_file)
#         if self.publication_date:
#             self.publication_date = parse(self.publication_date)
#         self.url = '/posts/' + str(self.url_title)
#         self.absolute_url = thedish.url + self.url
#         md_file = os.path.join(post_directory, 'post.md')
#         html_file = os.path.join(post_directory, 'post.html')
#         if not os.path.isfile(html_file):
#             if not os.path.isfile(md_file):
#                 CannotFixError("No post.md or post.html file found: " + self.url_title)
#             markdownFromFile(input=md_file, output=html_file, encoding="utf-8")
#         self.html = codecs.open(html_file, encoding='utf-8').read()


#     def fix_publication_date(self):
#         if not self.publication_date:
#             raise CannotFixError("No publication date provided for article: " + self.url_title)

#     def fix_title(self):
#         if not validate_length(self.title, 'title'):
#             raise CannotFixError("Can't fix the title!")

#     def fix_url(self):
#         if not validate_length(self.url_title, 'url_title'):
#             raise CannotFixError('Cannot fix url_title!')
#         allowed_chars = set(string.ascii_lowercase + string.digits + '-')
#         if not set(self.url_title) <= allowed_chars:
#             logger.warning('Illegal characters in URL!: ' + self.url_title)

#     def fix_blurb(self):
#         if not validate_length(self.blurb, 'blurb'):
#             raise CannotFixError('Cannot fix blurb!')

#     def fix_description(self):
#         if not validate_length(self.description, 'description'):
#             raise CannotFixError('Cannot fix description!')

#     def fix_teams(self):
#         # teams are selected from a list of known good teams, so they can't
#         # really be messed up. So here, we just have to make sure that there
#         # are teams listed at all
#         if not self.teams:
#             raise CannotFixError('No valid teams were provided when ' \
#                                  + 'constructing Post: ' + self.url_title)
#         all_teams = get_teams_from_disk()
#         valid_team_names = [team for team in all_teams
#                           if team.name in self.teams
#                           or team.url_name in self.teams]
#         self.teams = valid_team_names #TODO construct team objects from sql table here
#         if not self.teams:
#             raise CannotFixError('No valid teams were provided when ' \
#                                  + 'constructing Post: ' + self.url_title)

#     def fix_authors(self):
#         # if no author name specified, use team name
#         if not self.authors:
#             logger.warning('No author names specified! Using team names instead.')
#             self.authors = [Author(name=team.name, nickname=team.name,
#                             headshot_src=team.logo_src) for team in post.teams]
#         self.authors = [self.fix_author(author) for author in self.authors]

#     def fix_author(self, author):
#         return Author(fix_author_name(author), fix_author_nickname(author),
#                       self.fix_author_headshot_src(author))

#     def fix_author_headshot_src(self, author):
#         default_images = ['/images/cow.png', '/images/dinosaur.png',
#                         '/images/elephant.png', '/images/hedgehog.png',
#                         '/images/monkey.jpeg', '/images/panda.png',
#                         '/images/paperplane.png', '/images/penguin.png',
#                         '/images/turkey.png']
#         headshot_src = author.headshot_src
#         looks_like_default_attempt = re.compile('^/images/[^/]*')
#         looks_like_global_author_attempt = re.compile('^/images/' + author.name + '/.*')
#         if looks_like_default_attempt.match(headshot_src):
#             if headshot_src not in default_images:
#                 logger.warning("Looks like you're trying to use a stock animal " \
#                             "image for the author " + author + ", but it " \
#                             "doesn't match any of the images available!")
#                 logger.warning("Replacing headshot_src with random animal for "
#                             + str(author))
#                 return default_images[random.randint(0, len(default_images)-1)]
#             # they've got a valid default image, use it
#             return headshot_src
#         # they're allowed to send us files to save in /images/$author_name/
#         # if they sent the file with the article, move it into the global
#         # directory
#         elif looks_like_global_author_attempt.match(headshot_src):
#             author_images_dir, filename = os.path.split(headshot_src)
#             author_images_dir = '/images/' + author.name
#             maybe_filename1 = os.path.join(www_dir, headshot_src)
#             maybe_filename2 = os.path.join(www_dir, author_images_dir + filename)
#             maybe_filename3 = os.path.join(www_dir, url, 'images', filename)
#             # if the file is already in the right place:
#             if os.path.isfile(maybe_filename1):
#                 return headshot_src
#             # maybe we can recover the right file by guessing
#             elif os.path.isfile(maybe_filename2):
#                 return author_images_dir + filename
#             # maybe it's in the post's images directory instead
#             elif os.path.isfile(maybe_filename3):
#                 if not os.path.isdir(author_images_dir):
#                     os.mkdir(author_images_dir, mode=755)
#                 shutil.copyfile(maybe_filename3, maybe_filename2)
#                 return author_images_dir + filename
#             else:
#                 logger.error('Cannot find headshot file, looks like you ' \
#                              + 'wanted to use a centrally saved one ' \
#                              + 'from /images/?: ' + headshot_src)
#                 raise CannotFixError('Cannot find headshot_src: ' +
#                                      headshot_src)
#         # otherwise it's just a regular file, probably saved in their post's
#         # images directory
#         else:
#             return self.fix_image_file_name(author.headshot_src)

#     def fix_image_file_name(self, file_name):
#         looks_like_local_attempt = re.compile('(\./).*')
#         # looks_like_absolute_attempt = re.compile('.*/posts/.*/images/.*')
#         unfixable = False
#         if looks_like_local_attempt.match(file_name):
#             supposed_file = os.path.join(www_dir, self.url, file_name)
#             if not os.path.isfile(supposed_file):
#                 logger.error("Looks like you referred to an image with a " \
#                              + "relative URL, but the image does not appear " \
#                              + " to exist: " \
#                              + file_name)
#                 raise CannotFixError('Cannot find image file: ' + file_name)
#             # make into absolute path for website
#             return supposed_file
#         else: # if looks_like_absolute_attempt.match(file_name):
#             supposed_file = os.path.join(www_dir, file_name)
#             if not os.path.isfile(supposed_file):
#                 logger.error("Looks like you're trying to use a post-specific " \
#                                 + "author headshot, but the file does not exist: " \
#                                 + file_name)
#                 raise CannotFixError('Cannot find image file: ' + file_name)

#     @staticmethod
#     def fix_author_name(author):
#         if not validate_length(author.name, 'name'):
#             raise CannotFixError("Can't fix the author name: " + author.name + "!")
#         return author.name

#     @staticmethod
#     def fix_author_nickname(author):
#         nickname = author.nickname
#         if not nickname:
#             nickname = author.name
#         if not nickname:
#             raise CannotFixError("No name or nickname provided for this author!")
#         if not validate_length(nickname, 'name'):
#             raise CannotFixError("Can't fix the author nickname: " + nickname + "!")
#         return nickname

#     @staticmethod
#     def fix_team_name(team_name):
#         allowed_team_names = [ 'biochemistry-and-bioinformatics',
#                             'cell-biology', 'forty-two', 'general-biology',
#                             'genomics', 'immune-system', 'marine-biology',
#                             'monumental-scientific-discoveries', 'neuroscience',
#                             'translational-biology']
#         if team_name not in allowed_team_names:
#             raise CannotFixError('Illegal team name!: ' + team_name)

# # load posts from posts directory, only on demand
# def get_posts_from_disk():
#     post_directories = os.listdir(os.path.join(www_dir, 'posts'))
#     # diretory names into full relative paths
#     post_directories = [os.path.join(www_dir, 'posts', post_directory)
#                         for post_directory in post_directories]
#     # make a list of all posts that don't throw errors
#     all_posts = []
#     for post_directory in post_directories:
#         try:
#             post = Post(post_directory)
#             if post:
#                 all_posts.append(post)
#         except:
#             continue
#             # if not re.match('.*\.zip$', post_directory) ]
