# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import re
import json
from html import escape


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


def addcal_button(calname, caption, icon_class='', params=''):
    """Build a styled button that inserts a calculator card into the page."""
    return cal_link(calurl(calname, params=params), caption, 'btn btn-info btncmd', icon_class, 'a', '', True)


def step2_spec(func, caption, step='run', spec='', source=None, place=''):
    """Build one step2 entry. source: 'input' (live form, shown before Calculate), 'output' or 'both'
    (cached result, shown after Calculate). place: optional insert slot, e.g. 'form_top'."""
    if not isinstance(step, str) or not step.strip():
        raise ValueError('step must be a non-empty string')

    entry = {
        'step': step,
        'caption': caption,
        'source': source or ('output' if step == 'chart' else 'both'),
    }
    if func:
        entry['func'] = func
    if spec != '':
        entry['spec'] = spec
    if place:
        entry['place'] = place
    return entry


def step2_attrs(entry, cid='', func=''):
    """htmx attributes of a step2 button. Input source: the form is posted to calculator func as a 'step2' command, so
    the server converts the live values exactly as Calculate does. Otherwise the cached result of card cid is used."""
    spec = entry.get('spec', '')
    vals = {
        'step': entry['step'],
        'func': entry.get('func', ''),
        'spec': spec if isinstance(spec, str) else json.dumps(spec, separators=(',', ':')),
        'source': entry.get('source', 'both'),
    }
    if vals['source'] == 'input':
        if not func:
            raise ValueError('an input source step2 button needs the calculator that hosts it')
        url, include, vals = f'/calc/{escape(str(func), quote=True)}/?part=2', 'hx-include="closest form" ', \
            {'extra': {'cmd': 'step2', **vals}}
    else:
        url, include, vals = '/calc/step2/', '', {**vals, 'src_cid': cid}
    vals_html = escape(json.dumps(vals, separators=(',', ':')), quote=True)
    return f'hx-post="{url}" {include}hx-vals="{vals_html}" hx-target="closest .calc" hx-swap="afterend"'


def step2_html(entry, func='', button_class=''):
    """Render one step2 entry as a button; func is the calculator hosting it (needed for an input source)."""
    classes = escape(f'btn btn-info btncmd {button_class}'.strip(), quote=True)
    return (f'<button type="button" class="{classes}" {step2_attrs(entry, func=func)}>'
            f'{escape(str(entry.get("caption", "")))}</button>')


def step2_button(calc, func, caption, step='run', spec='', source='input', button_class=''):
    """Hand-placed step2 button for any insert slot of calculator calc (form_top, form_bottom, out_top, ...)."""
    return step2_html(step2_spec(func, caption, step, spec, source), calc, button_class)


def action_spec(cmd, caption='', spec=None, args=None, kwargs=None, extra=None,
                sync_table=False, update_after_swap=False):
    """Build one same-card action entry for a btn:0 field, bound as schema[field]['button'].
    cmd is the command the calculator hooks receive (e.g. 'load', '__modify'); spec maps payload properties to
    field names, args/kwargs name the fields the command modifies, extra holds literal values.
    sync_table: sync the input tables before the request; update_after_swap: re-enable the table update button."""
    if not isinstance(cmd, str) or not cmd.strip():
        raise ValueError('cmd must be a non-empty string')

    entry = {'cmd': cmd}
    for key, value in (('caption', caption), ('spec', spec), ('args', args), ('kwargs', kwargs),
                       ('extra', extra), ('sync_table', sync_table), ('update_after_swap', update_after_swap)):
        if value:
            entry[key] = value
    return entry


def action_attrs(entry, func):
    """htmx attributes that post the form with a command to the calculator func and refresh the form."""
    payload = {'cmd': entry['cmd'], **(entry.get('extra') or {}), **(entry.get('spec') or {})}
    if entry.get('args'):
        payload['args'] = list(entry['args'])
    if entry.get('kwargs'):
        payload['kwargs'] = entry['kwargs']
    # | hx-swap must be explicit, see callback_button()
    vals = escape(json.dumps({'extra': payload, 'qcalc_structural_cmd': '1'}, separators=(',', ':')), quote=True)
    flags = ''.join(f' data-qcalc-{name}="1"' for name, key in
                    (('sync-table', 'sync_table'), ('update-after-swap', 'update_after_swap')) if entry.get(key))
    return (f'data-qcalc-action="1"{flags} hx-post="/calc/{escape(str(func), quote=True)}/?part=2" '
            f'hx-target="closest form" hx-swap="innerHTML" hx-vals="{vals}"')


def action_button(func, caption, cmd, spec=None, args=None, kwargs=None, extra=None,
                  sync_table=False, update_after_swap=False, button_class=''):
    """Hand-placed same-card action button for a form insert (form_top, form_bottom, ...) of calculator func.
    Takes the same arguments as action_spec(); inside the form, prefer a btn:0 field bound to action_spec()."""
    entry = action_spec(cmd, caption, spec, args, kwargs, extra, sync_table, update_after_swap)
    classes = escape(f'btn btn-info btncmd {button_class}'.strip(), quote=True)
    return f'<button type="button" class="{classes}" {action_attrs(entry, func)}>{escape(str(caption))}</button>'


def button_attrs(entry, func='', cid=''):
    """htmx attributes of a button bound to a field: a same-card action (cmd) or a step2 entry (step)."""
    return action_attrs(entry, func) if 'cmd' in entry else step2_attrs(entry, cid, func)


def prefix_button_names(entry, prefix):
    """Copy of a button entry with its field names prefixed, for a calculator nested in another one."""
    entry = dict(entry)
    if isinstance(entry.get('spec'), dict):  # values are field names, keys are payload properties or other-calculator arguments
        entry['spec'] = {k: prefix + v if isinstance(v, str) else v for k, v in entry['spec'].items()}
    if entry.get('args'):
        entry['args'] = [prefix + name for name in entry['args']]
    if entry.get('kwargs'):
        entry['kwargs'] = {prefix + name: action for name, action in entry['kwargs'].items()}
    return entry


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
