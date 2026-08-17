# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from pathlib import Path


def edit_html_file(request, **kwargs):
    if not (request.user.is_active and request.user.is_staff):
        return HttpResponseForbidden("Error (EHF): Document editing is restricted to authorized users")

    # only allow editing .html files within the configured help/docs roots
    allowed_roots = [Path(settings.HELP_FILES_DIR).resolve(), Path(settings.DOCS_FILES_DIR).resolve()]
    try:
        file_path = Path(str(kwargs.get('file_path'))).resolve()
    except OSError:
        return HttpResponse("Invalid path!", status=400)
    if file_path.suffix != '.html' or not any(
            root in file_path.parents or root == file_path for root in allowed_roots):
        return HttpResponseForbidden("Path is not allowed to be edited")

    if file_path.exists():
        if request.method == 'POST':
            # Update the content if form is submitted
            content = request.POST.get('content')
            file_path.write_text(content, encoding='utf-8')
        else:
            # Read the content of the HTML file
            content = file_path.read_text(encoding='utf-8')

        return render(request, 'edit_html.html',
                      {'content': content, 'file': file_path.as_posix()})
    else:
        return HttpResponse("File not found!")
