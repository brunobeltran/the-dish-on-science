import thedish
import dishsql
import sys

if __name__ == '__main__':
    post_dir = sys.argv[1]
    print('Attempting to construct post from {}'.format(post_dir))
    post = thedish.Post(post_dir)
    dishsql.insert_new_post(post)




