from django.urls import path
from . import views

urlpatterns = [
    # Page d'accueil
    path('', views.accueil, name='accueil'),
    path('accueil/', views.accueil, name='accueil'),

    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Pages Collège et Lycée
    path('college/', views.page_college, name='college'),
    path('lycee/', views.page_lycee, name='lycee'),

    # Liste des classes
    path('college/classes/', views.page_college, name='classes_college'),
    path('lycee/classes/', views.page_lycee, name='classes_lycee'),

    # Détails d'une classe et liste des élèves
    path('classe/<int:classe_id>/', views.liste_eleves, name='liste_eleves'),

    # Ajouter un élève
    path('classe/<int:classe_id>/ajouter/', views.ajouter_eleve, name='ajouter_eleve'),

    # Classement d'une classe
    path('classe/<int:classe_id>/classement/', views.classement_classe, name='classement_classe'),

    # Détails d'un élève
    path('eleve/<int:eleve_id>/', views.detail_eleve, name='detail_eleve'),

    # Ajouter une note pour un élève
    path('eleve/<int:eleve_id>/note/ajouter/', views.ajouter_note, name='ajouter_note'),

    # Générer le bulletin PDF d'un élève
    path('eleve/<int:eleve_id>/bulletin/', views.bulletin_pdf, name='bulletin_pdf'),

    # Modifier une note
    path('eleve/<int:eleve_id>/matiere/<int:matiere_id>/modifier/', views.modifier_notes, name='modifier_notes'),

    # Pages spécifiques pour les élèves
    path('mes-notes/', views.mes_notes, name='mes_notes'),
]
