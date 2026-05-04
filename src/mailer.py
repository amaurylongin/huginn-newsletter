"""Envoi SMTP — destinataires depuis le secret RECIPIENTS."""
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_newsletter(recipients, html_body, issue_number, start_date, end_date):
    """Envoie la revue à tous les destinataires en To."""
    smtp_user     = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    smtp_host     = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port     = int(os.environ.get("SMTP_PORT", 587))

    subject = (
        f"Revue Huginn N°{issue_number:03d} — "
        f"semaine du {start_date.day}/{start_date.month}"
    )

    msg = MIMEMultipart("alternative")
    msg["From"]     = f"HUGINN · Veille ARQUUS <{smtp_user}>"
    msg["To"]       = ", ".join(recipients)
    msg["Subject"]  = subject
    msg["Reply-To"] = smtp_user

    msg.attach(MIMEText("Consultez l'édition en ligne via le lien d'archive.", "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipients, msg.as_string())

    print(f"✓ Mail envoyé à {len(recipients)} destinataire(s)")
