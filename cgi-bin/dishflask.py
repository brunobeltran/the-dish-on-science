#!/usr/bin/python
from flask import Flask, render_template, url_for, send_from_directory
from collections import namedtuple
import random
import os
import json
import codecs
from glob import glob
from dateutil.parser import parse


cgi_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.abspath(os.path.join(cgi_dir, os.path.pardir))
www_dir = os.path.join(app_dir, "WWW")

app = Flask(__name__, static_url_path='')
# print("Content-Type: text/html")
# print
app.debug = True
app.template_folder = os.path.join(www_dir, 'templates')

TheDish = namedtuple('TheDish', ['official_name', 'subtitle', 'long_name',
                     'blurb', 'description', 'url', 'logo_src'])
thedish = TheDish(official_name='The Dish on Science',
                  subtitle='as told by graduate students',
                  long_name='The Dish on Science: As Told by Graduate Students',
                  blurb='A science blogging club for graduate students.',
                  description='Started by Sam Piekos, The Dish on Science (The Dish for short) offers an avenue for frustrated graduate students to write about the things that they love on the days when those things decide to hate them.',
                  url='http://brunobeltran.org/',
                  logo_src='./images/logo-bruno-dish-9.png')
# usused since Author is just a field of post for now
# Author = namedtuple('Author', ['name', 'headshot_src'])

# load all the team information from a global file
Team = namedtuple('Team', ['url', 'name', 'blurb', 'description', 'logo_src'])
team_data_file = os.path.join(www_dir, 'assets', 'info', 'blog-teams.json')
team_data = codecs.open(team_data_file, 'r', encoding='utf-8').read()
teams = json.loads(team_data, encoding='utf-8', object_hook=lambda d: namedtuple('Team', d.keys())(*d.values())).teams

class Post(object):
    """Knows about a blog post for The Dish."""

    def __init__(self, post_directory):
        """ Read JSON into self.__dict__ and pull in HTML of post"""
        post_file = os.path.join(post_directory, 'post_info.json')
        post_data = codecs.open(post_file, 'r', encoding='utf-8').read()
        data = json.loads(post_data, object_hook=lambda d: namedtuple('Post', d.keys())(*d.values()))
        self.__dict__ = data.__dict__.copy()
        self.publication_date = parse(self.publication_date)
        self.url = '/' + str(self.url_title)
        self.absolute_url = thedish.url + self.url
        self.teams = [team for team in teams if team.name in self.teams]
        html_file = glob(os.path.join(post_directory, '*.html'))
        if html_file:
# glob returns a list of files, even if that list is of length 1
            self.html = codecs.open(html_file[0], encoding='utf-8').read()
        else:
            self.html = ''


# load posts from posts directory
post_directories = os.listdir(os.path.join(www_dir, 'posts'))
recent_posts = [Post(os.path.join(www_dir, 'posts', post_directory)) for post_directory in post_directories]
popular_posts = list(recent_posts)
random.shuffle(popular_posts)

def render_default(error=None):
    return render_template('index.html', thedish=thedish, teams=teams,
                            popular_posts=popular_posts,
                            recent_posts=recent_posts,
                            error=error)

@app.route('/topics/<team_name>/')
def show_team_page(team_name):
    matching_team = [team for team in teams if team.url == team_name]
    if not matching_team:
        error_string = "There is no page for the topic '{}'.".format(team_name)
        return render_default(error=error_string)
    return render_template('team.html', thedish=thedish, teams=teams,
                            popular_posts=popular_posts,
                            recent_posts=recent_posts,
                            team=matching_team[0],
                            error=None)

@app.route('/science-dictionary/')
def show_dictionary_page():
    error_string = "The 'dictionary' feature is not yet implemented!"
    return render_default(error=error_string)

@app.route('/')
@app.route('/index')
@app.route('/index.htm')
@app.route('/index.html')
@app.route('/home')
@app.route('/cgi-bin/')
def show_home_page():
    return render_default()

# @app.route('/assets/<path:path>')
# def send_assets(path):
#     return send_from_directory('/var/www/thedishonscience.com/assets/', path)

# @app.route('/images/<path:path>')
# def send_images(path):
#     return send_from_directory('/var/www/thedishonscience.com/images/', path)

# @app.route('/documents/<path:path>')
# def send_documents(path):
#     return send_from_directory('/var/www/thedishonscience.com/documents/', path)

# @app.route('/temp_images/<path:path>')
# def send_temp_images(path):
#     return send_from_directory('/var/www/thedishonscience.com/temp_images/', path)

@app.route('/<post_name>')
def send_post(post_name):
    matching_post = [post for post in recent_posts if post.url_title == post_name]
    if not matching_post:
        error_string = "No post with URL '{}{}'".format(thedish.url, post_name)
        return render_default(error=error_string)
    return render_template('post.html', thedish=thedish, teams=teams,
                            popular_posts=popular_posts,
                            post=matching_post[0],
                            error=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)