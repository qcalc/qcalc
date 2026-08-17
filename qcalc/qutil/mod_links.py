# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import re
import json


def page_link(pageurl, caption='', link_class="", icon_class="", cid='', card=False):
    link_class = f'class="{link_class}"' if link_class else ''
    hx_trigger = ''
    if cid:  # | page will be replaced anyway if cid is available or not
        # | but if cid is available the check will be performed at front end and will end there
        trig = f"click[get_card_once('{cid}')]"
        hx_trigger = f' hx-trigger="{trig}"'
    if not card:
        icon_class = f'<i class="{icon_class} mr-2"></i>' if icon_class else ''
        return (f'<a {link_class} href="{pageurl}" hx-get="{pageurl}?part=1"{hx_trigger}'
                f' hx-target="#page-holder" hx-swap="innerHTML">{icon_class}<span>{caption}</span></a>')
    else:
        link_card = (f'<a {link_class} href="{pageurl}" hx-get="{pageurl}?part=1"{hx_trigger}'
                     f' hx-target="#page-holder" hx-swap="innerHTML">{link_card_body(icon_class, caption)}</a>')
        return f'<div class="col mb-4">{link_card}</div>'


def href_url(addurl):
    path = addurl.replace("add/?path=", "").replace("part=1", "").replace("add/?fname=", "")
    path = re.sub(r'cid=[^&]*', '', path)
    path = path.replace("?&", "?")
    if path.endswith("&"):
        path = path[:-1]
    if path.endswith("?"):
        path = path[:-1]
    path = path.replace("&", "?") # if only & it should be ?
    return path


def calurl(calname, params=''):
    return f'/calc/add/?path={calname}/{params}' if params else f'/calc/add/?fname={calname}'


def hx_target(target):
    target_swap = ''
    if target == 'f':  # add cal first
        target_swap = f" hx-target='#content-holder' hx-swap='afterbegin'"
    elif target == 'b':  # insert before
        target_swap = f" hx-target='closest .calc' hx-swap='beforebegin'"
    elif target == 'r':  # replace this
        target_swap = f" hx-target='closest .calc' hx-swap='outerHTML'"
    elif target == 'a':  # insert after
        target_swap = f" hx-target='closest .calc' hx-swap='afterend'"
    elif target == 'l':  # add cal last
        target_swap = f" hx-target='#card-space' hx-swap='beforebegin'"
    return target_swap


def link_card_body(icon_class, caption):
    return f"""
    <div class="card h-100 text-center shadow-sm">
      <div class="card-body">
        <i class="{icon_class} mb-3" style="font-size: 2em;"></i>
        <h6 class="card-text">{caption}</h6>
      </div>
    </div>
    """


def cal_link(calurl, caption='', link_class='', icon_class='', target='a', cid='', button=False, card=False):
    link_class = f'class="{link_class}"' if link_class else ''
    href = href_url(calurl)
    target_swap = hx_target(target)
    hx_trigger = ''
    if cid:  # | some calculator may need to be instantiated only once
        trig = f"click[get_card_once('{cid}')]"
        hx_trigger = f' hx-trigger="{trig}"'
    button = 'button' if button else 'a'
    if not card:
        icon_class = f'<i class="{icon_class} mr-2"></i>' if icon_class else ''
        return (f'<{button} {link_class} href="{href}" hx-get="{calurl}"{hx_trigger}{target_swap}>'
                f'{icon_class}<span>{caption}</span></{button}>')
    else:
        link_card = (f'<{button} {link_class} href="{href}" hx-get="{calurl}"{hx_trigger}{target_swap}>'
                     f'{link_card_body(icon_class, caption)}</{button}>')
        return f'<div class="col mb-4">{link_card}</div>'


def command_button(sfunc, caption, cmd, args=None, kwargs=None):  # , position=''
    # | to execute calculator callback command
    # | 'if', '' = inside form, default
    # | 'rc' = anywhere inside card, replace card
    # | hx-swap="innerHTML" is the default
    args = [] if args is None else args
    kwargs = {} if kwargs is None else kwargs
    htm = '<button type="submit" class="btn btn-info btncmd" '  # POST

    htm += f'hx-post="/calc/{sfunc}/?part=2" hx-target="closest form" '

    extra = {"extra": {"cmd": cmd, "args": args, "kwargs": kwargs}}
    htm += "hx-vals='" + json.dumps(extra) + "'>"
    htm += f'{caption}</button>'
    return htm


def addcal_button(calname, caption, icon_class=''):
    return cal_link(calurl(calname), caption, 'btn btn-info btncmd', icon_class, 'a', '', True)


def list2table(lst, cols, cid, elem, url_format='', url_col=-1):
    copy_lst = lst.copy()
    if url_format != '':
        for i in range(len(lst)):
            url_col_val = url_format.format(_item=lst[i])
            if url_col == -1:  # keep just 1 column
                copy_lst[i] = url_col_val
            else:  # keep all columns
                copy_lst[i][url_col] = url_col_val
    df = pd.DataFrame(copy_lst, columns=cols)
    df.index = range(1, len(df) + 1)
    tbl_id = f'{cid}_{elem}_table'
    tbl = df.to_html(escape=False, table_id=tbl_id,
                     classes=f'table table-responsive table-out {cid}',
                     index=False)  # + table_js() # url formatter required
    return tbl


# def table_js():
#     scr = '<script src="/static/js/tabulator-out.js"></script>'
#     return scr


if __name__ == '__main__':
    # print(table_js())
    print(command_button('cost', 'Refresh', '__modify', args=['a', 'b']))
    print(cal_link(calurl('gold'), 'Gold', cid='xyz'))
    print(cal_link(calurl('bmi', 'weight/50 kg/height/5.5 ft/'), 'Gold', cid='xyz'))
    print(page_link('/page/home/'))
