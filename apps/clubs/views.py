# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.contrib import messages
# pyrefly: ignore [missing-import]
from django.db.models import Q, Count
from .models import (
    Club, DemandeAffiliation, PieceJustificativeAffiliation, ParametresAffiliation,
    VoletOrganigrammeClub, MembreOrganigrammeClub,
)
from .forms import (
    ClubForm, RejetDemandeForm, ParametresAffiliationForm, ModeleAttestationForm, PieceJustificativeAffiliationForm,
    VoletOrganigrammeClubForm, MembreOrganigrammeClubForm,
)


def gest_club_requis(view_func):
    """Réservé au GEST_CLUB uniquement (pas GEST_LIGUE) pour les actions d'écriture."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_club()):
            messages.error(request, "Accès réservé au Gestionnaire de Club.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


def gest_ligue_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_ligue()):
            messages.error(request, "Accès réservé au Gestionnaire de Ligue.")
            return redirect('accounts:tableau_de_bord')
        if not request.user.ligue and not request.user.is_superuser:
            messages.error(request, "Votre compte n'est rattaché à aucune ligue.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


@gest_ligue_requis
def liste_clubs(request):
    clubs = Club.objects.filter(ligue=request.user.ligue).order_by('nom_club')
    statut_filtre = request.GET.get('statut', '')
    if statut_filtre:
        clubs = clubs.filter(statut_club=statut_filtre)
    return render(request, 'clubs/liste.html', {
        'clubs':         clubs,
        'statut_filtre': statut_filtre,
        'statuts':       Club.STATUT_CHOICES,
    })


@gest_ligue_requis
def exporter_clubs(request):
    """
    Exporte la liste des clubs de la ligue au format CSV (compatible Excel).
    """
    import csv
    from django.http import HttpResponse

    clubs = Club.objects.filter(ligue=request.user.ligue).order_by('nom_club')
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="clubs_ligue_kadiogo.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Nom du Club', 'Sigle', 'Code Club', 'Maître / Fondateur',
        'Localité', 'Adresse', 'Téléphone', 'Email',
        'Latitude', 'Longitude', 'Statut'
    ])

    for c in clubs:
        writer.writerow([
            c.nom_club,
            c.sigle_club or '',
            c.code_club or '',
            c.nom_fondateur or '',
            c.localite or '',
            c.adresse or '',
            c.telephone or '',
            c.email or '',
            c.latitude if c.latitude is not None else '',
            c.longitude if c.longitude is not None else '',
            c.get_statut_club_display(),
        ])

    return response


@gest_ligue_requis
def importer_clubs(request):
    """
    Importe des clubs à partir d'un fichier CSV / Excel.
    """
    import csv

    if request.method == 'POST' and request.FILES.get('fichier'):
        fichier = request.FILES['fichier']
        try:
            lignes = fichier.read().decode('utf-8-sig', errors='ignore').splitlines()
            if not lignes:
                messages.error(request, "Le fichier est vide.")
                return redirect('clubs:liste')

            reader = csv.reader(lignes, delimiter=';')
            headers = [h.strip().lower() for h in next(reader, [])]

            if len(headers) <= 1 and ',' in lignes[0]:
                reader = csv.reader(lignes, delimiter=',')
                headers = [h.strip().lower() for h in next(reader, [])]

            import_count = 0
            for row in reader:
                if not row or not any(row):
                    continue
                d = dict(zip(headers, [v.strip() for v in row]))

                nom_club = d.get('nom du club') or d.get('nom_club') or d.get('nom')
                if not nom_club:
                    continue

                sigle = d.get('sigle') or d.get('sigle_club') or ''
                code = d.get('code club') or d.get('code_club') or ''
                fondateur = d.get('maître / fondateur') or d.get('fondateur') or d.get('maître') or d.get('nom_fondateur') or ''
                localite = d.get('localité') or d.get('localite') or 'Ouagadougou'
                adresse = d.get('adresse') or ''
                telephone = d.get('téléphone') or d.get('telephone') or ''
                email = d.get('email') or ''

                lat_val = d.get('latitude') or None
                lng_val = d.get('longitude') or None
                try:
                    latitude = float(lat_val) if lat_val else None
                except ValueError:
                    latitude = None
                try:
                    longitude = float(lng_val) if lng_val else None
                except ValueError:
                    longitude = None

                club, created = Club.objects.get_or_create(
                    ligue=request.user.ligue,
                    nom_club=nom_club,
                    defaults={
                        'sigle_club': sigle,
                        'code_club': code if code else None,
                        'nom_fondateur': fondateur,
                        'localite': localite,
                        'adresse': adresse,
                        'telephone': telephone,
                        'email': email,
                        'latitude': latitude,
                        'longitude': longitude,
                        'statut_club': 'AFFILIE',
                    }
                )
                if not created:
                    if sigle: club.sigle_club = sigle
                    if fondateur: club.nom_fondateur = fondateur
                    if localite: club.localite = localite
                    if adresse: club.adresse = adresse
                    if telephone: club.telephone = telephone
                    if email: club.email = email
                    if latitude is not None: club.latitude = latitude
                    if longitude is not None: club.longitude = longitude
                    club.save()
                import_count += 1

            messages.success(request, f"{import_count} club(s) importé(s) / mis à jour avec succès.")
        except Exception as exc:
            messages.error(request, f"Erreur lors de l'importation du fichier : {exc}")

    return redirect('clubs:liste')


@gest_ligue_requis
def telecharger_modele_clubs(request):
    """
    Télécharge un modèle de fichier CSV pour l'import de clubs.
    """
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="modele_import_clubs.csv"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Nom du Club', 'Sigle', 'Code Club', 'Maître / Fondateur',
        'Localité', 'Adresse', 'Téléphone', 'Email',
        'Latitude', 'Longitude'
    ])
    writer.writerow([
        'Dragon Rouge Wushu', 'DRW', 'CL01', 'Maître Ouedraogo',
        'Ouagadougou, Secteur 15', 'Rue 14.25', '+226 70 12 34 56', 'contact@dragonrouge.bf',
        '12.3714', '-1.5197'
    ])
    return response


@gest_ligue_requis
def creer_club(request):
    if request.method == 'POST':
        form = ClubForm(request.POST, request.FILES, ligue=request.user.ligue)
        if form.is_valid():
            club = form.save(commit=False)
            club.ligue = request.user.ligue
            club.save()
            messages.success(request, f"Club « {club.nom_club} » créé avec succès.")
            return redirect('clubs:liste')
    else:
        form = ClubForm(ligue=request.user.ligue)
    return render(request, 'clubs/form.html', {
        'form':  form,
        'titre': 'Enregistrer un club',
    })


@login_required
def modifier_club(request, pk):
    user = request.user
    if user.is_superuser or user.est_gest_ligue():
        club = get_object_or_404(Club, pk=pk, ligue=user.ligue)
    elif user.est_gest_club() and hasattr(user, 'club') and user.club and user.club.pk == pk:
        club = user.club
    else:
        messages.error(request, "Vous n'avez pas l'autorisation de modifier ce club.")
        return redirect('accounts:tableau_de_bord')

    ligue_context = user.ligue if hasattr(user, 'ligue') and user.ligue else (club.ligue if club else None)

    if request.method == 'POST':
        form = ClubForm(request.POST, request.FILES, instance=club, ligue=ligue_context)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le club « {club.nom_club} » a été mis à jour avec succès.")
            if user.est_gest_club():
                return redirect('clubs:mon_affiliation')
            return redirect('clubs:detail', pk=club.pk)
    else:
        form = ClubForm(instance=club, ligue=ligue_context)
    return render(request, 'clubs/form.html', {
        'form':  form,
        'titre': f'Modifier — {club.nom_club}',
        'club':  club,
    })


@gest_ligue_requis
def detail_club(request, pk):
    club = get_object_or_404(Club, pk=pk, ligue=request.user.ligue)
    demandes    = club.demandes_affiliation.select_related('annee_sportive').order_by('-date_demande')
    return render(request, 'clubs/detail.html', {
        'club':           club,
        'nb_pratiquants': club.pratiquants.count(),
        'nb_actifs':      club.pratiquants.filter(actif=True).count(),
        'nb_inactifs':    club.pratiquants.filter(actif=False).count(),
        'demandes':       demandes,
    })


@gest_ligue_requis
def toggle_statut_club(request, pk):
    club = get_object_or_404(Club, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        if club.statut_club == 'AFFILIE':
            club.statut_club = 'SUSPENDU'
            messages.warning(request, f"Club « {club.nom_club} » suspendu.")
        elif club.statut_club == 'SUSPENDU':
            club.statut_club = 'AFFILIE'
            messages.success(request, f"Club « {club.nom_club} » réactivé (affilié).")
        else:
            messages.error(request, "Action non autorisée pour ce statut.")
        club.save()
    return redirect('clubs:liste')


@gest_ligue_requis
def supprimer_club(request, pk):
    club = get_object_or_404(Club, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        if club.pratiquants.exists():
            messages.error(request, f"Impossible de supprimer « {club.nom_club} » : il contient des licenciés.")
            return redirect('clubs:detail', pk=pk)
        nom = club.nom_club
        club.delete()
        messages.success(request, f"Club « {nom} » supprimé.")
        return redirect('clubs:liste')
    return render(request, 'clubs/confirmer_suppression.html', {'club': club})


@gest_ligue_requis
def demandes_affiliation(request):
    from apps.exams.models import AnneeSportive
    from django.db.models import Q

    ligue = request.user.ligue
    statut_filtre = request.GET.get('statut', '')
    annee_id = request.GET.get('annee', '')
    q = request.GET.get('q', '').strip()

    qs = DemandeAffiliation.objects.filter(club__ligue=ligue).select_related('club', 'annee_sportive', 'approuve_par')

    if statut_filtre and statut_filtre != 'TOUS':
        qs = qs.filter(statut_affiliation=statut_filtre)
    
    if annee_id:
        qs = qs.filter(annee_sportive_id=annee_id)

    if q:
        qs = qs.filter(
            Q(club__nom_club__icontains=q) |
            Q(club__sigle_club__icontains=q) |
            Q(club__code_club__icontains=q)
        )

    demandes = qs.order_by('-date_demande')
    annees = AnneeSportive.objects.all().order_by('-date_debut')

    nb_en_attente_ligue = DemandeAffiliation.objects.filter(club__ligue=ligue, statut_affiliation='EN_ATTENTE_VALID_LIGUE').count()
    nb_en_attente_paiement = DemandeAffiliation.objects.filter(club__ligue=ligue, statut_affiliation='EN_ATTENTE_PAIEMENT').count()
    nb_en_attente_financier = DemandeAffiliation.objects.filter(club__ligue=ligue, statut_affiliation='EN_ATTENTE_VALID_FINANCIER').count()
    nb_approuvees = DemandeAffiliation.objects.filter(club__ligue=ligue, statut_affiliation='APPROUVEE').count()
    nb_rejetees = DemandeAffiliation.objects.filter(club__ligue=ligue, statut_affiliation='REJETEE').count()
    nb_total = DemandeAffiliation.objects.filter(club__ligue=ligue).count()

    return render(request, 'clubs/demandes_affiliation.html', {
        'demandes': demandes,
        'annees': annees,
        'statut_filtre': statut_filtre,
        'annee_id': annee_id,
        'q': q,
        'nb_en_attente_ligue': nb_en_attente_ligue,
        'nb_en_attente_paiement': nb_en_attente_paiement,
        'nb_en_attente_financier': nb_en_attente_financier,
        'nb_approuvees': nb_approuvees,
        'nb_rejetees': nb_rejetees,
        'nb_total': nb_total,
    })


@gest_ligue_requis
def historique_affiliations_ligue(request):
    """
    Vue d'archivage et historique complet de toutes les affiliations passées et présentes de la Ligue.
    """
    from apps.exams.models import AnneeSportive
    from django.db.models import Q

    ligue = request.user.ligue
    statut_filtre = request.GET.get('statut', '')
    annee_id = request.GET.get('annee', '')
    q = request.GET.get('q', '').strip()

    qs = DemandeAffiliation.objects.filter(club__ligue=ligue).select_related('club', 'annee_sportive', 'approuve_par')

    if statut_filtre:
        qs = qs.filter(statut_affiliation=statut_filtre)
    if annee_id:
        qs = qs.filter(annee_sportive_id=annee_id)
    if q:
        qs = qs.filter(
            Q(club__nom_club__icontains=q) |
            Q(club__sigle_club__icontains=q) |
            Q(club__code_club__icontains=q)
        )

    demandes = qs.order_by('-date_demande')
    annees = AnneeSportive.objects.all().order_by('-date_debut')

    nb_total = DemandeAffiliation.objects.filter(club__ligue=ligue).count()
    nb_approuvees = DemandeAffiliation.objects.filter(club__ligue=ligue, statut_affiliation='APPROUVEE').count()
    nb_rejetees = DemandeAffiliation.objects.filter(club__ligue=ligue, statut_affiliation='REJETEE').count()
    nb_en_cours = nb_total - nb_approuvees - nb_rejetees

    return render(request, 'clubs/historique_affiliations.html', {
        'demandes': demandes,
        'annees': annees,
        'statut_filtre': statut_filtre,
        'annee_id': annee_id,
        'q': q,
        'nb_total': nb_total,
        'nb_approuvees': nb_approuvees,
        'nb_rejetees': nb_rejetees,
        'nb_en_cours': nb_en_cours,
    })


@gest_ligue_requis
def detail_demande_affiliation(request, pk):
    demande = get_object_or_404(
        DemandeAffiliation, pk=pk,
        club__ligue=request.user.ligue,
    )
    pieces   = demande.pieces_justificatives.order_by('type_piece')
    paiement = getattr(demande, 'paiement', None)
    return render(request, 'clubs/detail_demande_affiliation.html', {
        'demande':  demande,
        'club':     demande.club,
        'pieces':   pieces,
        'paiement': paiement,
    })


@gest_ligue_requis
def valider_demande(request, pk):
    demande = get_object_or_404(
        DemandeAffiliation, pk=pk,
        club__ligue=request.user.ligue,
        statut_affiliation='EN_ATTENTE_VALID_LIGUE'
    )
    if request.method == 'POST':
        demande.approuver(utilisateur=request.user)
        messages.success(request, f"Affiliation de « {demande.club.nom_club} » approuvée avec succès pour la saison {demande.annee_sportive.libelle}.")
        return redirect('clubs:demandes_affiliation')
    return render(request, 'clubs/confirmer_validation.html', {'demande': demande})


@gest_ligue_requis
def rejeter_demande(request, pk):
    demande = get_object_or_404(
        DemandeAffiliation, pk=pk,
        club__ligue=request.user.ligue,
        statut_affiliation='EN_ATTENTE_VALID_LIGUE'
    )
    if request.method == 'POST':
        form = RejetDemandeForm(request.POST)
        if form.is_valid():
            demande.rejeter_par_ligue(motif=form.cleaned_data['motif'])
            messages.warning(request, f"Demande de « {demande.club.nom_club} » rejetée.")
            return redirect('clubs:demandes_affiliation')
    else:
        form = RejetDemandeForm()
    return render(request, 'clubs/rejeter_demande.html', {
        'form':    form,
        'demande': demande,
    })


def attestation_affiliation(request, pk):
    """
    Vue imprimable / téléchargeable d'Attestation Officielle d'Affiliation.
    Accessible aux gestionnaires de ligue et au gestionnaire du club concerné.
    """
    demande = get_object_or_404(DemandeAffiliation, pk=pk, statut_affiliation='APPROUVEE')
    user = request.user
    
    if not user.is_authenticated:
        return redirect('accounts:login')

    est_autorise = False
    if user.est_gest_ligue and user.ligue == demande.club.ligue:
        est_autorise = True
    elif user.est_gest_club and hasattr(user, 'club') and user.club == demande.club:
        est_autorise = True
    elif user.is_superuser:
        est_autorise = True

    if not est_autorise:
        messages.error(request, "Vous n'avez pas l'autorisation de consulter cette attestation.")
        return redirect('accounts:accueil')

    ligue = demande.club.ligue
    params = getattr(ligue, 'parametres_affiliation', None)
    return render(request, 'clubs/attestation_affiliation.html', {
        'demande': demande,
        'club':    demande.club,
        'ligue':   ligue,
        'annee':   demande.annee_sportive,
        'params':  params,
    })


@gest_club_requis
def historique_affiliations_club(request):
    """
    Vue d'historique de toutes les demandes d'affiliation passées et présentes du Club.
    """
    club = request.user.club
    demandes = DemandeAffiliation.objects.filter(club=club).select_related('annee_sportive', 'approuve_par').order_by('-date_demande')
    
    return render(request, 'clubs/mes_demandes_affiliation.html', {
        'club': club,
        'demandes': demandes,
    })


@gest_ligue_requis
def gerer_parametres_affiliation(request):
    ligue  = request.user.ligue
    params = ParametresAffiliation.objects.filter(ligue=ligue).first()

    if request.method == 'POST':
        form = ParametresAffiliationForm(request.POST, instance=params)
        if form.is_valid():
            p = form.save(commit=False)
            p.ligue = ligue
            p.save()
            messages.success(
                request,
                f"Montant des frais d'affiliation enregistré : {p.montant_frais_affiliation:,.0f} FCFA."
            )
            return redirect('clubs:parametres_affiliation')
    else:
        form = ParametresAffiliationForm(instance=params)

    return render(request, 'clubs/parametres_affiliation.html', {
        'params': params,
        'form':   form,
    })


@gest_ligue_requis
def gerer_modele_attestation(request):
    ligue = request.user.ligue
    params, _ = ParametresAffiliation.objects.get_or_create(ligue=ligue)

    if request.method == 'POST':
        form = ModeleAttestationForm(request.POST, instance=params)
        if form.is_valid():
            form.save()
            messages.success(request, "Le modèle d'attestation officielle a été enregistré avec succès.")
            return redirect('clubs:modele_attestation')
    else:
        form = ModeleAttestationForm(instance=params)

    return render(request, 'clubs/modele_attestation.html', {
        'params': params,
        'form':   form,
    })


# ─── Organigramme Club ────────────────────────────────────────────────────────

def gest_club_requis(view_func):
    """Réservé au GEST_CLUB uniquement (pas GEST_LIGUE) pour les actions d'écriture."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_club()):
            messages.error(request, "Accès réservé au Gestionnaire de Club.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Affiliation — côté Gestionnaire de Club ─────────────────────────────────

def _annee_active_club(club):
    from apps.exams.models import AnneeSportive
    if not club.ligue:
        return None
    return AnneeSportive.objects.filter(ligue=club.ligue, statut='ACTIVE').first()


@gest_club_requis
def mon_affiliation(request):
    club  = request.user.club
    annee = _annee_active_club(club)

    demande = None
    pieces  = []
    paiement = None
    if annee:
        demande = DemandeAffiliation.objects.filter(club=club, annee_sportive=annee).first()
        if demande:
            pieces   = demande.pieces_justificatives.order_by('-date_upload')
            paiement = getattr(demande, 'paiement', None)

    params = ParametresAffiliation.objects.filter(ligue=club.ligue).first() if club.ligue else None

    return render(request, 'clubs/mon_affiliation.html', {
        'club':          club,
        'annee':         annee,
        'demande':       demande,
        'pieces':        pieces,
        'paiement':      paiement,
        'params':        params,
        'piece_form':    PieceJustificativeAffiliationForm(),
    })


@gest_club_requis
def enregistrer_recepisse_club(request):
    club = request.user.club
    if request.method == 'POST':
        numero = request.POST.get('numero_recepisse', '').strip()
        date_delivrance = request.POST.get('date_delivrance_recepisse', '').strip()
        loi = request.POST.get('loi_reglementation', '').strip() or 'Loi N° 064-2015/CNT'
        date_expiration = request.POST.get('date_expiration_recepisse', '').strip()

        club.numero_recepisse = numero
        club.loi_reglementation = loi

        if date_delivrance:
            from django.utils.dateparse import parse_date
            club.date_delivrance_recepisse = parse_date(date_delivrance)
        else:
            club.date_delivrance_recepisse = None

        if date_expiration:
            from django.utils.dateparse import parse_date
            club.date_expiration_recepisse = parse_date(date_expiration)
        else:
            club.date_expiration_recepisse = None

        club.save()
        messages.success(request, "Les informations du récépissé d'existence ont été mises à jour.")

    return redirect('clubs:mon_affiliation')


@gest_club_requis
def demarrer_demande_affiliation(request):
    club  = request.user.club
    annee = _annee_active_club(club)

    if not annee:
        messages.error(request, "Aucune année sportive active pour votre ligue.")
        return redirect('clubs:mon_affiliation')

    params = ParametresAffiliation.objects.filter(ligue=club.ligue).first()
    if not params:
        messages.error(request, "Le montant des frais d'affiliation n'a pas encore été défini par la ligue. Contactez-la.")
        return redirect('clubs:mon_affiliation')

    if request.method == 'POST':
        # 1. Enregistrement automatique des détails du récépissé saisis dans le formulaire unique
        numero = request.POST.get('numero_recepisse', '').strip()
        date_delivrance = request.POST.get('date_delivrance_recepisse', '').strip()
        loi = request.POST.get('loi_reglementation', '').strip() or 'Loi N° 064-2015/CNT'

        if numero:
            club.numero_recepisse = numero
        if loi:
            club.loi_reglementation = loi
        if date_delivrance:
            from django.utils.dateparse import parse_date
            club.date_delivrance_recepisse = parse_date(date_delivrance)
        club.save()

        # 2. Contrôle d'exigence du récépissé (si configuré par la ligue)
        if params.exiger_recepisse_valide:
            if not club.numero_recepisse or not club.date_delivrance_recepisse:
                messages.error(
                    request,
                    "La ligue exige la saisie obligatoire du récépissé d'existence (numéro et date de délivrance)."
                )
                return redirect('clubs:mon_affiliation')

        # 3. Contrôle d'expiration du récépissé
        if not club.recepisse_est_valide():
            messages.error(
                request,
                "Votre récépissé d'existence officiel est expiré. Veuillez fournir la date de votre nouveau récépissé renouvelé."
            )
            return redirect('clubs:mon_affiliation')

        demande, _created = DemandeAffiliation.objects.get_or_create(
            club=club, annee_sportive=annee,
            defaults={'montant_frais': params.montant_frais_affiliation},
        )
        demande.montant_frais = params.montant_frais_affiliation
        demande.save()
        try:
            demande.soumettre()
            messages.success(
                request,
                "Demande d'affiliation enregistrée et démarrée avec succès. Vous pouvez à présent joindre vos pièces justificatives et procéder au paiement."
            )
        except Exception as exc:
            messages.error(request, str(exc))
    return redirect('clubs:mon_affiliation')


@gest_club_requis
def ajouter_piece_affiliation(request):
    club  = request.user.club
    annee = _annee_active_club(club)
    demande = get_object_or_404(DemandeAffiliation, club=club, annee_sportive=annee) if annee else None

    if not demande or demande.statut_affiliation != 'EN_ATTENTE_PAIEMENT':
        messages.error(request, "Vous ne pouvez pas ajouter de pièce dans l'état actuel de la demande.")
        return redirect('clubs:mon_affiliation')

    if request.method == 'POST':
        form = PieceJustificativeAffiliationForm(request.POST, request.FILES)
        if form.is_valid():
            piece = form.save(commit=False)
            piece.demande = demande
            piece.save()
            messages.success(request, f"« {piece.get_type_piece_display()} » ajouté.")
        else:
            messages.error(request, "Impossible d'ajouter ce fichier : vérifiez le formulaire.")
    return redirect('clubs:mon_affiliation')


@gest_club_requis
def supprimer_piece_affiliation(request, pk):
    piece = get_object_or_404(
        PieceJustificativeAffiliation, pk=pk, demande__club=request.user.club
    )
    if piece.demande.statut_affiliation != 'EN_ATTENTE_PAIEMENT':
        messages.error(request, "Vous ne pouvez pas supprimer cette pièce dans l'état actuel de la demande.")
        return redirect('clubs:mon_affiliation')
    if request.method == 'POST':
        piece.delete()
        messages.success(request, "Pièce supprimée.")
    return redirect('clubs:mon_affiliation')


def organigramme_club_acces(view_func):
    """GEST_LIGUE peut voir, GEST_CLUB peut modifier."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_ligue() or request.user.est_gest_club()):
            messages.error(request, "Accès non autorisé.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


@organigramme_club_acces
def organigramme_club(request, club_pk):
    club   = get_object_or_404(Club, pk=club_pk, ligue=request.user.ligue)
    from apps.ligues.models import VoletOrganigramme, MembreOrganigramme
    from apps.ligues.forms import MembreOrganigrammeForm
    volets = VoletOrganigramme.objects.filter(ligue=club.ligue).prefetch_related('membres').all()
    for v in volets:
        v.membres_du_club = v.membres.filter(club=club)
    peut_modifier = request.user.is_superuser or request.user.est_gest_club()
    form_membre = MembreOrganigrammeForm()
    return render(request, 'clubs/organigramme.html', {
        'club':          club,
        'volets':        volets,
        'peut_modifier': peut_modifier,
        'form_membre':   form_membre,
    })


@gest_club_requis
def ajouter_membre_club(request, volet_pk):
    from apps.ligues.models import VoletOrganigramme, MembreOrganigramme
    from apps.ligues.forms import MembreOrganigrammeForm
    club_id = request.POST.get('club_id') or request.GET.get('club_id')
    if club_id:
        club = get_object_or_404(Club, pk=club_id)
    else:
        club = getattr(request.user, 'club', None)

    if not club:
        messages.error(request, "Impossible de déterminer le club concerné.")
        return redirect('accounts:tableau_de_bord')

    volet = get_object_or_404(VoletOrganigramme, pk=volet_pk, ligue=club.ligue)
    if request.method == 'POST':
        form = MembreOrganigrammeForm(request.POST)
        if form.is_valid():
            membre = form.save(commit=False)
            membre.volet = volet
            membre.club  = club
            membre.save()
            messages.success(request, f"{membre.prenom} {membre.nom} ajouté au volet « {volet.nom_volet} ».")
    return redirect('clubs:organigramme', club_pk=club.pk)


@gest_club_requis
def modifier_membre_club(request, pk):
    from apps.ligues.models import MembreOrganigramme
    from apps.ligues.forms import MembreOrganigrammeForm
    user_club = getattr(request.user, 'club', None)
    if request.user.is_superuser:
        membre = get_object_or_404(MembreOrganigramme, pk=pk)
    else:
        membre = get_object_or_404(MembreOrganigramme, pk=pk, club=user_club)
    club = membre.club or user_club
    if request.method == 'POST':
        form = MembreOrganigrammeForm(request.POST, instance=membre)
        if form.is_valid():
            form.save()
            messages.success(request, "Membre modifié.")
    return redirect('clubs:organigramme', club_pk=club.pk if club else 1)


@gest_club_requis
def toggle_actif_membre_club(request, pk):
    from apps.ligues.models import MembreOrganigramme
    user_club = getattr(request.user, 'club', None)
    if request.user.is_superuser:
        membre = get_object_or_404(MembreOrganigramme, pk=pk)
    else:
        membre = get_object_or_404(MembreOrganigramme, pk=pk, club=user_club)
    club = membre.club or user_club
    membre.actif = not membre.actif
    membre.save()
    etat = "activé" if membre.actif else "désactivé"
    messages.success(request, f"{membre.prenom} {membre.nom} {etat}.")
    return redirect('clubs:organigramme', club_pk=club.pk if club else 1)


@gest_club_requis
def supprimer_membre_club(request, pk):
    from apps.ligues.models import MembreOrganigramme
    user_club = getattr(request.user, 'club', None)
    if request.user.is_superuser:
        membre = get_object_or_404(MembreOrganigramme, pk=pk)
    else:
        membre = get_object_or_404(MembreOrganigramme, pk=pk, club=user_club)
    club = membre.club or user_club
    if request.method == 'POST':
        nom = f"{membre.prenom} {membre.nom}"
        membre.delete()
        messages.success(request, f"{nom} supprimé de l'organigramme.")
    return redirect('clubs:organigramme', club_pk=club.pk if club else 1)


def annuaire_clubs(request):
    """
    Annuaire public des clubs (accessible à tous les visiteurs).
    Affiche tous les clubs à l'exclusion de ceux ayant le statut SUSPENDU.
    Permet la recherche par nom, sigle ou localité.
    """
    query = request.GET.get('q', '').strip()
    clubs_qs = Club.objects.exclude(statut_club='SUSPENDU').select_related('ligue')

    if query:
        clubs_qs = clubs_qs.filter(
            Q(nom_club__icontains=query) |
            Q(sigle_club__icontains=query) |
            Q(localite__icontains=query)
        )

    if request.method == 'POST' and 'envoyer_message' in request.POST:
        club_id = request.POST.get('club_id')
        nom_expediteur = request.POST.get('nom_expediteur', '').strip()
        email_expediteur = request.POST.get('email_expediteur', '').strip()
        telephone_expediteur = request.POST.get('telephone_expediteur', '').strip()
        message_contenu = request.POST.get('message', '').strip()

        club_cible = Club.objects.filter(pk=club_id).exclude(statut_club='SUSPENDU').first()
        if club_cible and nom_expediteur and (email_expediteur or telephone_expediteur) and message_contenu:
            from config.emails import envoyer_email_notification

            sujet = f"Message de {nom_expediteur} pour {club_cible.nom_club}"
            titre = f"Nouveau message pour {club_cible.nom_club}"
            contenu_msg = (
                f"Bonjour,<br><br>"
                f"Un nouveau message a été envoyé depuis l'annuaire public des clubs pour <strong>{club_cible.nom_club}</strong> :<br><br>"
                f"• <strong>Nom de l'expéditeur :</strong> {nom_expediteur}<br>"
                f"• <strong>Email :</strong> {email_expediteur or 'Non renseigné'}<br>"
                f"• <strong>Téléphone :</strong> {telephone_expediteur or 'Non renseigné'}<br><br>"
                f"<strong>Contenu du message :</strong><br>"
                f"{message_contenu}"
            )

            destinataires = []
            if club_cible.email:
                destinataires.append(club_cible.email)
            # Toujours ajouter une copie à la Ligue (info@kadiogokungfu.teeritech.bf)
            destinataires.append('info@kadiogokungfu.teeritech.bf')

            if email_expediteur:
                # Envoyer un accusé de réception à l'expéditeur
                envoyer_email_notification(
                    destinataires=[email_expediteur],
                    sujet=f"Confirmation d'envoi à {club_cible.nom_club}",
                    titre_entete="Votre message a été transmis",
                    contenu_html_ou_texte=f"Bonjour {nom_expediteur},<br><br>Votre message destiné au club <strong>{club_cible.nom_club}</strong> a bien été transmis.",
                    motif_ou_details=message_contenu
                )

            envoyer_email_notification(
                destinataires=destinataires,
                sujet=sujet,
                titre_entete=titre,
                contenu_html_ou_texte=contenu_msg,
                reply_to=email_expediteur
            )

            messages.success(
                request,
                f"Votre message pour le club « {club_cible.nom_club} » a été transmis avec succès par email !"
            )
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires du formulaire de contact.")
        return redirect(f"{request.path}?q={query}")

    clubs = clubs_qs.annotate(nb_pratiquants=Count('pratiquants'))

    from apps.ligues.models import Ligue
    ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()

    context = {
        'clubs': clubs,
        'query': query,
        'nb_total_clubs': clubs.count(),
        'ligue': ligue,
    }
    return render(request, 'clubs/annuaire.html', context)


def organigramme_visuel_club(request, club_pk):
    """
    Vue graphique de l'organigramme d'un club (arbre visuel avec boîtes et connecteurs).
    """
    from apps.ligues.models import VoletOrganigramme
    club = get_object_or_404(Club, pk=club_pk)
    volets = VoletOrganigramme.objects.filter(club=club).prefetch_related('membres')
    for volet in volets:
        membres = list(volet.membres.filter(actif=True).order_by('ordre', 'nom'))
        niveaux_dict = {}
        for m in membres:
            niveaux_dict.setdefault(m.ordre, []).append(m)
        volet.niveaux_membres = [
            {'niveau': lvl, 'membres': sorted(m_list, key=lambda x: x.nom)}
            for lvl, m_list in sorted(niveaux_dict.items())
        ]

    return render(request, 'clubs/organigramme_visuel.html', {
        'club': club,
        'volets': volets,
    })

