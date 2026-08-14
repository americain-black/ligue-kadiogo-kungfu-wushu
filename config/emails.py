import logging
import threading
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)

def _envoyer_email_async(msg):
    try:
        msg.send(fail_silently=True)
    except Exception as e:
        logger.error(f"Erreur envoi email d'arrière-plan : {e}")

def envoyer_email_notification(destinataires, sujet, titre_entete, contenu_html_ou_texte, motif_ou_details=None, reply_to=None):
    """
    Envoie un email de notification au format HTML propre aux couleurs de la Ligue.
    Fonctionne de manière asynchrone en arrière-plan sans bloquer la requête HTTP.
    """
    if not destinataires:
        return False

    if isinstance(destinataires, str):
        destinataires = [destinataires]

    # Filtrer les adresses emails valides
    destinataires = [d.strip() for d in destinataires if d and '@' in d]
    if not destinataires:
        return False

    expediteur = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@kadiogokungfu.teeritech.bf')

    reply_to_list = None
    if reply_to:
        if isinstance(reply_to, str):
            reply_to_list = [reply_to.strip()]
        elif isinstance(reply_to, list):
            reply_to_list = [r.strip() for r in reply_to if r and '@' in r]

    # Template HTML propre
    html_body = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; color: #1e293b; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }}
            .header {{ background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: #ffffff; padding: 24px; text-align: center; }}
            .header h2 {{ margin: 0; font-size: 1.25rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }}
            .header p {{ margin: 6px 0 0 0; font-size: 0.85rem; opacity: 0.9; }}
            .content {{ padding: 28px 24px; line-height: 1.6; font-size: 0.95rem; }}
            .card-motif {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 14px; margin: 16px 0; border-radius: 4px; color: #991b1b; font-weight: 500; }}
            .footer {{ background-color: #0f172a; color: #94a3b8; text-align: center; padding: 16px; font-size: 0.8rem; border-top: 1px solid #1e293b; }}
            .footer strong {{ color: #ffffff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{titre_entete}</h2>
                <p>Ligue du Kadiogo de Kung-Fu Wushu</p>
            </div>
            <div class="content">
                {contenu_html_ou_texte}
                {f'<div class="card-motif"><strong>Motif / Informations complémentaires :</strong><br>{motif_ou_details}</div>' if motif_ou_details else ''}
                <p style="margin-top: 24px; font-size: 0.85rem; color: #64748b;">
                    Ceci est un message automatique généré par la plateforme de la Ligue du Kadiogo de Kung-Fu Wushu (<a href="http://kadiogofunfu.bf" style="color:#dc2626;">kadiogofunfu.bf</a>).
                </p>
            </div>
            <div class="footer">
                &copy; 2026 <strong>TEERI TECH INTERNATIONAL</strong> pour la Ligue du Kadiogo de Kung-Fu Wushu.
            </div>
        </div>
    </body>
    </html>
    """

    texte_brut = f"{titre_entete}\n\n{contenu_html_ou_texte}\n\n{f'Motif / Détails : {motif_ou_details}' if motif_ou_details else ''}"

    try:
        msg = EmailMultiAlternatives(
            subject=f"[Ligue Kadiogo Wushu] {sujet}",
            body=texte_brut,
            from_email=expediteur,
            to=destinataires,
            reply_to=reply_to_list
        )
        msg.attach_alternative(html_body, "text/html")
        # Envoie dans un thread d'arrière-plan sans bloquer la vue web
        thread = threading.Thread(target=_envoyer_email_async, args=(msg,), daemon=True)
        thread.start()
        return True
    except Exception as e:
        logger.error(f"Erreur préparation email '{sujet}' : {e}")
        return False
