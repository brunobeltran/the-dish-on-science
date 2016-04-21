#!/bin/bash

# move to the script's directory
app_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $app_dir

# activate the venv in charge of holding the markdown conversion stuff
. venv-markdown-converter/bin/activate
set -eu

# single configuration variable: the directory with all the posts in it
posts_dir=./WWW/posts

# new posts will be zip files dropped into the posts folder
for post_zip in ${app_dir}/${posts_dir}/*.zip; do
    echo "UNZIPPING POST: $post_zip"
    unzip $post_zip -d ${app_dir}/${posts_dir}
    echo "UNZIPPING COMPLETE!"
    post_url=${post_zip%.zip}
    post_url=$(basename $post_url)
    post_dir=${app_dir}/${posts_dir}/${post_url}
    # just in case people dragged over crap, clean it up
    echo "REMOVING MAC CRUD FILES"
    rm -rf ${app_dir}/${posts_dir}/__MAC* ${app_dir}/${posts_dir}/.DS_*
    rm -rf ${post_dir}/__MAC* ${post_dir}/.DS_*
    echo "REMOVING COMPLETE!"
    # convert post.md to html for use by dishflask
    if [[ ! -f ${post_dir}/post.html ]]; then
        if [[ ! -f ${post_dir}/post.md ]]; then
            echo ERROR! There is no post.md in ${post_dir}!
            return 1
        fi
        echo "CONVERTING POST.MD TO POST.HTML"
        python -m markdown -x markdown.extensions.footnotes \
            ${post_dir}/post.md >${post_dir}/post.html
        echo "CONVERSION COMPLETE!"
    else
        echo "FOUND A POST.HTML FILE! LEAVING IT AS-IS."
    fi
    echo "INSERTING NEW POST INTO MYSQL SERVER..."
    python ./cgi-bin/insert_post.py "$post_dir"
    echo "INSERTION COMPLETE!"
    echo "CLEANING UP...REMOVING ZIP FILE."
    rm $post_zip
    echo "REMOVAL COMPLETE!"
    echo "SUCCESSFULLY ADDED NEW POST: ${post_dir}"
done

# deactivate the venv
deactivate
