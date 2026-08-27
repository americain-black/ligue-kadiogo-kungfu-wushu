from apps.accounts.models import Role
from apps.clubs.models import Club


def role_et_espace_contexte(request):
    """
    Context processor global qui détermine l'espace/rôle actif de l'utilisateur
    et la liste des espaces disponibles auxquels il a droit.
    """
    user = request.user
    if not user.is_authenticated:
        return {
            'espaces_disponibles': [],
            'role_actif': None,
            'espace_actif_info': None,
        }

    roles_obj = list(user.roles.all())
    noms_roles = {r.nom_role for r in roles_obj}

    # Est-ce que le compte a la qualité de Super Admin ?
    est_admin_systeme = user.is_superuser or Role.SUPER_ADMIN in noms_roles

    espaces_disponibles = []

    # 1. Super Admin
    if est_admin_systeme:
        espaces_disponibles.append({
            'code': Role.SUPER_ADMIN,
            'nom': 'Super Administration',
            'libelle': 'Espace réservé au Super Administrateur',
            'icone': 'bi-gear-fill',
            'badge_bg': 'bg-dark',
            'url_dashboard': 'accounts:dashboard_super_admin',
        })

    # 2. Gestionnaire Ligue (Administrateur Principal / SG)
    if Role.GEST_LIGUE in noms_roles or user.est_gest_ligue():
        espaces_disponibles.append({
            'code': Role.GEST_LIGUE,
            'nom': 'Gestion Ligue',
            'libelle': 'Espace dédié au Gestionnaire de la Ligue',
            'icone': 'bi-building',
            'badge_bg': 'bg-danger',
            'url_dashboard': 'accounts:dashboard_ligue',
        })

    # 3. Responsable Technique
    if Role.GEST_TECHNIQUE in noms_roles:
        espaces_disponibles.append({
            'code': Role.GEST_TECHNIQUE,
            'nom': 'Direction Technique',
            'libelle': 'Espace dédié à la Direction Technique',
            'icone': 'bi-award-fill',
            'badge_bg': 'bg-primary',
            'url_dashboard': 'accounts:dashboard_ligue',
        })

    # 4. Gestionnaire Financier
    if Role.GEST_FINANCIER in noms_roles:
        espaces_disponibles.append({
            'code': Role.GEST_FINANCIER,
            'nom': 'Gestion Financière',
            'libelle': 'Espace dédié au Gestionnaire Financier',
            'icone': 'bi-coin',
            'badge_bg': 'bg-success',
            'url_dashboard': 'accounts:dashboard_financier',
        })

    # 5. Chargé de Communication
    if Role.GEST_COM in noms_roles:
        espaces_disponibles.append({
            'code': Role.GEST_COM,
            'nom': 'Communication',
            'libelle': 'Espace dédié au Chargé de Communication',
            'icone': 'bi-megaphone-fill',
            'badge_bg': 'bg-info text-dark',
            'url_dashboard': 'communication:liste_actualites',
        })

    # 6. Gestionnaire Club
    if Role.GEST_CLUB in noms_roles or user.est_gest_club():
        club = getattr(user, 'club', None)
        nom_club_str = f" — {club.nom_club}" if club else " (Aucun club)"
        espaces_disponibles.append({
            'code': Role.GEST_CLUB,
            'nom': f"Gestion Club{nom_club_str}",
            'libelle': f"Espace dédié au Club{nom_club_str}",
            'icone': 'bi-people-fill',
            'badge_bg': 'bg-secondary',
            'url_dashboard': 'accounts:dashboard_club',
            'club_obj': club,
        })

    # 7. Jury
    if Role.JURY in noms_roles or user.est_jury():
        espaces_disponibles.append({
            'code': Role.JURY,
            'nom': 'Membre du Jury',
            'libelle': 'Espace dédié au Membre du Jury',
            'icone': 'bi-pencil-square',
            'badge_bg': 'bg-warning text-dark',
            'url_dashboard': 'accounts:dashboard_jury',
        })

    # Si aucun rôle spécifique n'est défini mais authentifié
    if not espaces_disponibles:
        espaces_disponibles.append({
            'code': 'PRATIQUANT',
            'nom': 'Pratiquant / Licencié',
            'libelle': 'Espace dédié au Pratiquant / Licencié',
            'icone': 'bi-person-circle',
            'badge_bg': 'bg-light text-dark',
            'url_dashboard': 'accounts:tableau_de_bord',
        })

    codes_valides = [e['code'] for e in espaces_disponibles]

    # Récupérer le rôle actif depuis la session
    role_actif = request.session.get('role_actif')

    # Si pas en session ou si le rôle n'est plus possédé par l'utilisateur, prendre le premier par défaut
    if not role_actif or role_actif not in codes_valides:
        role_actif = codes_valides[0]
        request.session['role_actif'] = role_actif

    # Récupérer les détails de l'espace actif
    espace_actif_info = next((e for e in espaces_disponibles if e['code'] == role_actif), espaces_disponibles[0])

    return {
        'espaces_disponibles': espaces_disponibles,
        'role_actif': role_actif,
        'espace_actif_info': espace_actif_info,
    }
