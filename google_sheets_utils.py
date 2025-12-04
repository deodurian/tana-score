import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

def enregistrer_dans_google_sheet(donnees):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        # 1. Essayer de charger depuis le fichier (Local)
        json_file = 'tana-461711-d81eb85d76fb.json'
        
        if os.path.exists(json_file):
            creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
        
        # 2. Sinon, essayer depuis une variable d'environnement (Production)
        elif os.environ.get('GOOGLE_CREDENTIALS_JSON'):
            import json
            creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON'))
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            
        else:
            raise Exception("Aucun fichier de credentials ni variable d'environnement trouvés.")

        client = gspread.authorize(creds)

        sheet = client.open_by_key("15sMF5fVDLo-ROM_sFKcpuSdAzg2YyWh_mX2bsxLowo8").sheet1

        # Vérifier si la feuille est vide (cellule A1 vide)
        if sheet.cell(1, 1).value == '':
            print("Feuille vide, ajout des en-têtes.")
            sheet.append_row(list(donnees.keys()))

        header = sheet.row_values(1)
        print("En-tête trouvé dans la feuille :", header)
        print("Données reçues :", donnees)

        row = [donnees.get(col, "") for col in header]
        print("Ligne à insérer :", row)

        sheet.append_row(row)
        print("Données ajoutées avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans Google Sheet : {e}")

def get_all_data_from_sheets():
    """
    Récupère toutes les données depuis Google Sheets.
    Retourne une liste de dictionnaires (comme données.json)
    """
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        # Authentification (même logique que enregistrer_dans_google_sheet)
        json_file = 'tana-461711-d81eb85d76fb.json'
        
        if os.path.exists(json_file):
            creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
        elif os.environ.get('GOOGLE_CREDENTIALS_JSON'):
            import json
            creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON'))
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            raise Exception("Aucun fichier de credentials ni variable d'environnement trouvés.")

        client = gspread.authorize(creds)
        sheet = client.open_by_key("15sMF5fVDLo-ROM_sFKcpuSdAzg2YyWh_mX2bsxLowo8").sheet1

        # Récupérer toutes les données
        all_values = sheet.get_all_values()
        
        if not all_values:
            return []
        
        # Première ligne = en-têtes
        headers = all_values[0]
        
        # Convertir en liste de dictionnaires
        data = []
        for row in all_values[1:]:  # Ignorer la ligne d'en-tête
            entry = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    entry[header] = row[i]
                else:
                    entry[header] = ""
            data.append(entry)
        
        return data
        
    except Exception as e:
        print(f"Erreur lors de la lecture de Google Sheets : {e}")
        return []