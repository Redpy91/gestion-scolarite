from django.db import models
from django.contrib.auth.models import User
import uuid


# -----------------------------
# Classe
# -----------------------------
class Classe(models.Model):
    NIVEAUX = (
        ('college', 'Collège'),
        ('lycee', 'Lycée'),
    )
    nom = models.CharField(max_length=50)
    niveau = models.CharField(max_length=10, choices=NIVEAUX)

    def __str__(self):
        return f"{self.nom} ({self.get_niveau_display()})"

# -----------------------------
# Élève
# -----------------------------
class Eleve(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to='eleves/', blank=True, null=True)
    classe = models.ForeignKey('Classe', on_delete=models.CASCADE)
    matricule = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    # Moyenne pour une matière
    def moyenne_matiere(self, matiere):
        notes = self.notes.filter(matiere=matiere)
        if not notes.exists():
            return None
        total = sum(note.valeur for note in notes)
        return round(total / notes.count(), 2)

    # Moyenne générale
    def moyenne_generale(self):
        notes = self.notes.all()
        if not notes.exists():
            return None

        total = 0
        total_coef = 0

        for note in notes:
            coef = note.matiere.coefficient
            total += note.valeur * coef
            total_coef += coef

        if total_coef == 0:
            return None

        return round(total / total_coef, 2)
# -----------------------------
# Matière
# -----------------------------
class Matiere(models.Model):
    NOM_MATIERES = (
        ('francais', 'Français'),
        ('anglais', 'Anglais'),
        ('hg', 'Histoire/Géo'),
        ('maths', 'Maths'),
        ('pc', 'Physique/Chimie'),
        ('svt', 'SVT'),
        ('ef', 'Education Française'),
        ('eps', 'EPS'),
        ('conduite', 'Conduite'),
    )
    nom = models.CharField(max_length=20, choices=NOM_MATIERES)
    
    coefficient = models.FloatField(default=1)
    classe = models.ForeignKey('Classe', on_delete=models.CASCADE, related_name='matieres', default=1)

    def __str__(self):
        return self.get_nom_display()

# -----------------------------
# Note
# -----------------------------
class Note(models.Model): 
    # Types de notes
    TYPE_NOTE_CHOICES = [
        ('I1', 'Interrogation 1'),
        ('I2', 'Interrogation 2'),
        ('I3', 'Interrogation 3'),
        ('D1', 'Devoir 1'),
        ('D2', 'Devoir 2'),
        ('D3', 'Devoir 3'),
        ('C',  'Composition'),
    ]

    # Semestres
    SEMESTRE_CHOICES = [
        (1, 'Semestre 1'),
        (2, 'Semestre 2'),
    ]

    # Relations
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='notes')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    
    # Champs
    type_note = models.CharField(max_length=2, choices=TYPE_NOTE_CHOICES)
    valeur = models.FloatField()
    semestre = models.IntegerField(choices=SEMESTRE_CHOICES)

    def __str__(self):
        return f"{self.eleve} - {self.matiere} - {self.get_type_note_display()}"