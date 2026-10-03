# Roadmap - 2 octobre 2026 (mise à jour)

## ✅ A - Stabiliser la base : TERMINÉ

- [x] Consolidation du code
- [x] Registre 207 bosses (SOURCE_BANK généré automatiquement)
- [x] Générateur d'associations fonctionnel
- [x] Lecteur de catalogue mis à jour (accepte ast.DictComp)
- [x] Overlay en temps réel fonctionnel
- [x] Combat tracking (tentatives, morts par boss)

**Critères validés** : temps concordant avec le jeu, projet cohérent sans patchs, overlay opérationnel.

## ✅ B - Lire les morts : TERMINÉ

- [x] Compteur de morts pour le slot actif
- [x] Vérification hausse sans double comptage
- [x] Intégration avec BossReader et DeathSession

**Critères validés** : morts observées en temps réel, persistantes après redémarrage.

## 🟡 C - Challenges : EN COURS

- [x] Créer un challenge
- [x] Choisir un challenge par slot
- [x] Reprendre un challenge
- [ ] Renommer un challenge
- [ ] Archiver les challenges terminés
- [ ] Indépendance des historiques après redémarrage (à tester)

**Reste** : interface d'archivage, validation complète de la persistance.

## 🟡 D - Boss vaincus : EN COURS

- [x] Event IDs configurés (flags +2005)
- [x] Lecture des flags de victoire
- [x] Affichage dans l'overlay
- [ ] Vérifier emplacement réel dans la mémoire (audit complet)
- [ ] Contrôles vaincus/vivants documentés pour tous les boss

**Reste** : audit des 207 flags, validation terrain.

## 🟡 E - Tentatives : EN COURS

- [x] Morts attribuées au boss suivi
- [x] Compteur de tentatives par combat
- [ ] Hausses multiples, reprise, baisse du compteur (à tester)
- [ ] Boss déjà vaincu au début : tentatives inconnues (gestion N/A)
- [ ] Ordre automatique de liste (convention, pas détection)

**Reste** : tests intensifs en conditions réelles.

## ✅ F - Overlay intégré : TERMINÉ

- [x] Serveur WebSocket intégré
- [x] Transmission des données (chrono, morts, boss, combat)
- [x] Interface compacte fonctionnelle
- [x] Changement de challenge sur la même source OBS

**Critères validés** : un lanceur, overlay à jour en temps réel.

## 🟡 G - Apparence : EN COURS

- [x] Lisibilité de base
- [x] Dimensions fonctionnelles
- [ ] Ornements, animations (CSS à améliorer)
- [ ] Validation dans la scène OBS (tests à faire)

**Reste** : polish visuel, tests OBS.

## 🟡 H - Windows : EN COURS

- [x] Script de build (`build_windows.bat`)
- [ ] Exe testé sans Python installé
- [ ] Stockage testé (chemins absolus vs relatifs)
- [ ] Livraison portable cohérente

**Reste** : build PyInstaller, tests sur machine sans Python.

## Règles

- Slot choisi explicitement
- Plusieurs challenges par slot
- Inconnus N/A
- Lecture en erreur : données anciennes
- Ne pas soustraire silencieusement les tentatives si les morts baissent
- Demander confirmation ou vérifier la session
- Pas de dates promises avant validation des lectures binaires

## Prochaines priorités

1. **Phase C** : Finaliser l'archivage des challenges
2. **Phase D** : Audit complet des 207 flags de victoire
3. **Phase E** : Tests intensifs de combat tracking
4. **Phase H** : Build Windows portable
