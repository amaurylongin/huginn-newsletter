"""Envoi de la revue via l'API Brevo — contacts récupérés depuis la liste Brevo."""
import os
import json
import urllib.request
import ssl


BREVO_API_URL = "https://api.brevo.com/v3"


def _brevo_request(endpoint, method="GET", data=None):
    """Appel générique à l'API Brevo."""
    api_key = os.environ["BREVO_API_KEY"]
    url = f"{BREVO_API_URL}/{endpoint}"

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def _fetch_recipients_from_brevo():
    """Récupère tous les emails de la liste Brevo configurée."""
    list_id = os.environ.get("BREVO_LIST_ID", "")
    if not list_id:
        raise RuntimeError("BREVO_LIST_ID manquant dans les variables d'environnement.")

    recipients = []
    offset = 0
    limit = 50  # max par page sur Brevo

    while True:
        result = _brevo_request(
            f"contacts/lists/{list_id}/contacts?limit={limit}&offset={offset}"
        )
        contacts = result.get("contacts", [])
        if not contacts:
            break

        for contact in contacts:
            email = contact.get("email", "").strip()
            if email:
                recipients.append({
                    "email": email,
                    "name": contact.get("attributes", {}).get("PRENOM", ""),
                })

        offset += limit
        if offset >= result.get("count", 0):
            break

    return recipients


def send_newsletter(recipients_unused, html_body, issue_number, start_date, end_date):
    """Envoie la revue via l'API Brevo à tous les contacts de la liste.

    Le paramètre recipients_unused est ignoré — les destinataires sont
    récupérés directement depuis la liste Brevo.
    """
    sender_email = os.environ.get("SMTP_USER", os.environ.get("BREVO_SENDER", ""))
    sender_name = "HUGINN · Veille ARQUUS"

    if not sender_email:
        raise RuntimeError(
            "Aucune adresse d'envoi configurée. "
            "Définir SMTP_USER ou BREVO_SENDER dans les secrets GitHub."
        )

    # Récupérer les contacts depuis Brevo
    brevo_recipients = _fetch_recipients_from_brevo()

    if not brevo_recipients:
        print("⚠ Aucun contact dans la liste Brevo. Arrêt de l'envoi.")
        return

    print(f"  → {len(brevo_recipients)} contact(s) récupéré(s) depuis Brevo")

    subject = (
        f"Revue Huginn N°{issue_number:03d} — "
        f"semaine du {start_date.day}/{start_date.month}"
    )

    # Envoi via l'API transactionnelle Brevo
    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": brevo_recipients,
        "subject": subject,
        "htmlContent": html_body,
        "replyTo": {
            "email": sender_email,
            "name": sender_name,
        },
    }

    try:
        result = _brevo_request("smtp/email", method="POST", data=payload)
        message_id = result.get("messageId", "inconnu")
        print(f"✓ Mail envoyé via Brevo à {len(brevo_recipients)} destinataire(s)")
        print(f"  → Message ID : {message_id}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        print(f"❌ Erreur Brevo ({e.code}) : {error_body}")
        raise
