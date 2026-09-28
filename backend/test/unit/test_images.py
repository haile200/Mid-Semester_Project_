"""The upload image cleaner, on images built in memory."""
import re
from io import BytesIO

import pytest
from PIL import Image

import images
from images import MAX_SIDE, InvalidImage, clean_image, save_image

GPS_IFD = 0x8825
MAKE = 0x010F
ORIENTATION = 0x0112


def make_image(fmt, size=(40, 20), mode='RGB', exif=None):
    image = Image.new(mode, size, 'red')
    out = BytesIO()
    options = {'exif': exif} if exif is not None else {}
    image.save(out, fmt, **options)
    return out.getvalue()


def camera_exif(orientation=None):
    exif = Image.Exif()
    exif[MAKE] = 'PhoneMaker'
    exif.get_ifd(GPS_IFD)[2] = (32.0, 4.0, 0.0)  # latitude
    if orientation:
        exif[ORIENTATION] = orientation
    return exif


def open_result(data):
    return Image.open(BytesIO(data))


@pytest.mark.parametrize('fmt, extension', [('JPEG', 'jpg'), ('PNG', 'png'), ('WEBP', 'webp')])
def test_allowed_formats_keep_their_format(fmt, extension):
    # Arrange
    data = make_image(fmt)

    # Act
    cleaned, result_extension = clean_image(data)

    # Assert
    assert result_extension == extension
    assert open_result(cleaned).format == fmt
    assert open_result(cleaned).size == (40, 20)


@pytest.mark.parametrize('fmt', ['JPEG', 'PNG', 'WEBP'])
def test_camera_metadata_and_location_are_removed(fmt):
    # Arrange: a photo that says where it was taken and with which phone.
    data = make_image(fmt, exif=camera_exif())
    assert open_result(data).getexif().get(MAKE) == 'PhoneMaker'

    # Act
    cleaned, _ = clean_image(data)

    # Assert
    exif = open_result(cleaned).getexif()
    assert MAKE not in exif
    assert not exif.get_ifd(GPS_IFD)


def test_the_camera_orientation_is_applied_before_the_metadata_goes():
    # Arrange: stored sideways, with a tag that says "rotate 90 degrees when showing".
    data = make_image('JPEG', size=(40, 20), exif=camera_exif(orientation=6))

    # Act
    cleaned, _ = clean_image(data)

    # Assert: without the tag, the pixels themselves must now stand upright.
    assert open_result(cleaned).size == (20, 40)


def test_large_images_are_shrunk_to_the_maximum_side():
    # Arrange
    data = make_image('JPEG', size=(MAX_SIDE * 2, MAX_SIDE))

    # Act
    cleaned, _ = clean_image(data)

    # Assert
    assert open_result(cleaned).size == (MAX_SIDE, MAX_SIDE // 2)


def test_transparent_png_keeps_its_transparency():
    # Arrange
    data = make_image('PNG', mode='RGBA')

    # Act
    cleaned, _ = clean_image(data)

    # Assert
    assert open_result(cleaned).mode == 'RGBA'


def test_a_cmyk_jpeg_is_accepted():
    # Arrange: print-oriented JPEGs use CMYK colors.
    data = make_image('JPEG', mode='CMYK')

    # Act
    cleaned, extension = clean_image(data)

    # Assert
    assert extension == 'jpg'
    assert open_result(cleaned).size == (40, 20)


@pytest.mark.parametrize('fmt', ['GIF', 'BMP', 'TIFF'])
def test_other_image_formats_are_refused(fmt):
    # Arrange
    data = make_image(fmt, mode='RGB')

    # Act and Assert
    with pytest.raises(InvalidImage, match='Only JPEG, PNG and WebP images are allowed'):
        clean_image(data)


@pytest.mark.parametrize('data', [
    b'',
    b'not an image at all',
    b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    make_image('JPEG')[:200],  # cut off in the middle
])
def test_files_that_are_not_valid_images_are_refused(data):
    # Arrange: nothing

    # Act and Assert
    with pytest.raises(InvalidImage, match='The file is not a valid image'):
        clean_image(data)


@pytest.mark.parametrize('size', [(40, 40), (50, 50)])
def test_images_with_too_many_pixels_are_refused(monkeypatch, size):
    # Arrange: a small file can decode to a huge image ("decompression bomb"). Over the limit Pillow
    # only warns (1600 pixels here); over twice the limit it refuses (2500). Both must be refused.
    monkeypatch.setattr(Image, 'MAX_IMAGE_PIXELS', 1000)
    data = make_image('PNG', size=size)

    # Act and Assert
    with pytest.raises(InvalidImage, match='The image is too large'):
        clean_image(data)


def test_save_image_writes_the_cleaned_image_under_a_random_name(tmp_path):
    # Arrange
    data = make_image('PNG', exif=camera_exif())

    # Act
    first = save_image(data, tmp_path)
    second = save_image(data, tmp_path)

    # Assert
    assert re.fullmatch(r'[0-9a-f]{32}\.png', first)
    assert first != second
    stored = (tmp_path / first).read_bytes()
    assert stored == clean_image(data)[0]


def test_save_image_writes_nothing_for_an_invalid_file(tmp_path):
    # Arrange: nothing

    # Act
    with pytest.raises(InvalidImage):
        save_image(b'nope', tmp_path)

    # Assert
    assert list(tmp_path.iterdir()) == []


def test_the_pixel_limit_is_set_for_the_whole_process():
    # Arrange: nothing

    # Act
    limit = Image.MAX_IMAGE_PIXELS

    # Assert: importing images lowers Pillow's default of about 89 million.
    assert limit == images.MAX_PIXELS
