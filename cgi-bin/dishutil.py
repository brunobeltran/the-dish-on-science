import xlrd
import dishsql
import re
import os
import datetime
import thedish
import jinja2
import codecs


def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)

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

    with dishsql.session_scope() as session:
        for page, count in to_update.items():
            post = session.query(dishsql.Post).\
                           filter_by(url_title=page).\
                           first()
            if post:
                post.view_count = post.view_count + count


default_preview_text = "Announcing cool new content from The Dish on Science!"
def create_announcement_email_given_posts_(new_posts, extra_article_pairs, preview_text=None, events=None, date=None):
    if date is None:
        date = datetime.datetime.now()
    if preview_text is None:
        preview_text = default_preview_text
    if len(extra_article_pairs) % 2 == 1:
        raise ValueError('Odd number of "extra" articles not allowed by email template.')
    email_rel_url = '/emails/dish-article-alert-' + date.strftime('%Y-%m-%d') + '.html'
    email_url = thedish.dish_info.url + email_rel_url
    email_file = thedish.www_dir + email_rel_url
    extra_article_pairs = [(extra_article_pairs[2*i], extra_article_pairs[2*i+1])
                           for i in range(int(len(extra_article_pairs)/2))]
    context = {'preview_text': preview_text, 'new_posts': new_posts,
               'article_pairs': extra_article_pairs, 'events': events,
               'thedish': thedish.dish_info, 'archive_url': email_url,
               'num_articles_plus_one': len(new_posts)+1}
    email = render(os.path.join(thedish.www_dir, 'templates/newsletter.html'), context=context)
    with codecs.open(email_file, 'w', encoding='utf=8') as f:
        f.write(email)

def create_announcement_email(new_posts, extra_article_pairs,
        preview_text=None, events=None, date=None):
    with dishsql.session_scope() as session:
        new_posts = [dishsql.get_post_by_name(post, session) for post in new_posts]
        extra_article_pairs = [dishsql.get_post_by_name(post, session) for post in extra_article_pairs]
        return create_announcement_email_given_posts_(new_posts,
                extra_article_pairs, preview_text, events, date)
