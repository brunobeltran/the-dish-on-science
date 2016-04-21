#!/bin/bash

# move to the script's directory
app_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. "${app_dir}/venv-markdown-converter/bin/activate"

echo "CONVERTING POST.MD TO POST.HTML"
python -m markdown -x markdown.extensions.footnotes "$1" >"${1%.md}.html"
echo "CONVERSION COMPLETE!"

deactivate
