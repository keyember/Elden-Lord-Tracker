# Roadmap — Elden Lord Tracker

## 🎯 Vision

**Elden Lord Tracker** est un outil de suivi Elden Ring pensé pour les challenges,
le suivi de progression et l'intégration OBS.

Priorité : construire d'abord un produit propre et agréable à utiliser,
puis fiabiliser les données et la détection des boss.

---

## 🟢 0 — Rebranding : Elden Lord Tracker

- [x] Nom du projet / repository : Elden Lord Tracker
- [ ] Remplacer « Elden Ring Tracker » dans l'interface
- [ ] Harmoniser README et documentation
- [ ] Identité visuelle cohérente
- [ ] Icône / logo de l'application
- [ ] Nettoyer les anciens intitulés et références

---

## 🟡 1 — Refonte de l'interface

- [ ] Repenser la fenêtre principale
- [ ] Hiérarchie visuelle claire
- [ ] Présentation dédiée au challenge actif
- [ ] Gestion des personnages / slots plus claire
- [ ] États visuels : actif, arrêté, erreur, données anciennes
- [ ] Design inspiré d'Elden Ring sans surcharger l'interface
- [ ] Icônes et éléments graphiques
- [ ] Animations et transitions légères
- [ ] Refonte des fenêtres et dialogues
- [ ] Réduire les éléments techniques visibles par l'utilisateur
- [ ] Validation Windows

---

## 🟡 2 — Refonte du système de Challenges

### Gestion

- [x] Créer un challenge
- [x] Sélectionner un challenge actif
- [x] Reprendre un challenge
- [ ] Nommer / renommer un challenge
- [ ] Dupliquer un challenge
- [ ] Archiver un challenge
- [ ] Restaurer un challenge archivé
- [ ] Supprimer un challenge
- [ ] Persistance complète après fermeture / redémarrage

### Données

- [x] Historique indépendant par challenge
- [x] Personnage / slot associé
- [x] Date de création
- [x] Statut du challenge
- [ ] Temps de jeu
- [ ] Boss vaincus
- [ ] Morts
- [ ] Tentatives
- [ ] Progression
- [ ] Historique des sessions

---

## 🟡 3 — Progression et statistiques

- [ ] Progression globale des boss
- [ ] Affichage X / total boss
- [ ] Pourcentage de progression
- [ ] Boss vaincus / restants
- [ ] Morts totales
- [ ] Tentatives totales
- [ ] Temps de run
- [ ] Statistiques par boss
- [ ] Statistiques par challenge
- [ ] Historique des sessions
- [ ] Résumé d'un challenge terminé

---

## 🟡 4 — Overlay

- [ ] Refonte graphique de l'overlay
- [ ] Cohérence visuelle avec l'application
- [ ] Meilleure gestion des images personnalisées
- [ ] Masquer le placeholder « Boss » lorsqu'une image personnalisée est présente
- [ ] Animations d'apparition / disparition
- [ ] Transition lors d'un changement de boss
- [ ] Affichage propre morts / tentatives
- [ ] Affichage de la progression du challenge
- [ ] États : combat, boss vaincu, aucun boss
- [ ] Paramètres d'affichage configurables
- [ ] Validation finale dans OBS

---

## 🔴 5 — Fiabilisation de la détection des boss

> Certains boss ne sont actuellement pas détectés correctement et n'apparaissent
> donc pas dans l'overlay. Cette phase sera traitée après la refonte du produit.

- [ ] Identifier tous les boss non détectés
- [ ] Identifier la cause de chaque problème
- [ ] Vérifier les Event IDs / flags
- [ ] Vérifier les associations boss ↔ données mémoire
- [ ] Tester les boss problématiques en jeu
- [ ] Corriger les associations
- [ ] Vérifier les faux positifs
- [ ] Vérifier les boss déjà vaincus
- [ ] Valider les 207 boss
- [ ] Documenter les exceptions techniques éventuelles

**Objectif :** tous les boss du registre doivent être correctement détectables
ou explicitement documentés comme exception.

---

## 🟡 6 — Combat Tracking

- [x] Morts attribuées au boss suivi
- [x] Compteur de tentatives par combat
- [ ] Validation des hausses multiples
- [ ] Validation après reprise
- [ ] Gestion d'une baisse du compteur
- [ ] Boss déjà vaincu au démarrage → tentatives inconnues / N/A
- [ ] Reprise après fermeture
- [ ] Reprise après crash
- [ ] Tests réels sur plusieurs boss

---

## 🟡 7 — Windows / Distribution

- [x] Script de build Windows
- [ ] Build PyInstaller propre
- [ ] Test sans Python installé
- [ ] Test sur installation vierge
- [ ] Gestion des chemins relatifs
- [ ] Gestion des données utilisateur
- [ ] Lanceur propre
- [ ] Livraison portable cohérente
- [ ] Nettoyage des outils de diagnostic inutiles

---

## ⚪ 8 — Documentation / Release

- [ ] README complet
- [ ] Guide d'installation
- [ ] Guide OBS
- [ ] Guide Challenges
- [ ] FAQ
- [ ] Changelog propre
- [ ] Documentation des limitations connues
- [ ] Release v1.0.0
- [ ] Package Windows final

---

# Ordre de priorité actuel

1. **Rebranding + identité Elden Lord Tracker**
2. **Refonte complète de l'interface**
3. **Refonte du système de Challenges**
4. **Progression et statistiques**
5. **Refonte / polish de l'overlay**
6. **Correction de la détection des boss**
7. **Finalisation du Combat Tracking**
8. **Build Windows + distribution**
9. **Documentation + v1.0**

---

# Règles

- Un challenge possède son propre historique.
- Les données de challenges différents ne sont jamais fusionnées automatiquement.
- Les données inconnues restent `N/A`.
- Une lecture en erreur conserve les dernières données valides et signale leur ancienneté.
- Les tentatives ne sont jamais soustraites silencieusement si les données diminuent.
- Les changements de personnage / save doivent être explicitement associés à un nouveau challenge lorsque nécessaire.
- Les corrections de détection des boss seront validées en conditions réelles avant d'être considérées comme terminées.
