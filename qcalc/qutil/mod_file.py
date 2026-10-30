# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from .mod_md import md2html, wrap_md_images


def decode_text(raw: bytes) -> str:
    # source files may be saved as utf-8 or utf-16 (BOM); utf-8-sig strips a utf-8 BOM,
    # and bad bytes are replaced rather than 500ing
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return raw.decode('utf-8', errors='replace')


def read_doc_text(doc_path):
    return decode_text(doc_path.read_bytes())


def read_doc_content(doc_path, *, allow_text=False, md_postprocess=None):
    if not doc_path.exists():
        return None

    if doc_path.suffix == '.md':
        document_html = wrap_md_images(md2html(read_doc_text(doc_path)))
        if md_postprocess:
            document_html = md_postprocess(document_html)
        return {'dyn_html': document_html, 'help_html': ''}

    if allow_text and doc_path.suffix == '.txt':
        from django.utils.html import escape, linebreaks

        document_html = linebreaks(escape(read_doc_text(doc_path)))
        return {'dyn_html': document_html, 'help_html': ''}

    return {'dyn_html': '', 'help_html': doc_path.as_posix()}
