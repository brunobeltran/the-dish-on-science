# Developer.md

Useful information for understanding how the dish website works.

The website requires:
1) a db_private directory, in .gitignore by default, that contains as
.dishlogin.cnf mysql configuration files pointing to a working mysql
installation with the table properties specified in the variable
dishsql.dish_db.
2) an apache server setup in a configuration compatible with the example conf
file, the-dish.conf
3) a working flask installation, python 3, and undocumented set of required
modules, including python-dateutil, xlrd, markdown, pymysql, sqlalchemy, enum34, and flask. Missing stuff can be
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




# Production Notes
In Stanford's server's chroot'd cgi environment, only python 2.6.6 exists, and
it has only a predefined set of packages installed.

This is why we keep a dishsql_admin, that can do things that aren't possible
when serving the website.

To install the website for the first time, or after adding a new article folder
to posts, simply
$ cd cgi-bin
$ ../venv-tdos/bin/ipython
>>> import dishsql
>>> dishsql.initialize_website()
where venv-tdos holds a python environment that has the requirements listed
above installed. On corn, this can be created with the pyenv-3.4 command
currently.
