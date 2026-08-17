# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import base64
import numpy as np
from PIL import Image
import io
import cv2
from .mod_qfile import QFile, qf2bio


class QImage:
    imgsize = (620, 620)

    def __init__(self, bio):
        self.b64 = None
        self.bio = bio  # bytesIO in memory buffer
        self.bio2b64()

    def __str__(self):
        return f'Image base64 size {len(self.b64)} bytes'

    def bio2b64(self):  # bio = bytesIO
        self.b64 = base64.b64encode(self.bio.getvalue()).decode()

    def image(self):
        return self.b64

    def imageB64(self):
        return self.b64

    def imagePIL(self):
        return Image.open(self.bio)

    def nparray(self):
        return cv2.imdecode(np.frombuffer(self.bio.getvalue(), np.uint8), cv2.IMREAD_COLOR)

    def imageCV2(self):
        return self.nparray()


def nparray_to_bio(np_array, format_='PNG'):
    # Function to convert NumPy array to BytesIO
    if np_array.dtype != np.uint8:
        np_array = (np_array * 255).astype(np.uint8)
    image = Image.fromarray(np_array)
    byte_io = io.BytesIO()
    image.save(byte_io, format=format_)
    byte_io.seek(0)
    return byte_io


def qf2img(qf: QFile, url=''):
    bio = qf2bio(qf, url)
    qimg = QImage(bio)
    return qimg
