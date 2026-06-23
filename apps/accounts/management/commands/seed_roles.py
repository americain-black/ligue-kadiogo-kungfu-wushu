from django.core.management.base import BaseCommand
from apps.accounts.models import Role, Permission, RolePermission


PERMISSIONS = [

    # ── SUPER ADMIN — Gestion système ────────────────────────────────
    ('creer_compte',           'Créer un compte utilisateur',          'systeme'),
    ('attribuer_role',         'Attribuer un rôle à un utilisateur',   'systeme'),
    ('retirer_role',           'Retirer un rôle à un utilisateur',     'systeme'),
    ('desactiver_compte',      'Désactiver/Réactiver un compte',       'systeme'),
    ('voir_connectes',         'Voir les comptes connectés en temps réel','systeme'),
    ('ajouter_ligue',          'Ajouter une ligue dans le système',    'systeme'),
    ('supprimer_ligue',        'Supprimer/Désactiver une ligue',       'systeme'),

    # ── GEST_LIGUE — Clubs & Affiliations ────────────────────────────
    ('valider_affiliation',    'Valider ou rejeter une affiliation',   'clubs'),
    ('suspendre_club',         'Suspendre un club affilié',            'clubs'),
    ('consulter_clubs',        'Consulter la liste des clubs',         'clubs'),

    # ── GEST_LIGUE — Années sportives ────────────────────────────────
    ('gerer_annees_sportives', 'Gérer les années sportives',           'annees'),

    # ── GEST_LIGUE — Sessions d'examen ───────────────────────────────
    ('creer_session',          'Créer une session d examen',           'examens'),
    ('gerer_sessions',         'Gérer les sessions d examen',          'examens'),
    ('gerer_rubriques',        'Gérer les rubriques et épreuves',      'examens'),
    ('affecter_jury',          'Affecter les membres du jury',         'examens'),
    ('autoriser_participation','Autoriser la participation candidat',  'examens'),

    # ── GEST_LIGUE — Résultats & Bulletins ───────────────────────────
    ('publier_resultats',      'Publier les résultats officiels',      'resultats'),
    ('gerer_bulletins',        'Générer et gérer les bulletins PDF',   'resultats'),

    # ── GEST_LIGUE — Communication ───────────────────────────────────
    ('publier_actualites',     'Publier des actualités officielles',   'communication'),
    ('valider_actualites',     'Valider les actualités des clubs',     'communication'),
    ('publier_documents',      'Publier des documents officiels',      'communication'),

    # ── GEST_LIGUE — Paiements (consultation) ────────────────────────
    ('consulter_paiements',    'Consulter les paiements validés',      'paiements'),

    # ── GEST_CLUB — Gestion du club ──────────────────────────────────
    ('soumettre_affiliation',  'Soumettre une demande d affiliation',  'clubs'),
    ('gerer_mon_club',         'Gérer les informations de son club',   'clubs'),
    ('gerer_pratiquants',      'Gérer les pratiquants de son club',    'pratiquants'),
    ('gerer_inscriptions',     'Inscrire les pratiquants aux examens', 'examens'),
    ('signaler_paiement',      'Signaler un paiement effectué',        'paiements'),
    ('gerer_actualites_club',  'Gérer les actualités de son club',     'communication'),
    ('consulter_resultats',    'Consulter les résultats de son club',  'resultats'),
    ('telecharger_bulletins',  'Télécharger les bulletins PDF',        'resultats'),

    # ── GEST_FINANCIER ───────────────────────────────────────────────
    ('valider_paiement',       'Valider ou rejeter un paiement',       'paiements'),
    ('voir_historique_paiem',  'Voir l historique des paiements',      'paiements'),

    # ── JURY ─────────────────────────────────────────────────────────
    ('saisir_notes',           'Saisir les notes d évaluation',        'jury'),
    ('valider_notes',          'Valider les notes saisies',            'jury'),
    ('consulter_evaluations',  'Consulter l historique des évaluations','jury'),
]


# ── Attribution des permissions par rôle ─────────────────────────────

ROLE_PERMS = {

    Role.SUPER_ADMIN: [
        'creer_compte',
        'attribuer_role',
        'retirer_role',
        'desactiver_compte',
        'voir_connectes',
        'ajouter_ligue',
        'supprimer_ligue',
    ],

    Role.GEST_LIGUE: [
        # Clubs
        'valider_affiliation',
        'suspendre_club',
        'consulter_clubs',
        # Années sportives
        'gerer_annees_sportives',
        # Examens
        'creer_session',
        'gerer_sessions',
        'gerer_rubriques',
        'affecter_jury',
        'autoriser_participation',
        # Résultats
        'publier_resultats',
        'gerer_bulletins',
        # Communication
        'publier_actualites',
        'valider_actualites',
        'publier_documents',
        # Paiements
        'consulter_paiements',
        # Hérite aussi des droits Gestionnaire Club
        'soumettre_affiliation',
        'gerer_mon_club',
        'gerer_pratiquants',
        'gerer_inscriptions',
        'signaler_paiement',
        'gerer_actualites_club',
        'consulter_resultats',
        'telecharger_bulletins',
        # Hérite aussi des droits Jury
        'saisir_notes',
        'valider_notes',
        'consulter_evaluations',
    ],

    Role.GEST_CLUB: [
        'soumettre_affiliation',
        'gerer_mon_club',
        'gerer_pratiquants',
        'gerer_inscriptions',
        'signaler_paiement',
        'gerer_actualites_club',
        'consulter_resultats',
        'telecharger_bulletins',
    ],

    Role.GEST_FINANCIER: [
        'valider_paiement',
        'voir_historique_paiem',
        'consulter_paiements',
    ],

    Role.JURY: [
        'saisir_notes',
        'valider_notes',
        'consulter_evaluations',
    ],
}


class Command(BaseCommand):
    help = "Initialise les rôles et permissions du système"

    def handle(self, *args, **kwargs):
        self.stdout.write("\n── Création des permissions ──────────────────")
        perms_cache = {}
        for code, nom, module in PERMISSIONS:
            perm, created = Permission.objects.update_or_create(
                code=code,
                defaults={'nom_permission': nom, 'module': module}
            )
            perms_cache[code] = perm
            s = "  ✓ créée      " if created else "  → mise à jour"
            self.stdout.write(f"{s} [{module}] {code}")

        self.stdout.write("\n── Création des rôles ────────────────────────")
        for role_code, role_label in Role.ROLE_CHOICES:
            role, created = Role.objects.get_or_create(nom_role=role_code)
            s = "  ✓ créé      " if created else "  → existant  "

            codes = ROLE_PERMS.get(role_code, [])
            for code in codes:
                if code in perms_cache:
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=perms_cache[code]
                    )

            self.stdout.write(f"{s} {role_label} ({len(codes)} permissions)")

        self.stdout.write(self.style.SUCCESS(
            "\n✅ Rôles et permissions initialisés avec succès !\n"
        ))