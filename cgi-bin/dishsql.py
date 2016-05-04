from __future__ import print_function

import os
import sys
import json
import codecs
from collections import namedtuple
from dateutil.parser import parse

from contextlib import contextmanager
import sqlalchemy as sa
from sqlalchemy import Table, Column
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from thedish import app_dir, www_dir, posts_dir

sql_dir = os.path.join(app_dir, "db_private")
Base = declarative_base()
Session = sessionmaker()

post_directories = [os.path.join(posts_dir, folder)
                    for folder in os.listdir(posts_dir)]
post_directories = [post_dir for post_dir in post_directories if os.path.isdir(post_dir)]


post_author_table = Table('post_author', Base.metadata,
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), index=True))

post_illustrator_table = Table('post_illustrator', Base.metadata,
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), index=True))

post_team_table = Table('post_team', Base.metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), index=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), index=True))

author_team_table = Table('author_team', Base.metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), index=True),
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True))

alumni_team_table = Table('alumni_team', Base.metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), index=True),
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True))

def replace_with_database_if_exists(collection, uniq_field, session):
        replacements = [
                session.query(uniq_field.class_)
                .filter(uniq_field == elem.__dict__[uniq_field.key])
                .first()
                for elem in collection
            ]
        collection = [elem if elem is not None else collection[i]
                      for i,elem in enumerate(replacements)]
        return collection
        #init['authors'] = [Author(**(author._asdict())) for author in init['authors']]
        #authors_in_db = [session.query(Author).filter_by(name=a.name).first()
        #                 for a in init['authors']]
        #init['authors'] = [a if a is not None else init['authors'][i] for i,a
        #                   in enumerate(authors_in_db)]


class Author(Base):
    """Knows about an author for The Dish."""
    __tablename__ = 'author'

    id = Column(sa.Integer, primary_key=True, nullable=False)
    name = Column(sa.String(100), nullable=False)
    url_name = Column(sa.String(100), index=True, unique=True)
    description = Column(sa.String(1000))
    headshot_src = Column(sa.String(200))
    posts = relationship("Post", secondary=post_author_table,
                         back_populates="authors")

    def __repr__(self):
        return "<Author(%r, %r)>" % (
            self.id, self.name
        )

class Team(Base):
    """Knows about a blog team for The Dish."""
    __tablename__ = 'team'

    id = Column(sa.Integer, primary_key=True, nullable=False)
    name = Column(sa.String(100), nullable=False)
    url_name = Column(sa.String(100), nullable=False, index=True, unique=True)
    blurb = Column(sa.String(200))
    description = Column(sa.String(1000))
    thumbnail_src = Column(sa.String(200))
    logo_src = Column(sa.String(200))
    members = relationship("Author", secondary=author_team_table)
    alumni = relationship("Author", secondary=alumni_team_table)
    posts = relationship("Post", secondary=post_team_table,
                         back_populates="teams")

    def __repr__(self):
        return "<Team(id=%r, name=%r, url_name=%r)>" % (
            self.id, self.name, self.url_name)

    @classmethod
    def from_urlname(cls, url_name, session):
        return session.query(Team).filter_by(url_name=url_name).first()

# to support the old post_info.json format
default_post_dict_keys = ['title', 'url_title', 'blurb', 'description',
                          'publication_date', 'five_by_two_image_src',
                          'two_by_one_image_src',
                          'one_by_one_image_src' ]
num_keys = len(default_post_dict_keys)
default_post_dict = dict(zip(default_post_dict_keys, [None]*num_keys))

class Post(Base):
    """Knows about a blog post for The Dish."""
    __tablename__ = 'post'

    id = Column(sa.Integer, primary_key=True, nullable=False)
    title = Column(sa.String(200), nullable=False)
    url_title = Column(sa.String(200), nullable=False, index=True, unique=True)
    blurb = Column(sa.String(200))
    description = Column(sa.String(1000))
    publication_date = Column(sa.Date, nullable=False)
    five_by_two_image_src = Column(sa.String(200), nullable=False)
    two_by_one_image_src = Column(sa.String(200))
    one_by_one_image_src = Column(sa.String(200))
    view_count = Column(sa.Integer, nullable=False)
    authors = relationship("Author", secondary=post_author_table,
                            back_populates="posts")
    illustrators = relationship("Author", secondary=post_illustrator_table)
    teams = relationship("Team", secondary=post_team_table,
                         back_populates="posts")

    def __repr__(self):
        return "<Post(id=%r, url_title=%r)>" %(
            self.id, self.url_title)

    @classmethod
    def from_urltitle(cls, url_title, session):
        return session.query(Post).filter_by(url_title=url_title).first()

    @classmethod
    def from_folder(cls, post_directory, session):
        """Get a Post object from a valid path."""
        if not os.path.isdir(post_directory):
            return None
        url_title = os.path.basename(post_directory)
        post = session.query(Post).filter_by(url_title=url_title).first()
        if post is not None:
            return post
        xlsx_file = os.path.join(post_directory, 'post_info.xlsx')
        xls_file = os.path.join(post_directory, 'post_info.xls')
        json_file = os.path.join(post_directory, 'post_info.json')
        if os.path.isfile(xlsx_file):
            return cls.from_excel(xlsx_file)
        elif os.path.isfile(xls_file):
            return cls.from_excel(xls_file)
        elif os.path.isfile(json_file):
            return cls.from_json(json_file, session)
        else:
            print("ERROR: The post directory {} does not have a post_info file!".format(post_directory), file=sys.stderr)
            return None

    @classmethod
    def from_json(cls, post_file, session):
        """ Read JSON into self.__dict__ and pull in HTML of post"""
        post_data = codecs.open(post_file, 'r', encoding='utf-8').read()
        try:
            data = json.loads(post_data, object_hook=lambda d: namedtuple('Post', d.keys())(*d.values()))
        except:
            print("ERROR: Cannot parse the file {}!".format(post_file), file=sys.stderr)
            return None
        init = default_post_dict.copy()
        init.update(data._asdict())
        if not init['publication_date']:
            print("ERROR: No publication_date field in the file {}!".format(post_file), file=sys.stderr)
            return None
        init['publication_date'] = parse(init['publication_date'])
# it's not expected that Teams get created all the time, so if it looks like
# you're trying to create a Team that does not exist, error out to force the
# admin can manually enter the team, as this is likely an error
        for i,team in enumerate(init['teams']):
            db_team = session.query(Team).filter_by(url_name=team).first()
            if db_team:
                init['teams'][i] = db_team
                continue
            db_team = session.query(Team).filter_by(name=team).first()
            if db_team:
                init['teams'][i] = db_team
                continue
# if the string provided doesn't match the team name or url name, it's not
# valid
            print("ERROR: The file {} references the team {}, which does not exist!".format(post_file, team), file=sys.stderr)
            return None
# on the other hand, authors will likely be created for most new posts, so if
# we find an author that did not previously exist, we will construct it, since
# at this point it nothing else in the post construction process can error
        init['authors'] = [Author(**(author._asdict())) for author in init['authors']]
        init['authors'] = replace_with_database_if_exists(init['authors'], Author.name, session)
        # authors_in_db = [session.query(Author).filter_by(name=a.name).first()
        #                  for a in init['authors']]
        # init['authors'] = [a if a is not None else init['authors'][i] for i,a
        #                    in enumerate(authors_in_db)]
        if 'illustrators' in init:
            init['illustrators'] = [Author(**(author._asdict())) for author in init['illustrators']]
            illustrators_in_db = [session.query(Author).filter_by(name=a.name).first()
                            for a in init['illustrators']]
            init['illustrators'] = [a if a is not None else init['illustrators'][i] for i,a
                            in enumerate(illustrators_in_db)]
# for now, post count will always restart at zero when an article is
# reconstructed from its JSON specification. TODO: put in correct view counts
# from e.g. google analytics upon recreation. Maybe somethign like the
# instructions at: https://developers.google.com/analytics/devguides/reporting/core/v4/#choosing_which_version_of_the_analytics_reporting_api_to_use
# ?
        init['view_count'] = 0
        return cls(**init)

    @property
    def url(self):
        return '/posts/' + str(self.url_title)

    @property
    def absolute_url(self):
        return thedish.url + self.url

    @property
    def post_directory(self):
        return os.path.join(posts_dir, self.url_title)

    @property
    def html(self):
        html_file = os.path.join(self.post_directory, 'post.html')
        md_file = os.path.join(self.post_directory, 'post.md')
        if not os.path.isfile(md_file) and not os.path.isfile(html_file):
            #TODO: allow LaTeX. For now, there's no post content here, return an empty post
            return ''
        should_rebuild_html = not os.path.isfile(html_file) \
                or os.path.isfile(md_file) \
                and os.path.getctime(md_file) > os.path.getctime(html_file)
        if should_rebuild_html:
            md_text = codecs.open(md_file, 'r', encoding='utf-8').read()
            html = markdown.markdown(md_text)
            codecs.open(html_file, 'w', encoding='utf-8', errors='xmlcharrefreplace').write(html)
        return codecs.open(html_file, 'r', encoding='utf-8').read()

# # metadata associated with the MySQL server we will be using to get post,
# # author, and team information
# metadata = sa.MetaData()
# team_table = Table('team', metadata,
#     Column('id', sa.Integer, primary_key=True, nullable=False),
#     Column('name', sa.String(100), nullable=False),
#     Column('url_name', sa.String(100), nullable=False, index=True, unique=True),
#     Column('blurb', sa.String(200)),
#     Column('description', sa.String(200)),
#     Column('thumbnail_src', sa.String(200)),
#     Column('logo_src', sa.String(200)))

# author_table = Table('author', metadata,
#     Column('id', sa.Integer, primary_key=True, nullable=False),
#     Column('name', sa.String(100), nullable=False),
#     Column('nickname', sa.String(100)),
#     Column('url_name', sa.String(100), nullable=False, index=True, unique=True),
#     Column('blurb', sa.String(200)),
#     Column('description', sa.String(200)),
#     Column('image_src', sa.String(200)))

# post_table = Table('post', metadata,
#     Column('id', sa.Integer, primary_key=True, nullable=False),
#     Column('title', sa.String(200), nullable=False),
#     Column('url_title', sa.String(200), nullable=False, index=True, unique=True),
#     Column('blurb', sa.String(200)),
#     Column('description', sa.String(200)),
#     Column('publication_date', sa.Date, nullable=False),
#     Column('five_by_two_image_src', sa.String(200), nullable=False),
#     Column('two_by_one_image_src', sa.String(200)),
#     Column('one_by_one_image_src', sa.String(200)),
#     Column('view_count', sa.Integer, nullable=False))

#myDB = URL(drivername='mysql', username='gthedishonscie', host='g-thedishonscience-dish-website.sudb.stanford.edu',
#    database='g_thedishonscience_dish_website', query={'read_default_file':
#    os.path.join(sql_dir, '.mylogin.cnf')})
#TODO find prettier way to do this
#connection_url = str(myDB) + "&charset=utf8"
#connection_url = "mysql://gthedishonscie:***REMOVED***@g-thedishonscience-dish-website.sudb.stanford.edu/g_thedishonscience_dish_website?charset=utf8"
connection_url = "mysql+pymysql://gthedishonscie:***REMOVED***@localhost/g_thedishonscience_dish_website?charset=utf8"
engine = sa.create_engine(name_or_url=connection_url, echo=True)
Base.metadata.create_all(engine)
Session.configure(bind=engine)
#metadata.create_all(engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def get_recent_posts_team(team_url_name, offset, limit):
    conn = engine.connect()
    select_team_id = select([team_table.c.id]
        ).where(team_table.c.url_name == team_url_name)
    team_id = conn.execute(select_team_id).fetchone()
    # if the requested team does not exist
    if team_id is None:
        return None
    # otherwise get the actual id to compare against from the results
    team_id = team_id[0]
    select_recent_posts_team = select([post_table.c.url_title]
        ).order_by(post_table.c.publication_date.desc()
        ).select_from(post_table.join(post_team_table)
        ).where(post_team_table.c.team_id == team_id
        ).offset(offset
        ).limit(limit)
    results = conn.execute(select_recent_posts_team)
    url_titles = results.fetchall()
    results.close()
    conn.close()
    if url_titles is None:
        return None
    posts = [Post.from_urltitle(url_title[0], session)
                  for url_title in url_titles]
    return posts

def get_recent_posts(offset, limit):
    conn = engine.connect()
    select_recent_posts_team = select([post_table.c.url_title]
        ).order_by(post_table.c.publication_date.desc()
        ).offset(offset
        ).limit(limit)
    results = conn.execute(select_recent_posts_team)
    url_titles = results.fetchall()
    results.close()
    conn.close()
    if url_titles is None:
        return None
# TODO use the database row to make the Post entry instead of re-reading the
# post_info.json file
    posts = [Post.from_urltitle(url_title[0], session)
                  for url_title in url_titles]
    return posts

def get_popular_posts(offset, limit):
    conn = engine.connect()
    select_recent_posts_team = select([post_table.c.url_title]
        ).order_by(post_table.c.view_count.desc()
        ).offset(offset
        ).limit(limit)
    results = conn.execute(select_recent_posts_team)
    url_titles = results.fetchall()
    results.close()
    conn.close()
    if url_titles is None:
        return None
# TODO use the database row to make the Post entry instead of re-reading the
# post_info.json file
    posts = [Post.from_urltitle(url_title[0], session)
                  for url_title in url_titles]
    return posts

def get_team_by_name(team_name):
    matching_teams = [team for team in teams if team.name == team_name or team.url_name == team_name]
    if not matching_teams:
        return None
    return matching_teams[0]

def get_post_by_name(post_name):
    conn = engine.connect()
    url_title = post_name
    select_if_exists_post = select([post_table.c.url_title]
        ).where(post_table.c.url_title == url_title)
    results = conn.execute(select_if_exists_post)
    url_title = results.fetchone()
    results.close()
    if url_title is None:
        return None
    update = post_table.update().where(
        post_table.c.url_title == url_title
        ).values({post_table.c.view_count: post_table.c.view_count+1})
    conn.execute(update)
    results.close()
    conn.close()
    return Post(os.path.join(www_dir, 'posts', url_title[0]))

def build_all_teams(session):
    """Construct all team rows from a global file, blog-teams.json."""
    team_data_file = os.path.join(www_dir, 'assets', 'info', 'blog-teams.json')
    team_data = codecs.open(team_data_file, 'r', encoding='utf-8').read()
    teams = json.loads(team_data, encoding='utf-8', object_hook=lambda d: namedtuple('Team', d.keys())(*d.values())).teams
    teams = [Team(**(team._asdict())) for team in teams]
    return teams

def insert_all_teams():
    """Insert all teams in blog-teams.json into the database."""
    with session_scope() as session:
        teams = build_all_teams(session)
        teams = [team for team in teams if session.query(Team).filter_by(url_name=team.url_name).first() is None]
        session.add_all(teams)

def build_all_posts(session):
    """Construct all post objects from the directories in :/WWW/posts"""
    return [Post.from_folder(post_dir, session) for post_dir in post_directories]

def insert_all_posts():
    with session_scope() as session:
        posts = build_all_posts(session)
        posts = [post for post in posts if session.query(Post).filter_by(url_title=post.url_title).first() is None]
        session.add_all(posts)

def initialize_website():
    """Insert all teams, then all posts/authors."""
    insert_all_teams()
    insert_all_posts()
