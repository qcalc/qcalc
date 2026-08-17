# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import io
import uuid
import os
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
import base64
import json
import requests


# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-DATA_UPLOAD_MAX_MEMORY_SIZE
# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-FILE_UPLOAD_MAX_MEMORY_SIZE
# nginx client_max_body_size


class QFile:
    def __init__(self, ffld, fdata):
        self.field_name: str = ffld
        self.file_name: str = fdata.name
        self.file_mem: InMemoryUploadedFile = fdata
        self.file_bytes = self.file_mem.read()
        # self.temp_file_name: str = fdata.file.name

        # print(ffld, fdata.name, self.file_mem.file.name)
        # print(settings.QCALC_TEMP_PATH)

    def __str__(self):
        return f'File {self.file_name}'

    def text(self):
        return self.file_bytes.decode('utf-8')

    def txt_buf(self):
        return io.StringIO(self.file_bytes.decode('utf-8'))

    def bin_buf(self):
        return io.BytesIO(self.file_bytes)  # base64.b64encode

    @property
    def file_type(self):
        ctypes = {
            'application/vnd.ms-excel': 'csv',
            'text/plain': 'txt',
            'text/xml': 'xml',
            'text/html': 'html',
            'application/json': 'json',
            'application/msaccess': 'accdb',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            # 'sqlite, unknown - application/octet-stream'
        }
        ct = self.file_mem.content_type
        return ctypes[ct] if ct in ctypes else 'unknown'

    def save2temp(self):
        temp_filename = str(uuid.uuid4())  # Use a unique identifier
        temp_filepath = os.path.join(settings.FILE_UPLOAD_TEMP_DIR, temp_filename)
        with open(temp_filepath, 'wb') as temp_file:
            for chunk in self.file_mem.chunks():
                temp_file.write(chunk)
        return temp_filename

    def to_dict(self):
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
        return json.dumps(self.to_dict())  # | simple json dumps

    @staticmethod
    def load_content(sfunc, content: dict):
        fdata = InMemoryUploadedFile(
            file=io.BytesIO(base64.b64decode(content['file'])),
            field_name=['field_name'],
            name=content['name'],
            content_type=content['content_type'],
            size=content['size'],
            charset=None  # content['charset']
        )
        return QFile(sfunc, fdata)


def qf2bio(qf: QFile, url=''):
    if url != '':  # url precedence
        response = requests.get(url)
        bio = io.BytesIO(response.content)
    elif qf is not None:
        bio = qf.bin_buf()
    else:
        raise Exception(f'Error (QF2BIO): A valid file or URL is not found')
    return bio
