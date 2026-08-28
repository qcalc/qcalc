# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qimage, qurl, QImage, qf2img, nparray_to_bio
import io
from PIL import Image
import rembg
import cv2
from qutil import demo_url
import os
from cv2 import dnn_superres
from django.conf import settings


def image_rembg__info():
    return {
        'title': 'Remove Background from an Image',
        'calculate': 'Process',
        'schema': {
            'upload_image': {
                'help_text': 'Maximum image file size is 10 MB. '
                             'Either select an image file to upload or enter the Image Url.'
            },
        }
    }


def image_rembg(upload_image: qimage = None, image_url: qurl = demo_url('owl.jpg')):
    qimg = qf2img(upload_image, image_url)
    with Image.open(qimg.bio) as img:
        img_out = rembg.remove(img)
        bio = io.BytesIO()
        img_out.save(bio, format='png')
    return {
        'Converted Image': QImage(bio),
        'Original Image': qimg
    }


def image_upscale__info():
    return {
        'title': 'Upscale Image to Higher Resolution',
        'calculate': 'Upscale',
        'schema': {
            'upload_image': {
                'help_text': 'Maximum image file size is 5 MB. '
                             'Either select an image file to upload or enter the Image Url.',
                'max_mb': '5', 'attrs': {'onchange': 'validateFileSize(this,5)'}
            },
            'option': {
                'type': 'choice',
                'choices': [
                    'Fastest and ok: FSRCNN-small',
                    'Fast and accurate: FSRCNN',
                    'Fast and good: ESPCN',
                    'Slow and better: LAPSRN',
                    # 'Slowest and best: EDSR',
                ],
            },
        },  # schema
        'related': {
            'r1': {
                "fields": {
                    "option": "Fast and accurate (FSRCNN)",
                    "scale": '2',
                },
                "relation": {
                    "Fastest and ok: FSRCNN-small": ['2', '3', '4'],
                    "Fast and accurate: FSRCNN": ['2', '3', '4'],
                    "Fast and good: ESPCN": ['2', '3', '4'],
                    "Slow and better: LAPSRN": ['2', '4', '8'],
                    # "Slowest and best: EDSR": ['2', '3', '4'],
                }
            }
        }
    }


def image_upscale(upload_image: qimage = None, image_url: qurl = demo_url('owl.jpg'),
                  option='Fast and accurate: FSRCNN', scale='2'):
    qimg = qf2img(upload_image, image_url)

    # Create an SR object
    # sr = dnn_superres.DnnSuperResImpl()
    sr = dnn_superres.DnnSuperResImpl_create()

    # Read image
    image = qimg.imageCV2()
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Read the desired model
    # model = "FSRCNN_x2.pb"
    option_key = option.split(':')[1].strip()
    model_name = f"{option_key}_x{scale}.pb"
    path = f"{settings.AI_MODELS_DIR}{model_name}"
    if not os.path.exists(path):
        raise FileNotFoundError(f"The model file {path} was not found")

    sr.readModel(path)
    # Set the desired model and scale to get correct pre- and post-processing
    # sr.setModel("edsr", scale)
    model_type = option_key.lower().replace('-small', '')
    sr.setModel(model_type, int(scale))
    # Upscale the image
    result_rgb = sr.upsample(image_rgb)
    # Save the image
    bio = nparray_to_bio(result_rgb, 'PNG')
    return {
        'Converted Image': QImage(bio),
        'Original Image': qimg
    }
