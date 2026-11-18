# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import base64
import numpy as np
from PIL import Image
import io
import cv2
from .mod_qfile import QFile, qf2bio
import qconst

class QImage:
    """Represent an image held in memory for use in calculator results.

    ``bio`` is a binary buffer containing image data; ``qf2img()`` is usually
    the easiest way to create it from an uploaded file. Use ``image()`` or
    ``imageB64()`` for base64 text, ``imagePIL()`` for a PIL image, and
    ``nparray()`` or ``imageCV2()`` for a NumPy image array.
    """

    imgsize = (qconst.CHART_WIDTH, qconst.CHART_HEIGHT)

    def __init__(self, bio):
        self.b64 = None
        self.bio = bio  # bytesIO in memory buffer
        self.bio2b64()

    def __str__(self):
        if self.b64 is None:
            return 'Image not encoded'
        return f'Image base64 size {len(self.b64)} bytes'

    def bio2b64(self):  # bio = bytesIO
        """Encode the current image buffer as base64 and store it on this object."""
        self.b64 = base64.b64encode(self.bio.getvalue()).decode()

    def image(self):
        """Return the image as base64 text, or ``None`` if it has not been encoded."""
        return self.b64

    def imageB64(self):
        """Return the base64-encoded image text; equivalent to ``image()``."""
        return self.b64

    def imagePIL(self):
        """Open and return the image as a PIL image object."""
        return Image.open(self.bio)

    def nparray(self):
        """Decode and return the image as an OpenCV NumPy array."""
        return cv2.imdecode(np.frombuffer(self.bio.getvalue(), np.uint8), cv2.IMREAD_COLOR)

    def imageCV2(self):
        """Return the image as an OpenCV NumPy array; equivalent to ``nparray()``."""
        return self.nparray()


def nparray_to_bio(np_array, format_='PNG'):
    """Convert a NumPy image array to a binary buffer suitable for ``QImage``.

    ``format_`` is an image format such as ``'PNG'`` or ``'JPEG'``. Arrays that
    are not ``uint8`` are scaled to 8-bit values before the image is written.
    The returned buffer is positioned at the beginning, ready to be read.
    """
    # Function to convert NumPy array to BytesIO
    if np_array.dtype != np.uint8:
        np_array = (np_array * 255).astype(np.uint8)
    image = Image.fromarray(np_array)
    byte_io = io.BytesIO()
    image.save(byte_io, format=format_)
    byte_io.seek(0)
    return byte_io


def qf2img(qf: QFile, url=''):
    """Create a ``QImage`` from an uploaded ``QFile`` or an image URL.

    When both are supplied, the URL takes precedence.
    """
    bio = qf2bio(qf, url)
    qimg = QImage(bio)
    return qimg
