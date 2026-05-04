"""Envoi de la revue via SMTP Brevo — pas de restriction IP contrairement à l'API REST."""
import os
import smtplib
import ssl
import sib_api_v3_sdk
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _fetch_recipients_from_brevo():
    """Récupère tous les emails de la liste Brevo via l'API REST (appelé depuis GitHub Actions).
    
    Note : cette partie utilise l'API REST mais uniquement en lecture (GET).
    Brevo ne restreint pas les IPs sur les appels GET dans certaines configurations.
    Si 401, on tombe en fallback sur RECIPIENTS env var.
    """
    api_key = os.environ.get("BREVO_API_KEY", "")
    list_id = os.environ.get("BREVO_LIST_ID", "")

    if not api_key or not list_id:
        return None  # fallback sur RECIPIENTS

    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = api_key
        client = sib_api_v3_sdk.ApiClient(configuration)
        api = sib_api_v3_sdk.ContactsApi(client)

        recipients = []
        offset = 0
        limit = 50

        while True:
            result = api.get_contacts_from_list(int(list_id), limit=limit, offset=offset)
            contacts = result.contacts or []
            if not contacts:
                break
            for contact in contacts:
                email = (contact.get("email") or "").strip()
                if email:
                    recipients.append(email)
            offset += limit
            if offset >= (result.count or 0):
                break

        print(f"  → {len(recipients)} contact(s) récupéré(s) depuis Brevo")
        return recipients

    except Exception as e:
        print(f"  ⚠ Impossible de lire la liste Brevo ({e}) — fallback sur RECIPIENTS")
        return None


def send_newsletter(recipients_unused, html_body, issue_number, start_date, end_date):
    """Envoie la revue via SMTP Brevo."""

    # Essayer Brevo API d'abord, sinon fallback sur secret RECIPIENTS
    recipients = _fetch_recipients_from_brevo()
    if not recipients:
        recipients_env = os.environ.get("RECIPIENTS", "")
        recipients = [r.strip() for r in recipients_env.split(",") if r.strip()]

    if not recipients:
        print("⚠ Aucun destinataire trouvé. Arrêt de l'envoi.")
        return

    # Identifiants SMTP Brevo
    smtp_host     = "smtp-relay.brevo.com"
    smtp_port     = 587
    smtp_user     = os.environ.get("BREVO_SMTP_LOGIN", os.environ.get("SMTP_USER", ""))
    smtp_password = os.environ.get("BREVO_SMTP_PASSWORD", os.environ.get("SMTP_PASSWORD", ""))
    sender_email  = os.environ.get("SMTP_USER", smtp_user)

    if not smtp_user or not smtp_password:
        raise RuntimeError(
            "Identifiants SMTP Brevo manquants. "
            "Définir BREVO_SMTP_LOGIN et BREVO_SMTP_PASSWORD dans les secrets GitHub."
        )

    subject = (
        f"Revue Huginn N°{issue_number:03d} — "
        f"semaine du {start_date.day}/{start_date.month}"
    )

    plain_fallback = (
        f"Revue Huginn N°{issue_number:03d}\n\n"
        "Consultez l'édition en ligne via le lien d'archive."
    )

    msg = MIMEMultipart("alternative")
    msg["From"]     = f"HUGINN · Veille ARQUUS <{sender_email}>"
    msg["To"]       = ", ".join(recipients)
    msg["Subject"]  = subject
    msg["Reply-To"] = sender_email

    msg.attach(MIMEText(plain_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(sender_email, recipients, msg.as_string())

    print(f"✓ Mail envoyé via SMTP Brevo à {len(recipients)} destinataire(s)")
