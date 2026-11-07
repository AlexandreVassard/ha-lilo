# Prêt à Pousser Lilo pour Home Assistant

Intégration Home Assistant pour piloter en Bluetooth le potager d'intérieur
**Lilo** de Prêt à Pousser : intensité de la lampe et horaires d'éclairage,
sans l'application officielle ni le cloud.

Elle vise les Lilo récents, qui annoncent le service BLE
`c9d9bfe1-324c-4b79-bbaf-8a473e6540ec` (nom Bluetooth `Lilo…`). Les anciens
modèles (service `53e11631-…`, gérés par
[assistant-lilo](https://github.com/jzarca01/assistant-lilo)) ne sont pas pris
en charge.

## Entités

| Entité | Rôle |
|---|---|
| `light.lilo…` | Lampe : allumée/éteinte et intensité (0–100 % côté Lilo) |
| `select.lilo…_mode` | Mode automatique ou manuel |
| `time.lilo…_allumage` | Heure d'allumage quotidienne |
| `time.lilo…_extinction` | Heure d'extinction quotidienne |
| `button.lilo…_actualiser` | Relit le Lilo (après un changement fait dans l'application) |

En mode automatique, le Lilo rétablit lui-même ses horaires : modifier une
heure fait donc passer en mode manuel, comme dans l'application. Choisir
*Automatique* applique le préréglage de l'application (100 %, 06:00–22:00).

Les LED du Lilo clignotent à chaque connexion Bluetooth. L'intégration ne
l'interroge donc pas en continu ; elle ne s'y connecte que :

- au démarrage de Home Assistant ;
- à chaque modification faite depuis Home Assistant ;
- une fois par jour, une minute après l'heure d'extinction (ou d'allumage,
  au choix dans les options de l'intégration), pour que le clignotement passe
  inaperçu ;
- sur appui du bouton *Actualiser*.

Un changement fait dans l'application officielle n'apparaît donc dans Home
Assistant qu'au relevé suivant. À chaque connexion, l'horloge interne du Lilo
est recalée sur celle de Home Assistant si elle a dérivé de plus d'une minute.

« Allumée » signifie que la lampe est active avec une intensité non nulle : le
Lilo ne s'éclaire réellement qu'entre l'heure d'allumage et l'heure
d'extinction.

Les modes de l'application ne sont que des préréglages de ces valeurs :

| Application | Intensité | Allumage | Extinction |
|---|---|---|---|
| Mode automatique | 100 | 06:00 | 22:00 |
| Éteindre le potager | 0 | 00:00 | 23:59 |
| Rallumer | 100 | 00:00 | 23:59 |
| Mode manuel | au choix | au choix | au choix |

## Installation

### HACS

1. HACS → menu ⋮ → *Dépôts personnalisés* → ajouter
   `https://github.com/AlexandreVassard/ha-lilo`, catégorie *Intégration*.
2. Installer **Prêt à Pousser Lilo**, puis redémarrer Home Assistant.

### Manuelle

Copier `custom_components/lilo` dans le dossier `config/custom_components/` de
Home Assistant, puis redémarrer.

### Configuration

Le Lilo est découvert automatiquement par l'intégration Bluetooth (adaptateur
local ou proxy ESPHome) : Paramètres → Appareils et services → *Découvert*. On
peut aussi l'ajouter à la main via *Ajouter une intégration* → *Prêt à Pousser
Lilo*.

Le Lilo n'accepte qu'une connexion Bluetooth à la fois. L'intégration se
connecte brièvement puis se déconnecte, mais tant que l'application officielle
est ouverte, Home Assistant ne peut pas joindre le Lilo.

## Protocole

Toutes les caractéristiques appartiennent au service
`c9d9bfe1-324c-4b79-bbaf-8a473e6540ec` et suivent le motif
`c9d9bfXX-324c-4b79-bbaf-8a473e6540ec`.

| XX | Accès | Contenu |
|---|---|---|
| `e2` | lecture, écriture, notification | Horloge, secondes depuis minuit (uint32 LE) |
| `e3` | lecture, écriture | Inconnu (`0xc3` observé) |
| `e4` | lecture, écriture | Mode (uint8) : `0xc3` manuel, `0xb2` automatique |
| `e5`, `e6` | lecture, écriture | Intensité 0–100 (uint8), 0 = éteint |
| `e7`, `e8` | lecture, écriture | Allumage, secondes depuis minuit (uint32 LE) |
| `e9`, `ea` | lecture, écriture | Extinction, secondes depuis minuit (uint32 LE) |
| `eb` | lecture | Inconnu (`0x06` observé) |
| `ec` | lecture, écriture | Inconnu (`0` observé) |

Chaque réglage est stocké en double, et l'application écrit les deux copies.
`tools/snapshot.sh` relève toutes ces valeurs avec `bluetoothctl`, ce qui aide
à décoder le reste du protocole :

```sh
ssh homeassistant 'bash -s' < tools/snapshot.sh ED:E7:3E:59:7D:D6
```
