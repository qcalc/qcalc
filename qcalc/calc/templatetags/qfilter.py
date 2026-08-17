# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django import template

from qcore import qhtml, _unit_table, qjson_dumps, _qty_info, find_unit, qpretty_json
from qutil import href_url, is_debug, user_name, user_process, hx_target, fid2owner
from django.utils.safestring import mark_safe
from qutil import page_link, iif, qaddr, cal_link, calurl, encode_url_param
from qvars import qc_gpref as gs
from qsite import STATIC_VERSION
from django.utils.html import format_html
from django.conf import settings
from calc import QCals, StdList, get_html, ancestors, QPref, QInput, cur_as_of
import re

register = template.Library()


# | start of lineless ------------------
class LinelessNodeX(template.Node):
    # remove all blank lines excluding that within textarea, pre
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)

        # List of tags to preserve blank lines inside, e.g., textarea for CodeMirror
        preserve_tags = ['textarea', 'pre']

        def preserve_blank_lines(match):
            # Capture the full tag including its content
            full_match = match.group(0)
            return full_match  # Return the match unchanged

        # Regex to match any content inside specified tags
        pattern = r'(<({})[^>]*>[\s\S]*?</\2>)'.format('|'.join(preserve_tags))

        # Store matched content to avoid modifying it
        markers = {}
        output_copy = output  # Copy the output to work on

        # Replace the matched content with markers
        for i, match in enumerate(re.finditer(pattern, output)):
            marker = f"__MARKER_{i}__"
            markers[marker] = preserve_blank_lines(match)
            output_copy = output_copy.replace(match.group(0), marker, 1)

        # Remove blank lines from the rest of the content (outside preserved tags)
        output_copy = re.sub(r'\n\s*\n+', '\n', output_copy)

        # Restore the original content inside the preserved tags
        for marker, original_content in markers.items():
            output_copy = output_copy.replace(marker, original_content)

        return output_copy


class LinelessNode(template.Node):
    # remove all blank lines including within textarea, pre
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        content = self.nodelist.render(context)
        # Use regex to remove empty lines
        content = re.sub(r'\n\s*\n', '\n', content)
        return content


@register.tag
def lineless(parser, token):
    """
    Removes all empty lines in the content - quicker
    """
    nodelist = parser.parse(('endlineless',))
    parser.delete_first_token()
    return LinelessNode(nodelist)


@register.tag
def lineless_ex(parser, token):
    """
    Removes empty lines in the content excluding textarea and pre -- slower
    """
    nodelist = parser.parse(('endlineless_ex',))
    parser.delete_first_token()
    return LinelessNodeX(nodelist)


# | end of lineless ------------------
@register.simple_tag
def setting(name):
    return getattr(settings, name)


@register.simple_tag
def site_addr():
    return qaddr()


@register.simple_tag
def replace(value, old_string, new_string):
    return value.replace(old_string, new_string)


@register.simple_tag
def access_by_key(value, arg_key):
    return value.get(arg_key, None)


@register.simple_tag
def get_fav_state(func_id, fav_dict):
    var_input_list = fav_dict.get(func_id, None)
    if var_input_list:
        return 0 in var_input_list
    return False


@register.simple_tag
def is_in(value, list_or_dict):
    """Check if value is in list_or_dict."""
    return value in list_or_dict


@register.filter
def jdumps(dict_):
    return qjson_dumps(dict_)


@register.simple_tag
def pretty_io(request, cid, name):
    json_data = {
        cid: {
            "function": name,
            "input": request.json_d4f,
            "output": request.ojson_d4f,
            "status": request.ojson_doc,
            "times": request.times,
        }
    }
    prj = qpretty_json(json_data)
    html_output = prj.replace('\n', '<br>').replace(' ', ' ')
    return mark_safe(html_output)


@register.simple_tag
def isdebug():
    return is_debug()


@register.simple_tag
def uinfo(request=None):
    return user_name(request)


@register.simple_tag
def upinfo():
    return user_process()

@register.filter
def ucal_name(func_id):
    return func_id.split('-')[0]

@register.simple_tag
def cur_asof():
    return cur_as_of()


@register.filter
def readonly_form(form):
    for field in form.fields.values():
        field.widget.attrs['readonly'] = 'readonly'
    return form


@register.filter
def hashelp(page):
    return page in ['cal', 'console']


@register.simple_tag
def tprint(v):  # for debugging
    print(v)


@register.simple_tag
def ctf(cond, tv, fv):
    return iif(cond, tv, fv)


@register.simple_tag
def cal_var_url(calc_id, input_id: int, encode=True, run=True, shareable_only=True, is_public=True, core=False):
    execute = '&run' if run else ''
    calc_core ='calc/core' if core else 'calc'
    calc_id, cal_name, calc_owner = fid2owner(calc_id)

    var_info = QInput.get_var_info(input_id)
    var_owner = var_info.user.username if var_info else ''
    variant = var_info.variant_id if var_info else 0
    token = var_info.access_token if var_info else ''
    is_example = var_info and var_info.is_example

    # if var_owner == qvars.app_user.username and variant > 0:  # | example - shareable
    if is_example and variant > 0 and is_public:  # | example - shareable
        # return f'{qaddr()}/calc/{calc_id}/' + encode_url_param(f"?variant={variant}{execute}", encode)
        return f'{qaddr()}/{calc_core}/{calc_id}/' + encode_url_param(f"?example={variant}{execute}", encode)
    elif token:  # | token - shareable
        return f'{qaddr()}/{calc_core}/{calc_id}/' + encode_url_param(f"?token={token}{execute}", encode)
    # elif var_owner != qvars.app_user.username and variant > 0 and not shareable_only: # | private - not shareable
    elif not is_example and variant > 0 and not shareable_only:  # | private - not shareable
        return f'{qaddr()}/{calc_core}/{calc_id}/' + encode_url_param(
            f"?variant={variant}&var_owner={var_owner}{execute}", encode)
    elif not calc_owner or not shareable_only or is_public:  # | standard, shareable or user, not shareable
        execute = '?run' if run else ''
        return f"{qaddr()}/{calc_core}/{calc_id}/{execute}"
    else:
        return None


@register.simple_tag
def cal_var_desc(func_id: str, input_id: int):
    cal_id, cal_name, cal_owner = fid2owner(func_id)
    var_info = QInput.get_var_info(input_id)
    var_owner = var_info.user.username if var_info else ''
    variant = var_info.variant_id if var_info else 0
    token = var_info.access_token if var_info else ''

    remark = f'Calculator: {cal_id}, '
    cal_owner = cal_owner or 'qcalc'
    remark += f'Created by: {cal_owner}, '

    # # if var_owner == qvars.app_user.username and variant > 0:
    # if var.is_example and variant > 0:
    #     remark += f'E#{variant}: {var.description if var else ''}, Variant owner: {var_owner}, '
    # # elif var_owner != qvars.app_user.username and variant > 0:
    # elif variant > 0:
    #     remark += f'V#{variant}: {var.description if var else ''}, Variant owner: {var_owner}, '
    remark += f'V#{variant}: {var_info.description if var_info else ''}, Variant owner: {var_owner}, '

    if token:
        remark += f'Access Token: {token}, '

    return remark


@register.filter
def home_url(url_part):
    return qaddr() + url_part


@register.simple_tag
def concat(*args):
    """Concatenates all arguments into a single string."""
    return ''.join(map(str, args))


@register.simple_tag
def parents(name, page_type):
    return ancestors(name, page_type)


@register.simple_tag
def add_head(title: str, desc: str, name: str = '',
             imagelist: list | None = None, csslist: list | None = None, categories: list | None = None):
    head = get_html(title, desc, name, imagelist, csslist, categories)
    return mark_safe(head)


@register.simple_tag
def static_ver(path):
    from django.templatetags.static import static

    full_url = static(path)
    return format_html(f'{full_url}?v={STATIC_VERSION}')


@register.simple_tag
def static_ver_theme(request, file):
    theme = QPref.getp1('theme', 'default')
    return static_ver(f'css/{file}-{theme}.css')


@register.simple_tag
def get_text(key):
    return StdList.text_list.get(key, '')


@register.filter
def deslash(uname_xpr, conv=0):
    # deslash with optional converted units
    # used in from_unit and to_units with conv() and conv2()
    def replace_slash(x):
        return x.replace('/', '!')

    if uname_xpr is None:
        return uname_xpr

    if conv == 0:
        return replace_slash(uname_xpr)
    else:
        if uname_xpr in _unit_table:
            return replace_slash(_unit_table[uname_xpr].conv_name)
        if uname_xpr in _qty_info:
            return replace_slash(_qty_info[uname_xpr]['qty'].unit.conv_name)

        try:
            unit = find_unit(uname_xpr)
            return replace_slash(unit.conv_name)
        except Exception:
            pass

        return replace_slash(uname_xpr)


@register.simple_tag
def render_help_text(field):
    from django.templatetags.static import static

    if hasattr(field, 'help_text'):
        return mark_safe(f"<a><img src='{static('calc/images/info.png')}' class='info' title='{field.help_text}'></a>")
    return ''


@register.simple_tag
def target_swap_first():
    return mark_safe(hx_target('f'))


@register.simple_tag
def target_swap_last():
    return mark_safe(hx_target('l'))


@register.simple_tag
def callink(calname, caption, link_class='', icon_class='', target='f', parameters='', card=False):
    return mark_safe(cal_link(calurl(calname, parameters), caption, link_class, icon_class, target, card=card))


@register.simple_tag
def pagelink(pageurl, caption, link_class='', icon_class='', card=False):
    # {% pagelink '/page/about/' 'About Page' %}
    return mark_safe(page_link(pageurl, caption, link_class, icon_class, card=card))


@register.filter
def showlabel(field):
    return ('_uom' not in field.name and '_part' not in field.name
            and not field.is_hidden and field.label)


@register.filter
def noindex(sfunc):
    return sfunc not in QCals.qc_user_list


@register.simple_tag
def demo_mode(user):
    # check node.is_visible() to be consistent
    return gs['demo_mode'] and user.is_active


@register.filter
def is_visible(node, request):
    return node.is_visible(request)


@register.filter
def uleafcount(node, user):
    # check is_visible rules in mode_tree.py
    if settings.DEBUG:
        return node.leafcount #- node.democount + \
            # iif(gs['demo_mode'], node.democount, 0)
    else:
        return node.leafcount - node.democount - node.admincount + \
            iif(gs['demo_mode'] and user.is_active, node.democount, 0) + \
            iif(user.is_staff, node.admincount, 0)


@register.filter
def href(addurl):
    return href_url(addurl)


@register.filter
def n1(counter, n: str) -> bool:
    return (counter - 1) % int(n) == 0


@register.filter
def n2(counter, n: str) -> bool:
    return counter % int(n) == 0


@register.filter
def endswith(string: str, suffix: str):
    return string.endswith(suffix)


@register.filter
def qtyval(fname, frm):  # weight_rq_uom
    # | used to determine value of qty to be used in conv() func link
    vfield = fname.replace('_uom', '')
    # | v = frm[vfield].value() if vfield in frm else None  # frm is not a dict
    try:
        v = frm[vfield].value()
        return v.replace(',', '')
    except:
        return '1'


@register.filter
def excluded(dict_):
    rdict = {}
    types = [qhtml]
    for k, v in dict_.items():
        # print(type(v))
        if type(v) not in types:
            rdict[k] = v
        else:
            rdict[k] = 'n/a'
    return rdict
