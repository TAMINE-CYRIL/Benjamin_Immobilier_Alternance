import os
import smtplib
from email.message import EmailMessage


class EmailDeliveryError(RuntimeError):
    pass


def _env_bool(name, default=False):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.lower() in {"1", "true", "yes", "on"}


def send_email(to_email, subject, text_body):
    """
    Envoie un email via SMTP. Les identifiants SMTP viennent de l'environnement.
    """
    host = os.getenv("SMTP_HOST")
    if not host:
        raise EmailDeliveryError("SMTP_HOST is not configured")

    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM") or username
    use_tls = _env_bool("SMTP_USE_TLS", default=True)

    if not sender:
        raise EmailDeliveryError("SMTP_FROM or SMTP_USERNAME must be configured")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
    except Exception as exc:
        raise EmailDeliveryError(str(exc)) from exc
