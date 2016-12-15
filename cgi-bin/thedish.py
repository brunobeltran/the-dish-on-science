from collections import namedtuple
import os
import json
import codecs
from dateutil.parser import parse
import time
from glob import glob
import re
import random
# import logging
# logging.basicConfig()
# logger = logging.Logger('thedish.py')


cgi_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.abspath(os.path.join(cgi_dir, os.path.pardir))
www_dir = os.path.join(app_dir, u"WWW")
posts_dir = os.path.join(www_dir, u'posts')

# load dish information from global file
dish_data_file = os.path.join(www_dir, 'assets', 'info', 'the-dish.json')
dish_info = json.load(codecs.open(dish_data_file, 'r', encoding='utf-8'))
# now make the dict into a namedtuple so that we have attr access to each key
# so that we can use our existing jinja2 templates
dish_info = dish_info['TheDish']
dish_info = namedtuple('TheDish', dish_info.keys())(**dish_info)

