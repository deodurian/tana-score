# TANA Score

Application web de quiz pour calculer le score TANA basé sur des questions personnelles.

## Fonctionnalités
- Quiz interactif avec questions conditionnelles
- Calcul automatique du score et pourcentage
- Envoi des résultats vers Google Sheets
- Génération d'image PNG du résultat (1080x1080)
- Design responsive avec animations

## Structure
- `tana.py` : Application Flask principale
- `TANA_code.py` : Logique de calcul du score
- `google_sheets_utils.py` : Intégration Google Sheets
- `templates/` : Pages HTML (accueil, quiz, résultats)
- `static/` : CSS, JavaScript, images

## Démarrage
```bash
pip install -r requirements.txt
python tana.py
```
Accès : http://localhost:5002

## Configuration Dashboard (Production)
Variables d'environnement requises sur Render :
- `GOOGLE_CREDENTIALS_JSON` : Contenu du fichier JSON des credentials Google
- `DASHBOARD_SECRET_URL` : Token secret pour l'URL du dashboard (ex: `xyz789abc`)
- `DASHBOARD_PASSWORD` : Mot de passe pour accéder au dashboard

Accès dashboard : `https://votre-site.com/dashboard/<DASHBOARD_SECRET_URL>`

