import os
import json
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

def is_postgres():
    return DATABASE_URL is not None and DATABASE_URL.startswith("postgres")

if is_postgres():
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3

DB_FILE = 'tana.db'

def get_db_connection():
    if is_postgres():
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(conn, query, params=(), commit=False, fetchone=False, fetchall=False):
    """Exécute une requête en s'adaptant à SQLite ou PostgreSQL."""
    if is_postgres():
        # Remplacer les ? par des %s pour PostgreSQL
        query = query.replace('?', '%s')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
    else:
        cursor = conn.cursor()
        cursor.execute(query, params)

    result = None
    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()

    if commit:
        conn.commit()
    
    cursor.close()
    return result

def init_db():
    conn = get_db_connection()
    
    if is_postgres():
        # PostgreSQL syntax
        execute_query(conn, '''
            CREATE TABLE IF NOT EXISTS submissions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                score_t REAL NOT NULL,
                pourcentage REAL NOT NULL,
                raw_data TEXT NOT NULL
            )
        ''', commit=True)
    else:
        # SQLite syntax
        execute_query(conn, '''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                score_t REAL NOT NULL,
                pourcentage REAL NOT NULL,
                raw_data TEXT NOT NULL
            )
        ''', commit=True)
    
    conn.close()

def insert_submission(t_score, pourcentage, raw_data_dict):
    conn = get_db_connection()
    raw_data_json = json.dumps(raw_data_dict)
    execute_query(conn,
        'INSERT INTO submissions (score_t, pourcentage, raw_data) VALUES (?, ?, ?)',
        (t_score, pourcentage, raw_data_json),
        commit=True
    )
    conn.close()

def get_stats_from_db(user_score=None):
    conn = get_db_connection()
    
    stats_row = execute_query(conn, '''
        SELECT COUNT(*) as total, AVG(score_t) as moyenne 
        FROM submissions
    ''', fetchone=True)
    
    total = stats_row['total'] or 0
    
    # Pour PostgreSQL, AVG retourne un Decimal, il faut le convertir
    try:
        moyenne = float(stats_row['moyenne']) if stats_row['moyenne'] is not None else 0
    except:
        moyenne = 0
        
    if total == 0:
        conn.close()
        return {
            'total': 0,
            'moyenne': 0,
            'mediane': 0,
            'percentile': 0
        }

    offset = (total - 1) // 2
    limit = 2 if total % 2 == 0 else 1
    
    # OFFSET et LIMIT sont supportés par les deux de la même manière
    median_rows = execute_query(conn, f'''
        SELECT score_t FROM submissions 
        ORDER BY score_t ASC 
        LIMIT {limit} OFFSET {offset}
    ''', fetchall=True)
    
    if len(median_rows) == 2:
        mediane = (median_rows[0]['score_t'] + median_rows[1]['score_t']) / 2
    elif len(median_rows) == 1:
        mediane = median_rows[0]['score_t']
    else:
        mediane = 0

    percentile = 0
    if user_score is not None:
        lower_count_row = execute_query(conn, '''
            SELECT COUNT(*) as lower_count 
            FROM submissions 
            WHERE score_t < ?
        ''', (user_score,), fetchone=True)
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
    conn = get_db_connection()
    rows = execute_query(conn, 'SELECT * FROM submissions ORDER BY timestamp DESC', fetchall=True)
    conn.close()
    
    results = []
    for row in rows:
        data = json.loads(row['raw_data'])
        # Formater la date en string si c'est un objet datetime (PostgreSQL)
        ts = row['timestamp']
        if isinstance(ts, datetime):
            ts = ts.strftime("%Y-%m-%d %H:%M:%S")
            
        data['Date_Soumission'] = ts
        data['T'] = row['score_t']
        data['pourcentage'] = row['pourcentage']
        results.append(data)
        
    return results

def get_recent_submissions(limit=10):
    conn = get_db_connection()
    rows = execute_query(conn, f'SELECT * FROM submissions ORDER BY timestamp DESC LIMIT {limit}', fetchall=True)
    conn.close()
    
    results = []
    for row in rows:
        data = json.loads(row['raw_data'])
        ts = row['timestamp']
        if isinstance(ts, datetime):
            ts = ts.strftime("%Y-%m-%d %H:%M:%S")
            
        data['timestamp'] = ts
        data['T'] = row['score_t']
        data['pourcentage'] = row['pourcentage']
        results.append(data)
    return results

def get_distribution():
    conn = get_db_connection()
    rows = execute_query(conn, 'SELECT score_t FROM submissions', fetchall=True)
    conn.close()
    
    scores = [row['score_t'] for row in rows]
    distribution = {
        '< -30': sum(1 for s in scores if s < -30),
        '-30 à -11': sum(1 for s in scores if -30 <= s <= -11),
        '-10 à -1': sum(1 for s in scores if -10 <= s <= -1),
        '0-10': sum(1 for s in scores if 0 <= s <= 10),
        '11-30': sum(1 for s in scores if 10 < s <= 30),
        '31-80': sum(1 for s in scores if 30 < s <= 80),
        '81-220': sum(1 for s in scores if 80 < s <= 220),
        '221-500': sum(1 for s in scores if 220 < s <= 500),
        '501+': sum(1 for s in scores if s > 500)
    }
    return distribution

def get_min_max_scores():
    conn = get_db_connection()
    row = execute_query(conn, 'SELECT MIN(score_t) as min_s, MAX(score_t) as max_s FROM submissions', fetchone=True)
    conn.close()
    if not row or row['min_s'] is None:
        return 0.0, 0.0
    return float(row['min_s']), float(row['max_s'])

def recalculate_all_scores():
    import TANA_code
    import json
    conn = get_db_connection()
    rows = execute_query(conn, 'SELECT id, raw_data FROM submissions', fetchall=True)
    
    updated_count = 0
    for row in rows:
        sub_id = row['id']
        raw_data_str = row['raw_data']
        try:
            data = json.loads(raw_data_str)
        except json.JSONDecodeError:
            continue
            
        # Completion automatique pour les nouvelles questions
        modified = False
        defaults = {
            'tel': 'jamais',
            'temps_rep': 'direct',
            'ghost': 'non',
            'tinder': 'jamais',
            'esquive': 'non'
        }
        for key, val in defaults.items():
            if key not in data:
                data[key] = val
                modified = True
                
        raw_data_json = json.dumps(data) if modified else raw_data_str
        
        # Calculate new T score
        t_score, pourcentage = TANA_code.calculer_T(data)
        
        execute_query(conn, 'UPDATE submissions SET score_t = ?, pourcentage = ?, raw_data = ? WHERE id = ?', 
                      (t_score, pourcentage, raw_data_json, sub_id), commit=False)
        updated_count += 1
        
    conn.commit()
    conn.close()
    return updated_count
