# Developer.md

Useful information for understanding how the dish website works.

The website requires:
1) a db_private directory, in .gitignore by default, that contains as
.dishlogin.cnf mysql configuration files pointing to a working mysql
installation with the table properties specified in the variable
dishsql.dish_db.
2) an apache server setup in a configuration compatible with the example conf
file, the-dish.conf
3) a working flask installation, python 2.7, and undocumented set of required
modules, including mysql-python, sqlalchemy, enum34, and flask. Missing stuff can be
inferred by running
$ python cgi-bin/dishflask.py

On first load, the website will detect that the sql tables it requires are
empty, and populate them using the information in WWW/assets/info/blog-teams.json
for the team information, and all the directories in the WWW/posts directory that
don't throw an error when passed to the "Post" constructor as the posts. This
constructor knows to construct post.html from post.md.

In particular, this means that you'll have to fill in old view count data by
hand if it exists, and keep the blog_teams.json file up to date with the sql
table teams. The SQL association table author_team is defined implicitly based
on which authors have written for what teams, which is why authors are not
listed in blog_teams.json.

A google analytics account exists for the actual dish website, and as of Nov
2016, it is faithfully tracking page views. So if the database must be rebuilt,
it is suggested that these page view counts be used to repopulate it.

For the latter problem it is suggested that you only update the blog-teams.json
file directly, then write an update script to update the relevant sql entries
from that file.

On each subsequent load, the site will use a global flask session to
communicate with the SQL server throughout the request, loading in the versions
of the post metadata stored in the sql server, and using the post.html file
directly.

In particular, this means that any updates to the post's metadata *must* be
sync'd with the sql server. Currently, the best way to do this is to manually
synchronize updates to post_info to the sql server.
