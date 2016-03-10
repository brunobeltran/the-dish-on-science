import sqlalchemy as sa
import os
from sqlalchemy import Table, Column
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_
from sqlalchemy.engine.url import URL
from thedish import teams, Post, app_dir, www_dir, all_posts

sql_dir = os.path.join(app_dir, "db_private")

# from sqlalchemy.ext.declarative import declarative_base
# Base = declarative_base()
# class Author(Base):
#     __tablename__ = 'author'

#     id = Column(sa.Integer, primary_key=True, nullable=False),
#     name = Column(sa.String(100), nullable=False),
#     url_name = Column(sa.String(100), nullable=False),
#     blurb = Column(sa.String(200)),
#     description = Column(sa.String(200)),
#     image_src = Column(sa.String(200))

#     def __repr__(self):
#         return "<Author(%r, %r)>" % (
#             self.id, self.name
#         )

# metadata associated with the MySQL server we will be using to get post,
# author, and team information
metadata = sa.MetaData()
team_table = Table('team', metadata,
    Column('id', sa.Integer, primary_key=True, nullable=False),
    Column('name', sa.String(100), nullable=False),
    Column('url_name', sa.String(100), nullable=False, index=True, unique=True),
    Column('blurb', sa.String(200)),
    Column('description', sa.String(200)),
    Column('thumbnail_src', sa.String(200)),
    Column('logo_src', sa.String(200)))

author_table = Table('author', metadata,
    Column('id', sa.Integer, primary_key=True, nullable=False),
    Column('name', sa.String(100), nullable=False),
    Column('nickname', sa.String(100)),
    Column('url_name', sa.String(100), nullable=False, index=True, unique=True),
    Column('blurb', sa.String(200)),
    Column('description', sa.String(200)),
    Column('image_src', sa.String(200)))

post_table = Table('post', metadata,
    Column('id', sa.Integer, primary_key=True, nullable=False),
    Column('title', sa.String(200), nullable=False),
    Column('url_title', sa.String(200), nullable=False, index=True, unique=True),
    Column('blurb', sa.String(200)),
    Column('description', sa.String(200)),
    Column('publication_date', sa.Date, nullable=False),
    Column('five_by_two_image_src', sa.String(200), nullable=False),
    Column('two_by_one_image_src', sa.String(200)),
    Column('one_by_one_image_src', sa.String(200)),
    Column('view_count', sa.Integer, nullable=False))

post_author_table = Table('post_author', metadata,
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), primary_key=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), primary_key=True))

post_team_table = Table('post_team', metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), primary_key=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), primary_key=True))

author_team_table = Table('author_team', metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), primary_key=True),
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), primary_key=True))

myDB = URL(drivername='mysql', username='gthedishonscie', host='localhost',
    database='g_thedishonscience_dish_website', query={'read_default_file':
    os.path.join(sql_dir, '.mylogin.cnf')})
#TODO find prettier way to do this
connection_url = str(myDB) + "&charset=utf8"
engine = sa.create_engine(name_or_url=connection_url, echo=False)
metadata.create_all(engine)

def insert_new_team(team):
    conn = engine.connect()
    # first make sure the team exists
    select_if_exists_team = select([team_table.c.id]
        ).where(team_table.c.url_name == team.url_name)
    res = conn.execute(select_if_exists_team)
    team_id = res.fetchone()
    res.close()
    if team_id is None:
        ins = team_table.insert().values(name=team.name,
            url_name=team.url_name, blurb=team.blurb,
            description=team.description, logo_src=team.logo_src,
            thumbnail_src=team.thumbnail_src)
        res = conn.execute(ins)
        team_id = res.inserted_primary_key
        res.close()
    # if the select was not empty, we will have a 1-tuple with the id
    # in it, otherwise, we will have a list of length one with the id
    team_id = team_id[0]
    # now make sure all the authors are in the author table
    for name in team.members:
        url_name = name.lower().replace(' ', '-')
        select_if_exists_name = select([author_table.c.id]
            ).where(author_table.c.url_name == url_name)
        res = conn.execute(select_if_exists_name)
        author_id = res.fetchone()
        res.close()
        if author_id is None:
            ins = author_table.insert().values(name=name, url_name=url_name)
            res = conn.execute(ins)
            author_id = res.inserted_primary_key
            res.close()
        # if the select was not empty, we will have a 1-tuple with the id
        # in it, otherwise, we will have a list of length one with the id
        author_id = author_id[0]
    # finally make sure each member of the team is linked in the association
    # table author_team
        select_if_exists_member = select([author_team_table]
            ).where(and_(author_team_table.c.team_id == team_id,
                    author_team_table.c.author_id == author_id))
        res = conn.execute(select_if_exists_member)
        key = res.fetchone()
        res.close()
        if key is None:
            ins = author_team_table.insert().values(
                author_id=author_id, team_id=team_id)
            res = conn.execute(ins)
            res.close()
    conn.close()

def insert_new_post(post):
    conn = engine.connect()
    url_title = post.url_title
    select_if_exists_post = select([post_table.c.id]
        ).where(post_table.c.url_title == url_title)
    res = conn.execute(select_if_exists_post)
    post_id = res.fetchone()
    res.close()
    if post_id is None:
        ins = post_table.insert().values(
            title=post.title,
            url_title=post.url_title, blurb=post.blurb,
            description=post.description,
            publication_date=post.publication_date,
            five_by_two_image_src=post.five_by_two_image_src,
            two_by_one_image_src=post.two_by_one_image_src,
            one_by_one_image_src=post.one_by_one_image_src,
            view_count=0)
        res = conn.execute(ins)
        post_id = res.inserted_primary_key
        res.close()
    post_id = post_id[0]
    # now make sure all the authors are in the author table
    for author in post.authors:
        url_name = author.name.lower().replace(' ', '-')
        select_if_exists_name = select([author_table.c.id]
            ).where(author_table.c.url_name == url_name)
        res = conn.execute(select_if_exists_name)
        author_id = res.fetchone()
        res.close()
        if author_id is None:
            ins = author_table.insert().values(name=author.name, url_name=url_name)
            res = conn.execute(ins)
            author_id = res.inserted_primary_key
            res.close()
        # if the select was not empty, we will have a 1-tuple with the id
        # in it, otherwise, we will have a list of length one with the id
        author_id = author_id[0]
        select_if_exists_post_author = select([post_author_table]
            ).where(and_(post_author_table.c.post_id == post_id,
                    post_author_table.c.author_id == author_id))
        res = conn.execute(select_if_exists_post_author)
        key = res.fetchone()
        res.close()
        if key is None:
            ins = post_author_table.insert().values(
                author_id=author_id, post_id=post_id)
            res = conn.execute(ins)
            res.close()
    # all teams should also be in the database by now
    for team in post.teams:
        select_team = select([team_table.c.id]).where(team_table.c.url_name ==
            team.url_name)
        team_id = conn.execute(select_team).fetchone()[0]
        select_if_exists_post_team = select([post_team_table]
            ).where(and_(post_team_table.c.post_id == post_id,
                         post_team_table.c.team_id == team_id))
        res = conn.execute(select_if_exists_post_team)
        key = res.fetchone()
        res.close()
        if key is None:
            ins = post_team_table.insert().values(
                team_id=team_id, post_id=post_id)
            res = conn.execute(ins)
            res.close()
    conn.close()

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
# TODO use the database row to make the Post entry instead of re-reading the
# post_info.json file
    posts = [Post(os.path.join(www_dir, 'posts', url_title[0]))
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
    posts = [Post(os.path.join(www_dir, 'posts', url_title[0]))
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
    posts = [Post(os.path.join(www_dir, 'posts', url_title[0]))
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
    res = conn.execute(select_if_exists_post)
    url_title = res.fetchone()
    res.close()
    if url_title is None:
        return None
    update = post_table.update().where(
        post_table.c.url_title == url_title
        ).values({post_table.c.view_count: post_table.c.view_count+1})
    conn.execute(update)
    res.close()
    conn.close()
    return Post(os.path.join(www_dir, 'posts', url_title[0]))

# get all the teams into the database
for team in teams:
    insert_new_team(team)

# get all the posts into the database
for post in all_posts:
    insert_new_post(post)

