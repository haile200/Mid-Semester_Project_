import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import app

# 1. Move mock classes OUTSIDE the test function
class DummyCursor:
    def __init__(self):
        self.queries = []
        self.lastrowid = 1
        self.description = (
            ('id',),
            ('name',),
            ('email',),
            ('password',),
            ('profile_picture',)
        )

    def execute(self, query, params=None):
        self.queries.append((query, params or ()))

    def fetchone(self):
        return None

    def close(self):
        pass

class DummyConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        pass

# 2. Use @patch decorators instead of nested 'with' blocks
# Note: The arguments are passed to the function in REVERSE order of the decorators
@patch('routes.auth.get_db')
@patch('routes.auth.bcrypt.gensalt', return_value=b'salt')
@patch('routes.auth.bcrypt.hashpw', return_value=b'hashed_password')
def test_signup_creates_user_with_hashed_password(mock_hashpw, mock_gensalt, mock_get_db):
    # Arrange
    dummy_cursor = DummyCursor()
    dummy_conn = DummyConnection(dummy_cursor)
    mock_get_db.return_value = dummy_conn
    
    client = app.test_client()
    
    # Act
    response = client.post(
        '/api/signup',
        json={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'secret123'
        }
    )

    # Assert
    assert response.status_code == 201
    assert response.get_json() == {'message': 'Registered successfully'}
    assert dummy_conn.committed is True
    
    # Verify the correct query was executed
    assert any(
        query.startswith('INSERT INTO users') for query, _ in dummy_cursor.queries
    )

@patch('routes.auth.get_db')
def test_signup_fails_with_existing_email(mock_get_db):
    # Arrange
    dummy_cursor = DummyCursor()
    dummy_cursor.fetchone = lambda: (1,)
    dummy_conn = DummyConnection(dummy_cursor)
    mock_get_db.return_value = dummy_conn
    
    client = app.test_client()
    
    # Act
    response = client.post(
        '/api/signup',
        json={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'secret123'
        }
    )

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Email already registered'}


def test_signup_fails_with_invalid_json():
    client = app.test_client()
        
    response = client.post('/api/signup', data='not a json', content_type='application/json')
        
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid JSON payload'}

def test_signup_fails_with_missing_fields():

    client = app.test_client()
        
    response = client.post('/api/signup', json={'name': 'Test User'})
        
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Name, email, and password are required'}


def test_signup_fails_with_empty_fields():

    client = app.test_client()
        
    response = client.post('/api/signup', json={'name': ' ', 'email': ' ', 'password': ' '})
        
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Name, email, and password are required'}

def test_login_fails_with_invalid_json():
    client = app.test_client()
        
    response = client.post('/api/login', data='not a json', content_type='application/json')
        
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid JSON payload'}

def test_login_fails_with_missing_fields():
    client = app.test_client()
        
    response = client.post('/api/login', json={'email': 'test@example.com'})
        
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Email and password are required'}

def test_login_fails_with_empty_fields():
    client = app.test_client()
        
    response = client.post('/api/login', json={'email': ' ', 'password': ' '})
        
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Email and password are required'}


@patch('routes.auth.get_db')
def test_login_fails_with_nonexistent_email(mock_get_db):
    # Arrange
    dummy_cursor = DummyCursor()
    dummy_cursor.fetchone = lambda: None
    dummy_conn = DummyConnection(dummy_cursor)
    mock_get_db.return_value = dummy_conn
    
    client = app.test_client()
    
    # Act
    response = client.post(
        '/api/login',
        json={
            'email': 'nonexistent@example.com',
            'password': 'secret123'
        }
    )

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Invalid credentials'}

@patch('routes.auth.get_db')
@patch('routes.auth.bcrypt.checkpw', return_value=False)
def test_login_fails_with_incorrect_password(mock_checkpw, mock_get_db):
    # Arrange
    dummy_cursor = DummyCursor()
    dummy_cursor.fetchone = lambda: (1, 'Test User', 'test@example.com', 'wrong_password', None)
    dummy_conn = DummyConnection(dummy_cursor)
    mock_get_db.return_value = dummy_conn


