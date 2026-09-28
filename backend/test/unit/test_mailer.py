"""The mailer against a fake SMTP server: no network, no mail account."""
import logging

import pytest

import mailer
from config import Config


class FakeSMTP:
    instances = []

    def __init__(self, host, port, context=None, timeout=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.logged_in_as = None
        self.sent = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def login(self, user, password):
        self.logged_in_as = (user, password)

    def send_message(self, message):
        self.sent.append(message)


@pytest.fixture
def smtp(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(mailer.smtplib, 'SMTP_SSL', FakeSMTP)
    monkeypatch.setattr(Config, 'SMTP_HOST', 'smtp.example.test')
    monkeypatch.setattr(Config, 'SMTP_PORT', 465)
    monkeypatch.setattr(Config, 'SMTP_USER', 'sender@example.test')
    monkeypatch.setattr(Config, 'SMTP_PASSWORD', 'app-password')
    monkeypatch.setattr(Config, 'MAIL_FROM', '')
    return FakeSMTP


def test_send_email_logs_in_and_sends_one_message(smtp):
    # Arrange: SMTP settings from the fixture

    # Act
    mailer.send_email('climber@example.test', 'Hello', 'Body text')

    # Assert
    server = smtp.instances[0]
    assert (server.host, server.port) == ('smtp.example.test', 465)
    assert server.timeout == mailer.TIMEOUT_SECONDS
    assert server.logged_in_as == ('sender@example.test', 'app-password')
    message = server.sent[0]
    assert message['To'] == 'climber@example.test'
    assert message['From'] == 'sender@example.test'
    assert message['Subject'] == 'Hello'
    assert message.get_content().strip() == 'Body text'


def test_mail_from_overrides_the_sender_address(smtp, monkeypatch):
    # Arrange
    monkeypatch.setattr(Config, 'MAIL_FROM', 'My Beta <sender@example.test>')

    # Act
    mailer.send_email('climber@example.test', 'Hello', 'Body')

    # Assert
    assert smtp.instances[0].sent[0]['From'] == 'My Beta <sender@example.test>'


def test_without_smtp_settings_the_email_is_logged_not_sent(smtp, monkeypatch, caplog):
    # Arrange: development machines and tests have no mail account.
    monkeypatch.setattr(Config, 'SMTP_PASSWORD', '')

    # Act
    with caplog.at_level(logging.WARNING, logger='mailer'):
        mailer.send_email('climber@example.test', 'Hello', 'the link is here')

    # Assert
    assert smtp.instances == []
    assert 'climber@example.test' in caplog.text
    assert 'the link is here' in caplog.text


def test_send_in_background_sends_on_another_thread(smtp):
    # Arrange: nothing

    # Act
    thread = mailer.send_in_background('climber@example.test', 'Hello', 'Body')
    thread.join(timeout=5)

    # Assert
    assert len(smtp.instances[0].sent) == 1


def test_a_failed_background_send_is_logged_not_raised(monkeypatch, caplog):
    # Arrange: the SMTP server refuses the connection.
    def refuse(*args, **kwargs):
        raise ConnectionRefusedError('connection refused')
    monkeypatch.setattr(mailer, 'send_email', refuse)

    # Act
    with caplog.at_level(logging.ERROR, logger='mailer'):
        thread = mailer.send_in_background('climber@example.test', 'Hello', 'Body')
        thread.join(timeout=5)

    # Assert
    assert 'Could not send email to climber@example.test' in caplog.text


def test_password_reset_email_has_the_name_link_and_expiry():
    # Arrange
    link = 'http://example.test/reset-password#token=abc'

    # Act
    subject, body = mailer.password_reset_email('Alex', link, minutes=30)

    # Assert
    assert subject == 'Reset your My Beta password'
    assert 'Hi Alex' in body
    assert link in body
    assert '30 minutes' in body
    assert 'ignore this email' in body
