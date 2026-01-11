from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from .models import Classe, Eleve, Matiere, Note
from .decorators import groupe_requis
from django.db.models import Avg
from django.utils.crypto import get_random_string
from datetime import date
from .utils import calculer_moyennes_par_semestre



# =============================
# ACCUEIL
# =============================
@login_required(login_url='login')
def accueil(request):
    return render(request, 'core/accueil.html')


# =============================
# COLLÈGE / LYCÉE
# =============================
@login_required(login_url='login')
def page_college(request):
    classes = Classe.objects.filter(niveau='college')
    return render(request, 'core/classes_college.html', {'classes': classes})


@login_required(login_url='login')
def page_lycee(request):
    classes = Classe.objects.filter(niveau='lycee')
    return render(request, 'core/classes_lycee.html', {'classes': classes})


# =============================
# LISTE DES ÉLÈVES
# =============================
@login_required(login_url='login')
def liste_eleves(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    eleves = Eleve.objects.filter(classe=classe)
    return render(request, 'core/liste_eleves.html', {
        'classe': classe,
        'eleves': eleves
    })


# =============================
# AJOUT ÉLÈVE
# =============================
from django.contrib.auth.models import User, Group
from django.contrib import messages
import random
import string


@login_required(login_url='login')
@groupe_requis('Prof')
def ajouter_eleve(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)

    if request.method == "POST":
        nom = request.POST["nom"]
        prenom = request.POST["prenom"]
        date_naissance = request.POST["date_naissance"]
        lieu_naissance = request.POST["lieu_naissance"]

        # Générer matricule automatique
        matricule = f"{classe.nom[:3].upper()}{random.randint(100,999)}"

        # Générer mot de passe temporaire aléatoire
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=matricule,
            password=password,
            first_name=nom,
            last_name=prenom
        )
        # Ajouter le groupe "Eleve"
        groupe_eleve = Group.objects.get(name="Eleve")
        user.groups.add(groupe_eleve)

        # Créer l'élève
        Eleve.objects.create(
            user=user,
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            lieu_naissance=lieu_naissance,
            classe=classe,
            matricule=matricule
        )

        # Générer le PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="compte_eleve_{matricule}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width / 2, height - 3*cm, "Compte élève")

        p.setFont("Helvetica", 12)
        p.drawString(3*cm, height - 5*cm, f"Nom : {nom}")
        p.drawString(3*cm, height - 6*cm, f"Prénom : {prenom}")
        p.drawString(3*cm, height - 7*cm, f"Matricule : {matricule}")
        p.drawString(3*cm, height - 8*cm, f"Mot de passe temporaire : {password}")

        p.drawString(3*cm, height - 10*cm, "⚠ Veuillez utiliser votre matricule et le mot de passe pour vous connectez.")

        p.showPage()
        p.save()

        return response

    return render(request, "core/ajouter_eleve.html", {
        "classe": classe
    })
# =============================
# LOGIN / LOGOUT
# =============================
def user_login(request):
    if request.user.is_authenticated:
        return redirect('accueil')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('accueil')
        else:
            messages.error(request, "Identifiants incorrects.")

    return render(request, 'core/login.html', {'login_page': True})


@login_required(login_url='login')
def user_logout(request):
    logout(request)
    return redirect('login')


# =============================
# DÉTAIL ÉLÈVE
# =============================
from django.shortcuts import get_object_or_404, render
from .models import Eleve, Matiere

def detail_eleve(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)

    # 🔹 1. Récupérer le semestre depuis l’URL (GET)
    try:
        semestre = int(request.GET.get('semestre', 1))
    except ValueError:
        semestre = 1

    if semestre not in [1, 2]:
        semestre = 1

    # 🔹 2. Matières de la classe
    matieres = Matiere.objects.filter(classe=eleve.classe)

    evaluations = ['I1', 'I2', 'I3', 'D1', 'D2', 'D3', 'C']

    # 🔹 3. Dictionnaire des moyennes par matière
    moyennes_matieres = {}

    for matiere in matieres:
        notes_matiere = eleve.notes.filter(
            matiere=matiere,
            semestre=semestre   # ✅ TRÈS IMPORTANT
        )

        interros = [n.valeur for n in notes_matiere if n.type_note in ['I1', 'I2', 'I3']]
        devoirs = [n.valeur for n in notes_matiere if n.type_note in ['D1', 'D2', 'D3']]
        composition = next(
            (n.valeur for n in notes_matiere if n.type_note == 'C'),
            None
        )

        # Note de classe
        note_classe = None
        if interros or devoirs:
            interro_moy = sum(interros) / len(interros) if interros else 0
            devoir_moy = sum(devoirs) / len(devoirs) if devoirs else 0
            note_classe = (interro_moy + devoir_moy) / 2

        # Moyenne finale
        moyenne = None
        if note_classe is not None and composition is not None:
            moyenne = (note_classe + composition) / 2
        elif note_classe is not None:
            moyenne = note_classe
        elif composition is not None:
            moyenne = composition

        moyennes_matieres[matiere.id] = {
            'coef': matiere.coefficient,
            'note_classe': note_classe,
            'moyenne': moyenne
        }
    notes_semestre = eleve.notes.filter(semestre=semestre)

    context = {
        'eleve': eleve,
        'matieres': matieres,
        'evaluations': evaluations,
        'moyennes_matieres': moyennes_matieres,
        'semestre': semestre,  # ✅ utilisé dans le select
        'notes_semestre': notes_semestre,  # ✅ IMPORTANT
    }

    return render(request, 'core/detail_eleve.html', context)


# =============================
# AJOUT NOTE (✅ VERSION UNIQUE)
# =============================
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Eleve, Matiere, Note

@login_required(login_url='login')
@groupe_requis('Prof')
def ajouter_note(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)

    # 🔥 MATIÈRES UNIQUEMENT DE LA CLASSE DE L'ÉLÈVE
    matieres = Matiere.objects.filter(classe=eleve.classe)

    if request.method == "POST":
        try:
            matiere_id = request.POST.get("matiere")
            type_note = request.POST.get("type_note")
            valeur = request.POST.get("valeur")
            semestre = request.POST.get("semestre")

            # Sécurité
            if not all([matiere_id, type_note, valeur, semestre]):
                raise ValueError("Tous les champs sont obligatoires")

            matiere = get_object_or_404(
                Matiere,
                id=matiere_id,
                classe=eleve.classe  # 🔒 sécurité absolue
            )

            Note.objects.create(
                eleve=eleve,
                matiere=matiere,
                type_note=type_note,
                valeur=float(valeur),
                semestre=int(semestre)
            )

            messages.success(request, "✅ Note ajoutée avec succès.")
            return redirect('detail_eleve', eleve_id=eleve.id)

        except Exception as e:
            messages.error(request, f"❌ Erreur : {e}")

    return render(request, 'core/ajouter_note.html', {
        'eleve': eleve,
        'matieres': matieres
    })


# =============================
# CLASSEMENT CLASSE
# =============================
@groupe_requis('Prof')
@login_required(login_url='login')
def classement_classe(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    eleves = Eleve.objects.filter(classe=classe)

    classement = []
    for eleve in eleves:
        moyenne = eleve.moyenne_generale()
        if moyenne is not None:
            classement.append((eleve, moyenne))

    classement.sort(key=lambda x: x[1], reverse=True)

    return render(request, 'core/classement.html', {
        'classe': classe,
        'classement': classement
    })


# =============================
# NOTES ÉLÈVE
# =============================@login_required
@login_required(login_url='login')
@groupe_requis('Eleve')
def mes_notes(request):
    eleve = get_object_or_404(Eleve, user=request.user)
    notes = Note.objects.filter(eleve=eleve).select_related('matiere')

    # Moyennes par matière
    moyennes = {}
    for matiere in Matiere.objects.all():
        moyenne = eleve.moyenne_matiere(matiere)
        if moyenne is not None:
            moyennes[matiere] = moyenne

    moyenne_generale = eleve.moyenne_generale()

    return render(request, 'core/mes_notes.html', {
        'eleve': eleve,
        'notes': notes,
        'moyennes': moyennes,
        'moyenne_generale': moyenne_generale
    })


from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import date
@login_required(login_url='login')
def bulletin_pdf(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)

    semestre = int(request.GET.get('semestre', 1))
    annee = date.today().year
    annee_scolaire = f"{annee-1}-{annee}"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=bulletin_{eleve.id}.pdf'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # =========================
    # EN-TÊTE
    # =========================
    p.setFont("Helvetica-Bold", 10)
    p.drawString(2*cm, height-2*cm, "REPUBLIQUE DU NIGER")
    p.drawString(2*cm, height-2.7*cm, "REGION D'AGADEZ")
    p.drawString(2*cm, height-3.4*cm, "DREMS / AGADEZ")
    p.drawString(2*cm, height-4.1*cm, "COMPLEXE D'ENSEIGNEMENT SECONDAIRE")

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height-2*cm, "BULLETIN SCOLAIRE")

    p.setFont("Helvetica", 10)
    p.drawRightString(width-2*cm, height-2*cm, f"Année scolaire : {annee_scolaire}")
    p.drawRightString(width-2*cm, height-2.7*cm, f"Semestre : {semestre}")

    # =========================
    # INFOS ÉLÈVE
    # =========================
    y = height - 6*cm
    p.setFont("Helvetica", 11)
    p.drawString(2*cm, y, f"Nom & Prénom : {eleve.nom} {eleve.prenom}")

    effectif = Eleve.objects.filter(classe=eleve.classe).count()

    # =========================
    # CALCUL MOYENNE SEMESTRIELLE
    # =========================
    total_coef_moy = 0
    total_coef = 0

    matieres = Matiere.objects.filter(classe=eleve.classe)
    notes_cache = {}

    for matiere in matieres:
        notes = Note.objects.filter(eleve=eleve, matiere=matiere, semestre=semestre)

        interros = [n.valeur for n in notes if n.type_note.startswith('I')]
        devoirs = [n.valeur for n in notes if n.type_note.startswith('D')]
        comp = next((n.valeur for n in notes if n.type_note == 'C'), None)

        note_classe = None
        if interros or devoirs:
            note_classe = (
                ((sum(interros)/len(interros) if interros else 0) +
                 (sum(devoirs)/len(devoirs) if devoirs else 0)) / 2
            )

        moyenne = None
        if note_classe is not None and comp is not None:
            moyenne = (note_classe + comp) / 2
        elif note_classe is not None:
            moyenne = note_classe
        elif comp is not None:
            moyenne = comp

        coef_moy = (moyenne or 0) * matiere.coefficient
        total_coef_moy += coef_moy
        total_coef += matiere.coefficient

        notes_cache[matiere.id] = {
            'note_classe': note_classe,
            'comp': comp,
            'coef_moy': coef_moy
        }

    moyenne_semestrielle = round(total_coef_moy / total_coef, 2) if total_coef else 0

    # =========================
    # RANG (CORRIGÉ SANS ERREUR)
    # =========================
    moyennes_classe = []

    for e in Eleve.objects.filter(classe=eleve.classe):
        somme, coef = 0, 0
        for m in matieres:
            notes = Note.objects.filter(eleve=e, matiere=m, semestre=semestre)

            interros = [n.valeur for n in notes if n.type_note.startswith('I')]
            devoirs = [n.valeur for n in notes if n.type_note.startswith('D')]
            comp = next((n.valeur for n in notes if n.type_note == 'C'), None)

            if interros or devoirs:
                nc = (
                    ((sum(interros)/len(interros) if interros else 0) +
                     (sum(devoirs)/len(devoirs) if devoirs else 0)) / 2
                )
                if comp is not None:
                    moy = (nc + comp) / 2
                    somme += moy * m.coefficient
                    coef += m.coefficient

        moyennes_classe.append(round(somme/coef, 2) if coef else 0)

    # ✅ RANG DENSE CORRECT
    rang, ex_aequo = calculer_rang_dense(moyenne_semestrielle, moyennes_classe)
    rang_affiche = f"{rang} ex æquo" if ex_aequo else str(rang)


    p.drawCentredString(
        width/2, y-0.7*cm,
        f"Classe : {eleve.classe.nom} | Effectif : {effectif} | Moyenne : {moyenne_semestrielle} | Rang : {rang_affiche}"
    )

    # =========================
    # TABLEAU DES NOTES
    # =========================
    y -= 2*cm

    colonnes = ["Disciplines", "Coef", "Nt.classe/20", "Comp/20", "Coef x Moy", "Appréciations", "Signature"]
    x = [2, 6, 8, 10, 12, 15, 18]
    w = [4, 2, 2, 2, 3, 3, 2]

    p.setFont("Helvetica-Bold", 10)
    for i, col in enumerate(colonnes):
        p.rect(x[i]*cm, y, w[i]*cm, 0.8*cm)
        p.drawCentredString((x[i]+w[i]/2)*cm, y+0.25*cm, col)

    y -= 0.8*cm
    p.setFont("Helvetica", 10)

    for m in matieres:
        d = notes_cache[m.id]
        valeurs = [
            m.get_nom_display(),
            m.coefficient,
            round(d['note_classe'],2) if d['note_classe'] else "—",
            d['comp'] if d['comp'] else "—",
            round(d['coef_moy'],2),
            "", ""
        ]
        for i, v in enumerate(valeurs):
            p.rect(x[i]*cm, y, w[i]*cm, 0.7*cm)
            p.drawCentredString((x[i]+w[i]/2)*cm, y+0.2*cm, str(v))
        y -= 0.7*cm

    # =========================
    # LIGNES TOTAUX & MOYENNES
    # =========================
    def ligne(label, valeur):
        nonlocal y
        p.rect(x[0]*cm, y, sum(w[:4])*cm, 0.7*cm)
        p.drawString(x[0]*cm+0.2*cm, y+0.2*cm, label)
        p.rect(x[4]*cm, y, w[4]*cm, 0.7*cm)
        p.drawCentredString((x[4]+w[4]/2)*cm, y+0.2*cm, str(valeur))
        for i in [5,6]:
            p.rect(x[i]*cm, y, w[i]*cm, 0.7*cm)
        y -= 0.7*cm

    ligne("Totaux", round(total_coef_moy,2))
    ligne("Moyenne Semestrielle", moyenne_semestrielle)
    ligne("Moyenne Annuelle", "")

    # =========================
    # TABLEAU CONDUITE / HONNEUR / ASSIDUITE
    # =========================
    y -= 0.2 * cm
    table_height = 6 * 0.7 * cm
    col_width = (width - 3 * cm) / 3
    start_x = 2 * cm

    titres = ["Conduite", "Tableau d'honneur", "Assiduité - Retard"]
    for i in range(3):
        p.rect(start_x + i * col_width, y - table_height, col_width, table_height)
        p.drawCentredString(start_x + i * col_width + col_width / 2, y - 0.4 * cm, titres[i])

    options_conduite = ["Bien", "Passable", "Mal", "Avertissement", "Blâme"]
    options_honneur = ["Inscrit(e)", "Félicitations", "Encouragement", "Non inscrit(e)"]

    yy = y - 1 * cm
    for opt in options_conduite:
        p.rect(start_x + 0.2 * cm, yy, 0.4 * cm, 0.4 * cm)
        p.drawString(start_x + 0.8 * cm, yy + 0.1 * cm, opt)
        yy -= 0.7 * cm

    yy = y - 1 * cm
    for opt in options_honneur:
        p.rect(start_x + col_width + 0.2 * cm, yy, 0.4 * cm, 0.4 * cm)
        p.drawString(start_x + col_width + 0.8 * cm, yy + 0.1 * cm, opt)
        yy -= 0.7 * cm

    # =========================
    # VISA & OBSERVATION
    # =========================
    y = y - table_height - 0.2 * cm
    col_w = (width - 3 * cm) / 2
    h = 3 * cm

    p.rect(2 * cm, y - h, col_w, h)
    p.rect(2 * cm + col_w, y - h, col_w, h)

    p.drawCentredString(2 * cm + col_w / 2, y - h / 2, "Visa des parents")
    p.drawCentredString(2 * cm + col_w + col_w / 2, y - 0.5 * cm, "Observation du Proviseur")

    p.showPage()
    p.save()
    return response





@groupe_requis('Prof')
@login_required(login_url='login')
def classement_classe(request, classe_id):
    # Récupérer la classe
    classe = get_object_or_404(Classe, id=classe_id)
    # Récupérer les élèves de la classe
    eleves = Eleve.objects.filter(classe=classe)

    # Construire le classement
    classement = []
    for eleve in eleves:
        moyenne = eleve.moyenne_generale()
        if moyenne is not None:
            classement.append((eleve, moyenne))

    # Trier du plus élevé au plus faible
    classement.sort(key=lambda x: x[1], reverse=True)

    return render(request, 'core/classement.html', {
        'classe': classe,
        'classement': classement
    })
    
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Eleve

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 🔹 SUPERUSER
            if user.is_superuser:
                return redirect('accueil')

            # 🔹 ÉLÈVE
            if user.groups.filter(name='Eleve').exists():
                return redirect('mes_notes')

            # 🔹 PROFESSEUR
            if user.groups.filter(name='Professeur').exists():
                return redirect('accueil')

            # 🔹 Cas par défaut
            return redirect('accueil')

        else:
            messages.error(request, "Identifiant ou mot de passe incorrect")

    return render(request, 'core/login.html')

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def user_login(request):
    if request.user.is_authenticated:
        return redirect('accueil')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 🔐 SI ÉLÈVE → MES NOTES
            if user.groups.filter(name="Eleve").exists():
                return redirect('mes_notes')

            # 🔐 SI PROF OU ADMIN → ACCUEIL
            return redirect('accueil')

        else:
            messages.error(request, "Identifiants incorrects")

    return render(request, "core/login.html")

from django.shortcuts import render, get_object_or_404, redirect
from .models import Eleve, Matiere, Note

def modifier_notes(request, eleve_id, matiere_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    matiere = get_object_or_404(Matiere, id=matiere_id)

    TYPES = ['I1', 'I2', 'I3', 'D1', 'D2', 'D3', 'C']

    # 🔹 semestre depuis GET ou POST (fallback = 1)
    semestre = request.GET.get('semestre') or request.POST.get('semestre') or 1
    semestre = int(semestre)

    # 🔹 récupérer les notes EXISTANTES DU SEMESTRE
    notes = {}
    for t in TYPES:
        notes[t] = Note.objects.filter(
            eleve=eleve,
            matiere=matiere,
            type_note=t,
            semestre=semestre
        ).first()

    # 🔹 TRAITEMENT DU FORMULAIRE
    if request.method == 'POST':
        for t in TYPES:
            valeur = request.POST.get(t)

            if valeur not in [None, ""]:
                note = Note.objects.filter(
                    eleve=eleve,
                    matiere=matiere,
                    type_note=t,
                    semestre=semestre
                ).first()

                if note:
                    note.valeur = float(valeur)
                    note.save()
                else:
                    Note.objects.create(
                        eleve=eleve,
                        matiere=matiere,
                        type_note=t,
                        valeur=float(valeur),
                        semestre=semestre
                    )

        return redirect('detail_eleve', eleve.id)

    context = {
        'eleve': eleve,
        'matiere': matiere,
        'notes': notes,
        'semestre': semestre
    }

    return render(request, 'core/modifier_note.html', context)

def calculer_rang_dense(moyenne_eleve, moyennes_classe):
    """
    Classement dense avec gestion ex æquo
    Retourne : rang, ex_aequo (True/False)
    """
    moyennes_triees = sorted(moyennes_classe, reverse=True)
    moyennes_uniques = sorted(set(moyennes_triees), reverse=True)

    rang = moyennes_uniques.index(moyenne_eleve) + 1
    ex_aequo = moyennes_triees.count(moyenne_eleve) > 1

    return rang, ex_aequo
