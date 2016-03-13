#!/bin/bash

# activate the venv in charge of holding the markdown conversion stuff
. venv-markdown-converter/bin/activate

# single configuration variable: the directory with all the posts in it
posts_dir=./WWW/posts

# move to the script's directory
app_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $app_dir

# new posts will be zip files dropped into the posts folder
for post_zip in ${app_dir}/${posts_dir}/*.zip; do
    unzip $post_zip -d ${app_dir}/${posts_dir}
    # just in case people dragged over crap, clean it up
    rm -rf ${app_dir}/${posts_dir}/__MAC* ${app_dir}/${posts_dir}/.DS_*
    post_url=${post_zip%.zip}
    post_url=$(basename $post_url)
    post_dir=${app_dir}/${posts_dir}/${post_url}
    # convert post.md to html for use by dishflask
    if [[ ! -f ${post_dir}/post.html ]]; then
        if [[ ! -f ${post_dir}/post.md ]]; then
            echo ERROR! There is no post.md in ${post_dir}!
            return 1
        fi
        echo Converting post.md to post.html
        python -m markdown -x markdown.extensions.footnotes \
            ${post_dir}/post.md >${post_dir}/post.html
    else
        echo Found a post.html file! Leaving it as-is.
    fi
    echo "Inserting new post into MySQL server..."
    python ./cgi-bin/insert_post.py "$post_dir"
    echo Cleaning up...removing zip file.
    rm $post_zip
done

# deactivate the venv
deactivate
