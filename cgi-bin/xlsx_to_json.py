import sys
import os
import logging
import xlrd
import json

# logging.basicConfig()
# logger = logging.Logger('xlsx_to_json')

sheet_idx = 0
title_col_idx = 2
values_col_idx = 3

post_directory = None
post_name = None

old2_title_rows = [
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
    u'']

class Old2RowIdx:
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
    publication_date = 20

old_title_rows = [
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
    u'Team Name(s)',
    u'Author Name(s)',
    u'Author Headshot File Name(s)',
    u'Illustrator Name(s)',
    u'Illustrator Headshot File Name(s)',
    u'2x1 (WxH) Image File Name',
    u'1x1 (WxH) Image File Name (Thumbnail)',
    u'']

class OldRowIdx:
    title = 6
    url_title = 7
    five_by_two_image_src = 8
    blurb = 9
    description = 10
    team_name = 11
    author_name = 12
    author_headshot = 13
    illustrator_name = 14
    illustrator_headshot = 15
    two_by_one_image_src = 16
    one_by_one_image_src = 17
    publication_date = 18 # no label
    author_nickname = 0 # empty cell
    illustrator_nickname = 0

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
    u'Team Name(s)',
    u'Author Name(s)',
    u'Author Nickname(s)',
    u'Author Headshot File Name(s)',
    u'Illustrator Name(s)',
    u'Illustrator Nickname(s)',
    u'Illustrator Headshot File Name(s)',
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
    publication_date = 20


class BadRowException(Exception):
    pass


def xlsx_to_json(xlsx_file_name, json_file_name):
    """xlsx_to_json(xlsx_file_name, json_file_name) translates from input xlsx
    to output json files"""
    wb = xlrd.open_workbook(xlsx_file_name)
    sh = wb.sheet_by_index(sheet_idx)
    title_col = sh.col(title_col_idx)
    title_rvs = [row.value for row in title_col]
    # first a simple sanity check that they're using the right excel sheet
    row_types = [title_rows, old_title_rows, old2_title_rows]
    idxs = [RowIdx, OldRowIdx, Old2RowIdx]
    for i, rows in enumerate(row_types):
        bad_rows = []
        for j, row in enumerate(title_rvs):
            if j >= len(rows) or rows[j] != row:
                bad_rows.append(row)
        if not bad_rows:
            idx = idxs[i]
            break
    else:
        raise BadRowException('Row labels differ from all known versions of '
                              + 'post_info.xlsx file: ' + ' '.join(title_rvs))
    value_col = sh.col(values_col_idx)
    post = {}
    post['title'] = value_col[idx.title].value
    post['url_title'] = value_col[idx.url_title].value
    post['blurb'] = value_col[idx.blurb].value
    post['description'] = value_col[idx.description].value
    # if the date string we entered got converted into a "excel date type
    # thing", convert it back into a string for storage in json
    if sh.cell_type(idx.publication_date, values_col_idx) == xlrd.XL_CELL_DATE:
        pdate = value_col[idx.publication_date].value
        pdate = xlrd.xldate.xldate_as_datetime(pdate, wb.datemode)
        post['publication_date'] = pdate.strftime('%Y-%m-%d')
    else:
        post['publication_date'] = value_col[idx.publication_date].value
    post['teams'] = []
    num_teams = 0
    # while there are more teams to add, append to teams list
    while True:
        try:
            cur_col = sh.col(values_col_idx + num_teams)
        except IndexError:
            break
        team_name = cur_col[idx.team_name].value
        if not team_name:
            break
        post['teams'].append(team_name)
        num_teams = num_teams + 1
    if not post['teams']:
        pass # logger.warning('No team name specified for post ' + post_directory + '!')
    post['authors'] = []
    num_authors = 0
    # while there are more authors to add, append to authors list
    while True:
        try:
            cur_col = sh.col(values_col_idx + num_authors)
        except IndexError:
            break
        author_name = cur_col[idx.author_name].value
        if not author_name:
            break
        post['authors'].append(dict())
        post['authors'][-1]['name'] = author_name
        post['authors'][-1]['nickname'] = value_col[idx.author_nickname].value
        post['authors'][-1]['headshot_src'] = value_col[idx.author_headshot].value
        num_authors = num_authors + 1
    post['illustrators'] = []
    num_illustrators = 0
    # while there are more illustrators to add, append to authors list
    while True:
        try:
            cur_col = sh.col(values_col_idx + num_illustrators)
        except IndexError:
            break
        illustrator_name = cur_col[idx.illustrator_name].value
        if not illustrator_name:
            break
        post['illustrators'].append(dict())
        post['illustrators'][-1]['name'] = illustrator_name
        post['illustrators'][-1]['nickname'] = value_col[idx.illustrator_nickname].value
        post['illustrators'][-1]['headshot_src'] = value_col[idx.illustrator_headshot].value
        num_illustrators = num_illustrators + 1
    post['five_by_two_image_src'] = value_col[idx.five_by_two_image_src].value
    post['two_by_one_image_src'] = value_col[idx.two_by_one_image_src].value
    post['one_by_one_image_src'] = value_col[idx.one_by_one_image_src].value

    # output the final post information to json
    with open(json_file_name, 'w') as f:
        json.dump(post, f, sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == '__main__':
    post_directory = os.path.abspath(sys.argv[1])
    post_name = os.path.basename(post_directory)
    pass # logger.info('Using post_directory = ' + post_directory)
    xlsx_file = os.path.join(post_directory, 'post_info.xlsx')
    outfile_name = os.path.join(post_directory, 'post_info.json')
    xlsx_to_json(xlsx_file, outfile_name)

