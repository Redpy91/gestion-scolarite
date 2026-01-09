from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Classe, Matiere


@receiver(post_save, sender=Classe)
def creer_matieres_par_defaut(sender, instance, created, **kwargs):
    if created:
        matieres = [
            'MATH', 'FR', 'HG', 'PC', 'SVT',
            'ANG', 'EPS', 'PHILO'
        ]

        for nom in matieres:
            Matiere.objects.get_or_create(
                nom=nom,
                classe=instance,
                defaults={
                    'coefficient': 1  # coefficient fixe par défaut
                }
            )
