import xlrd
import sys
import os
import logging
from dishsql import max_url_length, max_name_length, max_path_length, \
                    max_blurb_length, max_title_length, max_description_length
from dishsql import preferred_url_length, preferred_name_length, \
                    preferred_path_length, preferred_blurb_length, \
                    preferred_title_length, preferred_description_length
from xlsx_to_json import xlsx_to_json
from thedish import Post

logging.basicConfig()
logger = logging.Logger('validate_post.py')

passed_validation = True

def make_absolute_link(relative_link, post_name):
    filename = os.path.basename(relative_link)
    return '/posts/' + post_name + '/images/' + filename

if __name__ == '__main__':
    post_directory = os.path.abspath(sys.argv[1])
    post_name = os.path.basename(post_directory)
    logger.info('Using post_directory = ' + post_directory)
                             + ' '.join(bad_rows))
    xlsx_file = os.path.join(post_directory, 'post_info.xlsx')
    json_file = os.path.join(post_directory, 'post_info.json')
    if os.path.isfile(xlsx_file):
        xlsx_to_json(xlsx_file, json_file)
    try:
        post = Post(post_directory)
    except:
        logger.error('Unable to construct Post from post_info file, did you ' \
                     'forget to fill out some fields in your Excel file?')
        raise
    post.fix_title()
    post.fix_url()
    post.fix_blurb()
    post.fix_descrition()
    post.fix_authors()
    post.fix_teams()
    post.fix_illustrators()
    post.fix_five_by_two_image_src()
    post.fix_two_by_one_image_src()
    post.fix_one_by_one_image_src()

    if post['url_title'] != post_name:
        logger.warning('Requested url_title does not match directory name of ' \
                       'post. Attempting to rename directory.')
        new_post_directory = os.path.join(os.path.split(post_directory)[0],
                                          post['url_title'])
        if os.path.isdir(new_post_directory):
            logger.error('Requested url_title already has a corresponding post'
                       + ' directory. Please remedy this error and rerun this'
                       + ' script.')
            raise OSError('New post directory name (' + new_post_directory +
                          ') requested by post in directory (' + post_directory
                          + ') already taken!')
        shutil.move(post_directory, new_post_directory)

