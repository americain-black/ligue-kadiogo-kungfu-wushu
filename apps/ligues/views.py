from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Ligue
from .forms import LigueForm


def super_admin_requis(view_func):
    """Décorateur : réserve la vue aux Super Admins."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_super_admin()):
            messages.error(request, "Accès réservé au Super Administrateur.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


@super_admin_requis
def liste_ligues(request):
    ligues = Ligue.objects.all().order_by('nom_ligue')
    return render(request, 'ligues/liste.html', {'ligues': ligues})


@super_admin_requis
def creer_ligue(request):
    if request.method == 'POST':
        form = LigueForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Ligue créée avec succès.")
            return redirect('ligues:liste')
    else:
        form = LigueForm()
    return render(request, 'ligues/form.html', {'form': form, 'titre': 'Créer une ligue'})


@super_admin_requis
def modifier_ligue(request, pk):
    ligue = get_object_or_404(Ligue, pk=pk)
    if request.method == 'POST':
        form = LigueForm(request.POST, request.FILES, instance=ligue)
        if form.is_valid():
            form.save()
            messages.success(request, "Ligue modifiée avec succès.")
            return redirect('ligues:liste')
    else:
        form = LigueForm(instance=ligue)
    return render(request, 'ligues/form.html', {
        'form': form, 'titre': 'Modifier la ligue', 'ligue': ligue
    })


@super_admin_requis
def toggle_statut_ligue(request, pk):
    ligue = get_object_or_404(Ligue, pk=pk)
    if ligue.statut == 'ACTIVE':
        ligue.statut = 'INACTIVE'
        messages.warning(request, f"Ligue « {ligue.nom_ligue} » désactivée.")
    else:
        ligue.statut = 'ACTIVE'
        messages.success(request, f"Ligue « {ligue.nom_ligue} » réactivée.")
    ligue.save()
    return redirect('ligues:liste')
