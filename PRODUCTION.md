# Mise en production

## Prérequis

- PostgreSQL avec PostGIS, accessible uniquement depuis l'application et les tâches d'exploitation.
- Python 3.13 et Node.js LTS.
- Un reverse proxy HTTPS avec un certificat valide.
- Un serveur SMTP TLS.
- Un stockage de sauvegarde distinct du serveur applicatif et une clé GPG de chiffrement.

## Préparation

1. Copier `.env.production.example` vers `.env` et remplacer toutes les valeurs d'exemple.
2. Installer les dépendances Python : `python -m pip install -r requirements.txt`.
3. Installer Chromium : `python -m playwright install chromium`.
4. Créer les tables : `python database/create_tables.py`.
5. Appliquer les migrations : `python database/migrations.py`.
6. Créer le premier compte : `python database/create_user.py utilisateur@example.com`.
7. Construire le frontend dans `apps/web` avec `npm ci` puis `npm run build`.

## Validation bloquante

Exécuter depuis la racine du projet :

```powershell
python -m services.jobs.validate_production
python -m pytest -q
python -m ruff check . --exclude apps/web/node_modules,venv
python -m pip_audit -r requirements.txt
cd apps/web
npm test -- --run
npm run build
npm run audit
```

La validation production refuse notamment les secrets d'exemple, les URL HTTP, les cookies non sécurisés, les migrations manquantes, une base inaccessible, l'absence d'utilisateur actif et un frontend non construit.

## Exécution

Le reverse proxy sert `apps/web/dist` et transmet `/api` à Uvicorn. L'API doit écouter sur une interface privée :

```powershell
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1
```

Conserver `TRUST_PROXY=false` si l'API est accessible directement. Si `TRUST_PROXY=true`, le pare-feu doit interdire tout accès qui contourne le reverse proxy.

Sondes de supervision :

- vivacité : `GET /api/health/live` ;
- disponibilité de la base : `GET /api/health/ready`.

## Automatisation et sauvegardes

- Installer l'automatisation avec `scripts/install_windows_task.ps1`.
- Lancer `scripts/backup_database.ps1` avec `-BackupDir` vers un stockage distinct, `-GpgRecipient` et `-RestrictAcl`.
- Tester régulièrement une restauration dans une base isolée avec `scripts/restore_database.ps1`.
- Superviser les échecs d'automatisation, les réponses 503 de la sonde de disponibilité, l'absence de sauvegarde récente et l'espace disque.
