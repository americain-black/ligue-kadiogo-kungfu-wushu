# pyrefly: ignore [missing-import]
from django import forms as django_forms
# pyrefly: ignore [missing-import]
from django.db.models import Q
# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.contrib import messages
# pyrefly: ignore [missing-import]
from django.db.models.deletion import ProtectedError
from .models import Pratiquant, Grade
from .forms import PratiquantForm


def gest_club_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_club()):
            messages.error(request, "Accès réservé au Gestionnaire de Club.")
            return redirect('accounts:tableau_de_bord')
        if not hasattr(request.user, 'club') and not request.user.is_superuser:
            messages.error(request, "Votre compte n'est rattaché à aucun club.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


def gest_ligue_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_ligue()):
            messages.error(request, "Accès réservé au Gestionnaire de Ligue.")
            return redirect('accounts:tableau_de_bord')
        if not getattr(request.user, 'ligue', None) and not request.user.is_superuser:
            messages.error(request, "Votre compte n'est rattaché à aucune ligue.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper



@login_required
def liste_pratiquants(request):
    if hasattr(request.user, 'club') and request.user.club:
        club  = request.user.club
        ligue = club.ligue
        pratiquants = Pratiquant.objects.filter(club=club).select_related('grade_actuel', 'club')
    elif (request.user.is_superuser or request.user.est_gest_ligue()) and hasattr(request.user, 'ligue') and request.user.ligue:
        ligue = request.user.ligue
        club  = None
        pratiquants = Pratiquant.objects.filter(club__ligue=ligue).select_related('grade_actuel', 'club')
    elif request.user.is_superuser:
        from apps.ligues.models import Ligue
        ligue = Ligue.objects.first()
        club  = None
        pratiquants = Pratiquant.objects.all().select_related('grade_actuel', 'club')
    else:
        messages.error(request, "Accès refusé.")
        return redirect('accounts:tableau_de_bord')

    filtre_statut     = request.GET.get('statut', 'actif')
    filtre_grade      = request.GET.get('grade', '')
    filtre_sexe       = request.GET.get('sexe', '')
    filtre_club       = request.GET.get('club', '')
    filtre_recherche  = request.GET.get('q', '').strip()

    if filtre_statut == 'inactif':
        pratiquants = pratiquants.filter(actif=False)
    else:
        pratiquants = pratiquants.filter(actif=True)

    if filtre_grade == 'sans':
        pratiquants = pratiquants.filter(grade_actuel__isnull=True)
    elif filtre_grade:
        pratiquants = pratiquants.filter(grade_actuel__pk=filtre_grade)

    if filtre_club and (request.user.is_superuser or request.user.est_gest_ligue()):
        pratiquants = pratiquants.filter(club__pk=filtre_club)

    if filtre_sexe:
        pratiquants = pratiquants.filter(sexe=filtre_sexe)

    if filtre_recherche:
        pratiquants = pratiquants.filter(
            Q(nom__icontains=filtre_recherche) | Q(prenom__icontains=filtre_recherche)
        )

    pratiquants = pratiquants.order_by('grade_actuel__id_grade', 'nom', 'prenom')

    grades = Grade.objects.filter(ligue=ligue).order_by('id_grade') if ligue else Grade.objects.none()
    clubs  = ligue.clubs.all().order_by('nom_club') if ligue else []

    filtre_grade_nom = ''
    if filtre_grade == 'sans':
        filtre_grade_nom = 'Sans grade'
    elif filtre_grade:
        grade_obj = grades.filter(pk=filtre_grade).first()
        filtre_grade_nom = grade_obj.nom if grade_obj else ''

    return render(request, 'practitioners/liste.html', {
        'pratiquants':       pratiquants,
        'club':              club,
        'ligue':             ligue,
        'clubs':             clubs,
        'filtre':            filtre_statut,
        'filtre_grade':      filtre_grade,
        'filtre_grade_nom':  filtre_grade_nom,
        'filtre_club':       filtre_club,
        'filtre_sexe':       filtre_sexe,
        'filtre_recherche':  filtre_recherche,
        'grades':            grades,
    })


@gest_club_requis
def ajouter_pratiquant(request):
    club  = request.user.club
    ligue = club.ligue
    if request.method == 'POST':
        form = PratiquantForm(request.POST, request.FILES, ligue=ligue)
        if form.is_valid():
            pratiquant = form.save(commit=False)
            pratiquant.club = club
            pratiquant.save()
            messages.success(request, f"{pratiquant.prenom} {pratiquant.nom} inscrit avec succès.")
            return redirect('practitioners:liste')
    else:
        form = PratiquantForm(ligue=ligue)
    import json
    grades_qs = Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade')
    grades_json = json.dumps({str(g.pk): g.id_grade for g in grades_qs})
    return render(request, 'practitioners/form.html', {
        'form':        form,
        'titre':       'Inscrire un licencié',
        'club':        club,
        'grades':      grades_qs,
        'grades_json': grades_json,
    })


@gest_club_requis
def modifier_pratiquant(request, pk):
    club       = request.user.club
    ligue      = club.ligue
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    if request.method == 'POST':
        form = PratiquantForm(request.POST, request.FILES, instance=pratiquant, ligue=ligue)
        if form.is_valid():
            form.save()
            messages.success(request, f"{pratiquant.prenom} {pratiquant.nom} modifié.")
            return redirect('practitioners:liste')
    else:
        form = PratiquantForm(instance=pratiquant, ligue=ligue)
    import json
    grades_qs = Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade')
    grades_json = json.dumps({str(g.pk): g.id_grade for g in grades_qs})
    return render(request, 'practitioners/form.html', {
        'form':        form,
        'titre':       f'Modifier — {pratiquant.prenom} {pratiquant.nom}',
        'pratiquant':  pratiquant,
        'club':        club,
        'grades':      grades_qs,
        'grades_json': grades_json,
    })


@login_required
def detail_pratiquant(request, pk):
    user = request.user
    if user.is_superuser or user.est_gest_ligue():
        ligue = getattr(user, 'ligue', None)
        if not ligue and user.is_superuser:
            from apps.ligues.models import Ligue
            ligue = Ligue.objects.first()
        pratiquant = get_object_or_404(Pratiquant.objects.select_related('club', 'grade_actuel'), pk=pk, club__ligue=ligue)
    elif user.est_gest_club() and hasattr(user, 'club') and user.club:
        pratiquant = get_object_or_404(Pratiquant.objects.select_related('club', 'grade_actuel'), pk=pk, club=user.club)
    else:
        messages.error(request, "Accès refusé.")
        return redirect('accounts:tableau_de_bord')

    resultats = (
        pratiquant.inscriptions
        .filter(resultat__publie=True)
        .select_related('session', 'grade_vise', 'resultat')
        .order_by('-session__date_examen')
    )
    historiques = pratiquant.historique_passages.all()
    from .forms import HistoriquePassageGradeForm
    historique_form = HistoriquePassageGradeForm()

    return render(request, 'practitioners/detail.html', {
        'pratiquant': pratiquant,
        'club': pratiquant.club,
        'resultats': resultats,
        'historiques': historiques,
        'historique_form': historique_form,
    })


@gest_ligue_requis
def ajouter_historique_passage(request, pk):
    pratiquant = get_object_or_404(Pratiquant, pk=pk)
    if request.method == 'POST':
        from .forms import HistoriquePassageGradeForm
        form = HistoriquePassageGradeForm(request.POST)
        if form.is_valid():
            h = form.save(commit=False)
            h.pratiquant = pratiquant
            h.save()
            messages.success(request, f"Passage de grade « {h.grade_libelle} » ajouté à l'historique de {pratiquant.prenom} {pratiquant.nom}.")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire d'historique.")
    return redirect('practitioners:detail', pk=pratiquant.pk)


@gest_ligue_requis
def supprimer_historique_passage(request, pk):
    from .models import HistoriquePassageGrade
    h = get_object_or_404(HistoriquePassageGrade, pk=pk)
    pratiquant_pk = h.pratiquant_id
    if request.method == 'POST':
        h.delete()
        messages.success(request, "Entrée d'historique supprimée.")
    return redirect('practitioners:detail', pk=pratiquant_pk)



@gest_club_requis
def toggle_actif_pratiquant(request, pk):
    club       = request.user.club
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    if request.method == 'POST':
        pratiquant.actif = not pratiquant.actif
        pratiquant.save()
        etat = "activé" if pratiquant.actif else "désactivé"
        messages.success(request, f"{pratiquant.prenom} {pratiquant.nom} {etat}.")
    return redirect('practitioners:liste')


@gest_club_requis
def supprimer_pratiquant(request, pk):
    club       = request.user.club
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    inscriptions = pratiquant.inscriptions.select_related('session', 'grade_vise').order_by('-session__date_examen')
    has_valide   = inscriptions.filter(statut__in=['PAIEMENT_VALIDE', 'AUTORISE']).exists()

    if request.method == 'POST':
        nom_complet = f"{pratiquant.prenom} {pratiquant.nom}"
        pratiquant.delete()   # CASCADE supprime aussi les inscriptions
        messages.success(request, f"{nom_complet} supprimé définitivement du club.")
        return redirect('practitioners:liste')

    return render(request, 'practitioners/confirmer_supprimer.html', {
        'pratiquant':   pratiquant,
        'inscriptions': inscriptions,
        'has_valide':   has_valide,
        'club':         club,
    })


# ── Vues GEST_LIGUE — Gestion des grades ──────────────────────────────────────

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


class GradeForm(django_forms.ModelForm):
    class Meta:
        model  = Grade
        fields = ['nom', 'actif']
        widgets = {
            'nom':   django_forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex : BLANC, ROUGE, ROUGE I, ROUGE II…',
            }),
            'actif': django_forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom':   'Nom du grade',
            'actif': 'Grade actif',
        }


@gest_ligue_requis
def liste_grades(request):
    ligue  = request.user.ligue
    grades = Grade.objects.filter(ligue=ligue).order_by('id_grade')
    return render(request, 'practitioners/grades_liste.html', {
        'grades':      grades,
        'ligue':       ligue,
        'nb_actifs':   grades.filter(actif=True).count(),
        'nb_inactifs': grades.filter(actif=False).count(),
    })


@gest_ligue_requis
def creer_grade(request):
    # pyrefly: ignore [missing-import]
    from django.db.models import Max
    ligue  = request.user.ligue
    max_id = Grade.objects.filter(ligue=ligue).aggregate(m=Max('id_grade'))['m'] or 0
    prochain_id = max_id + 1
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.ligue    = ligue
            grade.id_grade = prochain_id  # toujours forcé côté serveur
            grade.save()
            messages.success(request, f"Grade « {grade.nom} » créé (ID {grade.id_grade}).")
            return redirect('practitioners:grades')
    else:
        form = GradeForm(initial={'id_grade': prochain_id})
    return render(request, 'practitioners/grade_form.html', {
        'form':        form,
        'titre':       'Créer un grade',
        'prochain_id': prochain_id,
    })


@gest_ligue_requis
def modifier_grade(request, pk):
    ligue = request.user.ligue
    grade = get_object_or_404(Grade, pk=pk, ligue=ligue)
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            g = form.save(commit=False)
            g.id_grade = grade.id_grade  # id_grade immuable
            g.save()
            messages.success(request, f"Grade « {grade.nom} » modifié.")
            return redirect('practitioners:grades')
    else:
        form = GradeForm(instance=grade)
    return render(request, 'practitioners/grade_form.html', {
        'form':  form,
        'titre': f'Modifier — {grade.nom}',
        'grade': grade,
    })


@gest_ligue_requis
def supprimer_grade(request, pk):
    ligue = request.user.ligue
    grade = get_object_or_404(Grade, pk=pk, ligue=ligue)

    # Inscriptions → PROTECT (bloquant)
    inscriptions    = grade.inscriptions.select_related('session', 'pratiquant').order_by('-session__date_examen')
    nb_inscriptions = inscriptions.count()
    # Pratiquants → SET_NULL (grade devient "Sans grade")
    pratiquants     = grade.pratiquants.select_related('club').order_by('nom', 'prenom')
    nb_pratiquants  = pratiquants.count()
    # Tarifs et rubriques → CASCADE (supprimés avec le grade)
    tarifs          = grade.tarifs.select_related('annee_sportive')
    nb_tarifs       = tarifs.count()
    rubriques       = grade.rubrique_grades.select_related('rubrique')
    nb_rubriques    = rubriques.count()

    peut_supprimer  = nb_inscriptions == 0

    if request.method == 'POST':
        if not peut_supprimer:
            messages.error(request, f"Impossible : {nb_inscriptions} inscription(s) utilisent ce grade.")
            return redirect('practitioners:supprimer_grade', pk=pk)
        nom = grade.nom
        grade.delete()  # CASCADE → tarifs + rubriques supprimés ; SET_NULL → grade_actuel des pratiquants
        messages.success(
            request,
            f"Grade « {nom} » supprimé"
            + (f" — {nb_pratiquants} licencié(s) sans grade" if nb_pratiquants else "")
            + (f" — {nb_tarifs} tarif(s) supprimé(s)" if nb_tarifs else "")
            + "."
        )
        return redirect('practitioners:grades')

    return render(request, 'practitioners/confirmer_supprimer_grade.html', {
        'grade':           grade,
        'inscriptions':    inscriptions[:10],
        'nb_inscriptions': nb_inscriptions,
        'pratiquants':     pratiquants,
        'nb_pratiquants':  nb_pratiquants,
        'tarifs':          tarifs,
        'nb_tarifs':       nb_tarifs,
        'rubriques':       rubriques,
        'nb_rubriques':    nb_rubriques,
        'peut_supprimer':  peut_supprimer,
    })


@gest_ligue_requis
def toggle_actif_grade(request, pk):
    ligue = request.user.ligue
    grade = get_object_or_404(Grade, pk=pk, ligue=ligue)
    if request.method == 'POST':
        grade.actif = not grade.actif
        grade.save()
        etat = "activé" if grade.actif else "désactivé"
        messages.success(request, f"Grade « {grade.nom} » {etat}.")
    return redirect('practitioners:grades')


# ─── Importation & Exportation de Pratiquants / Athlètes ─────────────────────

import csv
import json
import io
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from django.http import HttpResponse, JsonResponse


def parse_xlsx_bytes(content_bytes):
    rows = []
    try:
        with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                with z.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    for si in root.iter():
                        if si.tag.endswith('si'):
                            txt = "".join(t.text for t in si.iter() if t.tag.endswith('t') and t.text)
                            shared_strings.append(txt)

            sheet_name = None
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                    sheet_name = name
                    break

            if not sheet_name:
                return []

            with z.open(sheet_name) as f:
                tree = ET.parse(f)
                root = tree.getroot()
                for row_el in root.iter():
                    if row_el.tag.endswith('row'):
                        cell_dict = {}
                        for cell in row_el.iter():
                            if cell.tag.endswith('c'):
                                ref = cell.attrib.get('r', '')
                                col_letter = ''.join([c for c in ref if c.isalpha()])
                                cell_type = cell.attrib.get('t', '')
                                val = ''
                                v_el = None
                                for child in cell:
                                    if child.tag.endswith('v'):
                                        v_el = child
                                        break
                                if v_el is not None and v_el.text:
                                    val = v_el.text
                                    if cell_type == 's' and val.isdigit():
                                        idx = int(val)
                                        if idx < len(shared_strings):
                                            val = shared_strings[idx]
                                elif cell_type == 'inlineStr':
                                    val = "".join(t.text for t in cell.iter() if t.tag.endswith('t') and t.text)
                                if col_letter:
                                    cell_dict[col_letter] = val
                        if cell_dict:
                            rows.append(cell_dict)
    except Exception as e:
        return []

    if not rows:
        return []

    header_row = rows[0]
    headers = {col: str(val).strip() for col, val in header_row.items() if val}

    result_dicts = []
    for r in rows[1:]:
        row_dict = {}
        for col, val in r.items():
            h = headers.get(col)
            if h:
                row_dict[h] = val
        if any(row_dict.values()):
            result_dicts.append(row_dict)

    return result_dicts


@login_required
def exporter_pratiquants(request):
    fmt = request.GET.get('format', 'csv').lower()

    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
        pratiquants = Pratiquant.objects.filter(club=club).select_related('grade_actuel', 'club')
        nom_fichier = f"pratiquants_{club.sigle_club or club.nom_club}"
    elif (request.user.is_superuser or request.user.est_gest_ligue()) and hasattr(request.user, 'ligue') and request.user.ligue:
        ligue = request.user.ligue
        pratiquants = Pratiquant.objects.filter(club__ligue=ligue).select_related('grade_actuel', 'club')
        nom_fichier = f"pratiquants_{ligue.sigle or 'ligue'}"
    elif request.user.is_superuser:
        pratiquants = Pratiquant.objects.all().select_related('grade_actuel', 'club')
        nom_fichier = "pratiquants_export"
    else:
        messages.error(request, "Accès refusé.")
        return redirect('accounts:tableau_de_bord')

    club_id_param = request.GET.get('club_id') or request.GET.get('club')
    if club_id_param and (request.user.is_superuser or request.user.est_gest_ligue()):
        from apps.clubs.models import Club
        c_found = Club.objects.filter(pk=club_id_param).first()
        if c_found:
            pratiquants = pratiquants.filter(club=c_found)
            nom_fichier = f"pratiquants_{c_found.sigle_club or c_found.nom_club}"

    filtre_statut = request.GET.get('statut', 'actif')
    filtre_grade = request.GET.get('grade', '')
    filtre_sexe = request.GET.get('sexe', '')
    filtre_recherche = request.GET.get('q', '').strip()

    if filtre_statut == 'inactif':
        pratiquants = pratiquants.filter(actif=False)
    elif filtre_statut == 'actif':
        pratiquants = pratiquants.filter(actif=True)

    if filtre_grade == 'sans':
        pratiquants = pratiquants.filter(grade_actuel__isnull=True)
    elif filtre_grade:
        pratiquants = pratiquants.filter(grade_actuel__pk=filtre_grade)

    if filtre_sexe:
        pratiquants = pratiquants.filter(sexe=filtre_sexe)

    if filtre_recherche:
        pratiquants = pratiquants.filter(
            Q(nom__icontains=filtre_recherche) | Q(prenom__icontains=filtre_recherche)
        )

    pratiquants = pratiquants.order_by('grade_actuel__id_grade', 'nom', 'prenom')

    if fmt == 'json':
        data = []
        for p in pratiquants:
            data.append({
                'matricule': p.matricule or '',
                'nom': p.nom,
                'prenom': p.prenom,
                'sexe': p.sexe,
                'date_naissance': p.date_naissance.strftime('%Y-%m-%d') if p.date_naissance else '',
                'lieu_naissance': p.lieu_naissance or '',
                'telephone': p.telephone or '',
                'grade': p.grade_actuel.nom if p.grade_actuel else '',
                'code_club': (p.club.code_club or p.club.sigle_club or p.club.nom_club) if p.club else '',
                'statut': 'Actif' if p.actif else 'Inactif',
            })
        response = JsonResponse(data, safe=False, json_dumps_params={'indent': 2, 'ensure_ascii': False})
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}.json"'
        return response

    elif fmt in ['excel', 'xlsx']:
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}.csv"'
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Matricule', 'Nom', 'Prénom', 'Sexe', 'Date de naissance', 'Lieu de naissance', 'Téléphone', 'Grade', 'Code_Club', 'Statut'])
        for p in pratiquants:
            writer.writerow([
                p.matricule or '',
                p.nom,
                p.prenom,
                p.sexe,
                p.date_naissance.strftime('%d/%m/%Y') if p.date_naissance else '',
                p.lieu_naissance or '',
                p.telephone or '',
                p.grade_actuel.nom if p.grade_actuel else 'Sans grade',
                (p.club.code_club or p.club.sigle_club or p.club.nom_club) if p.club else '',
                'Actif' if p.actif else 'Inactif',
            ])
        return response

    else: # CSV par défaut
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}.csv"'
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Matricule', 'Nom', 'Prénom', 'Sexe', 'Date de naissance', 'Lieu de naissance', 'Téléphone', 'Grade', 'Code_Club', 'Statut'])
        for p in pratiquants:
            writer.writerow([
                p.matricule or '',
                p.nom,
                p.prenom,
                p.sexe,
                p.date_naissance.strftime('%Y-%m-%d') if p.date_naissance else '',
                p.lieu_naissance or '',
                p.telephone or '',
                p.grade_actuel.nom if p.grade_actuel else '',
                (p.club.code_club or p.club.sigle_club or p.club.nom_club) if p.club else '',
                'Actif' if p.actif else 'Inactif',
            ])
        return response


@login_required
def importer_pratiquants(request):
    if request.method != 'POST':
        return redirect('practitioners:liste')

    fichier = request.FILES.get('fichier')
    if not fichier:
        messages.error(request, "Veuillez sélectionner un fichier à importer.")
        return redirect('practitioners:liste')

    nom_fichier = fichier.name.lower()
    content = fichier.read()

    if hasattr(request.user, 'club') and request.user.club:
        club_defaut = request.user.club
        ligue = club_defaut.ligue
    elif hasattr(request.user, 'ligue') and request.user.ligue:
        ligue = request.user.ligue
        club_defaut = ligue.clubs.first()
    elif request.user.is_superuser:
        from apps.ligues.models import Ligue
        ligue = Ligue.objects.first()
        club_defaut = ligue.clubs.first() if ligue else None
    else:
        messages.error(request, "Votre compte n'est rattaché à aucun club ou ligue.")
        return redirect('practitioners:liste')

    # Si le GL ou Superutilisateur a sélectionné un club dans le formulaire d'import
    club_id_post = request.POST.get('club_id')
    if club_id_post and (request.user.is_superuser or request.user.est_gest_ligue()) and ligue:
        from apps.clubs.models import Club
        club_choisi = Club.objects.filter(pk=club_id_post, ligue=ligue).first()
        if club_choisi:
            club_defaut = club_choisi

    if not club_defaut:
        messages.error(request, "Aucun club n'est configuré pour importer des licenciés.")
        return redirect('practitioners:liste')

    rows_data = []

    if content.startswith(b'PK\x03\x04') or nom_fichier.endswith('.xlsx') or nom_fichier.endswith('.xls'):
        rows_data = parse_xlsx_bytes(content)
        if not rows_data:
            messages.error(request, "Impossible de lire le fichier Excel (.xlsx). Vérifiez qu'il contient des données valides.")
            return redirect('practitioners:liste')
    elif nom_fichier.endswith('.json'):
        try:
            data = json.loads(content.decode('utf-8'))
            if isinstance(data, list):
                rows_data = data
            elif isinstance(data, dict) and 'pratiquants' in data:
                rows_data = data['pratiquants']
        except Exception as e:
            messages.error(request, f"Erreur de lecture du fichier JSON : {e}")
            return redirect('practitioners:liste')
    else:
        decoded = None
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                decoded = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if not decoded:
            messages.error(request, "Impossible de lire le fichier. Encodage non reconnu.")
            return redirect('practitioners:liste')

        lines = decoded.splitlines()
        premiere_ligne = lines[0] if lines else ""
        delimiter = ';' if ';' in premiere_ligne else ('\t' if '\t' in premiere_ligne else ',')

        reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
        for row in reader:
            rows_data.append(row)

    if not rows_data:
        messages.error(request, "Le fichier importé est vide.")
        return redirect('practitioners:liste')

    nb_crees = 0
    nb_mis_a_jour = 0
    nb_erreurs = 0
    from apps.clubs.models import Club

    for idx, raw_row in enumerate(rows_data, start=2):
        row = {str(k).strip().lower(): str(v).strip() for k, v in raw_row.items() if k}
        
        nom = row.get('nom') or row.get('noms') or row.get('last_name') or row.get('nom_pratiquant') or row.get('nom(s)') or row.get('nom_prenom') or row.get('nom et prenom') or row.get('nom & prenom')
        prenom = row.get('prenom') or row.get('prénom') or row.get('prenoms') or row.get('prénoms') or row.get('first_name') or row.get('prenom(s)') or row.get('prénom(s)')

        if nom and not prenom:
            parts = nom.strip().split(maxsplit=1)
            nom = parts[0]
            prenom = parts[1] if len(parts) > 1 else 'Non précisé'
        elif prenom and not nom:
            parts = prenom.strip().split(maxsplit=1)
            nom = parts[0]
            prenom = parts[1] if len(parts) > 1 else 'Non précisé'

        if not nom or not prenom:
            nb_erreurs += 1
            continue

        dob_str = row.get('date_naissance') or row.get('date de naissance') or row.get('naissance') or row.get('dob') or ''
        date_naissance = None
        if dob_str:
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'):
                try:
                    date_naissance = datetime.strptime(dob_str, fmt).date()
                    break
                except ValueError:
                    pass
            if not date_naissance:
                try:
                    val_num = float(dob_str)
                    if val_num > 1000:
                        date_naissance = datetime(1899, 12, 30).date() + timedelta(days=int(val_num))
                except Exception:
                    pass
        if not date_naissance:
            date_naissance = datetime(2000, 1, 1).date()

        sexe_str = (row.get('sexe') or row.get('gender') or 'M').strip().upper()
        sexe = 'F' if sexe_str.startswith('F') else 'M'

        lieu_naissance = row.get('lieu_naissance') or row.get('lieu de naissance') or row.get('lieu') or ''
        telephone = row.get('telephone') or row.get('téléphone') or row.get('contact') or ''

        matricule = (row.get('matricule') or '').strip()
        if matricule.upper() in ('', '-', '0', 'N/A', 'NA', 'NONE', 'NULL', 'AUCUN') or len(matricule) < 2:
            matricule = None

        grade_str = row.get('grade') or row.get('grade_actuel') or ''
        grade_obj = None
        if grade_str and ligue:
            grade_obj = Grade.objects.filter(ligue=ligue, nom__iexact=grade_str).first()
            if not grade_obj and grade_str.isdigit():
                grade_obj = Grade.objects.filter(ligue=ligue, pk=int(grade_str)).first()

        club_row_str = row.get('code_club') or row.get('code') or row.get('club') or row.get('nom_club') or row.get('sigle_club') or row.get('sigle') or ''
        club_cible = club_defaut
        if club_row_str and ligue and (request.user.is_superuser or request.user.est_gest_ligue()) and not club_id_post:
            found_club = (
                Club.objects.filter(ligue=ligue, code_club__iexact=club_row_str).first() or
                Club.objects.filter(ligue=ligue, sigle_club__iexact=club_row_str).first() or
                Club.objects.filter(ligue=ligue, nom_club__iexact=club_row_str).first() or
                Club.objects.filter(ligue=ligue, nom_club__icontains=club_row_str).first()
            )
            if found_club:
                club_cible = found_club

        p_qs = Pratiquant.objects.none()
        if matricule:
            p_mat = Pratiquant.objects.filter(matricule=matricule, club=club_cible).first()
            if not p_mat:
                p_mat = Pratiquant.objects.filter(matricule=matricule).first()
            if p_mat:
                p_qs = Pratiquant.objects.filter(pk=p_mat.pk)

        if not p_qs.exists():
            p_qs = Pratiquant.objects.filter(club=club_cible, nom__iexact=nom, prenom__iexact=prenom)

        pratiquant = p_qs.first()
        if pratiquant:
            pratiquant.nom = nom.upper()
            pratiquant.prenom = prenom.title()
            pratiquant.club = club_cible
            pratiquant.sexe = sexe
            if dob_str and date_naissance:
                pratiquant.date_naissance = date_naissance
            if lieu_naissance:
                pratiquant.lieu_naissance = lieu_naissance
            if telephone:
                pratiquant.telephone = telephone
            if grade_obj:
                pratiquant.grade_actuel = grade_obj
            if matricule:
                if not Pratiquant.objects.filter(matricule=matricule).exclude(pk=pratiquant.pk).exists():
                    pratiquant.matricule = matricule
            pratiquant.save()
            nb_mis_a_jour += 1
        else:
            if matricule and Pratiquant.objects.filter(matricule=matricule).exists():
                matricule = None
            Pratiquant.objects.create(
                club=club_cible,
                nom=nom.upper(),
                prenom=prenom.title(),
                date_naissance=date_naissance,
                sexe=sexe,
                lieu_naissance=lieu_naissance,
                telephone=telephone,
                grade_actuel=grade_obj,
                matricule=matricule or None
            )
            nb_crees += 1

    msg = f"Importation réussie : {nb_crees} licencié(s) créé(s), {nb_mis_a_jour} mis à jour."
    if nb_erreurs > 0:
        msg += f" ({nb_erreurs} ligne(s) ignorée(s))."
        messages.warning(request, msg)
    else:
        messages.success(request, msg)

    return redirect('practitioners:liste')


@login_required
def telecharger_modele_import(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="modele_import_licencies.csv"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nom', 'Prénom', 'Date de naissance', 'Sexe', 'Lieu de naissance', 'Téléphone', 'Grade', 'Code_Club'])
    writer.writerow(['OUEDRAOGO', 'Moussa', '2005-04-12', 'M', 'Ouagadougou', '70000000', 'BLANC', 'CC'])
    writer.writerow(['SAWADOGO', 'Awa', '2008-09-25', 'F', 'Ouagadougou', '76000000', 'ROUGE', 'DN'])
    return response
