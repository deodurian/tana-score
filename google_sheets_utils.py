import gspread 
from oauth2client.service_account import ServiceAccountCredentials 

def enregistrer_dans_google_sheet(donnees):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
    'tana-461711-d81eb85d76fb.json', scope
    )
    client = gspread.authorize(creds)

    # Ouvre la feuille par son ID (prends l'ID dans l'URL du Google Sheet)
    sheet = client.open_by_key("15sMF5fVDLo-ROM_sFKcpuSdAzg2YyWh_mX2bsxLowo8").sheet1

    # Ajoute une ligne avec les données (adapter l'ordre si besoin)
    sheet.append_row([
    donnees.get("sexe", ""),
    donnees.get("age", ""),
    donnees.get("ex", ""),
    donnees.get("bodycount", ""),
    donnees.get("instagram", ""),
    donnees.get("abonnes", ""),
    donnees.get("premier", ""),
    donnees.get("trompe", "non"),
    donnees.get("plaisir", "non"),
    donnees.get("refaire", "non"),
    donnees.get("T")
    ])
    