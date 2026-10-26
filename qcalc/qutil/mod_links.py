# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import re
import json
from html import escape
from textwrap import dedent


def page_link(pageurl, caption='', link_class="", icon_class="", cid='', card=False):
    """Build an HTMX page-navigation link (or card link) HTML snippet."""
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
    path = path.replace("&", "?")  # if only & it should be ?
    return path


def calurl(calname, params=''):
    """Build calculator add/load URL from calculator name and optional params."""
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
    """Build an HTMX calculator-launch link/button (or card variant)."""
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


def _spin_inner(caption, spinner):
    """Wrap a button caption with the shared calculate-button spinner markup."""
    if not spinner:
        return caption
    return (f'<span class="calculate-content">{caption}</span>'
            '<span class="htmx-indicator calculate-spinner"><div class="spinner"></div></span>')


def callback_button(sfunc, caption, cmd, args=None, kwargs=None, spinner=False):
    """Build a submit button that posts a calculator callback command.

    The generated button posts to ``/calc/<sfunc>/?part=2`` with command payload
    in ``hx-vals`` so server-side callback handlers can execute structured UI
    actions (for example format/load/check commands).
    Set ``spinner=True`` to show the calculate-button spinner while the request runs.
    """
    # | to execute calculator callback command
    # | 'if', '' = inside form, default
    # | 'rc' = anywhere inside card, replace card
    args = [] if args is None else args
    kwargs = {} if kwargs is None else kwargs
    btn_class = 'btn btn-info btncmd btn-spin' if spinner else 'btn btn-info btncmd'
    htm = f'<button type="submit" class="{btn_class}" '  # POST

    # | hx-swap must be explicit: the form itself carries hx-swap="outerHTML"
    # | (for its own #output-part target) and hx-swap is inheritable, so
    # | without this the swap would delete the <form> element itself instead
    # | of just replacing its contents
    htm += f'hx-post="/calc/{sfunc}/?part=2" hx-target="closest form" hx-swap="innerHTML" '

    # | this button expects the FULL form back (its whole purpose is to
    # | update input, e.g. Format Code/Load Code/Validate Code) - the server's
    # | default response for an ordinary POST is now the output-only
    # | fragment, so mark this submit as structural
    extra = {"extra": {"cmd": cmd, "args": args, "kwargs": kwargs}, "qcalc_structural_cmd": "1"}
    htm += "hx-vals='" + json.dumps(extra) + "'>"
    htm += f'{_spin_inner(caption, spinner)}</button>'
    return htm


def action_button(name, caption, button_class='', spinner=False):
    """Build a named button for a calculator form action script.
    action_button() is suitable for manually constructed form_top or form_bottom inserts, 
    such as Apply Rates and Apply Compare. It is not currently a replacement for 
    declarative form-field buttons btn:0.
    Set ``spinner=True`` to show the calculate-button spinner while the action runs.
    """
    if not isinstance(name, str) or not name:
        raise ValueError('name must be a non-empty string')

    classes = 'btn btn-info btncmd ml-2'
    if spinner:
        classes += ' btn-spin'
    if button_class:
        classes += f' {button_class}'

    return (
        f'<button type="button" class="{escape(classes, quote=True)}" '
        f'name="{escape(name, quote=True)}">{_spin_inner(escape(str(caption)), spinner)}</button>'
    )


def action_script(
    button_name, cmd, field_refs=None, args=None, kwargs=None, extra=None,
    sync_table_data=False, enable_table_update_after_swap=False):
    """Build a named action_button handler that submits a structured calculator command."""
    if not isinstance(button_name, str) or not button_name:
        raise ValueError('button_name must be a non-empty string')

    def field_ref(field_name):
        if not isinstance(field_name, str) or not field_name:
            raise ValueError('Calculator field names must be non-empty strings')
        return f'@{field_name}'

    payload = {'cmd': cmd}
    payload.update(extra or {})

    if field_refs:
        payload.update({
            property_name: field_ref(field_name)
            for property_name, field_name in field_refs.items()
        })
    if args:
        payload['args'] = [field_ref(field_name) for field_name in args]
    if kwargs:
        payload['kwargs'] = {
            field_ref(field_name): action
            for field_name, action in kwargs.items()
        }

    selector = json.dumps(f'button[name="{button_name}"]')
    payload_json = json.dumps(payload, separators=(',', ':'))
    sync_script = 'updateAllData($(this));' if sync_table_data else ''
    update_script = (
        'qcalc_EnableTableUpdateAfterSwap(cid);'
        if enable_table_update_after_swap else ''
    )

    return dedent(f'''
        $(document).ready(function() {{
            const buttonSelector = {selector};
            $(buttonSelector).on("click", function() {{
                {sync_script}
                const cid = getCidOf($(this));
                {update_script}
                const busyButton = $(this).addClass("is-busy");
                $(document).one("htmx:afterRequest", function() {{ busyButton.removeClass("is-busy"); }});
                window.QCalcActions.updateExtra(cid, {payload_json});
                window.QCalcActions.qcalc_FullFormSubmit(cid);
            }});
        }});
    ''')


def addcal_button(calname, caption, icon_class=''):
    """Build a styled button that inserts a calculator card into the page."""
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


if __name__ == '__main__':
    print(callback_button('cost', 'Refresh', '__modify', args=['a', 'b']))
    print(cal_link(calurl('gold'), 'Gold', cid='xyz'))
    print(cal_link(calurl('bmi', 'weight/50 kg/height/5.5 ft/'), 'Gold', cid='xyz'))
    print(page_link('/page/home/'))
