# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import io
import uuid
import os
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
import base64
import json
from qutil.mod_url import fetch_url
from qutil.mod_file import decode_text


# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-DATA_UPLOAD_MAX_MEMORY_SIZE
# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-FILE_UPLOAD_MAX_MEMORY_SIZE
# nginx client_max_body_size


class QFile:
    """Represent a file supplied to a calculator through a file input.

    You normally receive a ``QFile`` from a ``qfile`` field rather than creating
    one yourself. Use ``text()`` for decoded text, ``txt_buf()`` for a text
    buffer, or ``bin_buf()`` for a binary buffer. ``file_name``, ``file_bytes``
    and ``file_type`` provide information about the upload.
    """

    def __init__(self, ffld, fdata):
        self.field_name: str = ffld
        self.file_name: str = fdata.name
        self.file_mem: InMemoryUploadedFile = fdata
        self.file_bytes = self.file_mem.read()
        # self.temp_file_name: str = fdata.file.name

    def __str__(self):
        return f'File {self.file_name}'

    def text(self):
        """Return the uploaded file's contents decoded as text."""
        return decode_text(self.file_bytes)

    def txt_buf(self):
        """Return a new readable text buffer containing the uploaded file."""
        return io.StringIO(decode_text(self.file_bytes))

    def bin_buf(self):
        """Return a new binary buffer containing the uploaded file's bytes."""
        return io.BytesIO(self.file_bytes)  # base64.b64encode

    @property
    def file_type(self):
        """Return a lowercase file-type name based on the filename and content type."""
        ctypes = {
            'application/vnd.ms-excel': 'csv',
            'text/plain': 'txt',
            'text/xml': 'xml',
            'text/html': 'html',
            'text/markdown': 'md',
            'application/json': 'json',
            'application/msaccess': 'accdb',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            # 'sqlite, unknown - application/octet-stream'
        }
        ext = os.path.splitext(self.file_name)[1].lower().lstrip('.')
        if ext in ('md', 'markdown'):  # browsers often send .md as text/plain
            return ext
        ct = self.file_mem.content_type
        if ct in ctypes:
            return ctypes[ct]
        return ext or 'unknown'

    def save2temp(self):
        """Save the upload to a temporary file and return its generated filename."""
        temp_filename = str(uuid.uuid4())  # Use a unique identifier
        temp_filepath = os.path.join(settings.FILE_UPLOAD_TEMP_DIR, temp_filename)
        with open(temp_filepath, 'wb') as temp_file:
            for chunk in self.file_mem.chunks():
                temp_file.write(chunk)
        return temp_filename

    def to_dict(self):
        """Return file metadata and base64-encoded content in a dictionary."""
        # file_content = io.BytesIO()
        # for chunk in self.file_mem.chunks():
        #     file_content.write(chunk)
        content = {
            'file': base64.b64encode(self.file_bytes).decode('utf-8'),
            'field_name': self.field_name,
            'name': self.file_name,
            'content_type': self.file_mem.content_type,
            'size': self.file_mem.size,
            # 'charset': self.file_mem.charset
        }
        return content

    def to_json(self):
        """Return the file metadata and base64-encoded content as JSON text."""
        return json.dumps(self.to_dict())  # | simple json dumps

    @staticmethod
    def load_content(sfunc, content: dict):
        """Recreate a ``QFile`` from a dictionary produced by ``to_dict()``.

        ``sfunc`` is the field name to use when the content has no field name.
        """
        fdata = InMemoryUploadedFile(
            file=io.BytesIO(base64.b64decode(content['file'])),
            field_name=content.get('field_name', sfunc),
            name=content['name'],
            content_type=content['content_type'],
            size=content['size'],
            charset=None  # content['charset']
        )
        return QFile(sfunc, fdata)


def qf2bio(qf: QFile, url=''):
    """Return a binary buffer containing an uploaded file or downloaded resource.

    Pass a ``QFile`` as ``qf``, or a non-empty ``url``. When both are supplied,
    the URL takes precedence. An error is raised when neither source is valid.
    """
    if url != '':  # url precedence
        bio = io.BytesIO(fetch_url(url).content)
    elif qf is not None:
        bio = qf.bin_buf()
    else:
        raise Exception('Error (QF2BIO): A valid file or URL is not found')
    return bio
