import pytest

from utils import html_to_text


@pytest.mark.parametrize('markup, expected', [
    ('<p>one</p><p>two</p>', 'one two'),
    ('first<br>second', 'first second'),
    ('<a href="https://example.com">link</a> text', 'link text'),
    ('rock &amp; roll', 'rock & roll'),
    ('  lots \n of   space  ', 'lots of space'),
    ('Plain text stays the same', 'Plain text stays the same'),
])
def test_html_to_text_returns_readable_plain_text(markup, expected):
    # Arrange: the parameters above

    # Act
    result = html_to_text(markup)

    # Assert
    assert result == expected


def test_html_to_text_rejoins_a_word_split_by_inline_markup():
    # Arrange: on screen this reads as one word, so the text must too.
    markup = 'id<strong>iot</strong>'

    # Act
    result = html_to_text(markup)

    # Assert
    assert result == 'idiot'
