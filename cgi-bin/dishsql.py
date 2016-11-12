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

# for creating posts objects from a directory
from xlsx_to_json import xlsx_to_json
from markdown import markdownFromFile

from contextlib import contextmanager
import sqlalchemy as sa
from sqlalchemy import Table, Column
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
# force utf-8 outside of dbapi calls as well
engine = sa.create_engine(name_or_url=dish_db, encoding='utf-8', echo=True)

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

# a useful exception during construction of Posts. oftentimes, we can fix small
# problems and will do so on the fly, like missing nicknames, but some problems
# we just can't fix..., like invalid team names.
class CannotFixError(Exception):
    pass

# the relationship tables are easy to specify, since no ORM needed
post_author_table = Table('post_author', Base.metadata,
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), index=True))

post_illustrator_table = Table('post_illustrator', Base.metadata,
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), index=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), index=True))
# TODO: to allow different nicknames per article, just add a column here
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

    def __init__(self, name, **kwargs):
        self.name = name
        self.url_name = urlify(name)
        for key, val in kwargs.items():
            setattr(self, key, val)


class Team(Base):
    """Knows about a blog team for The Dish."""
    __tablename__ = 'team'

    id = Column(sa.Integer, primary_key=True, nullable=False)
    name = Column('name', sa.String(limits['max']['name']), nullable=False)
    url_name = Column('url_name', sa.String(limits['max']['url_name']),
                      nullable=False, index=True, unique=True)
    blurb = Column('blurb', sa.String(limits['max']['blurb']))
    description = Column('description', sa.String(limits['max']['description']))
    thumbnail_src = Column('thumbnail_src', sa.String(limits['max']['path']))
    logo_src = Column('logo_src', sa.String(limits['max']['path']))
    members = relationship("Author", secondary=author_team_table,
                         back_populates="teams")
    posts = relationship("Post", secondary=post_team_table,
                         back_populates="teams")

    def __repr__(self):
        return "<Team(id=%r, name=%r, url_name=%r)>" % (
            self.id, self.name, self.url_name)

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


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
default_post_dict['illustrators'] = []
default_post_dict['authors'] = []
default_post_dict['teams'] = []

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

    # make a list of the methods that are to be run on a newly constructed post
    # to check its integrity. To get around the fact that the Post class is
    # itself non-existent at this point in time, we get the list via a
    # classmethod that doesn't have to use the identifier "Post" explicitly

    # fix_url must be first, since other error loggers depend on its presence.
    # fix_teams before you fix_authors, so that the author/team associations
    # are correctly inserted. fix_authors also fixes illustrators
    @classmethod
    def post_integrity_checkers(cls):
        return  [cls.fix_url, cls.fix_publication_date, cls.fix_blurb,
                 cls.fix_description, cls.fix_title,
                 cls.fix_five_by_two_image_src,
                 cls.fix_two_by_one_image_src,
                 cls.fix_one_by_one_image_src,
                 cls.fix_teams, cls.fix_authors]

    def __repr__(self):
        return "<Post(id=%r, url_title=%r)>" %(
            self.id, self.url_title)

    # this dict should have the form one would get form loading a
    # post_info.json file directly as a python dict.
    # because Post has associations to other objects (i.e. Author and Team), it
    # doesn't really make sense for a Post to exist outside of the context of a
    # session with the SQL server.
    def __init__(self, post_dict, session):
        for key, val in default_post_dict.items():
            setattr(self, key, val)
        for key, val in post_dict.items():
            setattr(self, key, val)
        self.session = session
        for fix_func in Post.post_integrity_checkers():
            fix_func(self)
        self.publication_date = dateutil.parser.parse(self.publication_date)

        # for now, post count will always restart at zero when an article is
        # reconstructed from its JSON specification. TODO: put in correct view
        # counts from e.g. google analytics upon recreation. ?Maybe somethign
        # like the instructions at?:
        # https://developers.google.com/analytics/devguides/reporting/core/v4/choosing_which_version_of_the_analytics_reporting_api_to_use
        self.view_count = 0

    @classmethod
    def from_urltitle(cls, url_title, session):
        return session.query(Post).filter_by(url_title=url_title).first()

    @classmethod
    def from_folder(cls, post_directory, session):
        """Get a Post object from a valid path. Should not be used during
        normal website operation, only for constructing post objects to insert
        into the SQL table."""
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
            return cls.from_json(json_file, session)
        elif os.path.isfile(xls_file):
            xlsx_to_json(xls_file, json_file)
            return cls.from_json(json_file, session)
        elif os.path.isfile(json_file):
            return cls.from_json(json_file, session)
        else:
            # logger.error("The post directory {} does not have a post_info file!".format(post_directory), file=sys.stderr)
            return None

    @classmethod
    def from_json(cls, post_file, session):
        """ Read JSON into a dict to pass our constructor. Should not be used
        during normal website operation, only for constructing post objects to
        insert into the SQL table."""
        post_data = codecs.open(post_file, 'r', encoding='utf-8').read()
        try:
            post_dict = json.loads(post_data)
        except:
            # logger.error("ERROR: Cannot parse the file {}!".format(post_file), file=sys.stderr)
            return None
        return cls(post_dict, session)

    @property
    def url(self):
        return '/posts/' + str(self.url_title)

    @property
    def absolute_url(self):
        return thedish.thedish.url + self.url

    @property
    def post_directory(self):
        return os.path.join(posts_dir, self.url_title)

    @property
    def html(self):
        """This goes against our usual rule of not doing stuff related to
        constructing posts during normal website operation, but this only
        incurs one ctime check, so we'll let it go for now."""
        html_file = os.path.join(self.post_directory, 'post.html')
        md_file = os.path.join(self.post_directory, 'post.md')
        if not os.path.isfile(md_file) and not os.path.isfile(html_file):
            #TODO: allow LaTeX. For now, there's no post content here, return an empty post
            return ''
        should_rebuild_html = not os.path.isfile(html_file) \
                or os.path.isfile(md_file) \
                and os.path.getctime(md_file) > os.path.getctime(html_file)
        if should_rebuild_html:
            #md_text = codecs.open(md_file, 'r', encoding='utf-8').read()
            html = markdownFromFile(input=md_file, output=html_file,
                                    encoding='utf-8')
            #codecs.open(html_file, 'w', encoding='utf-8', errors='xmlcharrefreplace').write(html)
        return codecs.open(html_file, 'r', encoding='utf-8').read()

    # helper methods to verify that a post we're constructing from a file is
    # not invalid
    def fix_publication_date(self):
        if not self.publication_date:
            raise CannotFixError("No publication date provided for article: " + self.url_title)

    def fix_title(self):
        if not validate_length(self.title, 'title'):
            raise CannotFixError("Can't fix the title!")

    def fix_url(self):
        if not validate_length(self.url_title, 'url_title'):
            raise CannotFixError('Cannot fix url_title!')
        allowed_chars = set(string.ascii_lowercase + string.digits + '-')
        if not set(self.url_title) <= allowed_chars:
            pass # logger.warning('Illegal characters in URL!: ' + self.url_title)

    def fix_blurb(self):
        if not validate_length(self.blurb, 'blurb'):
            raise CannotFixError('Cannot fix blurb!')

    def fix_description(self):
        if not self.description:
            raise CannotFixError('No description provided!')
        if not validate_length(self.description, 'description'):
            new_len = limits['max']['description']
            # logger.warning('Truncating post description!')
            self.description = self.description[0:new_len-3] + '...'


    def fix_teams(self):
        # teams are selected from a list of known good teams, so they can't
        # really be messed up. So here, we just have to make sure that there
        # are teams listed at all....or so I thought. turns out people don't
        # know how to use drop down menus, so we'll have to really check this.
        if not self.teams:
            raise CannotFixError('No teams were provided when ' \
                                 + 'constructing Post: ' + self.url_title)
        # # old way of checking if team names were valid, used the json file
        # # holding team information directly
        # all_teams = get_teams_from_disk()
        # valid_team_names = [team for team in all_teams
        #                   if team.name in self.teams
        #                   or team.url_name in self.teams]
        # self.teams = valid_team_names #TODO construct team objects from sql table here

        # it's not expected that Teams get created all the time, so if it looks
        # like you're trying to create a Team that does not exist, error out to
        # force the admin can manually enter the team, as this is likely an
        # error
        for i,team in enumerate(self.teams):
            db_team = self.session.query(Team).filter_by(url_name=team).first()
            if db_team:
                self.teams[i] = db_team
                continue
            db_team = self.session.query(Team).filter_by(name=team).first()
            if db_team:
                self.teams[i] = db_team
                continue
            # if the string provided doesn't match the team name or url name,
            # it's not valid
            raise CannotFixError("Post {} references the team {}, which "
                                + "does not exist!".format(self.url_title, team))

    def fix_authors(self):
        # if no author name specified, use team name
        if not self.authors:
            # logger.warning('No author names specified! Using team names instead.')
            self.authors = [Author(name=team.name, nickname=team.name,
                            headshot_src=team.logo_src) for team in self.teams]
        # open up a session for querying if the authors exist ONLY, no updating
        # will be done in this session
        self.authors = [self.fix_author(author) for author in self.authors]
        if not self.illustrators:
            self.illustrators = []
        else:
            self.illustrators = [self.fix_author(illustrator)
                                for illustrator in self.illustrators]
        # writing an article for a team makes you part of that team
        for team in self.teams:
            for author in self.authors:
                if team not in author.teams:
                    author.teams.append(team)
            for illustrator in self.illustrators:
                if team not in illustrator.teams:
                    illustrator.teams.append(team)

    def fix_author(self, author):
        # authors will likely be created for most new posts, so if we find an
        # author that did not previously exist, we will construct it

        # must fix name first, others use it for logging
        name=Post.fix_author_name(author)
        nickname= Post.fix_author_nickname(author)
        headshot_src=self.fix_author_headshot_src(author)
        author = Author(name=name, nickname=nickname, headshot_src=headshot_src)
        author = replace_with_database_if_exists(author, Author.url_name, self.session)
        return author

    def fix_author_headshot_src(self, author):
        default_images = ['/images/cow.png', '/images/dinosaur.png',
                        '/images/elephant.png', '/images/hedgehog.png',
                        '/images/monkey.jpeg', '/images/panda.png',
                        '/images/paperplane.png', '/images/penguin.png',
                        '/images/turkey.png']
        if 'headshot_src' in author:
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
            maybe_filename3 = os.path.join(thedish.www_dir, url, 'images', filename)
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
            return self.fix_image_file_name(author['headshot_src'])

    #TODO: update these to downsample large images, crop to get
    # two_by_one/one_by_one from five_by_one, etc..
    def fix_five_by_two_image_src(self):
        self.fix_image_file_name(self.five_by_two_image_src)

    def fix_two_by_one_image_src(self):
        if self.two_by_one_image_src:
            self.fix_image_file_name(self.two_by_one_image_src)
        else:
            self.two_by_one_image_src = self.five_by_two_image_src

    def fix_one_by_one_image_src(self):
        if self.one_by_one_image_src:
            self.fix_image_file_name(self.one_by_one_image_src)
        else:
            self.one_by_one_image_src = self.five_by_two_image_src


    def fix_image_file_name(self, file_name):
        looks_like_local_attempt = re.compile('(\./).*')
        # looks_like_absolute_attempt = re.compile('.*/posts/.*/images/.*')
        unfixable = False
        if looks_like_local_attempt.match(file_name):
            # don't forget to strip the / from self.url, os.path.join ignores
            # all arguments that come before the first one that it thinks looks
            # like an absolute path
            supposed_file = os.path.join(thedish.www_dir, self.url[1:], file_name)
            if not os.path.isfile(supposed_file):
                # logger.error("Looks like you referred to an image with a " \
                             # + "relative URL, but the image does not appear " \
                             # + " to exist: " \
                             # + file_name)
                raise CannotFixError('Cannot find image file: ' + file_name)
            # make into absolute path for website
            return supposed_file
        else: # if looks_like_absolute_attempt.match(file_name):
            # if it's a properly formatted absolute url, it should start with
            if file_name[0] == '/':
                supposed_file = os.path.join(thedish.www_dir, file_name[1:])
            # but try to do the right thing even if it doesn't
            else:
                supposed_file = os.path.join(thedish.www_dir, file_name)
            if not os.path.isfile(supposed_file):
                # logger.error("Looks like you're trying to use a post-specific " \
                                # + "author headshot, but the file does not exist: " \
                                # + file_name)
                raise CannotFixError('Cannot find image file: ' + file_name)

    @staticmethod
    def fix_author_name(author):
        if 'name' not in author or not validate_length(author['name'], 'name'):
            raise CannotFixError("Can't fix the author name: " + author['name'] + "!")
        return author['name']

    @staticmethod
    def fix_author_nickname(author):
        if 'nickname' in author:
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

# helper function to convert from the user friendly (page #, posts/page)
# parameter space, to the less intuitive (offset, limit) parameter space used
# to query the SQL tables
def pc_to_ol(page, count):
    return (count*(page - 1), count)

def get_recent_posts_team(team_url_name, page, count, session):
    offset, limit = pc_to_ol(page, count)
    team = get_team_by_name(team_url_name)
    if team is None:
        return None
    posts = (session
             .query(Post)
             .with_parent(team, 'teams')
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
    post.view_count += 1
    session.add(post)
    return post

def get_all_teams(session):
    return session.query(Team).all()

def build_all_teams():
    """Construct all team rows from a global file, blog-teams.json."""
    team_data_file = os.path.join(thedish.www_dir, 'assets', 'info', 'blog-teams.json')
    team_data = codecs.open(team_data_file, 'r', encoding='utf-8').read()
    # read in and unpack the top-level object "teams"
    teams = json.loads(team_data, encoding='utf-8')['teams']
    teams = [Team(**team) for team in teams]
    return teams

def insert_all_teams(only_new=False):
    """Insert all teams in blog-teams.json into the database."""
    with session_scope() as session:
        teams = build_all_teams()
        if only_new:
            teams = [team for team in teams if session.query(Team).filter_by(url_name=team.url_name).first() is None]
        session.add_all(teams)

def build_all_posts(session):
    """Construct all post objects from the directories in :/WWW/posts. Doesn't
    really make sense outside of the context of a sql session, since the posts
    have associations with pre-existings teams which are supposed to be in the
    Team table."""
    post_directories = [os.path.join(thedish.posts_dir, folder)
                        for folder in os.listdir(thedish.posts_dir)]
    post_directories = [post_dir for post_dir in post_directories if os.path.isdir(post_dir)]
    return [Post.from_folder(post_dir, session) for post_dir in post_directories]

def insert_all_posts(only_new=False):
    with session_scope() as session:
        posts = build_all_posts(session)
        if only_new:
            posts = [post for post in posts if session.query(Post).filter_by(url_title=post.url_title).first() is None]
        session.add_all(posts)

def initialize_website(only_new=False):
    """Insert all teams, then all posts/authors."""
    insert_all_teams(only_new)
    insert_all_posts(only_new)
