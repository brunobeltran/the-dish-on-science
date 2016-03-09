import sqlalchemy as sa
from sqlalchemy import Table, Column
from sqlalchemy import declarative_base
Base = declarative_base()
class Author(Base):
    __tablename__ = 'author'

    id = Column(sa.Integer, primary_key=True, nullable=False),
    name = Column(sa.String(100), nullable=False),
    url_name = Column(sa.String(100), nullable=False),
    blurb = Column(sa.String(200)),
    description = Column(sa.String(200)),
    image_src = Column(sa.String(200))

    def __repr__(self):
        return "<Author(%r, %r)>" % (
            self.id, self.name
        )


sql_dir = os.path.join(app_dir, "db_private")

# metadata associated with the MySQL server we will be using to get post,
# author, and team information
metadata = sa.MetaData()
team_table = Table('team', metadata,
    Column('id', sa.Integer, primary_key=True, nullable=False),
    Column('name', sa.String(100), nullable=False),
    Column('url_name', sa.String(100), nullable=False),
    Column('blurb', sa.String(200)),
    Column('description', sa.String(200)),
    Column('thumbnail_src', sa.String(200)),
    Column('logo_src', sa.String(200)))

author_table = Table('author', metadata,
    Column('id', sa.Integer, primary_key=True, nullable=False),
    Column('name', sa.String(100), nullable=False),
    Column('url_name', sa.String(100), nullable=False),
    Column('blurb', sa.String(200)),
    Column('description', sa.String(200)),
    Column('image_src', sa.String(200)))

post_table = Table('post', metadata,
    Column('id', sa.Integer, primary_key=True, nullable=False),
    Column('title', sa.String(200), nullable=False),
    Column('url_title', sa.String(200), nullable=False),
    Column('blurb', sa.String(200)),
    Column('description', sa.String(200)),
    Column('publication_date', sa.Date, nullable=False),
    Column('five_by_two_image_src', sa.String(200)),
    Column('two_by_one_image_src', sa.String(200)),
    Column('one_by_one_image_src', sa.String(200)))

post_author_table = Table('post_author', metadata,
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), primary_key=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), primary_key=True))

post_team_table = Table('post_team', metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), primary_key=True),
    Column('post_id', sa.Integer, sa.ForeignKey('post.id'), primary_key=True))

author_team_table = Table('author_team', metadata,
    Column('team_id', sa.Integer, sa.ForeignKey('team.id'), primary_key=True),
    Column('author_id', sa.Integer, sa.ForeignKey('author.id'), primary_key=True))

myDB = URL(drivername='mysql', username='root', host='localhost',
    database='thedishonscience', query={'read_default_file':
    os.path.join(sql_dir, '.mylogin.cnf')})
engine = sa.create_engine(name_or_url=myDB, echo=True)
metadata.create_all(engine)


