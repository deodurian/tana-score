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
Accès : http://localhost:5000
