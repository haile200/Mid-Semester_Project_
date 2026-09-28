"""Checks and cleans uploaded images with Pillow.

Every upload is decoded and saved again, never stored as received. That proves it is a real image
of an allowed type, drops metadata such as the GPS position phones write into photos, and shrinks
oversized pictures.
"""
import os
import secrets
import warnings
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}
SAVE_OPTIONS = {'JPEG': {'quality': 85, 'optimize': True}, 'PNG': {'optimize': True}, 'WEBP': {'quality': 85}}
MAX_SIDE = 2000

# A small file can decode to gigabytes of pixels (a "decompression bomb"). Pillow's default limit
# of about 89 million pixels is too generous for a server with 1 GB of memory.
MAX_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class InvalidImage(ValueError):
    pass


def clean_image(data):
    """Returns (re-encoded bytes, file extension). Raises InvalidImage."""
    try:
        # Above the limit Pillow only warns; this turns the warning into the same refusal as above twice the limit.
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                image_format = image.format
                if image_format not in ALLOWED_FORMATS:
                    raise InvalidImage('Only JPEG, PNG and WebP images are allowed')
                if image_format == 'JPEG':
                    # Decodes big JPEGs at a reduced scale directly, which needs far less memory.
                    image.draft('RGB', (MAX_SIDE, MAX_SIDE))
                image.load()
                # The orientation lives in the metadata about to be dropped, so turn the pixels first.
                upright = ImageOps.exif_transpose(image)
    except InvalidImage:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise InvalidImage('The image is too large') from error
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        raise InvalidImage('The file is not a valid image') from error

    upright.thumbnail((MAX_SIDE, MAX_SIDE))
    if image_format == 'JPEG' and upright.mode not in ('RGB', 'L'):
        upright = upright.convert('RGB')

    out = BytesIO()
    # No exif= argument, so none of the original metadata is written.
    upright.save(out, image_format, **SAVE_OPTIONS[image_format])
    return out.getvalue(), ALLOWED_FORMATS[image_format]


def save_image(data, directory):
    """Cleans the image and stores it under a random name. Returns the file name."""
    cleaned, extension = clean_image(data)
    name = f'{secrets.token_hex(16)}.{extension}'
    with open(os.path.join(directory, name), 'wb') as file:
        file.write(cleaned)
    return name
