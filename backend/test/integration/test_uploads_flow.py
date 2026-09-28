"""Image uploads end to end: real routes, files written to a temporary folder."""
import re
from io import BytesIO

import pytest
from PIL import Image

import routes.uploads
from app import app
from config import Config
from rate_limit import SlidingWindowLimiter

USER = {'name': 'Photographer', 'email': 'photo@example.com', 'password': 'Password123!'}


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, 'UPLOAD_DIR', str(tmp_path))
    monkeypatch.setattr(routes.uploads, 'upload_limiter', SlidingWindowLimiter(100, 3600))
    return tmp_path


def log_in(client):
    client.post('/api/signup', json=USER)
    client.post('/api/login', json={'email': USER['email'], 'password': USER['password']})


def jpeg_bytes():
    out = BytesIO()
    Image.new('RGB', (30, 20), 'blue').save(out, 'JPEG')
    return out.getvalue()


def upload(client, data=None, field='image', filename='photo.jpg'):
    payload = {} if data is None else {field: (BytesIO(data), filename)}
    return client.post('/api/uploads', data=payload, content_type='multipart/form-data')


def test_upload_requires_login(client, upload_dir):
    # Arrange: nobody is logged in

    # Act
    response = upload(client, jpeg_bytes())

    # Assert
    assert response.status_code == 401
    assert list(upload_dir.iterdir()) == []


def test_an_uploaded_image_gets_a_url_that_serves_it(client, upload_dir):
    # Arrange
    log_in(client)

    # Act
    response = upload(client, jpeg_bytes())
    served = client.get(response.get_json()['url'])

    # Assert
    assert response.status_code == 201
    assert re.fullmatch(r'/uploads/[0-9a-f]{32}\.jpg', response.get_json()['url'])
    assert served.status_code == 200
    assert served.mimetype == 'image/jpeg'
    assert Image.open(BytesIO(served.data)).size == (30, 20)
    assert len(list(upload_dir.iterdir())) == 1


def test_the_file_name_the_browser_sent_is_ignored(client):
    # Arrange
    log_in(client)

    # Act
    response = upload(client, jpeg_bytes(), filename='../../evil.html')

    # Assert
    assert response.status_code == 201
    assert 'evil' not in response.get_json()['url']


@pytest.mark.parametrize('kwargs, message', [
    ({}, 'Choose an image to upload'),
    ({'data': jpeg_bytes(), 'field': 'photo'}, 'Choose an image to upload'),
    ({'data': b'<html>not an image</html>', 'filename': 'x.jpg'}, 'The file is not a valid image'),
])
def test_bad_uploads_are_refused(client, upload_dir, kwargs, message):
    # Arrange
    log_in(client)

    # Act
    response = upload(client, **kwargs)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': message}
    assert list(upload_dir.iterdir()) == []


def test_a_request_over_the_size_limit_gets_413(client, monkeypatch):
    # Arrange: a 1 KB limit keeps the test fast; production allows 5 MB.
    log_in(client)
    monkeypatch.setitem(app.config, 'MAX_CONTENT_LENGTH', 1024)

    # Act
    response = upload(client, b'x' * 4096)

    # Assert
    assert response.status_code == 413
    assert response.get_json() == {'message': 'The file is too large. Images can be up to 5 MB.'}


def test_the_app_limits_requests_to_5_mb():
    # Arrange: the test above lowers the limit, so this one checks the real setting.

    # Act
    limit = app.config['MAX_CONTENT_LENGTH']

    # Assert
    assert limit == 5 * 1024 * 1024


def test_uploads_per_user_are_limited(client, monkeypatch):
    # Arrange
    monkeypatch.setattr(routes.uploads, 'upload_limiter', SlidingWindowLimiter(1, 3600))
    log_in(client)
    upload(client, jpeg_bytes())

    # Act
    response = upload(client, jpeg_bytes())

    # Assert
    assert response.status_code == 429
    assert 'Retry-After' in response.headers


@pytest.mark.parametrize('path', ['/uploads/missing.jpg', '/uploads/../config.py', '/uploads/..%2Fconfig.py'])
def test_only_uploaded_files_are_served(client, path):
    # Arrange: nothing

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 404


def test_a_post_can_use_an_uploaded_image(client):
    # Arrange
    log_in(client)
    url = upload(client, jpeg_bytes()).get_json()['url']

    # Act
    client.post('/api/posts', json={'title': 'Topout view', 'body': '<p>Worth it.</p>', 'imageUrl': url})
    posts = client.get('/api/posts').get_json()

    # Assert
    assert posts[0]['image_url'] == url
