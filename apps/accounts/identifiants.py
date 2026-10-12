"""
Attribution et transmission des identifiants de connexion.

Le gestionnaire ne choisit jamais le mot de passe d'un utilisateur : le système génère
un mot de passe provisoire, l'envoie par email (si possible), l'affiche une seule fois
au gestionnaire, et oblige l'utilisateur à le remplacer à sa première connexion.
"""
import secrets

from django.urls import reverse

from config.emails import envoyer_email_notification

# Caractères sans ambiguïté à la lecture (pas de 0/O, 1/l/I) : le mot de passe peut être dicté ou recopié
_LETTRES = 'abcdefghjkmnpqrstuvwxyz'
_CHIFFRES = '23456789'

CLE_SESSION = 'identifiants_a_transmettre'

# Résultats possibles de l'envoi par email
EMAIL_ENVOYE = 'envoye'
EMAIL_ECHEC = 'echec'
EMAIL_ABSENT = 'absent'


def generer_mot_de_passe_provisoire():
    """Ex : Kf-4827-hmtq (12 caractères, facile à recopier)."""
    chiffres = ''.join(secrets.choice(_CHIFFRES) for _ in range(4))
    lettres = ''.join(secrets.choice(_LETTRES) for _ in range(4))
    return f"Kf-{chiffres}-{lettres}"


def attribuer_mot_de_passe_provisoire(utilisateur):
    """Remplace le mot de passe de l'utilisateur par un mot de passe provisoire et le retourne."""
    mot_de_passe = generer_mot_de_passe_provisoire()
    utilisateur.set_password(mot_de_passe)
    utilisateur.doit_changer_mot_de_passe = True
    utilisateur.save(update_fields=['password', 'doit_changer_mot_de_passe'])
    return mot_de_passe


def _envoyer_par_email(utilisateur, mot_de_passe, url_connexion, nouveau_compte):
    if not utilisateur.email:
        return EMAIL_ABSENT

    roles = ', '.join(utilisateur.get_roles_display()) or 'Utilisateur'
    if nouveau_compte:
        sujet = "Vos identifiants de connexion"
        intro = f"Un compte <strong>{roles}</strong> vient de vous être créé sur la plateforme de la Ligue."
    else:
        sujet = "Votre nouveau mot de passe provisoire"
        intro = "Un nouveau mot de passe provisoire vient de vous être attribué sur la plateforme de la Ligue."

    contenu = (
        f"<p>Bonjour {utilisateur.civilite} {utilisateur.get_full_name() or utilisateur.username},</p>"
        f"<p>{intro}</p>"
        f"<p>• <strong>Adresse de connexion :</strong> <a href=\"{url_connexion}\">{url_connexion}</a><br>"
        f"• <strong>Nom d'utilisateur :</strong> {utilisateur.username}<br>"
        f"• <strong>Mot de passe provisoire :</strong> <code style=\"font-size:1.05rem\">{mot_de_passe}</code></p>"
        f"<p>À votre première connexion, vous devrez choisir votre propre mot de passe. "
        f"Ne communiquez jamais vos identifiants à une autre personne.</p>"
    )
    envoye = envoyer_email_notification(
        destinataires=[utilisateur.email],
        sujet=sujet,
        titre_entete=sujet,
        contenu_html_ou_texte=contenu,
        synchrone=True,
    )
    return EMAIL_ENVOYE if envoye else EMAIL_ECHEC


def transmettre_identifiants(request, utilisateur, nouveau_compte=True):
    """
    Attribue un mot de passe provisoire, tente l'envoi par email et prépare
    le récapitulatif affiché une seule fois au gestionnaire.
    """
    mot_de_passe = attribuer_mot_de_passe_provisoire(utilisateur)
    url_connexion = request.build_absolute_uri(reverse('accounts:login'))
    statut_email = _envoyer_par_email(utilisateur, mot_de_passe, url_connexion, nouveau_compte)

    request.session[CLE_SESSION] = {
        'utilisateur_id': utilisateur.pk,
        'nom_complet': utilisateur.get_full_name() or utilisateur.username,
        'roles': ', '.join(utilisateur.get_roles_display()),
        'username': utilisateur.username,
        'mot_de_passe': mot_de_passe,
        'email': utilisateur.email,
        'telephone': utilisateur.telephone,
        'url_connexion': url_connexion,
        'statut_email': statut_email,
        'nouveau_compte': nouveau_compte,
    }
    return statut_email
