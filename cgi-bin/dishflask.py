#!/afs/ir/group/thedishonscience/venv-tdos/bin/python3.4
from flask import Flask, render_template, url_for, send_from_directory, request, g, redirect
from collections import namedtuple
import random
import os
import json
from thedish import dish_info, cgi_dir, app_dir, www_dir
import dishsql

app = Flask(__name__, static_url_path='')
app.debug = False
app.template_folder = os.path.join(www_dir, 'templates')

posts_per_page = 3
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

class Paginator():
    """Keeps track of number of pages, which one we're on, and what prev/next
    page links should point to. Assumes that it gets recreated every time a
    page is changed."""
    def __init__(self, page=1, count=posts_per_page, num_posts=None):
        # initialize to requested values
        self.page = page
        self.count = count
        self._session = getattr(g, 'session', None)
        if num_posts is None:
            self.num_posts = dishsql.get_num_posts(self._session)
        else:
            self.num_posts = num_posts
        # bound page and count to possible values
        self.count = max(1, self.count)
        self.num_pages = (self.num_posts // self.count)
        self.num_pages = max(1, self.num_pages)
        if self.num_pages*self.count < self.num_posts:
            self.num_pages += 1
        self.page = max(1, self.page)
        self.page = min(self.num_pages, self.page)
        # fill in attributes used in index.html template
        self.prev_page = max(1, self.page - 1)
        self.next_page = min(self.num_pages, self.page + 1)
        self.current_url = request.path
        return

    @classmethod
    def from_query_string(cls, num_posts=None):
        if 'page' in request.args:
            try:
                page = int(request.args['page'])
            except ValueError:
                page = 1
        else:
            page = 1
        if 'count' in request.args:
            try:
                count = int(request.args['count'])
            except ValueError:
                count = posts_per_page
        else:
            count = posts_per_page
        return cls(page, count, num_posts)



def render_template_with_defaults(template, recent_posts=None, popular_posts=None,
                                  thedish=dish_info, error=None, pager=None,
                                  **kwargs):
    session = getattr(g, 'session', None)
    teams = dishsql.get_all_teams(session)
    if pager is None:
        pager = Paginator.from_query_string()
    if recent_posts is None:
        recent_posts = dishsql.get_recent_posts(page=pager.page, count=pager.count, session=session)
    if popular_posts is None:
        popular_posts = dishsql.get_popular_posts(page=1, count=popular_posts_per_page, session=session)
    return render_template(template, thedish=dish_info, teams=teams,
                           popular_posts=popular_posts,
                           recent_posts=recent_posts,
                           pager=pager,
                           error=error, **kwargs)

@app.route('/topics/<team_name>/', methods=['GET'])
def show_team_page(team_name):
    session = getattr(g, 'session', None)
    matching_team = dishsql.get_team_by_name(team_name, session)
    if not matching_team:
        error_string = "There is no page for the topic '{}'.".format(team_name)
        return render_template_with_defaults('index.html', error=error_string)
    num_posts = dishsql.get_num_posts_team(session, team_name)
    pager = Paginator.from_query_string(num_posts)
    recent_posts = dishsql.get_recent_posts_team(team_url_name=team_name,
            page=pager.page, count=pager.count, session=session)
    return render_template_with_defaults('team.html', team=matching_team,
                                         recent_posts=recent_posts, pager=pager)

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
    pager = Paginator.from_query_string()
    recent_posts = dishsql.get_recent_posts(page=pager.page, count=pager.count, session=session)
    return render_template_with_defaults('index.html', recent_posts=recent_posts)

@app.route('/posts/<post_name>/')
def send_post(post_name):
    session = getattr(g, 'session', None)
    matching_post = dishsql.get_post_by_name(post_name, session)
    if not matching_post:
        error_string = "No post with URL '{}posts/{}'".format(dish_info.url, post_name)
        return render_template_with_defaults('index.html', error=error_string)
    return render_template_with_defaults('post.html', post=matching_post)

@app.route('/editing/articles')
@app.route('/editing/articles.xlsx')
def redirect_to_drive():
    return redirect("https://drive.google.com/open?id=1R69WfpVN3L8xKHOSkQHUpIPWH-8kdpxCEwqbGm5bsrQ",
                    code=302)


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
    error_string += "<br />"
    error_string += dish_info.url[0:-1] + request.path
    # error_string += "<br />"
    # error_string += "<br />"
    # error_string += "Here's our homepage instead, hope you find what you're looking for!"
    return render_template_with_defaults('index.html', error=error_string)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
