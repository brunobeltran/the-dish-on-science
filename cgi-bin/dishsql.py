from __future__ import print_function

import os
import sys
import json
import codecs
import string
import re
from collections import namedtuple
import dateutil.parser
import random
# from enum import Enum

# for creating posts objects from a directory
from xlsx_to_json import xlsx_to_json
sys.path = ['Python-Markdown'] + sys.path
from markdown import markdownFromFile

from contextlib import contextmanager
import sqlalchemy as sa
from sqlalchemy import Table, Column, orm
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import thedish
# import logging
# logging.basicConfig()
# logger = logging.Logger('dishsql.py')

# setup object that knows how to open connection to database

# # the connection we're going to make, as a URL, looks like:
# connection_url = "mysql://gthedishonscie:[password]@g-thedishonscience-dish-website.sudb.stanford.edu/g_thedishonscience_dish_website?charset=utf8"
sql_dir = os.path.join(thedish.app_dir, "db_private")
dish_db = URL(drivername='mysql',
              database='g_thedishonscience_dish_website',
              query={'charset': 'utf8', 'read_default_file':
                     os.path.join(sql_dir, '.dishlogin.cnf')}
              # charset='utf8' # force utf-8 in mysql connections/sessions
             )
# a debugging version that outputs all sql queries emitted
# engine = sa.create_engine(name_or_url=dish_db, encoding='utf-8', echo=True)
# force utf-8 outside of dbapi calls as well
engine = sa.create_engine(name_or_url=dish_db, encoding='utf-8', echo=False)

# object to hold all information about our schema and ORM
Base = declarative_base()
# object to create sessions with the SQL backend using the connection described
# above in engine
Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations. A context
    manager for a sqlalchemy session."""
    session = Session() # use the sessionmaker object we created above
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def urlify(string):
    """Make a string (e.g. author name) into a URL friendly format."""
    return string.lower().replace(' ', '-')

def replace_with_database_if_exists(obj, uniq_field, session):
    """Helper method to aid in construction of e.g. Post objects. Returns a
    copy of its input, with all objects that were already in the database
    replaced by their fetch'd counterparts. Takes an object, a session, and a
    column to query equality by."""
    replacement = session.query(uniq_field.class_
        ).filter(uniq_field == obj.__dict__[uniq_field.key]
        ).first()
    return replacement if replacement else obj
    ## here's the in-place version of the code, took a list of obj's
    # replacements = [
    #         session.query(uniq_field.class_)
    #         .filter(uniq_field == elem.__dict__[uniq_field.key])
    #         .first()
    #         for elem in collection
    #     ]
    # collection = [elem if elem is not None else collection[i]
    #               for i,elem in enumerate(replacements)]
    # return collection
    ## originally generalized from the following outdated,specific code
    #init['authors'] = [Author(**(author._asdict())) for author in init['authors']]
    #authors_in_db = [session.query(Author).filter_by(name=a.name).first()
    #                 for a in init['authors']]
    #init['authors'] = [a if a is not None else init['authors'][i] for i,a
    #                   in enumerate(authors_in_db)]

# centralized location for all size limits of our tables
limits = {'preferred': {}, 'max': {}}
limits['max']['name'] = 200
limits['max']['url_name'] = 200
limits['max']['title'] = 200
limits['max']['blurb'] = 400
limits['max']['url_title'] = 200
limits['max']['description'] = 1000
limits['max']['team_description'] = 1250 # to accomodate marine-biology
limits['max']['path'] = 200

limits['preferred']['name'] = 200
limits['preferred']['url_name'] = 200
limits['preferred']['title'] = 200
limits['preferred']['blurb'] = 100
limits['preferred']['url_title'] = 100
limits['preferred']['description'] = 500
limits['preferred']['path'] = 200

def validate_length(data, name):
    if len(data) > limits['preferred'][name]:
        pass # logger.warning(name + ' longer than recommended: ' + data)
    if len(data) > limits['max'][name]:
        # logger.error(name + ' too long to fit into database: ' + data)
        return False
    return True

class CannotFixError(Exception):
    """a useful exception during construction of Posts. oftentimes, we can fix small
    problems and will do so on the fly, like missing nicknames, but some problems
    we just can't fix..., like invalid team names."""
    pass

class UpdateBehavior(object):
    """an enum describing what kind of behavior to perform on construction of a ORM
    object if it already exists in the database"""
    replace = 0
    update = 1
    leave = 2
# class UpdateBehavior(Enum):
#     """an enum describing what kind of behavior to perform on construction of a ORM
#     object if it already exists in the database"""
#     replace = 0
#     update = 1
#     leave = 2

def execute_update_behavior(new_cls, existing_cls, session, update_behavior):
    if existing_cls is None:
        return new_cls
    if update_behavior == UpdateBehavior.leave:
        return existing_cls
    elif update_behavior == UpdateBehavior.update:
        for attr in new_cls._sa_instance_state.attrs.keys():
            if attr not in new_cls._sa_instance_state.unmodified:
                setattr(existing_cls, attr, getattr(new_cls, attr))
        if new_cls in session:
            session.expunge(new_cls)
        return existing_cls
    elif update_behavior == UpdateBehavior.replace:
        existing_cls.delete()
        session.add(new_cls)
        return new_cls
    else:
        raise ValueError("Unknown UpdateBehavior requested.")

# the relationship tables are easy to specify, since no ORM needed
post_author_table = Table('post_author', Base.metadata,
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), index=True))

post_illustrator_table = Table('post_illustrator', Base.metadata,
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), index=True))
# to allow different nicknames per article, add a column here
# and an analogous one in the illustrator table
    #Column('nickname', sa.String(limits['max']['name']))

post_team_table = Table('post_team', Base.metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), index=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), index=True))

author_team_table = Table('author_team', Base.metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), index=True),
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True))


# throughout the code, illustrators are always an instance of the Author class.
# there is no "class Illustrator(Base):"...
class Author(Base):
    """Knows about an author for The Dish."""
    __tablename__ = 'author'

    id = Column(sa.Integer, primary_key=True, nullable=False)
    name = Column(sa.String(limits['max']['name']), nullable=False)
    nickname = Column(sa.String(limits['max']['name']))
    url_name = Column(sa.String(limits['max']['url_name']), nullable=False, index=True, unique=True)
    description = Column(sa.String(limits['max']['description']))
    headshot_src = Column(sa.String(limits['max']['path']), nullable=False)
    blurb = Column('blurb', sa.String(limits['max']['blurb']))
    description = Column('description', sa.String(limits['max']['description']))
    posts = relationship("Post", secondary=post_author_table,
                         back_populates="authors")
    teams = relationship("Team", secondary=author_team_table,
                         back_populates="members")

    def __repr__(self):
        return "<Author(%r, %r)>" % (
            self.id, self.name
        )

    @property
    def line_broken_nickname(self):
        if self.nickname is None:
            return None
        if len(self.nickname) > 14:
            return self.nickname.replace(' ', '<br />').replace('-', '-<br />')
        else:
            return self.nickname

    @classmethod
    def get_or_create(cls, author_dict, session=None,
                      update_behavior=UpdateBehavior.update):
        self = cls()
        if 'url_name' not in author_dict:
            author_dict['url_name'] = urlify(author_dict['name'])
        for key, val in author_dict.items():
            setattr(self, key, val)
        # gracefully return an object if no database connection
        if session is None:
            return self
        # post we're constructing musn't be flushed yet, so that we can choose
        # which version we're keeping based on update_behavior
        with session.no_autoflush:
            existing_author = session.query(Author).filter_by(url_name=author_dict['url_name']).first()
            # this line wouldn't work in a classical constructor
            self = execute_update_behavior(self, existing_author, session, update_behavior)
        return self
        # if update_behavior == UpdateBehavior.leave:
        #     # this line won't work if this is made a classical constructor
        #     self = existing_author
        # elif update_behavior == UpdateBehavior.update:
        #     for key, val in author_dict.items():
        #         setattr(existing_author, key, val)
        # elif update_behavior == UpdateBehavior.replace:
        #     existing_author.delete()
        #     for key, val in author_dict.items():
        #         setattr(self, key, val)
        #     session.add(self)
        # else:
        #     raise ValueError("Author.get_or_create: unknown UpdateBehavior")
        # return self

class Team(Base):
    """Knows about a blog team for The Dish."""
    __tablename__ = 'team'

    id = Column(sa.Integer, primary_key=True, nullable=False)
    name = Column('name', sa.String(limits['max']['name']), nullable=False)
    url_name = Column('url_name', sa.String(limits['max']['url_name']),
                      nullable=False, index=True, unique=True)
    blurb = Column('blurb', sa.String(limits['max']['blurb']))
    description = Column('description', sa.String(limits['max']['team_description']))
    thumbnail_src = Column('thumbnail_src', sa.String(limits['max']['path']))
    logo_src = Column('logo_src', sa.String(limits['max']['path']))
    members = relationship("Author", secondary=author_team_table,
                         back_populates="teams")
    posts = relationship("Post", secondary=post_team_table,
                         back_populates="teams")

    def __repr__(self):
        return "<Team(id=%r, name=%r, url_name=%r)>" % (
            self.id, self.name, self.url_name)

    @classmethod
    def get_or_create(cls, team_dict, session=None, update_behavior=UpdateBehavior.leave):
        self = cls()
        for key, val in team_dict.items():
            setattr(self, key, val)
        # gracefully return an object if no database connection
        if session is None:
            return self
        # team we're constructing musn't be flushed yet, so that we can choose
        # which version we're keeping based on update_behavior
        with session.no_autoflush:
            existing_team = session.query(Team).filter_by(url_name=team_dict['url_name']).first()
            # this line wouldn't work in a classical constructor
            self = execute_update_behavior(self, existing_team, session, update_behavior)
        return self
        # if update_behavior == UpdateBehavior.leave:
        #     # this line won't work if this is made a classical constructor
        #     self = existing_team
        # elif update_behavior == UpdateBehavior.update:
        #     for key, val in team_dict.items():
        #         setattr(existing_team, key, val)
        # elif update_behavior == UpdateBehavior.replace:
        #     existing_team.delete()
        #     for key, val in team_dict.items():
        #         setattr(self, key, val)
        #     session.add(self)
        # else:
        #     raise ValueError("Team.get_or_create: unknown UpdateBehavior")
        # return self

    @classmethod
    def from_urlname(cls, url_name, session):
        return session.query(Team).filter_by(url_name=url_name).first()

    @property
    def url(self):
        return '/topics/' + str(self.url_name)

    @property
    def absolute_url(self):
        return thedish.dish_info.url + self.url

# to support the old post_info.json format
default_post_dict_keys = ['title', 'url_title', 'blurb', 'description',
                          'publication_date', 'five_by_two_image_src',
                          'two_by_one_image_src',
                          'one_by_one_image_src' ]
num_keys = len(default_post_dict_keys)
default_post_dict = dict(zip(default_post_dict_keys, [None]*num_keys))
default_post_dict['illustrators'] = []
default_post_dict['authors'] = []
default_post_dict['teams'] = []

# helper methods to verify that a post we're constructing from a file is
# not invalid
def fix_publication_date(post_dict):
    if not 'publication_date' in post_dict:
        raise CannotFixError("No publication date provided for article: "
                                + post_dict['url_title'])

def fix_title(post_dict):
    if not validate_length(post_dict['title'], 'title'):
        raise CannotFixError("Can't fix the title!")

def fix_url(post_dict):
    if not validate_length(post_dict['url_title'], 'url_title'):
        raise CannotFixError('Cannot fix url_title!')
    allowed_chars = set(string.ascii_lowercase + string.digits + '-')
    if not set(post_dict['url_title']) <= allowed_chars:
        pass # logger.warning('Illegal characters in URL!: ' + post_dict['url_title'])

def fix_blurb(post_dict):
    if not validate_length(post_dict['blurb'], 'blurb'):
        raise CannotFixError('Cannot fix blurb!')

def fix_description(post_dict):
    if not 'description' in post_dict:
        raise CannotFixError('No description provided!')
    if not validate_length(post_dict['description'], 'description'):
        new_len = limits['max']['description']
        # logger.warning('Truncating post description!')
        post_dict['description'] = post_dict['description'][0:new_len-3] + '...'


def fix_teams(post_dict, session):
    # teams are selected from a list of known good teams, so they can't
    # really be messed up. So here, we just have to make sure that there
    # are teams listed at all....or so I thought. turns out people don't
    # know how to use drop down menus, so we'll have to really check this.
    if not 'teams' in post_dict:
        raise CannotFixError('No teams were provided when '
                             + 'constructing Post: ' + post_dict['url_title'])

    # it's not expected that Teams get created all the time, so if it looks
    # like you're trying to create a Team that does not exist, error out to
    # force the admin can manually enter the team, as this is likely an
    # error
    for i,team in enumerate(post_dict['teams']):
        db_team = session.query(Team).filter_by(url_name=team).first()
        if db_team:
            post_dict['teams'][i] = db_team
            continue
        db_team = session.query(Team).filter_by(name=team).first()
        if db_team:
            post_dict['teams'][i] = db_team
            continue
        # if the string provided doesn't match the team name or url name,
        # it's not valid
        raise CannotFixError(post_dict['url_title'] + " references the team "
                             + team + ", which does not exist!")

def fix_authors(post_dict, session=None):
    # if no author name specified, use team name
    if not 'authors' in post_dict:
        # logger.warning('No author names specified! Using team names instead.')
        post_dict['authors'] = [Author.get_or_create(team, session) for team in post_dict['teams']]
    # open up a session for querying if the authors exist ONLY, no updating
    # will be done in this session
    post_dict['authors'] = [fix_author(post_dict, author, session)
                            for author in post_dict['authors']]
    if not 'illustrators' in post_dict:
        post_dict['illustrators'] = []
    else:
        post_dict['illustrators'] = [fix_author(post_dict, illustrator, session)
                                     for illustrator in post_dict['illustrators']]
    # writing an article for a team makes you part of that team
    for team in post_dict['teams']:
        for author in post_dict['authors']:
            if team not in author.teams:
                author.teams.append(team)
        for illustrator in post_dict['illustrators']:
            if team not in post_dict['teams']:
                illustrator.teams.append(team)

def fix_author(post_dict, author, session=None):
    # authors will likely be created for most new posts, so if we find an
    # author that did not previously exist, we will construct it

    # must fix name first, others use it for logging
    author['name'] = Post.fix_author_name(author)
    author['nickname'] = Post.fix_author_nickname(author)
    author['headshot_src'] = fix_author_headshot_src(post_dict, author)
    author = Author.get_or_create(author, session)
    return author

def fix_author_headshot_src(post_dict, author):
    default_images = ['/images/cow.png', '/images/dinosaur.png',
                    '/images/elephant.png', '/images/hedgehog.png',
                    '/images/monkey.jpeg', '/images/panda.png',
                    '/images/paperplane.png', '/images/penguin.png',
                    '/images/turkey.png']
    if 'headshot_src' in author and author['headshot_src']:
        headshot_src = author['headshot_src']
    else:
        # logger.warning("No headshot prived for author {} in post {},
        #                "using a random default.".format(
        #                author['name'], self.url_title)
        rand_idx = random.randint(0, len(default_images)-1)
        headshot_src = default_images[rand_idx]
    looks_like_default_attempt = re.compile('^/images/[^/]*')
    looks_like_global_author_attempt = re.compile('^/images/' + author['name'] + '/.*')
    if looks_like_default_attempt.match(headshot_src):
        if headshot_src not in default_images:
            # logger.warning("Looks like you're trying to use a stock animal " \
                        # "image for the author " + author + ", but it " \
                        # "doesn't match any of the images available!")
            # logger.warning("Replacing headshot_src with random animal for "
                        # + str(author))
            return default_images[random.randint(0, len(default_images)-1)]
        # they've got a valid default image, use it
        return headshot_src
    # they're allowed to send us files to save in /images/$author_name/
    # if they sent the file with the article, move it into the global
    # directory
    elif looks_like_global_author_attempt.match(headshot_src):
        author_images_dir, filename = os.path.split(headshot_src)
        author_images_dir = '/images/' + author['name']
        maybe_filename1 = os.path.join(thedish.www_dir, headshot_src)
        maybe_filename2 = os.path.join(thedish.www_dir, author_images_dir + filename)
        maybe_filename3 = os.path.join(thedish.www_dir, 'posts', post_dict['url_title'], 'images', filename)
        # if the file is already in the right place:
        if os.path.isfile(maybe_filename1):
            return headshot_src
        # maybe we can recover the right file by guessing
        elif os.path.isfile(maybe_filename2):
            return author_images_dir + filename
        # maybe it's in the post's images directory instead
        elif os.path.isfile(maybe_filename3):
            if not os.path.isdir(author_images_dir):
                os.mkdir(author_images_dir, mode=755)
            shutil.copyfile(maybe_filename3, maybe_filename2)
            return author_images_dir + filename
        else:
            # logger.error('Cannot find headshot file, looks like you ' \
                            # + 'wanted to use a centrally saved one ' \
                            # + 'from /images/?: ' + headshot_src)
            raise CannotFixError('Cannot find headshot_src: ' +
                                    headshot_src)
    # otherwise it's just a regular file, probably saved in their post's
    # images directory
    else:
        return fix_image_file_name(post_dict, author['headshot_src'])

#TODO: update these to downsample large images, crop to get
# two_by_one/one_by_one from five_by_one, etc..
def fix_five_by_two_image_src(post_dict):
    if 'five_by_two_image_src' not in post_dict \
    or not post_dict['five_by_two_image_src']:
        CannotFixError('No main article image (five_by_two_image_src) provided'
                       + 'for article: ' + post_dict['url_title'])
    post_dict['five_by_two_image_src'] = fix_image_file_name(post_dict, post_dict['five_by_two_image_src'])

def fix_two_by_one_image_src(post_dict):
    if 'two_by_one_image_src' in post_dict and post_dict['two_by_one_image_src']:
        post_dict['two_by_one_image_src'] = fix_image_file_name(post_dict, post_dict['two_by_one_image_src'])
    else:
        post_dict['two_by_one_image_src'] = post_dict['five_by_two_image_src']

def fix_one_by_one_image_src(post_dict):
    if 'one_by_one_image_src' in post_dict and post_dict['one_by_one_image_src']:
        post_dict['one_by_one_image_src'] = fix_image_file_name(post_dict, post_dict['one_by_one_image_src'])
    else:
        post_dict['one_by_one_image_src'] = post_dict['five_by_two_image_src']


def fix_image_file_name(post_dict, file_name):
    if not file_name:
        raise CannotFixError('Cannot fix empty image file name from post: '
                       + post_dict['url_title'])
    looks_like_local_attempt = re.compile('(\./).*')
    looks_like_raw_filename = re.compile('[a-zA-Z0-9-_]+\.[a-zA-Z]')
    # looks_like_absolute_attempt = re.compile('.*/posts/.*/images/.*')
    if looks_like_local_attempt.match(file_name):
        # don't forget to strip the / from self.url, os.path.join ignores
        # all arguments that come before the first one that it thinks looks
        # like an absolute path
        supposed_file = os.path.normpath(os.path.join(thedish.www_dir,
                                                      'posts',
                                                      post_dict['url_title'],
                                                      file_name))
        if not os.path.isfile(supposed_file):
            # logger.error("Looks like you referred to an image with a " \
                            # + "relative URL, but the image does not appear " \
                            # + " to exist: " \
                            # + file_name)
            raise CannotFixError(post_dict['url_title']
                                 + ': Cannot find image file: ' + file_name)
        # make into absolute path for website
        file_name = os.path.normpath(os.sep + os.path.join('posts', post_dict['url_title'], file_name))
    elif looks_like_raw_filename.match(file_name):
        local_option = os.path.normpath(os.path.join(thedish.www_dir,
                                                      'posts',
                                                      post_dict['url_title'],
                                                      'images',
                                                      file_name))
        absolute_option = os.path.normpath(os.path.join(thedish.www_dir,
                                                        'images',
                                                        file_name))
        if os.path.isfile(local_option):
            file_name = os.path.normpath(os.sep + os.path.join('posts',
                                                               post_dict['url_title'],
                                                               'images',
                                                               file_name))
        elif os.path.isfile(absolute_option):
            file_name = os.path.normpath(os.sep + os.path.join('images', file_name))
        else:
            raise CannotFixError(post_dict['url_title'] + ': Cannot find file '
                                 + file_name + '. Seems to be a filename with '
                                 + 'no path information but not found in '
                                 + '/images or in /posts/NAME/images.')

    else: # if looks_like_absolute_attempt.match(file_name):
        # if it's a properly formatted absolute url, it should start with
        if file_name[0] != '/':
            # but try to do the right thing even if it doesn't
            file_name = '/' + file_name
        supposed_file = os.path.join(thedish.www_dir, file_name[1:])
        if not os.path.isfile(supposed_file):
            # logger.error("Looks like you're trying to use a post-specific " \
                            # + "author headshot, but the file does not exist: " \
                            # + file_name)
            raise CannotFixError(post_dict['url_title']
                                 + ': Cannot find image file: ' + file_name)
    return file_name


class Post(Base):
    """Knows about a blog post for The Dish."""
    __tablename__ = 'post'

    id = Column(sa.Integer, primary_key=True, nullable=False)
    title = Column(sa.String(limits['max']['title']), nullable=False)
    url_title = Column(sa.String(limits['max']['url_title']), nullable=False, index=True, unique=True)
    blurb = Column(sa.String(limits['max']['blurb']))
    description = Column(sa.String(limits['max']['description']))
    publication_date = Column(sa.Date, nullable=False)
    five_by_two_image_src = Column(sa.String(limits['max']['path']), nullable=False)
    two_by_one_image_src = Column(sa.String(limits['max']['path']))
    one_by_one_image_src = Column(sa.String(limits['max']['path']))
    view_count = Column(sa.Integer, nullable=False)
    authors = relationship("Author", secondary=post_author_table,
                            back_populates="posts")
    illustrators = relationship("Author", secondary=post_illustrator_table)
    teams = relationship("Team", secondary=post_team_table,
                         back_populates="posts")

    # fix_url must be first, since other error loggers depend on its presence.
    # fix_teams before you fix_authors, so that the author/team associations
    # are correctly inserted. fix_authors also fixes illustrators.
    # fix_two_by.. and fix_one_by.. count on five_by_two image src being
    # correctly present.
    post_integrity_checkers = [fix_url, fix_publication_date, fix_blurb,
                 fix_description, fix_title,
                 fix_five_by_two_image_src,
                 fix_two_by_one_image_src,
                 fix_one_by_one_image_src]
    post_association_checkers = [fix_teams, fix_authors]

    def __repr__(self):
        return "<Post(id=%r, url_title=%r)>" %(
            self.id, self.url_title)

    # this dict should have the form one would get form loading a
    # post_info.json file directly as a python dict.
    # because Post has associations to other objects (i.e. Author and Team), it
    # doesn't really make sense for a Post to exist outside of the context of a
    # session with the SQL server.
    @classmethod
    def get_or_create(cls, post_dict, session=None, update_behavior=UpdateBehavior.leave):
        self = cls()
        for key, val in default_post_dict.items():
            setattr(self, key, val)
        self.post_dict = post_dict.copy()
        self.session = session
        for fix_func in Post.post_integrity_checkers:
            fix_func(self.post_dict)
        with self.session.no_autoflush: # post we're constructing musn't be flushed yet
            for ass_func in Post.post_association_checkers:
                ass_func(self.post_dict, self.session)
        for key, val in self.post_dict.items():
            setattr(self, key, val)
        # interesting corner case, because of no_autoflush, and since we keep
        # authors and illustartors in the same table...having an author also
        # list themselves as an illustrator causes an error. For now, seems
        # fine to just delete the "illustrator" from the list
        new_illustrators = []
        for illustrator in self.illustrators:
            is_also_author = [author for author in self.authors
                              if illustrator.url_name == author.url_name]
            is_new = illustrator in session.new
            if is_also_author and is_new:
                session.expunge(illustrator)
                new_illustrators.append(is_also_author[0])
            else:
                new_illustrators.append(illustrator)
        self.illustrators = new_illustrators
        self.publication_date = dateutil.parser.parse(self.publication_date)

        # for now, post count will always restart at zero when an article is
        # reconstructed from its JSON specification
        self.view_count = 0

        # and always reconstruct html if necessary
        html_file = os.path.join(self.post_directory, 'post.html')
        md_file = os.path.join(self.post_directory, 'post.md')
        # if not os.path.isfile(md_file) and not os.path.isfile(html_file):
        #     #TODO: allow LaTeX.
        should_rebuild_html = not os.path.isfile(html_file) \
                or os.path.isfile(md_file) \
                and os.path.getctime(md_file) > os.path.getctime(html_file)
        if should_rebuild_html:
            markdownFromFile(input=md_file, output=html_file,
                             encoding='utf-8',
                             extensions=['markdown.extensions.footnotes'])
        # gracefully return an object even is there is no connection
        if session is None:
            return self
        # post we're constructing musn't be flushed yet, so that we can choose
        # which version we're keeping based on update_behavior
        with self.session.no_autoflush:
            existing_post = session.query(Post).filter_by(url_title=self.url_title).first()
            # this line wouldn't work in a classical constructor
            self = execute_update_behavior(self, existing_post, session, update_behavior)
        return self

    @classmethod
    def from_urltitle(cls, url_title, session):
        return session.query(Post).filter_by(url_title=url_title).first()

    @classmethod
    def from_folder(cls, post_directory, session=None,
                    update_behavior=UpdateBehavior.update):
        """Get a Post object from a valid path. Should not be used during
        normal website operation, only for constructing post objects to insert
        into the SQL table. if the post exists in the database already, the
        kwarg replace=True specifies whether to replace the entry with the data
        in the directory specified."""
        if not os.path.isdir(post_directory):
            return None
        url_title = os.path.basename(post_directory)
        xlsx_file = os.path.join(post_directory, 'post_info.xlsx')
        xls_file = os.path.join(post_directory, 'post_info.xls')
        json_file = os.path.join(post_directory, 'post_info.json')
        # excel file should take priority, json file should be generated from
        # it
        if os.path.isfile(xlsx_file):
            xlsx_to_json(xlsx_file, json_file)
            return cls.from_json(json_file, session, update_behavior)
        elif os.path.isfile(xls_file):
            xlsx_to_json(xls_file, json_file)
            return cls.from_json(json_file, session, update_behavior)
        elif os.path.isfile(json_file):
            return cls.from_json(json_file, session, update_behavior)
        else:
            # logger.error("The post directory {} does not have a post_info file!".format(post_directory), file=sys.stderr)
            return None

    @classmethod
    def from_json(cls, post_file, session=None,
                  update_behavior=UpdateBehavior.update):
        """ Read JSON into a dict to pass our constructor. Should not be used
        during normal website operation, only for constructing post objects to
        insert into the SQL table."""
        post_data = codecs.open(post_file, 'r', encoding='utf-8').read()
        try:
            post_dict = json.loads(post_data)
        except:
            # logger.error("ERROR: Cannot parse the file {}!".format(post_file), file=sys.stderr)
            return None
        return cls.get_or_create(post_dict, session, update_behavior)

    @property
    def url(self):
        return '/posts/' + str(self.url_title)

    @property
    def absolute_url(self):
        return thedish.dish_info.url + self.url

    @property
    def post_directory(self):
        return os.path.join(thedish.posts_dir, self.url_title)

    @property
    def html(self):
        """Read the html file into memory and return it."""
        html_file = os.path.join(self.post_directory, 'post.html')
        if not os.path.isfile(html_file):
            return '<p>Error, post not found!</p>'
        return codecs.open(html_file, 'r', encoding='utf-8').read()

    @staticmethod
    def fix_author_name(author):
        if 'name' not in author or not validate_length(author['name'], 'name'):
            raise CannotFixError("Can't fix the author name: " + author['name'] + "!")
        return author['name']

    @staticmethod
    def fix_author_nickname(author):
        if 'nickname' in author and author['nickname']:
            nickname = author['nickname']
        elif 'name' in author:
            nickname = author['name']
        else:
            raise CannotFixError("No name or nickname provided for this author!")
        if not validate_length(nickname, 'name'):
            raise CannotFixError("Can't fix the author nickname: " + nickname + "!")
        return nickname

# now we've specified all information about the database schema and ORM
# mapping, go ahead and create that database structure on the sql server if it
# doesn't already exist
Base.metadata.create_all(engine)

def pc_to_ol(page, count):
    """Helper function to convert from the user friendly (page #, posts/page)
    parameter space, to the less intuitive (offset, limit) parameter space used
    to query the SQL tables."""
    return (count*(page - 1), count)

def get_recent_posts_team(team_url_name, page, count, session):
    offset, limit = pc_to_ol(page, count)
    team = get_team_by_name(team_url_name, session)
    if team is None:
        return None
    posts = (session
             .query(Post)
             .with_parent(team, 'posts')
             .order_by(sa.desc(Post.publication_date))
             .offset(offset)
             .limit(limit)
             .all())
    return posts

def get_recent_posts(page, count, session):
    offset, limit = pc_to_ol(page, count)
    posts = (session
             .query(Post)
             .order_by(sa.desc(Post.publication_date))
             .offset(offset)
             .limit(limit)
             .all())
    return posts

def get_popular_posts(page, count, session):
    offset, limit = pc_to_ol(page, count)
    posts = (session
             .query(Post)
             .order_by(sa.desc(Post.view_count))
             .offset(offset)
             .limit(limit)
             .all())
    return posts

def get_team_by_name(team_name, session):
    return session.query(Team).filter_by(url_name=team_name).first()

def get_post_by_name(post_name, session):
    post = session.query(Post).filter_by(url_title=post_name).first()
    if post:
        post.view_count += 1
        session.add(post)
    return post

def get_all_teams(session):
    return session.query(Team).all()

def get_num_posts(session):
    return session.query(Post).count()

def get_num_posts_team(session, team_url_name):
    team = get_team_by_name(team_url_name, session)
    return session.query(Post).with_parent(team, 'posts').count()

def insert_all_teams(update_behavior=UpdateBehavior.update):
    """Insert all teams in global file blog-teams.json into the database."""
    with session_scope() as session:
        team_data_file = os.path.join(thedish.www_dir, 'assets', 'info', 'blog-teams.json')
        team_data = codecs.open(team_data_file, 'r', encoding='utf-8').read()
        # read in and unpack the top-level object "teams"
        teams = json.loads(team_data, encoding='utf-8')['teams']
        teams = [Team.get_or_create(team, session, update_behavior) for team in teams]
        # request that all changes be committed.
        session.add_all(teams)

def insert_post(post_dir, update_behavior=UpdateBehavior.update):
    """Attempt to insert/update a post from it's directory"""
    with session_scope() as session:
        post = Post.from_folder(post_dir, session, update_behavior)
        session.commit()

def insert_all_posts(update_behavior=UpdateBehavior.update):
    with session_scope() as session:
        """Construct all post objects from the directories in :/WWW/posts. Doesn't
        really make sense outside of the context of a sql session, since the posts
        have associations with pre-existings teams which are supposed to be in the
        Team table."""
        post_directories = [os.path.join(thedish.posts_dir, folder)
                            for folder in os.listdir(thedish.posts_dir)]
        post_directories = [post_dir for post_dir in post_directories
                            if os.path.isdir(post_dir)]
        for post_dir in post_directories:
            post = Post.from_folder(post_dir, session, update_behavior)
            # need to commit posts as they're created, since they use
            # no_autoflush during their own creation
            session.commit()

def initialize_website(update_behavior=UpdateBehavior.update):
    """Insert all teams, then all posts/authors."""
    insert_all_teams(update_behavior)
    insert_all_posts(update_behavior)

if __name__ == '__main__':
    initialize_website(update_behavior=UpdateBehavior.update)
