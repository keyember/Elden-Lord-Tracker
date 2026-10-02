# Elden Ring Tracker - v0.2.0 consolidee
## Installation
Python 3.10+ avec Tkinter et lanceur py sur Windows.
Fermer l'ancien tracker ET l'ancien lancer_overlay avant de lancer cette version.
Extraire toute l'archive dans un NOUVEAU dossier. Lancer lancer.bat.
Ne pas appliquer les anciens scripts de mise a jour a cette version.
Aucune dependance externe pour l'utilisation en Python.

## Utilisation
Le fichier est detecte si un seul profil Steam existe ; sinon le choisir.
Les noms sont charges automatiquement depuis une copie dans un thread de travail.
Choisir le personnage puis Demarrer. Changer le choix et appliquer pour changer de slot.
Arreter suspend le suivi et marque les donnees comme anciennes.
Le serveur overlay demarre avec le tracker : plus besoin de lancer_overlay.bat.
OBS : source Navigateur, URL http://127.0.0.1:8765, largeur 460, hauteur 850.
Des erreurs de port peuvent indiquer qu'un ancien serveur tourne encore.
La copie est tentee toutes les 2 secondes, sauf si un cycle dure plus longtemps.

## Donnees et logs
%LOCALAPPDATA%\EldenRingTracker contient diagnostic.json, runtime.json,
temp_save.sl2, tracker.log et obs/.
Les fichiers existants sont reutilises ; aucune sauvegarde de jeu n'est modifiee.
Le diagnostic peut etre remplace par le slot nouvellement selectionne.
Il n'existe PAS encore d'historique de challenge a conserver dans cette version.
Pour eviter les conflits, lancer une seule instance du tracker.

## Limites
Layout PC teste sur la sauvegarde fournie, pas sur toutes les versions du jeu.
Checksum du slot et du resume verifie ; pas de garantie de coherence de tout le fichier.
Noms vides : nom indisponible, pas preuve d'un slot libre.
Temps lu dans le resume : doit etre compare au menu du jeu, pas un chronometre independant.
Morts, boss, tentatives, challenge : N/A ; historique indisponible.
L'overlay marque les releves anciens, les erreurs et l'arret du suivi.
Le design a ete reconstruit dans le meme esprit ; des differences mineures sont possibles.
Interface, serveur et build doivent etre testes sur Windows.

## Tests et exe
py -3 -m unittest discover -s tests -v
build_windows.bat cree un environnement et installe PyInstaller (Internet requis).
Le resultat est un dossier portable dans dist/EldenRingTracker, avec les assets overlay.
Aucun exe precompile n'est inclus. Conserver tout le dossier distribue.
# Elden-Lord-Tracker
