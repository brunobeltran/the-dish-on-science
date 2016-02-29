#!/bin/bash

for post in ./WWW/posts/*.zip; do
    unzip $post
    post_url=${post%.zip}
    post_dir=./WWW/posts/${post_url}
    if [[ ! -f ${post_dir}/post.html ]]; then
        if [[ ! -f ${post_dir}/post.md ]]; then
            echo ERROR! There is no post.md in ${post_dir}!
            return 1
        fi
        ./Markdown-2.6.5/bin/markdown_py -o 'html5' \
            <${post_dir}/post.md >${post_dir}/post.html
    fi
    #TODO add code to insert post into SQL server
done
