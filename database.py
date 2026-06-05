import sqlite3
import json
from datetime import datetime

DB_FILE = 'tana.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # On crée une table pour stocker les soumissions
    # On stocke toutes les données brutes dans une colonne JSON par simplicité,
    # et on extrait le score (T) et le pourcentage pour les requêtes rapides
    conn.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            score_t REAL NOT NULL,
            pourcentage REAL NOT NULL,
            raw_data TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_submission(t_score, pourcentage, raw_data_dict):
    conn = get_db_connection()
    raw_data_json = json.dumps(raw_data_dict)
    conn.execute(
        'INSERT INTO submissions (score_t, pourcentage, raw_data) VALUES (?, ?, ?)',
        (t_score, pourcentage, raw_data_json)
    )
    conn.commit()
    conn.close()

def get_stats_from_db(user_score=None):
    """
    Calcule les statistiques globales depuis SQLite de manière très rapide.
    """
    conn = get_db_connection()
    
    # Récupérer le nombre total et la moyenne
    stats_row = conn.execute('''
        SELECT COUNT(*) as total, AVG(score_t) as moyenne 
        FROM submissions
    ''').fetchone()
    
    total = stats_row['total'] or 0
    moyenne = stats_row['moyenne'] or 0
    
    if total == 0:
        conn.close()
        return {
            'total': 0,
            'moyenne': 0,
            'mediane': 0,
            'percentile': 0
        }

    # Calcul de la médiane via SQLite (tri et pagination)
    offset = (total - 1) // 2
    limit = 2 if total % 2 == 0 else 1
    
    median_rows = conn.execute(f'''
        SELECT score_t FROM submissions 
        ORDER BY score_t ASC 
        LIMIT {limit} OFFSET {offset}
    ''').fetchall()
    
    if len(median_rows) == 2:
        mediane = (median_rows[0]['score_t'] + median_rows[1]['score_t']) / 2
    else:
        mediane = median_rows[0]['score_t']

    # Calcul du percentile
    percentile = 0
    if user_score is not None:
        lower_count_row = conn.execute('''
            SELECT COUNT(*) as lower_count 
            FROM submissions 
            WHERE score_t < ?
        ''', (user_score,)).fetchone()
        lower_count = lower_count_row['lower_count']
        percentile = (lower_count / total) * 100

    conn.close()
    
    return {
        'total': total,
        'moyenne': round(moyenne, 2),
        'mediane': round(mediane, 2),
        'percentile': round(percentile, 2)
    }

def get_all_submissions_for_export():
    """
    Récupère toutes les soumissions pour l'export CSV.
    """
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM submissions ORDER BY timestamp DESC').fetchall()
    conn.close()
    
    results = []
    for row in rows:
        # Reconstruire un dictionnaire plat
        data = json.loads(row['raw_data'])
        data['Date_Soumission'] = row['timestamp']
        data['T'] = row['score_t']
        data['pourcentage'] = row['pourcentage']
        results.append(data)
        
    return results

def get_recent_submissions(limit=10):
    conn = get_db_connection()
    rows = conn.execute(f'SELECT * FROM submissions ORDER BY timestamp DESC LIMIT {limit}').fetchall()
    conn.close()
    
    results = []
    for row in rows:
        data = json.loads(row['raw_data'])
        data['timestamp'] = row['timestamp']
        data['T'] = row['score_t']
        data['pourcentage'] = row['pourcentage']
        results.append(data)
    return results

def get_distribution():
    conn = get_db_connection()
    # On récupère tous les scores pour calculer la distribution
    rows = conn.execute('SELECT score_t FROM submissions').fetchall()
    conn.close()
    
    scores = [row['score_t'] for row in rows]
    distribution = {
        '0-10': sum(1 for s in scores if s <= 10),
        '11-30': sum(1 for s in scores if 10 < s <= 30),
        '31-80': sum(1 for s in scores if 30 < s <= 80),
        '81-220': sum(1 for s in scores if 80 < s <= 220),
        '221-500': sum(1 for s in scores if 220 < s <= 500),
        '501+': sum(1 for s in scores if s > 500)
    }
    return distribution
