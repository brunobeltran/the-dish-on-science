************
Developer.md
************

Useful information for understanding how the dish website works.

The website requires:
1) a db_private directory, in .gitignore by default, that contains a
.dishlogin.cnf mysql configuration file pointing to a working mysql installation
with a database called g_thedishonscience_dish_website (charset utf8).
2) an apache server setup in a configuration compatible with the example conf
file, the-dish.conf
3) a working flask installation, python 2, and the modules:
python-dateutil, xlrd, markdown, pymysql, sqlalchemy, enum34, and flask

Run the website locally by executing:
$ python2 cgi-bin/dishflask.py

On first load, the website will detect that the sql tables it requires are
empty, and populate them using the information in WWW/assets/info/blog-teams.json
for the team information, and all the directories in the WWW/posts directory that
don't throw an error when passed to the "Post" constructor as the posts. This
constructor knows to construct post.html from post.md.

In particular, this means that you'll have to fill in old view count data by
hand if it exists, and keep the blog_teams.json file up to date with the sql
table teams if they change. The SQL association table author_team is defined
implicitly based on which authors have written articles for what teams, which is
why authors are not listed in blog_teams.json.

A google analytics account exists for the actual dish website, and as of Nov
2016, it is faithfully tracking page views. So if the database must be rebuilt,
it is suggested that these page view counts be used to repopulate it, although
some several thousand pageviews would be missing if that was done.

If you must change information about the teams on a regular basis, it is
suggested that you simply modify the file WWW/assets/info/blog-teams.json
directly, then write an update script to update the relevant sql entries
from that file.

On each subsequent load after the first, the site will use a global flask
session to communicate with the SQL server throughout the request, loading in
the versions of the post metadata stored in the sql server, and using the
post.html file directly.

In particular, this means that any updates to the post's metadata *must* be
sync'd with the sql server. Because Stanford's servers use an *ancient* version
of Python (<2.7), we currently maintain a separate version of the dishsql module
for performing such updates (dishsql_admin.py). This module contains functions
for updating various aspects of the SQL database. If you're unsure what to do,
you should just run dishsql_admin.initialize_website().




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
