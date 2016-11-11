#!/usr/bin/python
from flask import Flask, render_template, url_for, send_from_directory, request, g
from collections import namedtuple
import random
import os
import json
from thedish import thedish, cgi_dir, app_dir, www_dir
from dishsql import thedish, www_dir

app = Flask(__name__, static_url_path='')
app.debug = False
app.template_folder = os.path.join(www_dir, 'templates')

posts_per_page = 10
popular_posts_per_page = 5

# the canonical Flask way of initializing/tearing down a request-wide object
@app.before_request
def before_request():
    g.session = dishsql.Session()

@app.teardown_request
def teardown_request(exception=None):
    session = getattr(g, 'session', None)
    try:
        session.commit()
    finally:
        session.close()

#TODO implement
# class Pagination():
#     """Keeps track of number of pages, which one we're on, and what arrows
#     should point to."""
#     def __init__(self, num_posts, cur_page=1, count=posts_per_page):
#         self.num_posts = num_posts
#         self.cur_page = cur_page
#         self.posts_per_page = posts_per_page

#     @property
#     def next_page_url_args(self):
#         return "page={d:page_num}&count={d:post_count}".format(
#             page_num=

def render_template_with_defaults(template, recent_posts=None, popular_posts=None,
                                  thedish=thedish, error=None,
                                  **kwargs):

    session = getattr(g, 'session', None)
    teams = dishsql.get_all_teams(session)
    if recent_posts is None:
        recent_posts = dishsql.get_recent_posts(page=1, count=posts_per_page, session=session)
    if popular_posts is None:
        popular_posts = dishsql.get_popular_posts(page=1, count=popular_posts_per_page, session=session)
    return render_template(template, thedish=thedish, teams=teams,
                           popular_posts=popular_posts,
                           recent_posts=recent_posts,
                           error=error, **kwargs)

@app.route('/topics/<team_name>/', methods=['GET'])
def show_team_page(team_name):
    session = getattr(g, 'session', None)
    try:
        page = int(request.args['page'])
    except: # ValueError from int conversion, or KeyError from dict access
        page = 1
    page = max(1, request.args['page'])
    matching_team = dishsql.get_team_by_name(team_name, session)
    if not matching_team:
        error_string = "There is no page for the topic '{}'.".format(team_name)
        return render_template_with_defaults('index.html', error=error_string)
    recent_posts = get_recent_posts_team(team_url_name=team_name, page=page,
                                         count=posts_per_page)
    return render_template_with_defaults('team.html', team=matching_team,
                                         recent_posts=recent_posts)

@app.route('/science-dictionary/')
def show_dictionary_page():
    error_string = "The 'dictionary' feature is not yet implemented!"
    return render_template_with_defaults('index.html', error=error_string)

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@app.route('/index.htm', methods=['GET'])
@app.route('/index.html', methods=['GET'])
@app.route('/home', methods=['GET'])
@app.route('/cgi-bin/', methods=['GET'])
def show_home_page():
    session = getattr(g, 'session', None)
    #return send_from_directory(www_dir, 'index.html')
    if 'page' in request.args:
        page = max(1, request.args['page'])
    else:
        page = 1
    recent_posts = dishsql.get_recent_posts(page=page, count=posts_per_page, session=session)
    return render_template_with_defaults('index.html', recent_posts=recent_posts)

@app.route('/posts/<post_name>/')
def send_post(post_name):
    session = getattr(g, 'session', None)
    matching_post = dishsql.get_post_by_name(post_name, session)
    if not matching_post:
        error_string = "No post with URL '{}posts/{}'".format(thedish.url, post_name)
        return render_template_with_defaults('index.html', error=error_string)
    return render_template_with_defaults('post.html', post=matching_post)

# @app.route('/assets/<path:path>')
# def send_assets(path):
#     return send_from_directory('/var/www/thedishonscience.com/WWW/assets/', path)

# @app.route('/images/<path:path>')
# def send_images(path):
#     return send_from_directory('/var/www/thedishonscience.com/WWW/images/', path)

# @app.route('/documents/<path:path>')
# def send_documents(path):
#     return send_from_directory('/var/www/thedishonscience.com/WWW/documents/', path)

# @app.route('/posts/<post_name>/images/<path:path>')
# def send_post_images(post_name, path):
#     return send_from_directory('/var/www/thedishonscience.com/WWW/posts/{}/images/'.format(post_name), path)

@app.errorhandler(404)
def page_not_found(e):
    error_string = "404! The page you have requested does not exist!"
    return render_template_with_defaults('index.html', error=error_string)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
