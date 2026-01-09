# core/utils.py
from collections import defaultdict
from .models import Note

def calculer_moyennes_par_semestre(eleve, semestre):
    resultats = {}

    notes = Note.objects.filter(eleve=eleve, semestre=semestre)

    notes_par_matiere = defaultdict(list)
    for note in notes:
        notes_par_matiere[note.matiere].append(note)

    for matiere, notes_matiere in notes_par_matiere.items():
        interros = [n.valeur for n in notes_matiere if n.type_note.startswith('I')]
        devoirs = [n.valeur for n in notes_matiere if n.type_note.startswith('D')]
        comp = next((n.valeur for n in notes_matiere if n.type_note == 'C'), None)

        note_interro = sum(interros) / len(interros) if interros else None
        note_devoir = sum(devoirs) / len(devoirs) if devoirs else None

        note_classe = None
        if note_interro is not None and note_devoir is not None:
            note_classe = round((note_interro + note_devoir) / 2, 2)
        elif note_interro is not None:
            note_classe = round(note_interro, 2)
        elif note_devoir is not None:
            note_classe = round(note_devoir, 2)

        moyenne = None
        if note_classe is not None and comp is not None:
            moyenne = round((note_classe + comp) / 2, 2)
        elif note_classe is not None:
            moyenne = note_classe
        elif comp is not None:
            moyenne = comp

        resultats[matiere.id] = {
            'coef': matiere.coefficient,
            'note_classe': note_classe,
            'moyenne': moyenne
        }

    return resultats
