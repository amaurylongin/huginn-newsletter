"""Envoi SMTP de la newsletter via Gmail."""
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_newsletter(recipients, html_body, issue_number, start_date, end_date):
    """Envoie la newsletter à la liste des destinataires.

    Chaque destinataire reçoit un message individuel (pour masquer les autres).
    """
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))

    subject = (
        f"Revue Huginn N°{issue_number:03d} — "
        f"semaine du {start_date.day}/{start_date.month}"
    )

    plain_fallback = (
        f"Revue Huginn N°{issue_number:03d}\n\n"
        "Votre client mail ne supporte pas le HTML. "
        "Consultez l'édition en ligne via le lien d'archive en bas du mail."
    )

    context = ssl.create_default_context()
    sent = 0
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(smtp_user, smtp_password)

        for recipient in recipients:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"HUGINN · Veille ARQUUS <{smtp_user}>"
            msg["To"] = recipient
            msg["Subject"] = subject
            msg["Reply-To"] = smtp_user

            msg.attach(MIMEText(plain_fallback, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            server.send_message(msg)
            sent += 1
            print(f"  ✓ Envoyé à {recipient}")

    print(f"Total : {sent} mail(s) envoyé(s).")
