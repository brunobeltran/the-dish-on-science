import thedish
import dishsql
import sys

if __name__ == '__main__':
    post_dir = sys.argv[1]
    print('Attempting to construct post from {}'.format(post_dir))
    post = thedish.Post(post_dir)
    print('Post successfully constructed!')
    print('Attempting to insert new post into database..')
    dishsql.insert_new_post(post)
    print('Success!')




