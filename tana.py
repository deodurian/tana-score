from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import sqlite3
from TANA_code import calculer_T
from google_sheets_utils import enregistrer_dans_google_sheet
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from flask import send_file

app = Flask(__name__)
app.secret_key = 'clé secrete'

DATA_FILE = "données.json"
DB_PATH = 'admins.db'

# --- Gestion SQLite admins ---

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        validated INTEGER NOT NULL DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

def add_admin(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = generate_password_hash(password)
    try:
        cursor.execute('INSERT INTO admins (email, password) VALUES (?, ?)', (email, hashed))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Email déjà existant
    conn.close()
    return True

def get_admin(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admins WHERE email = ?', (email,))
    admin = cursor.fetchone()
    conn.close()
    return admin

def validate_admin(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE admins SET validated = 1 WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def delete_admin(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admins WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def get_pending_admins():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admins WHERE validated = 0')
    admins = cursor.fetchall()
    conn.close()
    return admins

# --- Gestion données formulaire ---

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(new_entry):
    data = load_data()
    data.append(new_entry)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Routes ---

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

@app.route("/")
def accueil():
    return render_template("acceuil.html")

@app.route("/quiz", methods=["GET"])
def quiz():
    return render_template('tana.html')

@app.route('/submit', methods=['POST'])
def submit():
    form = request.form
    if (
        "premier" in form and "age" in form and "score" in form and
        form["premier"].isdigit() and form["age"].isdigit() and form["score"].isdigit()
        and int(form["premier"]) == 0 and int(form["age"]) == 70 and int(form["score"]) == 35
    ):
        session['admin_candidate'] = True
        return redirect(url_for('admin_login'))

    save_data(dict(form))
    t_score, pourcentage = calculer_T(dict(form))
    try:
        all_data = {key: form.get(key, "") for key in form.keys()}
        all_data["T"] = t_score
        all_data["pourcentage"] = pourcentage
        enregistrer_dans_google_sheet(all_data)
    except Exception as e:
        print("Erreur envoi Google Sheets:", e)
    return render_template('resultat.html', T=t_score, pourcentage=pourcentage)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if not session.get('admin_candidate') and not session.get('admin'):
        return redirect(url_for('accueil'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = get_admin(email)
        if admin:
            if not admin['validated']:
                return render_template('admin_login.html', error="Compte en attente de validation.")
            if check_password_hash(admin['password'], password):
                session.pop('admin_candidate', None)
                session['admin'] = True
                session['admin_email'] = email
                return redirect(url_for('admin'))
            else:
                return render_template('admin_login.html', error="Mot de passe incorrect.")
        # fallback legacy password for first-time admin
        if email == "admin@local" and password == 'administratoraccess':
            session.pop('admin_candidate', None)
            session['admin'] = True
            session['admin_email'] = email
            return redirect(url_for('admin'))
        return render_template('admin_login.html', error="Identifiants incorrects.")
    return render_template('admin_login.html', error=None)

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not add_admin(email, password):
            return render_template('admin_register.html', error="Email déjà utilisé")
        return render_template('admin_register.html', message="Demande envoyée. En attente de validation.")
    return render_template('admin_register.html', error=None)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        email = request.form.get('email')
        action = request.form.get('action')
        if action == 'valider':
            validate_admin(email)
        elif action == 'refuser':
            delete_admin(email)
        return redirect(url_for('admin'))

    data = load_data()
    pending = get_pending_admins()

    return render_template('admin.html', donnees=data, demandes=pending)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('accueil'))

# Routes supplémentaires pour admin (download, stats, etc.)
@app.route('/admin/download')
def admin_download():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return send_from_directory('.', DATA_FILE, as_attachment=True)

@app.route('/admin/stats')
def admin_stats():
    if not session.get('admin'):
        return {"error": "non autorisé"}, 403

    data = load_data()
    total = len(data)
    try:
        scores = [float(d.get("T", 0)) for d in data if "T" in d]
        moyenne = sum(scores) / len(scores) if scores else 0
    except Exception:
        moyenne = 0

    return {
        "total_users": total,
        "score_moyen": round(moyenne, 2),
        "connected": 1
    }

@app.route('/googlee76869bb6ba74b8b.html')
def google_verify():
    return send_from_directory('static', 'googlee76869bb6ba74b8b.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')



# Route pour servir robots.txt
@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')


# --- Génération et téléchargement d'une image du score ---


@app.route('/telecharger_image')
def telecharger_image():
    try:
        t_score = request.args.get('T', default='0')
        pourcentage = request.args.get('pourcentage', default='0')
        try:
            pourcentage_val = float(pourcentage)
        except Exception:
            pourcentage_val = 0

        # Créer un fond rose (carré 1080x1080)
        background = Image.new('RGBA', (1920, 1920), "#fcaec0")

        # Charger et redimensionner l'image (carré 1080x1080)
        image_path = os.path.join('static', 'tana logo chrome rose.webp')
        image = Image.open(image_path).convert("RGBA").resize((1920, 1920))

        # Fusionner sur fond
        background.paste(image, (0, 0), image)

        # Utiliser le fond final comme base de travail
        image = background
        largeur, hauteur = image.size
        draw = ImageDraw.Draw(image)

        # Charger police DejaVuSans si dispo, sinon défaut
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font_titre = ImageFont.truetype(font_path, 80)
            font_label = ImageFont.truetype(font_path, 40)
            font_valeur = ImageFont.truetype(font_path, 80)
            font_phrase = ImageFont.truetype(font_path, 40)
        except IOError:
            font_titre = font_label = font_valeur = font_phrase = ImageFont.load_default()

        # Ajouter logo en haut à gauche
        try:
            logo_path = os.path.join("static", "tana logo noir.png")
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((300, 300))
            image.paste(logo, (50, 50), logo)
        except Exception as e:
            print("Logo non trouvé ou erreur d'insertion :", e)

        # Titre "Score TANA" centré, souligné
        texte_titre = "Score TANA"
        w_titre = draw.textbbox((0, 0), texte_titre, font=font_titre)[2]
        draw.text(((largeur - w_titre) / 2, 80), texte_titre, fill="purple", font=font_titre)
        # Soulignement
        draw.line(((largeur - w_titre) / 2, 200, (largeur + w_titre) / 2, 200), fill="purple", width=5)

        # Bloc "Score brut" encadré sombrement
        label_score = "Score brut"
        val_score = str(t_score)
        w_label = draw.textbbox((0, 0), label_score, font=font_label)[2]
        w_val = draw.textbbox((0, 0), val_score, font=font_valeur)[2]
        x_center = largeur // 2

        # Label
        draw.text((x_center - w_label / 2, 250), label_score, fill="pink", font=font_label)
        # Encadré sombre
        rect_y0 = 330
        rect_y1 = 480
        rect_x0 = x_center - w_val / 2 - 30
        rect_x1 = x_center + w_val / 2 + 30
        # Removed the rectangle drawing here as per instructions
        # draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill="pink")
        draw.text((x_center - w_val / 2, 340), val_score, fill="purple", font=font_valeur)

        # Bloc "Pourcentage" encadré sombrement
        label_pct = "Pourcentage"
        val_pct = f"{pourcentage}%"
        w_label2 = draw.textbbox((0, 0), label_pct, font=font_label)[2]
        w_val2 = draw.textbbox((0, 0), val_pct, font=font_valeur)[2]
        # Label
        draw.text((x_center - w_label2 / 2, 530), label_pct, fill="pink", font=font_label)
        # Encadré sombre
        rect2_y0 = 610
        rect2_y1 = 760
        rect2_x0 = x_center - w_val2 / 2 - 30
        rect2_x1 = x_center + w_val2 / 2 + 30
        # Removed the rectangle drawing here as per instructions
        # draw.rectangle([rect2_x0, rect2_y0, rect2_x1, rect2_y1], fill="pink")
        draw.text((x_center - w_val2 / 2, 620), val_pct, fill="purple", font=font_valeur)

        # Phrase personnalisée en bas selon le score
        try:
            t_score_val = float(t_score)
        except:
            t_score_val = 0

        if t_score_val <= 10:
            phrase = "Bravo à toi, tu n'es pas une tana."
        elif t_score_val <= 30:
            phrase = "Aïe… c’est pas que tu es une tana, c’est que tu aimes bien t’amuser."
        elif t_score_val <= 80:
            phrase = "Oula, on a affaire à une tana timide, mais une tana quand même."
        elif t_score_val <= 220:
            phrase = "Une tana moyenne."
        elif t_score_val <= 500:
            phrase = "On rentre dans une catégorie de tana qui nous dépasse."
        elif t_score_val <= 1000:
            phrase = "Tu vis pour t’amuser. Une vie de péché."
        else:
            phrase = "On a dépassé les limites humaines… consulte un psy peut-être 😅"

        w_phrase = draw.textbbox((0, 0), phrase, font=font_phrase)[2]
        draw.text(((largeur - w_phrase) / 2, 900), phrase, fill="purple", font=font_phrase)

        # Enregistrer en mémoire
        buf = BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)

        return send_file(buf, mimetype='image/png', as_attachment=True, download_name='score_tana.png')
    except Exception as e:
        print("Erreur lors de la génération de l'image :", e)
        return "Erreur interne lors de la génération de l'image.", 500
