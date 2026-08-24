from django.core.management.base import BaseCommand
from config.emails import envoyer_email_notification
from django.conf import settings

class Command(BaseCommand):
    help = "Envoie un e-mail de test pour vérifier la configuration SMTP et les notifications HTML."

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            nargs='?',
            default='blackamericainbusness@gmail.com',
            help="Adresse e-mail du destinataire pour le test"
        )

    def handle(self, *args, **options):
        destinataire = options['email']
        self.stdout.write(self.style.WARNING(f"🧪 Tentative d'envoi d'un e-mail de test vers : {destinataire}..."))
        self.stdout.write(f"⚙️ Expéditeur configuré : {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Non défini')}")
        self.stdout.write(f"📡 Serveur SMTP : {getattr(settings, 'EMAIL_HOST', 'Console')} (Port: {getattr(settings, 'EMAIL_PORT', 587)})")

        sujet = "Test de Notification — Ligue du Kadiogo"
        titre = "Test du système d'e-mails"
        contenu = f"""
            <p>Bonjour,</p>
            <p>Ceci est un message de test envoyé depuis la plateforme de la <strong>Ligue du Kadiogo de Kung-Fu Wushu</strong>.</p>
            <p>Si vous recevez ce message, votre configuration d'envoi d'e-mails fonctionne parfaitement ! 🎉</p>
        """
        motif = "Test technique automatique du système de notifications."

        succes = envoyer_email_notification(
            destinataires=[destinataire],
            sujet=sujet,
            titre_entete=titre,
            contenu_html_ou_texte=contenu,
            motif_ou_details=motif
        )

        if succes:
            self.stdout.write(self.style.SUCCESS(f"✅ Ordre d'envoi d'e-mail exécuté avec succès vers {destinataire} !"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Échec lors de la préparation/envoi de l'e-mail vers {destinataire}."))
