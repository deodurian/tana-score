import gspread
from oauth2client.service_account import ServiceAccountCredentials

def enregistrer_dans_google_sheet(donnees):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'tana-461711-d81eb85d76fb.json', scope
        )
        client = gspread.authorize(creds)

        sheet = client.open_by_key("15sMF5fVDLo-ROM_sFKcpuSdAzg2YyWh_mX2bsxLowo8").sheet1

        # Vérifier si la feuille est vide (cellule A1 vide)
        if sheet.cell(1, 1).value == '':
            print("Feuille vide, ajout des en-têtes.")
            sheet.append_row(list(donnees.keys()))

        header = list(donnees.keys())
        row = list(donnees.values())

        print("Clés envoyées :", header)
        print("Valeurs envoyées :", row)

        sheet.append_row(header)
        sheet.append_row(row)
        print("Données ajoutées avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans Google Sheet : {e}")