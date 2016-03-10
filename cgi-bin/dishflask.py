#!/usr/bin/python
from flask import Flask, render_template, url_for, send_from_directory, request
from collections import namedtuple
import random
import os
import json
from thedish import thedish, cgi_dir, app_dir, www_dir, teams
from dishsql import get_popular_posts, get_recent_posts, get_team_by_name, \
                    get_post_by_name, get_recent_posts_team

app = Flask(__name__, static_url_path='')
app.debug = True
app.template_folder = os.path.join(www_dir, 'templates')

posts_per_page = 10
popular_posts_per_page = 5

def render_template_with_defaults(template, recent_posts=None, popular_posts=None,
                                  teams=teams, thedish=thedish, error=None,
                                  **kwargs):
    if recent_posts is None:
        recent_posts = get_recent_posts(offset=0, limit=posts_per_page)
    if popular_posts is None:
        popular_posts = get_popular_posts(offset=0, limit=popular_posts_per_page)
    return render_template(template, thedish=thedish, teams=teams,
                            popular_posts=popular_posts,
                            recent_posts=recent_posts,
                            error=error, **kwargs)

@app.route('/topics/<team_name>/', methods=['GET'])
def show_team_page(team_name):
    if 'start' in request.args:
        start = max(0, request.args['start'])
    else:
        start = 0
    matching_team = get_team_by_name(team_name)
    if not matching_team:
        error_string = "There is no page for the topic '{}'.".format(team_name)
        return render_template_with_defaults('index.html', error=error_string)
    recent_posts = get_recent_posts_team(team_url_name=team_name, offset=start,
                                         limit=posts_per_page)
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
    if 'start' in request.args:
        start = max(0, request.args['start'])
    else:
        start = 0
    recent_posts = get_recent_posts(offset=start, limit=posts_per_page)
    return render_template_with_defaults('index.html', recent_posts=recent_posts)

@app.route('/posts/<post_name>/')
def send_post(post_name):
    matching_post = get_post_by_name(post_name)
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
