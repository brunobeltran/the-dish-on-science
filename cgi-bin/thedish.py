from collections import namedtuple
import os
import json
import codecs

cgi_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.abspath(os.path.join(cgi_dir, os.path.pardir))
www_dir = os.path.join(app_dir, "WWW")
posts_dir = os.path.join(www_dir, 'posts')

TheDish = namedtuple('TheDish', ['official_name', 'subtitle', 'long_name',
                     'blurb', 'description', 'url', 'logo_src'])
# load dish information from global file
dish_data_file = os.path.join(www_dir, 'assets', 'info', 'the-dish.json')
dish_data = codecs.open(dish_data_file, 'r', encoding='utf-8').read()
thedish = json.loads(dish_data, encoding='utf-8', object_hook=lambda d: namedtuple('TheDish', d.keys())(*d.values())).TheDish
