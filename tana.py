from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import json
import os
from TANA_code import calculer_T
from google_sheets_utils import enregistrer_dans_google_sheet

app = Flask(__name__)
app.secret_key = 'clé secrete'

DATA_FILE = "données.json"

def load_data():
    """Charge les données existantes ou crée un fichier vide si nécessaire."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(new_entry):
    """Ajoute une nouvelle entrée (dictionnaire) au fichier JSON de données."""
    data = load_data()
    data.append(new_entry)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)



# Route de la page d'accueil
@app.route("/")
def accueil():
    return render_template("acceuil.html")  # Nouveau template

# Route du quiz
@app.route("/quiz", methods=["GET"])
def quiz():
    """Affiche le formulaire multi-étapes."""
    
    return render_template('tana.html')

@app.route('/submit', methods=['POST'])
def submit():
    """
    Traite les réponses du formulaire.
    Si certaines réponses déclenchent le mode admin, redirige vers admin_login.
    Sinon, calcule le score T et affiche le résultat.
    """
    form = request.form
    # Condition stricte pour accéder à l'admin : premier==0, age==70, score==35
    if (
        "premier" in form and "age" in form and "score" in form and
        form["premier"].isdigit() and form["age"].isdigit() and form["score"].isdigit()
        and int(form["premier"]) == 0 and int(form["age"]) == 70 and int(form["score"]) == 35
    ):
        session['admin_candidate'] = True
        return redirect(url_for('admin_login'))

    # Sinon, on calcule le score et affiche le résultat
    save_data(dict(form))
    enregistrer_dans_google_sheet(dict(form))
    # 'compute_t_score' retourne (score_brut, pourcentage_sigmoide)
    t_score, pourcentage = calculer_T(dict(form))
    return render_template('resultat.html', T=t_score, pourcentage=pourcentage)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Page de connexion pour l'admin. Vérifie un mot de passe simple."""
    # N'autorise l'accès qu'à ceux qui sont passés par /submit avec la bonne combinaison
    if not session.get('admin_candidate'):
        return redirect(url_for('accueil'))

    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'administratoraccess':
            session.pop('admin_candidate', None)
            session['admin'] = True
            return redirect(url_for('admin'))
        return render_template('admin_login.html', error="Mot de passe incorrect.")
    return render_template('admin_login.html', error=None)



@app.route('/admin')
def admin():
    """
    Page d'administration affichant toutes les données collectées.
    Protégée par une condition de session.
    """
    if not session.get('admin'):
        # S'assure que l'utilisateur est "connecté" en tant qu'admin
        return redirect(url_for('admin_login'))
    data = load_data()  # Charge toutes les réponses sauvegardées
    return render_template('admin.html', donnees=data)

# --- Routes supplémentaires admin ---
from flask import send_file, jsonify

@app.route('/admin/download')
def admin_download():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return send_file(DATA_FILE, as_attachment=True)

@app.route('/admin/stats')
def admin_stats():
    if not session.get('admin'):
        return jsonify({"error": "non autorisé"}), 403

    data = load_data()
    total = len(data)
    try:
        scores = [float(d.get("T", 0)) for d in data if "T" in d]
        moyenne = sum(scores) / len(scores) if scores else 0
    except Exception:
        moyenne = 0

    return jsonify({
        "total_users": total,
        "score_moyen": round(moyenne, 2),
        "connected": 1  # valeur fictive pour l'instant
    })

@app.route('/googlee76869bb6ba74b8b.html')
def google_verify():
    return send_from_directory('static', 'googlee76869bb6ba74b8b.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

if __name__ == '__main__':
    app.run(debug=True, port = 5000)
