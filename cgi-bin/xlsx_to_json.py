import sys
import os
import logging
import xlrd
import json

logging.basicConfig()
logger = logging.Logger('xlsx_to_json')

sheet_idx = 0
title_col_idx = 2
values_col_idx = 3

post_directory = None
post_name = None

title_rows = [
    u'',
    u'',
    u'',
    u'',
    u'',
    u'Fields',
    u'Post Title',
    u'Post URL',
    u'5x2 (WxH) Image File Name',
    u'Post Blurb',
    u'Post Description',
    u'Team Name',
    u'Author Name',
    u'Author Nickname',
    u'Author Headshot File Name',
    u'Illustrator Name',
    u'Illustrator Nickname',
    u'Illustrator Headshot File Name',
    u'2x1 (WxH) Image File Name',
    u'1x1 (WxH) Image File Name (Thumbnail)',
    u'Publication Date'
]
class RowIdx:
    title = 6
    url_title = 7
    five_by_two_image_src = 8
    blurb = 9
    description = 10
    team_name = 11
    author_name = 12
    author_nickname = 13
    author_headshot = 14
    illustrator_name = 15
    illustrator_nickname = 16
    illustrator_headshot = 17
    two_by_one_image_src = 18
    one_by_one_image_src = 19
    publication_date = 19


class BadRowException(Exception):
    pass


def xlsx_to_json(xlsx_file_name, json_file_name):
    wb = xlrd.open_workbook(xlsx_file_name)
    sh = wb.sheet_by_index(sheet_idx)
    title_col = sh.col(title_col_idx)
    title_rvs = [row.value for row in title_col]
    # first a simple sanity check that they're using the right excel sheet
    bad_rows = [row for i, row in enumerate(title_rvs) if title_rows[i] != row]
    if bad_rows:
        raise BadRowException('Row labels differ from post_info.xlsx: '
                              + ' '.join(bad_rows) + '\nAre you using the '
                              + 'right post_info.xlsx file?')
    value_col = sh.col(values_col_idx)
    post = {}
    post['title'] = value_col[RowIdx.title].value
    post['url_title'] = value_col[RowIdx.url_title].value
    post['blurb'] = value_col[RowIdx.blurb].value
    post['description'] = value_col[RowIdx.description].value
    post['publication_date'] = value_col[RowIdx.publication_date].value
    post['teams'] = []
    num_teams = 0
    # while there are more teams to add, append to teams list
    while True:
        try:
            cur_col = sh.col(values_col_idx + num_teams)
        except IndexError:
            break
        team_name = cur_col[RowIdx.team_name].value
        if not team_name:
            break
        post['teams'].append(team_name)
        num_teams = num_teams + 1
    if not post['teams']:
        logger.warning('No team name specified for post ' + post_directory + '!')
    post['authors'] = []
    num_authors = 0
    # while there are more authors to add, append to authors list
    while True:
        try:
            cur_col = sh.col(values_col_idx + num_authors)
        except IndexError:
            break
        author_name = cur_col[RowIdx.author_name].value
        if not author_name:
            break
        post['authors'].append(dict())
        post['authors'][-1]['name'] = author_name
        post['authors'][-1]['nickname'] = value_col[RowIdx.author_nickname].value
        post['authors'][-1]['headshot_src'] = value_col[RowIdx.author_headshot].value
        num_authors = num_authors + 1
    post['illustrators'] = []
    num_illustrators = 0
    # while there are more illustrators to add, append to authors list
    while True:
        try:
            cur_col = sh.col(values_col_idx + num_illustrators)
        except IndexError:
            break
        illustrator_name = cur_col[RowIdx.illustrator_name].value
        if not illustrator_name:
            break
        post['illustrators'].append(dict())
        post['illustrators'][-1]['name'] = illustrator_name
        post['illustrators'][-1]['nickname'] = value_col[RowIdx.illustrator_nickname].value
        post['illustrators'][-1]['headshot_src'] = value_col[RowIdx.illustrator_headshot].value
        num_illustrators = num_illustrators + 1
    post['five_by_two_image_src'] = value_col[RowIdx.five_by_two_image_src].value
    post['two_by_one_image_src'] = value_col[RowIdx.two_by_one_image_src].value
    post['one_by_one_image_src'] = value_col[RowIdx.one_by_one_image_src].value

    # output the final post information to json
    with open(json_file_name, 'w') as f:
        json.dump(post, f, sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == '__main__':
    post_directory = os.path.abspath(sys.argv[1])
    post_name = os.path.basename(post_directory)
    logger.info('Using post_directory = ' + post_directory)
    xlsx_file = os.path.join(post_directory, 'post_info.xlsx')
    outfile_name = os.path.join(post_directory, 'post_info.json')
    xlsx_to_json(xlsx_file, outfile_name)

