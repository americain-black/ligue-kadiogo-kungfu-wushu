# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.urls import path, include, re_path
# pyrefly: ignore [missing-import]
from django.conf import settings
# pyrefly: ignore [missing-import]
from django.views.static import serve

urlpatterns = [
    path('admin/',   admin.site.urls),
    path('',         include('apps.accounts.urls', namespace='accounts')),
    path('ligues/',  include('apps.ligues.urls',   namespace='ligues')),
    path('clubs/',       include('apps.clubs.urls',        namespace='clubs')),
    path('pratiquants/', include('apps.practitioners.urls', namespace='practitioners')),
    path('examens/',     include('apps.exams.urls',         namespace='exams')),
    path('paiements/',    include('apps.payments.urls',      namespace='payments')),
    path('evaluations/',  include('apps.evaluations.urls',   namespace='evaluations')),
    path('resultats/',    include('apps.results.urls',       namespace='results')),
    path('communication/', include('apps.communication.urls', namespace='communication')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
