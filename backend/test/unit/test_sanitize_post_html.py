import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils import sanitize_post_html


def test_keeps_every_format_the_editor_produces():
    # Arrange
    editor_html = '<p>Crux is the <strong>heel hook</strong>, then <em>rest</em> and <u>match</u>.</p><p><br></p>'

    # Act
    result = sanitize_post_html(editor_html)

    # Assert
    assert result == editor_html


def test_keeps_http_links_and_forces_safe_rel():
    # Arrange
    link_html = '<p><a href="https://example.com" target="_blank">topo</a></p>'

    # Act
    result = sanitize_post_html(link_html)

    # Assert
    assert 'href="https://example.com"' in result
    assert 'rel="noopener noreferrer"' in result


def test_removes_script_tags():
    # Arrange
    payload = '<script>fetch("/api/logout", {method: "POST"})</script><p>ok</p>'

    # Act
    result = sanitize_post_html(payload)

    # Assert
    assert result == '<p>ok</p>'


def test_removes_event_handler_attributes():
    # Arrange
    payload = '<p onclick="alert(1)">x</p><img src=x onerror="alert(document.cookie)">'

    # Act
    result = sanitize_post_html(payload)

    # Assert
    assert result == '<p>x</p>'


def test_strips_javascript_urls_from_links():
    # Arrange
    payload = '<a href="javascript:alert(1)">click</a>'

    # Act
    result = sanitize_post_html(payload)

    # Assert
    assert 'javascript:' not in result
    assert 'href' not in result


def test_escapes_plain_text_special_characters():
    # Arrange
    text = 'just text & <3'

    # Act
    result = sanitize_post_html(text)

    # Assert
    assert result == 'just text &amp; &lt;3'
