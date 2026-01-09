

# Register your models here.
from django.contrib import admin
from .models import Classe, Eleve, Matiere, Note

# -----------------------------
# Classe
# -----------------------------
@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau')          # Affiche le nom et le niveau (collège/lycée)
    search_fields = ('nom',)                   # Recherche par nom de classe
    list_filter = ('niveau',)                  # Filtre par niveau

# -----------------------------
# Élève
# -----------------------------
@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'classe', 'date_naissance', 'lieu_naissance')
    search_fields = ('nom', 'prenom')
    list_filter = ('classe',)
    readonly_fields = ('matricule',)           # Si matricule est généré automatiquement
    # Permet d'ajouter un élève directement dans l'admin

# -----------------------------
# Matière
# -----------------------------
@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'coefficient')     # Affiche nom et coefficient
    search_fields = ('nom',)

# -----------------------------
# Note
# -----------------------------
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'matiere', 'type_note', 'valeur', 'semestre')
    search_fields = ('eleve__nom', 'eleve__prenom', 'matiere__nom')
    list_filter = ('semestre', 'type_note', 'matiere')
