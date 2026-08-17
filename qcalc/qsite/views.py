# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from . import __version__
from calc import QCals, QCache, QPref, get_help_path, cur_as_of
from .mod_docs import get_doc_path, build_docs_tree
from qutil import HtmxHttpRequest, get_page, q1139_request_init
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe
from pathlib import Path
import time
import markdown
from qvars import qc_gpref as gs
import qenv
from django.http import Http404, JsonResponse
import json
from calculators.all.general.cal_evacon import qeval
from calculators.all.admin.cal_email import email_send
from qcore import QEncoderBase
import qutil as ut
from django.shortcuts import render, redirect
from .forms import ContactForm
import qconst


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request, request.POST, post=True)
        if form.is_valid():  # POST valid
            if form.cleaned_data['honeypot']:  # Likely a bot
                return render(request, 'pages/contact_no_thanks.html', {})

            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Construct the email message
            email_subject = f"Contact form submission: {subject}"
            email_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            recipient_emails = settings.CONTACT_EMAIL
            sender_email = email
            cc_emails = ''
            email_send(email_subject, recipient_emails, cc_emails,
                       email_message, sender_email, False)
            context = {'form': form}
            return render(request, 'pages/contact_thank_you.html', context)
        else:  # POST invalid
            context = {'form': form}
            return render(request, 'pages/contact_part.html', context)
    else:  # GET
        form = ContactForm(request)
        context = {'form': form}
        return get_page(request, '', context, 'contact')


def _license_text():
    license_path = Path(settings.PROJ_DIR) / 'LICENSE'
    if not license_path.exists():
        return ''
    return mark_safe(escape(_read_doc_text(license_path)))

def about_data(request: HtmxHttpRequest):
    st = time.time()
    q1139_request_init(request)  # required for QPref
    return {
        'ver': __version__,
        'license_text': _license_text(),
        'platform': qenv.get_platform_info(),
        'worker_count': qenv.get_worker_count(),
        'env_file': qenv.env_file(),
        'instance_info': qenv.get_worker_info(),
        'debug': settings.DEBUG,
        'demo': gs['demo_mode'],
        'as_of': cur_as_of(),
        'qcals_user': QCals.qc_user_list,
        'qcals_demo': QCals.qc_demo_list,
        'qcals_admin': QCals.qc_admin_list,
        'qfuncs': QCals.internals(),
        'cache': 'Active' if QCache.isactive() else 'Not Active',
        'paths': [settings.APP_DIR, settings.HELP_FILES_DIR,
                  settings.JSON_FILES_DIR],
        'prefs': [QPref.getp1('fuzzy_search'),
                  QPref.getp1('semantic_search')],
        'ptime': int((time.time() - st) * 1000),
    }


def show_page(request: HtmxHttpRequest, **kwargs):
    context = {}
    pname = kwargs.get('pname', '')
    if pname == 'about':
        context = {'data': about_data(request)}

    return get_page(request, '', context, pname)


def docs_tree(request: HtmxHttpRequest):
    template = 'tree-docs.html'
    ut.q1139_request_init(request)
    root = build_docs_tree()
    context = {
        "docs_data": root.children,
        "request": request,
        "title": "Documentation",
    }
    return ut.get_page(request, template, context, 'docs_tree')

def show_docs(request: HtmxHttpRequest):  # /help/ or /catalog/help/ or /calc/help/
    return docs_tree(request)

def show_tour(request: HtmxHttpRequest):
    return get_page(request, page='tour')


def q1_add_page_help(request: HtmxHttpRequest, **kwargs):
    pname = kwargs.get('pname', "").strip()
    template = 'page-help-partial.html'
    context = {'dyn_html': ''}
    help_path = get_help_path('page_' + pname)
    help_exists = help_path.exists()

    if help_exists:
        if help_path.suffix == '.html':
            context['help_html'] = help_path.as_posix()
        else:  # .md
            document_html = markdown.markdown(
                help_path.read_text(encoding='utf-8'),
                extensions=qconst.MARKDOWN_EXTENSIONS, output_format='html'
            )
            context['help_html'] = ""
            context['dyn_html'] = document_html
    else:
        context['help_html'] = 'nohelp.html'

    current_user = request.user
    if current_user.is_active and current_user.is_staff:
        context['editable'] = help_exists and help_path.suffix == '.html'
        context['createable'] = not help_exists
    title = f'Help Page for {pname}'
    info = {'name': pname, 'title': title}
    context['info'] = info
    context['help_path'] = help_path.as_posix()
    return ut.get_page(request, template, context, page=f'page_{pname}_help', as_card=True)

def _read_doc_text(doc_path):
    # source files may be saved as utf-8 or utf-16 (BOM); fall back to replacing bad bytes rather than 500ing
    raw = doc_path.read_bytes()
    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        return raw.decode('utf-16')
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return raw.decode('utf-8', errors='replace')

def q1_add_doc(request: HtmxHttpRequest, **kwargs):
    pname = kwargs.get('pname', "").strip()
    template = 'page-help-partial.html'
    doc_path = get_doc_path(pname)
    doc_exists = doc_path.exists()

    if doc_exists and doc_path.suffix == '.md':
        document_html = markdown.markdown(
            _read_doc_text(doc_path),
            extensions=qconst.MARKDOWN_EXTENSIONS, output_format='html'
        )
        context = {'help_html': '', 'dyn_html': document_html}
    elif doc_exists and doc_path.suffix in ['.txt']: #,'', '.py'
        # plain text has no markup, so escape it and turn newlines into <br> to preserve line breaks
        from django.utils.html import escape, linebreaks
        document_html = linebreaks(escape(_read_doc_text(doc_path)))
        context = {'dyn_html': document_html, 'help_html': ''}
    else: #.html
        context = {'dyn_html': '', 'help_html': doc_path.as_posix() if doc_exists else 'nodoc.html'}

    current_user = request.user
    if current_user.is_active and current_user.is_staff:
        context['editable'] = doc_exists and doc_path.suffix == '.html'
    title = ut.smart_title(doc_path.stem)
    info = {'name': doc_path.stem, 'title': title}
    context['info'] = info
    context['help_path'] = doc_path.as_posix()
    return ut.get_page(request, template, context, page=f'{doc_path.name}', as_card=True)

def q1_create_doc(request: HtmxHttpRequest, **kwargs):
    if not (request.user.is_active and request.user.is_staff):
        msg = f'Error (CD): Document creation is restricted to authorized users'
        return ut.show_modal(request, f"Create Doc", msg)
    file = kwargs.get('file', "").strip()
    doc_path = get_doc_path(file)
    if not doc_path.exists() and doc_path.suffix == '.html':
        try:
            f = open(doc_path.as_posix(), "w")
            f.write("Edit content")
            f.close()
        except Exception as e:
            return ut.show_modal(request, "Create Doc", f'Error (CD): {e}')
    elif doc_path.suffix != '.html':
        msg = f'Error (CD): Can not edit non .html file {doc_path.as_posix()} at the moment'
        return ut.show_modal(request, f"Create Doc", msg)
    else:
        msg = f'Error (CD): Document {doc_path.as_posix()} already exists'
        return ut.show_modal(request, f"Create Doc", msg)

    return redirect(f'/qedit/{doc_path.as_posix()}')

def show_home(request: HtmxHttpRequest):
    items = [
        {
            "url": "/catalog/calc/",
            "hx_get": "/catalog/calc/?part=1",
            "hx_trigger": "click[get_card_once('calc_tree__page')]",
            "icon_class": "icon-tree6",
            "title": "Calculator Catalog (Tree)",
            "description": "Explore the calculator catalog in a tree structure.",
        },
        {
            "url": "/catalog/calc/calculators/",
            "hx_get": "/catalog/calc/calculators/?part=1",
            "hx_trigger": "click[get_card_once('calc_cals__page')]",
            "icon_class": "icon-grid",
            "title": "Calculator Catalog (Directory)",
            "description": "Browse calculators in a simple directory format.",
        },
        {
            "url": "/catalog/qty/",
            "hx_get": "/catalog/qty/?part=1",
            "hx_trigger": "click[get_card_once('qty_tree__page')]",
            "icon_class": "icon-tree7",
            "title": "Quantity Catalog (Tree)",
            "description": "Explore quantities organized in a tree structure.",
        },
        {
            "url": "/catalog/qty/units/",
            "hx_get": "/catalog/qty/units/?part=1",
            "hx_trigger": "click[get_card_once('qty_units__page')]",
            "icon_class": "icon-grid5",
            "title": "Quantity Catalog (Directory)",
            "description": "Access quantities in a directory format.",
        },
        {
            "url": "/catalog/user/",
            "hx_get": "/catalog/user/?part=1",
            "hx_trigger": "click[get_card_once('ucalc_tree__page')]",
            "icon_class": "icon-tree5",
            "title": "Personal Catalog (Tree)",
            "description": "Explore your personal catalog in a tree view.",
        },
        {
            "url": "/catalog/user/personal/",
            "hx_get": "/catalog/user/personal/?part=1",
            "hx_trigger": "click[get_card_once('ucalc_personal__page')]",
            "icon_class": "icon-list",
            "title": "Personal Catalog (Directory)",
            "description": "Access your personal catalog in a directory format.",
        },
        {
            "url": "/catalog/pcalc/",
            "hx_get": "/catalog/pcalc/?part=1",
            "hx_trigger": "click[get_card_once('pcalc_tree__page')]",
            "icon_class": "icon-snowflake",
            "title": "Public Catalog (Tree)",
            "description": "Explore the public catalog in a tree structure.",
        },
        {
            "url": "/catalog/pcalc/pcals/",
            "hx_get": "/catalog/pcalc/pcals/?part=1",
            "hx_trigger": "click[get_card_once('pcalc_pcals__page')]",
            "icon_class": "icon-sphere",
            "title": "Public Catalog (Directory)",
            "description": "Access the public catalog in a directory format.",
        },
        {
            "url": "/tour/",
            "hx_get": "/tour/?part=1",
            "hx_trigger": "click[get_card_once('intro__page')]",
            "icon_class": "icon-notebook",
            "title": "Quick Tour",
            "description": "Get started with qCalc.",
        },
        {
            "url": "/help/",
            "hx_get": "/help/?part=1",
            "hx_trigger": "click[get_card_once('guide__page')]",
            "icon_class": "icon-notebook",
            "title": "User Guide",
            "description": "Browse all user guides and documentation.",
        },
    ]
    return get_page(request, context={"items": items}, page='home')


def show_cal(request: HtmxHttpRequest):
    return get_page(request, page='cal')


def execute_command(request: HtmxHttpRequest):
    if request.method == 'POST':
        data = json.loads(request.body)
        command = data.get('command', '')
        stdout = ""
        try:
            result, stdout = qeval(request, command)
        except Exception as e:
            result = str(e)

        if result is not None and stdout:
            resp = {'response': f'{str(result)}\n{stdout}'}
        elif result is not None:
            resp = {'response': str(result)}
        else:
            resp = {'response': str(stdout)}
        return JsonResponse(resp, encoder=QEncoderBase)  # response
