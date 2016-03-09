The Dish on Science Website
Author: Bruno Beltran <brunobeltran0@gmail.com>

Uses Flask to populate a couple of simple templates with posts and "team" names
from JSON files.


Theme:
------
Future Imperfect by HTML5 UP
html5up.net | @n33co
Free for personal and commercial use under the CCA 3.0 license
(html5up.net/license)

Modifications are Copyright (C) 2015 Bruno Beltran -- but
also free to use under the same CCA 3.0 license.

Database:
---------
CREATE TABLE team (
    team_id INTEGER NOT NULL,
    PRIMARY KEY (team_id),
    name VARCHAR(100) NOT NULL,
    url VARCHAR(100) NOT NULL,
    blurb VARCHAR(200) NOT NULL,
    description VARCHAR(2000) NOT NULL
)
CREATE TABLE author (
    author_id INTEGER NOT NULL,
    PRIMARY KEY (author_id),
    name VARCHAR(100),
    default_picture_src VARCHAR(100)
)
CREATE_TABLE team_author (
    author_id INTEGER references authors(author_id),
    team_id INTEGER references teams(team_id),
    constraint pk_author_teams primary key (team_id, author_id)
)
CREATE TABLE post (
    post_id INTEGER NOT NULL,
    PRIMARY KEY (post_id),
    title VARCHAR(200) NOT NULL,
    blurb VARCHAR(200) NOT NULL,
    description VARCHAR(2000) NOT NULL,
    date DATE NOT NULL,
    url VARCHAR(200) NOT NULL;
    image_src VARCHAR(200) NOT NULL,
    square_image_src VARCHAR(200) NOT NULL
)
CREATE TABLE post_author (
    post_id INTEGER references posts(post_id),
    author_id INTEGER references authors(author_id),
    constraint pk_author_teams primary key (post_id, author_id)
)
CREATE TABLE post_team (
    post_id INTEGER references posts(post_id),
    team_id INTEGER references teams(team_id),
    constraint pk_author_teams primary key (post_id, team_id)
)

