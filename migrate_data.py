import json
import os
import database
from google_sheets_utils import get_all_data_from_sheets
from TANA_code import calculer_T

def migrate():
    print("Initialisation de la base de données...")
    database.init_db()
    
    print("Récupération des données depuis Google Sheets...")
    try:
        data = get_all_data_from_sheets()
        if not data:
            print("Aucune donnée ou erreur Google Sheets, essai de données.json...")
            if os.path.exists('données.json'):
                with open('données.json', 'r') as f:
                    data = json.load(f)
    except Exception as e:
        print(f"Erreur lors de l'accès à Google Sheets: {e}")
        print("Essai de données.json...")
        if os.path.exists('données.json'):
            with open('données.json', 'r') as f:
                data = json.load(f)
        else:
            data = []

    if not data:
        print("Aucune donnée à migrer.")
        return

    print(f"{len(data)} entrées trouvées. Migration en cours...")
    
    success = 0
    errors = 0
    for i, entry in enumerate(data):
        try:
            # Vérifier si T ou pourcentage est déjà présent, sinon recalculer
            t_score = entry.get('T')
            pourcentage = entry.get('pourcentage')
            
            if not t_score or not pourcentage:
                t_score, pourcentage = calculer_T(entry)
                entry['T'] = t_score
                entry['pourcentage'] = pourcentage
            else:
                t_score = float(t_score)
                # Le pourcentage peut avoir un '%' dans Google Sheets
                if isinstance(pourcentage, str) and '%' in pourcentage:
                    pourcentage = float(pourcentage.replace('%', ''))
                else:
                    pourcentage = float(pourcentage)
            
            database.insert_submission(t_score, pourcentage, entry)
            success += 1
            if success % 10 == 0:
                print(f"{success} entrées migrées...")
        except Exception as e:
            print(f"Erreur lors de la migration de la ligne {i}: {e}")
            errors += 1

    result_msg = f"Migration terminée ! Succès: {success}, Erreurs: {errors}"
    print(result_msg)
    return result_msg
if __name__ == '__main__':
    migrate()
