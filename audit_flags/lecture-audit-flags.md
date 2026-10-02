# Audit en lot des flags - 2 octobre 2026

Base du tracker : commit 276e455050acc983801a849c7cb741c80415bd5f.
Configuration de 207 rencontres reconstruite depuis le commit et verifiee a l'identique par son empreinte Git : 98ec464b89f6c3002501c8e735cf4a6a67279043.

## Resultats

- 204 entrees de flags de victoire extraites de la liste nommee. Ce chiffre n'est pas un total de boss distincts.
- 191 cles numeriques retrouvees avec un libelle dans la reference.
- 2 cles retrouvees avec le libelle non renseigne XXXX.
- 3 alias historiques : Margit, Godrick et Radahn. Les IDs de reference sont fournis, mais leurs flag_id actuels dans boss_catalog.json ne sont pas verifies ici.
- 11 cles absentes de cette reference.

## Perimetre et securite

Cette analyse rapproche les IDs encodes dans les cles de combat_catalog.json. Elle ne confirme pas tous les noms de boss du catalogue ni les valeurs observees en jeu. L'API GitHub n'a pas fourni le diff complet de boss_catalog.json.

Aucun flag n'a ete corrige, aucun suivi n'a ete active, aucun historique n'a ete modifie et aucun commit n'a ete publie.

La liste nommee sert surtout aux victoires. La reference generale distingue des plages persistantes et reinitialisables : cela ne suffit pas a choisir un flag de combat pour chaque boss. La reference traduite et detaillee est repertoriee par le wiki, mais son contenu n'a pas ete recupere.

## Signaux de combat deja verifies dans les scripts locaux

- Assassin des Couteaux noirs, Deathtouched Catacombs : 30112805, victoire 30110800, script m30_11_00_00.evs.py.
- Duelliste gardien du tombeau, Murkwater Catacombs : 30042805, victoire 30040800, script m30_04_00_00.evs.py.

Les deux flags figurent dans la condition d'activation de l'IA avec la presence du joueur dans l'arene. La remise a zero via la fonction commune et le suivi effectif en jeu restent a verifier. Le CSV les presente comme propositions de source, pas comme suivis actives.

## Points a examiner

- flag_1039430800
- flag_1036480800
- flag_1037420800
- flag_1036450800
- flag_1038510800
- flag_1042550800
- flag_1039510800
- flag_1044530800
- flag_30200800
- flag_12030390
- flag_2049440800

Exemples de differences non appliquees : flag_1036450800 dans la configuration, tandis que la reference contient 1036450340 ; flag_30200800 dans la configuration, tandis que la reference contient 30200810. Ces differences ne justifient pas une correction automatique.

## Sources

Liste nommee : https://soulsmodding.com/doku.php?id=er-refmat:event-flag-list
Reference generale : https://soulsmods.github.io/elden-ring-eventparam/
Index de la reference detaillee : https://soulsmodding.wikidot.com/reference:main
Scripts vanilla : Grimrukh/soulstruct-vanilla, revision e6de1b79370755152f4f89c4a106a2d67c9ae674.
