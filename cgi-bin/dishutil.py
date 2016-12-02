import xlrd
import dishsql_admin
import re


def update_counts_manually(file_name):
    """Reads an excel file whose first column (A) is the page name and
    second column (B) is the number of uncounted views to increment the sql
    table's counters by."""
    wb = xlrd.open_workbook(file_name)
    sh = wb.sheet_by_index(0)
    pages = sh.col(0)
    counts = sh.col(1)
    # for now, we only keep track of post page view counts, so we can ignore
    # everything else
    extract_post_name = re.compile('.*/posts/([-a-zA-Z0-9]*)/?')
    to_update = dict()
    for i, page in enumerate(pages):
        match = extract_post_name.match(page.value)
        if match:
            to_update[match.groups()[0]] = counts[i].value

    with dishsql_admin.session_scope() as session:
        for page, count in to_update.items():
            post = session.query(dishsql_admin.Post).\
                           filter_by(url_title=page).\
                           first()
            if post:
                post.view_count = post.view_count + count





