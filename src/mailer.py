"""Envoi de la revue via le SDK officiel Brevo."""
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


def _get_client():
    """Configure et retourne le client Brevo."""
    api_key = os.environ.get("BREVO_API_KEY", "")
    if not api_key:
        raise RuntimeError("BREVO_API_KEY manquant dans les secrets GitHub.")
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = api_key
    return sib_api_v3_sdk.ApiClient(configuration)


def _fetch_recipients_from_brevo(client):
    """Récupère tous les emails de la liste Brevo configurée."""
    list_id = os.environ.get("BREVO_LIST_ID", "")
    if not list_id:
        raise RuntimeError("BREVO_LIST_ID manquant dans les secrets GitHub.")

    api = sib_api_v3_sdk.ContactsApi(client)
    recipients = []
    offset = 0
    limit = 50

    while True:
        result = api.get_contacts_from_list(
            int(list_id),
            limit=limit,
            offset=offset
        )
        contacts = result.contacts or []
        if not contacts:
            break

        for contact in contacts:
            email = (contact.get("email") or "").strip()
            if email:
                fname = (contact.get("attributes") or {}).get("PRENOM", "")
                recipients.append(
                    sib_api_v3_sdk.SendSmtpEmailTo(
                        email=email,
                        name=fname if fname else None
                    )
                )

        offset += limit
        if offset >= (result.count or 0):
            break

    return recipients


def send_newsletter(recipients_unused, html_body, issue_number, start_date, end_date):
    """Envoie la revue via l'API Brevo à tous les contacts de la liste."""
    sender_email = os.environ.get("SMTP_USER", "")
    if not sender_email:
        raise RuntimeError("SMTP_USER manquant — adresse d'envoi non définie.")

    client = _get_client()

    # Récupérer les contacts depuis la liste Brevo
    brevo_recipients = _fetch_recipients_from_brevo(client)

    if not brevo_recipients:
        print("⚠ Aucun contact dans la liste Brevo. Arrêt de l'envoi.")
        return

    print(f"  → {len(brevo_recipients)} contact(s) récupéré(s) depuis Brevo")

    subject = (
        f"Revue Huginn N°{issue_number:03d} — "
        f"semaine du {start_date.day}/{start_date.month}"
    )

    # Envoi via l'API transactionnelle Brevo
    api = sib_api_v3_sdk.TransactionalEmailsApi(client)

    email = sib_api_v3_sdk.SendSmtpEmail(
        sender=sib_api_v3_sdk.SendSmtpEmailSender(
            name="HUGINN · Veille ARQUUS",
            email=sender_email
        ),
        to=brevo_recipients,
        subject=subject,
        html_content=html_body,
        reply_to=sib_api_v3_sdk.SendSmtpEmailReplyTo(
            email=sender_email,
            name="HUGINN · Veille ARQUUS"
        )
    )

    try:
        result = api.send_transac_email(email)
        print(f"✓ Mail envoyé via Brevo à {len(brevo_recipients)} destinataire(s)")
        print(f"  → Message ID : {result.message_id}")
    except ApiException as e:
        print(f"❌ Erreur Brevo ({e.status}) : {e.body}")
        raise
