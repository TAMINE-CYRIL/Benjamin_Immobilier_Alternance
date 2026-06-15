# Cahier des charges - Logiciel de veille et d'analyse commerciale

## 1. Contexte et objectifs

Ce cahier des charges definit les specifications d'un logiciel personnalise de veille et d'analyse commerciale pour le pole developpement immobilier de Benjamin Immobilier.

Le logiciel devra permettre de collecter, enrichir, analyser et visualiser des donnees immobilieres issues de multiples sources, notamment le scraping, les APIs et l'open data, afin d'identifier des opportunites foncieres a fort potentiel.

## 2. Module 1 - Scraping d'annonces immobilieres

### 2.1 Objectif

Automatiser la collecte d'annonces sur des plateformes immobilieres comme Leboncoin, SeLoger, Logic-Immo, etc.

### 2.2 Technologies

- Crawl4AI comme moteur de scraping open source.
- Extraction des donnees structurees :
  - prix ;
  - surface ;
  - geolocalisation.
- Mecanismes d'anti-blocage :
  - rotation IP ;
  - rotation des user-agents.
- Frequence de scraping : toutes les 6 a 12 heures.

### 2.3 Contraintes

- Maintenance des scripts en cas de changement de structure HTML des plateformes ciblees.
- Hebergement sur serveur securise, de type VPS ou cloud prive.

## 3. Module 2 - Connexion a des APIs de donnees publiques

### 3.1 Objectif

Enrichir les donnees collectees avec des sources externes, notamment les donnees cadastrales, urbanistiques et publiques.

### 3.2 Sources prevues

- API Pappers Immobilier.
- Geoportail de l'urbanisme :
  - zonage PLU ;
  - contraintes urbanistiques.
- API cadastre.
- OpenData Gouv.
- Fichiers deces INSEE.
- PLUi Aix-en-Provence.

### 3.3 Fonctionnalites

- Association automatique des donnees externes a chaque bien ou terrain detecte.
- Detection d'anomalies ou de signaux faibles, par exemple un terrain libre identifie a la suite d'une succession.

## 4. Module 3 - Interface de recherche et filtres multicriteres

### 4.1 Objectif

Permettre aux utilisateurs de filtrer les opportunites detectees selon des criteres personnalises.

### 4.2 Fonctionnalites

- Filtres multicriteres :
  - zone geographique ;
  - prix ;
  - surface ;
  - type de bien ;
  - constructibilite ;
  - anciennete de publication.
- Affichage des resultats sous forme de liste.
- Affichage des resultats sur une carte interactive, avec Mapbox ou Leaflet.
- Acces a une fiche complete pour chaque opportunite.
- Acces aux documents et liens sources associes.

### 4.3 Specifications techniques

- Frontend : Vue.js ou React.js.
- Backend : Node.js ou Django.
- Base de donnees et moteur de recherche : PostgreSQL avec PostGIS et recherche plein texte indexee.
- Rafraichissement automatique des donnees avec synchronisation quotidienne.

## 5. Intelligence artificielle et analyse predictive

### 5.1 Objectif

Exploiter les donnees collectees et enrichies afin de prioriser les opportunites foncieres et d'assister les equipes dans leur analyse commerciale.

### 5.2 Fonctionnalites

- Classement automatique des opportunites par pertinence selon plusieurs criteres :
  - rentabilite ;
  - rarete ;
  - localisation ;
  - potentiel foncier.
- Agent IA pour la detection d'anomalies, par exemple une incoherence entre le prix et la localisation.
- Generateur automatique de rapport d'opportunite fonciere.

## 6. Architecture logicielle recommandee

L'architecture recommandee repose sur une application web modulaire, capable d'integrer progressivement de nouvelles sources de donnees et de nouveaux outils d'analyse.

### 6.1 Composants principaux

- Interface web : Vue.js ou React.js.
- Backend API : Node.js ou Django.
- Scraping : Crawl4AI.
- Enrichissement : Python et APIs REST.
- Base de donnees et moteur de recherche : PostgreSQL avec PostGIS et recherche plein texte indexee.

### 6.2 Flux de donnees

1. Collecte automatisee des annonces immobilieres.
2. Normalisation et stockage des donnees collectees.
3. Enrichissement via APIs publiques et donnees open data.
4. Indexation plein texte et geographique dans PostgreSQL.
5. Analyse, scoring et detection d'anomalies.
6. Visualisation dans l'interface web.

## 7. Securite, accessibilite et evolutivite

### 7.1 Securite

- Hebergement cloud securise, par exemple OVH, AWS ou equivalent, derriere un reverse proxy HTTPS.
- Acces au site uniquement en HTTPS en production, avec HSTS et redirection HTTP vers HTTPS.
- Authentification des utilisateurs :
  - tokens d'acces signes ;
  - cookies `HttpOnly`, `Secure`, `SameSite=Lax` ou `Strict`, avec duree de vie configurable ;
  - réinitialisation de mot de passe par email avec token a usage unique, expiration et audit ;
  - SSO ou MFA a prevoir en phase 2 si l'application est exposee sur Internet.
- Tout environnement de production doit refuser de demarrer avec des secrets par defaut ou trop faibles.
- Protection CSRF des routes mutantes, car l'authentification repose sur des cookies.
- Principe du moindre privilege pour les fonctions d'exploitation, imports, exports, suppressions et parametres.
- Protection des endpoints API par authentification, validation stricte des parametres et en-tetes HTTP de securite.
- Journalisation des actions sensibles dans un journal d'audit non modifiable depuis l'interface :
  - connexions et echecs de connexion ;
  - consultations sensibles ;
  - exports ;
  - lancements d'automatisations ;
  - changements d'utilisateurs et de droits.
- Gestion des secrets :
  - fichier `.env` exclu du versionnement ;
  - modele `.env.example` sans secret reel ;
  - rotation des secrets en cas d'incident ;
  - analyse de secrets avant livraison.
- Analyse des dependances Python et npm avant mise en production.
- Sauvegardes PostgreSQL chiffrees, stockees separement, avec retention definie et test de restauration regulier.
- Verification TLS activee pour les API externes ; aucun contournement TLS ne doit etre autorise en production.
- Supervision minimale :
  - alertes sur echecs de connexion repetes ;
  - erreurs API ;
  - automatisations echouees ;
  - sauvegardes absentes ;
  - espace disque faible.

### 7.2 Conformite RGPD

- Gestion conforme des donnees personnelles.
- Minimisation des donnees collectees.
- Conservation limitee des donnees sensibles.
- Tracabilite des traitements.
- Registre des traitements de donnees.
- Purge automatique des donnees obsoletes.
- Procedure d'export ou de suppression sur demande legitime.

### 7.3 Evolutivite

- Systeme modulaire permettant l'integration future de nouvelles sources de donnees.
- Architecture extensible pour ajouter de nouveaux modules d'analyse.
- Separation claire entre collecte, enrichissement, stockage, analyse et visualisation.
