from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ActualiteForm, DocumentForm, RejetActualiteForm
from .models import Actualite, Document


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


def _ligue_site():
    from apps.ligues.models import Ligue
    return Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()


# ═══════════════════════════════════════════════════════════════════════
# Public
# ═══════════════════════════════════════════════════════════════════════

def liste_actualites_publique(request):
    ligue = _ligue_site()
    q = request.GET.get('q', '').strip()
    actualites = (
        Actualite.objects.filter(ligue=ligue, statut='PUBLIEE', est_public=True)
        .order_by('-date_publication')
        if ligue else Actualite.objects.none()
    )
    if q:
        actualites = actualites.filter(Q(titre__icontains=q) | Q(contenu__icontains=q))
    return render(request, 'communication/actualites_publique.html', {
        'actualites': actualites, 'q': q,
    })


def detail_actualite_publique(request, pk):
    ligue = _ligue_site()
    actualite = get_object_or_404(Actualite, pk=pk, ligue=ligue, statut='PUBLIEE', est_public=True)
    return render(request, 'communication/detail_actualite_publique.html', {
        'actualite': actualite,
    })


def liste_documents_publique(request):
    ligue = _ligue_site()
    q = request.GET.get('q', '').strip()
    documents = (
        Document.objects.filter(ligue=ligue, est_public=True)
        .order_by('-date_publication')
        if ligue else Document.objects.none()
    )
    if q:
        documents = documents.filter(titre__icontains=q)
    return render(request, 'communication/documents_publique.html', {
        'documents': documents, 'q': q,
    })


# ═══════════════════════════════════════════════════════════════════════
# Gestion — Ligue
# ═══════════════════════════════════════════════════════════════════════

@gest_ligue_requis
def liste_actualites(request):
    actualites = Actualite.objects.filter(ligue=request.user.ligue).select_related('club').order_by('-date_creation')

    statut = request.GET.get('statut', '')
    if statut:
        actualites = actualites.filter(statut=statut)

    source = request.GET.get('source', '')
    if source:
        actualites = actualites.filter(source=source)

    q = request.GET.get('q', '').strip()
    if q:
        actualites = actualites.filter(Q(titre__icontains=q) | Q(contenu__icontains=q))

    return render(request, 'communication/liste_actualites.html', {
        'actualites':      actualites,
        'statut_filtre':   statut,
        'source_filtre':   source,
        'q':               q,
        'statut_choices':  Actualite.STATUT_CHOICES,
        'source_choices':  Actualite.SOURCE_CHOICES,
    })


@gest_ligue_requis
def detail_actualite(request, pk):
    actualite = get_object_or_404(Actualite, pk=pk, ligue=request.user.ligue)
    return render(request, 'communication/detail_actualite.html', {'actualite': actualite})


@gest_ligue_requis
def creer_actualite(request):
    if request.method == 'POST':
        form = ActualiteForm(request.POST, request.FILES)
        if form.is_valid():
            actualite = form.save(commit=False)
            actualite.ligue  = request.user.ligue
            actualite.source = 'LIGUE'
            actualite.auteur = request.user
            actualite.save()
            messages.success(request, "Actualité créée en brouillon.")
            return redirect('communication:detail_actualite', pk=actualite.pk)
    else:
        form = ActualiteForm()
    return render(request, 'communication/actualite_form.html', {
        'form': form, 'titre': 'Nouvelle actualité',
    })


@gest_ligue_requis
def modifier_actualite(request, pk):
    actualite = get_object_or_404(Actualite, pk=pk, ligue=request.user.ligue, source='LIGUE')
    if request.method == 'POST':
        form = ActualiteForm(request.POST, request.FILES, instance=actualite)
        if form.is_valid():
            form.save()
            messages.success(request, "Actualité modifiée.")
            return redirect('communication:detail_actualite', pk=actualite.pk)
    else:
        form = ActualiteForm(instance=actualite)
    return render(request, 'communication/actualite_form.html', {
        'form': form, 'titre': 'Modifier l\'actualité', 'actualite': actualite,
    })


@gest_ligue_requis
def supprimer_actualite(request, pk):
    actualite = get_object_or_404(Actualite, pk=pk, ligue=request.user.ligue)
    est_publiee = actualite.statut == 'PUBLIEE'
    form = None

    if request.method == 'POST':
        if est_publiee:
            form = RejetActualiteForm(request.POST)
            if form.is_valid():
                actualite.rejeter(motif=form.cleaned_data['motif'])
                messages.warning(request, f"Actualité « {actualite.titre} » retirée de la publication.")
                return redirect('communication:liste_actualites')
        else:
            actualite.delete()
            messages.success(request, "Actualité supprimée.")
            return redirect('communication:liste_actualites')
    elif est_publiee:
        form = RejetActualiteForm()

    return render(request, 'communication/confirmer_suppression_actualite.html', {
        'actualite': actualite, 'form': form, 'est_publiee': est_publiee,
    })


@gest_ligue_requis
def publier_actualite(request, pk):
    actualite = get_object_or_404(
        Actualite, pk=pk, ligue=request.user.ligue,
        statut__in=['BROUILLON', 'EN_ATTENTE'],
    )
    if request.method == 'POST':
        actualite.est_public = request.POST.get('visibilite', 'public') == 'public'
        actualite.publier(validee_par=request.user)
        messages.success(request, f"Actualité « {actualite.titre} » publiée.")
        return redirect('communication:liste_actualites')
    return render(request, 'communication/confirmer_publication.html', {'actualite': actualite})


@gest_ligue_requis
def toggle_visibilite_actualite(request, pk):
    actualite = get_object_or_404(Actualite, pk=pk, ligue=request.user.ligue, statut='PUBLIEE')
    if request.method == 'POST':
        actualite.est_public = not actualite.est_public
        actualite.save()
        messages.success(
            request,
            f"Actualité « {actualite.titre} » rendue "
            + ("publique." if actualite.est_public else "privée."),
        )
    return redirect('communication:detail_actualite', pk=actualite.pk)


@gest_ligue_requis
def rejeter_actualite(request, pk):
    actualite = get_object_or_404(
        Actualite, pk=pk, ligue=request.user.ligue,
        source='CLUB', statut='EN_ATTENTE',
    )
    if request.method == 'POST':
        form = RejetActualiteForm(request.POST)
        if form.is_valid():
            actualite.rejeter(motif=form.cleaned_data['motif'])
            messages.warning(request, f"Actualité « {actualite.titre} » rejetée.")
            return redirect('communication:liste_actualites')
    else:
        form = RejetActualiteForm()
    return render(request, 'communication/rejeter_actualite.html', {
        'form': form, 'actualite': actualite,
    })


@gest_ligue_requis
def liste_documents(request):
    documents = Document.objects.filter(ligue=request.user.ligue).order_by('-date_publication')
    q = request.GET.get('q', '').strip()
    if q:
        documents = documents.filter(titre__icontains=q)
    return render(request, 'communication/liste_documents.html', {'documents': documents, 'q': q})


@gest_ligue_requis
def creer_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.ligue  = request.user.ligue
            document.auteur = request.user
            document.save()
            messages.success(request, "Document publié.")
            return redirect('communication:liste_documents')
    else:
        form = DocumentForm()
    return render(request, 'communication/document_form.html', {
        'form': form, 'titre': 'Nouveau document',
    })


@gest_ligue_requis
def modifier_document(request, pk):
    document = get_object_or_404(Document, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document modifié.")
            return redirect('communication:liste_documents')
    else:
        form = DocumentForm(instance=document)
    return render(request, 'communication/document_form.html', {
        'form': form, 'titre': 'Modifier le document', 'document': document,
    })


@gest_ligue_requis
def supprimer_document(request, pk):
    document = get_object_or_404(Document, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        document.delete()
        messages.success(request, "Document supprimé.")
        return redirect('communication:liste_documents')
    return render(request, 'communication/confirmer_suppression_document.html', {'document': document})


# ═══════════════════════════════════════════════════════════════════════
# Gestion — Club
# ═══════════════════════════════════════════════════════════════════════

@gest_club_requis
def mes_actualites(request):
    actualites = Actualite.objects.filter(club=request.user.club).order_by('-date_creation')
    return render(request, 'communication/mes_actualites.html', {
        'actualites': actualites, 'club': request.user.club,
    })


@gest_club_requis
def detail_actualite_club(request, pk):
    actualite = get_object_or_404(Actualite, pk=pk, club=request.user.club)
    return render(request, 'communication/detail_actualite_club.html', {
        'actualite': actualite, 'club': request.user.club,
    })


@gest_club_requis
def creer_actualite_club(request):
    club = request.user.club
    if request.method == 'POST':
        form = ActualiteForm(request.POST, request.FILES)
        if form.is_valid():
            actualite = form.save(commit=False)
            actualite.ligue  = club.ligue
            actualite.club   = club
            actualite.source = 'CLUB'
            actualite.auteur = request.user
            actualite.save()
            messages.success(request, "Actualité enregistrée en brouillon. Soumettez-la pour validation quand elle est prête.")
            return redirect('communication:detail_actualite_club', pk=actualite.pk)
    else:
        form = ActualiteForm()
    return render(request, 'communication/actualite_form_club.html', {
        'form': form, 'titre': 'Proposer une actualité', 'club': club,
    })


@gest_club_requis
def modifier_actualite_club(request, pk):
    actualite = get_object_or_404(
        Actualite, pk=pk, club=request.user.club,
        statut__in=['BROUILLON', 'REJETEE'],
    )
    if request.method == 'POST':
        form = ActualiteForm(request.POST, request.FILES, instance=actualite)
        if form.is_valid():
            form.save()
            messages.success(request, "Actualité modifiée.")
            return redirect('communication:detail_actualite_club', pk=actualite.pk)
    else:
        form = ActualiteForm(instance=actualite)
    return render(request, 'communication/actualite_form_club.html', {
        'form': form, 'titre': 'Modifier l\'actualité', 'actualite': actualite, 'club': request.user.club,
    })


@gest_club_requis
def soumettre_actualite_club(request, pk):
    actualite = get_object_or_404(
        Actualite, pk=pk, club=request.user.club,
        statut__in=['BROUILLON', 'REJETEE'],
    )
    if request.method == 'POST':
        actualite.soumettre()
        messages.success(request, "Actualité soumise à la ligue pour validation.")
        return redirect('communication:mes_actualites')
    return render(request, 'communication/confirmer_soumission.html', {
        'actualite': actualite, 'club': request.user.club,
    })


@gest_club_requis
def supprimer_actualite_club(request, pk):
    actualite = get_object_or_404(
        Actualite, pk=pk, club=request.user.club, statut='BROUILLON',
    )
    if request.method == 'POST':
        actualite.delete()
        messages.success(request, "Actualité supprimée.")
        return redirect('communication:mes_actualites')
    return render(request, 'communication/confirmer_suppression_actualite_club.html', {
        'actualite': actualite, 'club': request.user.club,
    })
