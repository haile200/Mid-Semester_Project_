"""Outgoing email over SMTP (Gmail with an app password in production).

Without SMTP settings the message is written to the log instead, so development and the tests
never need a mail account.
"""
import logging
import smtplib
import ssl
import threading
from email.message import EmailMessage

from config import Config

log = logging.getLogger('mailer')

# Fails well before gunicorn's 30 s worker timeout, although sending runs off the request anyway.
TIMEOUT_SECONDS = 15


def send_email(to, subject, body):
    if not (Config.SMTP_USER and Config.SMTP_PASSWORD):
        log.warning('SMTP is not configured, so this email to %s was not sent:\n%s\n%s', to, subject, body)
        return

    message = EmailMessage()
    message['From'] = Config.MAIL_FROM or Config.SMTP_USER
    message['To'] = to
    message['Subject'] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, context=context, timeout=TIMEOUT_SECONDS) as smtp:
        smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        smtp.send_message(message)


def _send_and_log_failure(to, subject, body):
    try:
        send_email(to, subject, body)
    except Exception:
        log.exception('Could not send email to %s', to)


def send_in_background(to, subject, body):
    """Sends without making the caller wait. Returns the thread so tests can wait for it.

    Sending takes a second or two, and a password reset only sends when the account exists;
    keeping it off the request makes both answers equally fast, so timing does not reveal who is registered.
    """
    thread = threading.Thread(target=_send_and_log_failure, args=(to, subject, body), daemon=True)
    thread.start()
    return thread


def password_reset_email(name, link, minutes):
    subject = 'Reset your My Beta password'
    body = (
        f'Hi {name},\n\n'
        'Someone asked to reset the password for your My Beta account. '
        f'To choose a new password, open this link within {minutes} minutes:\n\n'
        f'{link}\n\n'
        'If you did not ask for this, you can ignore this email. Your password stays the same.\n'
    )
    return subject, body
