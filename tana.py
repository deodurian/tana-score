from flask import Flask, render_template, request, send_from_directory, redirect, url_for, Response
import json
import os
import csv
from io import StringIO
from TANA_code import calculer_T
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from flask import send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import database

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tana-secret-key-super-secure')

# --- Initialisation Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'dashboard_login'

class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser(user_id)
    return None

# --- Initialisation SQLite ---
with app.app_context():
    database.init_db()
    try:
        database.recalculate_all_scores()
        print("Scores recalculés au démarrage avec succès.")
    except Exception as e:
        print(f"Erreur lors du recalcul des scores : {e}")

# --- Validation des données ---
def validate_form(form):
    errors = []
    
    always_required = ['sexe', 'age', 'premier', 'date', 'ex', 'score', 'insta', 'abo', 
                      'chien', 'ami', 'bz', 'demi_famille', 'tel', 'temps_rep', 'ghost', 'tinder', 'esquive']
    
    for field in always_required:
        if field not in form or form.get(field) == '':
            errors.append(f"Le champ '{field}' est obligatoire")
    
    if errors:
        return False, " | ".join(errors)
    
    try:
        age = int(form.get('age', 0))
        if not (13 <= age <= 100):
            errors.append("L'âge doit être entre 13 et 100 ans")
    except ValueError:
        errors.append("L'âge doit être un nombre")
    
    premier = -1
    try:
        premier = int(form.get('premier', 0))
        if not (0 <= premier <= 100):
            errors.append("L'âge de la première fois doit être entre 0 et 100")
    except ValueError:
        errors.append("L'âge de la première fois doit être un nombre")
        premier = -1
    
    try:
        date = int(form.get('date', 0))
        if date < 0:
            errors.append("Le nombre de dates ne peut pas être négatif")
    except ValueError:
        errors.append("Le nombre de dates doit être un nombre")
    
    try:
        ex = int(form.get('ex', 0))
        if ex < 0:
            errors.append("Le nombre d'ex ne peut pas être négatif")
    except ValueError:
        errors.append("Le nombre d'ex doit être un nombre")
    
    try:
        score = int(form.get('score', 0))
        if score < 0:
            errors.append("Le score Snap ne peut pas être négatif")
    except ValueError:
        errors.append("Le score Snap doit être un nombre")
    
    try:
        insta = int(form.get('insta', 0))
        if insta < 0:
            errors.append("Les abonnés Instagram ne peuvent pas être négatifs")
    except ValueError:
        errors.append("Les abonnés Instagram doivent être un nombre")
    
    try:
        abo = int(form.get('abo', 0))
        if abo < 0:
            errors.append("Les abonnements Instagram ne peuvent pas être négatifs")
    except ValueError:
        errors.append("Les abonnements Instagram doivent être un nombre")
    
    bodyc = -1
    if premier > 0:
        if 'bodyc' not in form or form.get('bodyc') == '':
            errors.append("Le bodycount est obligatoire si vous avez déjà eu une première fois")
        else:
            try:
                bodyc = int(form.get('bodyc', 0))
                if bodyc < 0:
                    errors.append("Le bodycount ne peut pas être négatif")
            except ValueError:
                errors.append("Le bodycount doit être un nombre")
    
    if bodyc > 0:
        if 'age_plus_vieux' not in form or form.get('age_plus_vieux') == '':
            errors.append("L'âge de la personne la plus vieille est obligatoire si le bodycount est supérieur à 0")
        else:
            try:
                age_vieux = int(form.get('age_plus_vieux', 0))
                if age_vieux < 0:
                    errors.append("L'âge ne peut pas être négatif")
            except ValueError:
                errors.append("L'âge de la personne la plus vieille doit être un nombre")
    
    valid_choices = {
        'sexe': ['h', 'f'],
        'chien': ['c', 'b'],
        'ami': ['f', 'g'],
        'bz': ['o', 'n'],
        'demi_famille': ['oui', 'non']
    }
    
    for field, allowed_values in valid_choices.items():
        if form.get(field) not in allowed_values:
            errors.append(f"Valeur invalide pour '{field}'")
    
    if form.get('trompe') and form.get('trompe') not in ['oui', 'non']:
        errors.append("Valeur invalide pour 'trompe'")
    
    if form.get('plaisir') and form.get('plaisir') not in ['oui', 'non']:
        errors.append("Valeur invalide pour 'plaisir'")
    
    if form.get('refaire') and form.get('refaire') not in ['oui', 'non']:
        errors.append("Valeur invalide pour 'refaire'")
    
    if form.get('maquillage') and form.get('maquillage') not in ['full', 'fond', 'eyeliner', 'creme']:
        errors.append("Valeur invalide pour 'maquillage'")
    
    if form.get('laisser_potes') and form.get('laisser_potes') not in ['oui_bien', 'depend', 'peut_etre', 'non_potes_dabord']:
        errors.append("Valeur invalide pour 'laisser_potes'")
    
    if errors:
        return False, " | ".join(errors)
    
    return True, None

# --- Routes ---

@app.route("/")
def accueil():
    return render_template("acceuil.html")

@app.route("/quiz", methods=["GET"])
def quiz():
    return render_template('tana.html')

@app.route("/quiz_duo", methods=["GET"])
def quiz_duo():
    return render_template('tana_duo.html')

@app.route('/submit', methods=['POST'])
def submit():
    form = request.form
    
    is_valid, error_message = validate_form(form)
    if not is_valid:
        return render_template('error.html', error=error_message), 400
        
    min_s, max_s = database.get_min_max_scores()
    
    t_score, pourcentage = calculer_T(dict(form))
    
    is_record_max = t_score > max_s and max_s != 0
    is_record_min = t_score < min_s and min_s != 0
    
    # Enregistrement dans SQLite
    database.insert_submission(t_score, pourcentage, dict(form))
    
    # Statistiques instantanées
    stats = database.get_stats_from_db(user_score=t_score)
    
    completion_time = form.get('completion_time', 'N/A')
    
    return render_template('resultat.html', 
                         T=t_score, 
                         pourcentage=pourcentage,
                         stats=stats,
                         distribution=database.get_distribution(),
                         completion_time=completion_time,
                         is_record_max=is_record_max,
                         is_record_min=is_record_min)

@app.route('/submit_duo', methods=['POST'])
def submit_duo():
    form = request.form
    
    # Séparer les données pour le joueur 1 et le joueur 2
    form_p1 = {k.replace('_1', ''): v for k, v in form.items() if k.endswith('_1')}
    form_p2 = {k.replace('_2', ''): v for k, v in form.items() if k.endswith('_2')}
    
    # Récupérer les clés sans suffixe (ex: completion_time)
    for k, v in form.items():
        if not k.endswith('_1') and not k.endswith('_2'):
            form_p1[k] = v
            form_p2[k] = v

    min_s, max_s = database.get_min_max_scores()
    
    t_score_1, pourcentage_1 = calculer_T(form_p1)
    t_score_2, pourcentage_2 = calculer_T(form_p2)
    
    is_record_max_1 = t_score_1 > max_s and max_s != 0
    is_record_min_1 = t_score_1 < min_s and min_s != 0
    
    # Update max/min for player 2 comparison
    current_max = max(max_s, t_score_1) if max_s != 0 else t_score_1
    current_min = min(min_s, t_score_1) if min_s != 0 else t_score_1
    
    is_record_max_2 = t_score_2 > current_max and current_max != 0
    is_record_min_2 = t_score_2 < current_min and current_min != 0
    
    database.insert_submission(t_score_1, pourcentage_1, form_p1)
    database.insert_submission(t_score_2, pourcentage_2, form_p2)
    
    stats_1 = database.get_stats_from_db(user_score=t_score_1)
    stats_2 = database.get_stats_from_db(user_score=t_score_2)
    
    diff = abs(t_score_1 - t_score_2)
    pire_tana = 1 if t_score_1 > t_score_2 else 2 if t_score_2 > t_score_1 else 0
    
    completion_time = form.get('completion_time', 'N/A')
    
    return render_template('resultat_duo.html',
                         T1=t_score_1, pourcentage1=pourcentage_1, stats1=stats_1,
                         T2=t_score_2, pourcentage2=pourcentage_2, stats2=stats_2,
                         diff=diff, pire_tana=pire_tana,
                         distribution=database.get_distribution(),
                         completion_time=completion_time,
                         is_record_max_1=is_record_max_1, is_record_min_1=is_record_min_1,
                         is_record_max_2=is_record_max_2, is_record_min_2=is_record_min_2)

@app.route('/googlee76869bb6ba74b8b.html')
def google_verify():
    return send_from_directory('static', 'googlee76869bb6ba74b8b.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@app.route('/telecharger_image')
def telecharger_image():
    try:
        from PIL import Image
        t_score = request.args.get('T', default='0')
        pourcentage = request.args.get('pourcentage', default='0')
        percentile = request.args.get('percentile', default='0')

        largeur, hauteur = 1080, 1080
        fond = Image.new('RGBA', (largeur, hauteur), "#fcaec0")

        try:
            decor_path = os.path.join('static', 'image fond.png')
            decor = Image.open(decor_path).convert("RGBA").resize((largeur, hauteur))
            fond.paste(decor, (0, 0), decor)
        except Exception as e:
            print("Erreur chargement décor :", e)

        image_path = os.path.join('static', 'tana logo chrome rose.webp')
        try:
            image_fond = Image.open(image_path).convert("RGBA").resize((largeur, hauteur))
            fond.paste(image_fond, (0, 0), image_fond)
        except Exception as e:
            print("Erreur chargement fond :", e)

        draw = ImageDraw.Draw(fond)

        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font_titre = ImageFont.truetype(font_path, 80)
            font_label = ImageFont.truetype(font_path, 40)
            font_valeur = ImageFont.truetype(font_path, 80)
            font_phrase = ImageFont.truetype(font_path, 30)
            font_classement = ImageFont.truetype(font_path, 35)
        except:
            font_titre = font_label = font_valeur = font_phrase = font_classement = ImageFont.load_default()

        try:
            logo_path = os.path.join("static", "tana logo noir.png")
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((120, 120))
            fond.paste(logo, (35, 35), logo)
        except Exception as e:
            print("Logo introuvable :", e)

        x_center = largeur // 2

        texte_titre = "Score TANA"
        w_titre = draw.textbbox((0, 0), texte_titre, font=font_titre)[2]
        draw.text(((largeur - w_titre) / 2, 80), texte_titre, fill="purple", font=font_titre)
        draw.line(((largeur - w_titre) / 2, 160, (largeur + w_titre) / 2, 160), fill="purple", width=4)

        label_score = "Score brut"
        val_score = f"{float(t_score):.2f}"
        w_label = draw.textbbox((0, 0), label_score, font=font_label)[2]
        w_val = draw.textbbox((0, 0), val_score, font=font_valeur)[2]

        draw.text((x_center - w_label / 2, 200), label_score, fill="black", font=font_label)
        draw.text((x_center - w_val / 2, 250), val_score, fill="darkred", font=font_valeur)

        label_pct = "Pourcentage"
        val_pct = f"{pourcentage}%"
        w_label2 = draw.textbbox((0, 0), label_pct, font=font_label)[2]
        w_val2 = draw.textbbox((0, 0), val_pct, font=font_valeur)[2]

        draw.text((x_center - w_label2 / 2, 400), label_pct, fill="black", font=font_label)
        draw.text((x_center - w_val2 / 2, 450), val_pct, fill="darkred", font=font_valeur)

        try:
            percentile_val = float(percentile)
            top_percent = 100 - percentile_val
            classement_text = f"Top {top_percent:.0f}%"
            w_classement = draw.textbbox((0, 0), classement_text, font=font_classement)[2]
            draw.text((x_center - w_classement / 2, 560), classement_text, fill="purple", font=font_classement)
        except:
            pass

        try:
            t_val = float(t_score)
        except:
            t_val = 0

        if t_val <= 10:
            phrase = "Bravo à toi, tu n'es pas une tana."
        elif t_val <= 30:
            phrase = "Aïe… c'est pas que tu es une tana, c'est que tu aimes bien t'amuser."
        elif t_val <= 80:
            phrase = "Oula, on a affaire à une tana timide, mais une tana quand même."
        elif t_val <= 220:
            phrase = "Une tana moyenne."
        elif t_val <= 500:
            phrase = "On rentre dans une catégorie de tana qui nous dépasse."
        elif t_val <= 1000:
            phrase = "Tu vis pour t'amuser. Une vie de péché."
        else:
            phrase = "On a dépassé les limites humaines… consulte un psy peut-être 😅"

        w_phrase = draw.textbbox((0, 0), phrase, font=font_phrase)[2]
        draw.text(((largeur - w_phrase) / 2, 650), phrase, fill="purple", font=font_phrase)

        buf = BytesIO()
        fond.save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype='image/png', as_attachment=True, download_name='score_tana.png')

    except Exception as e:
        print("Erreur génération image :", e)
        return "Erreur lors de la génération de l'image", 500

# --- Dashboard Routes ---

@app.route('/dashboard/login', methods=['GET', 'POST'])
def dashboard_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        expected_user = os.environ.get('DASHBOARD_USER', 'admin')
        expected_password = os.environ.get('DASHBOARD_PASSWORD', 'admin123')
        
        if username == expected_user and password == expected_password:
            user = AdminUser(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('dashboard_login.html', error="Identifiants incorrects")
    
    return render_template('dashboard_login.html', error=None)

@app.route('/dashboard/logout')
@login_required
def dashboard_logout():
    logout_user()
    return redirect(url_for('dashboard_login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        stats = database.get_stats_from_db()
        distribution = database.get_distribution()
        recent = database.get_recent_submissions(10)
        min_s, max_s = database.get_min_max_scores()
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             distribution=distribution,
                             recent=recent,
                             total_scores=stats['total'],
                             total_entries=stats['total'],
                             min_score=min_s,
                             max_score=max_s)
    except Exception as e:
        print(f"Erreur dashboard: {e}")
        return render_template('error.html', 
                             error=f"Impossible de charger les données: {str(e)}"), 500

@app.route('/dashboard/export')
@login_required
def dashboard_export():
    try:
        data = database.get_all_submissions_for_export()
        if not data:
            return "Aucune donnée à exporter", 404
            
        si = StringIO()
        
        fieldnames = set()
        for row in data:
            fieldnames.update(row.keys())
        fieldnames = list(fieldnames)
        
        main_fields = ['Date_Soumission', 'T', 'pourcentage']
        for field in main_fields:
            if field in fieldnames:
                fieldnames.remove(field)
        fieldnames = main_fields + sorted(fieldnames)
        
        writer = csv.DictWriter(si, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        output = Response(si.getvalue(), mimetype='text/csv')
        output.headers["Content-Disposition"] = "attachment; filename=export_tana.csv"
        return output
    except Exception as e:
        print(f"Erreur export: {e}")
        return "Erreur lors de l'export CSV", 500

@app.route('/dashboard/migrate')
@login_required
def dashboard_migrate():
    try:
        from migrate_data import migrate
        result = migrate()
        return f"<h1>Résultat de la migration</h1><p>{result}</p><br><a href='/dashboard'>Retour au dashboard</a>"
    except Exception as e:
        return f"<h1>Erreur</h1><p>{str(e)}</p>", 500

@app.route('/dashboard/recalculate')
@login_required
def dashboard_recalculate():
    try:
        updated = database.recalculate_all_scores()
        return f"<h1>Succès</h1><p>{updated} scores ont été recalculés et complétés.</p><br><a href='/dashboard'>Retour au dashboard</a>"
    except Exception as e:
        return f"<h1>Erreur</h1><p>{str(e)}</p><br><a href='/dashboard'>Retour au dashboard</a>"

@app.route('/dashboard/cleanup')
@login_required
def dashboard_cleanup():
    try:
        deleted = database.nettoyer_doublons()
        return f"<h1>Nettoyage Réussi</h1><p>{deleted} doublons (identiques à moins de 5 minutes d'intervalle) ont été supprimés.</p><br><a href='/dashboard'>Retour au dashboard</a>"
    except Exception as e:
        return f"<h1>Erreur</h1><p>{str(e)}</p><br><a href='/dashboard'>Retour au dashboard</a>"

@app.route('/dashboard/data')
@login_required
def dashboard_data():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    try:
        rows, total = database.get_paginated_submissions(page, per_page)
        total_pages = (total + per_page - 1) // per_page
        return render_template('data_management.html', rows=rows, page=page, total_pages=total_pages, total=total)
    except Exception as e:
        return f"<h1>Erreur</h1><p>{str(e)}</p><br><a href='/dashboard'>Retour au dashboard</a>"

@app.route('/dashboard/data/delete/<int:id>', methods=['POST'])
@login_required
def dashboard_data_delete(id):
    try:
        database.delete_submission(id)
        return redirect(url_for('dashboard_data'))
    except Exception as e:
        return f"<h1>Erreur</h1><p>{str(e)}</p><br><a href='/dashboard/data'>Retour aux données</a>"

@app.route('/dashboard/data/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def dashboard_data_edit(id):
    if request.method == 'POST':
        raw_data = request.form.get('raw_data')
        try:
            database.update_submission_raw_data(id, raw_data)
            return redirect(url_for('dashboard_data'))
        except Exception as e:
            return f"<h1>Erreur lors de la sauvegarde</h1><p>{str(e)}</p><br><a href='/dashboard/data'>Retour</a>"
            
    row = database.get_submission_by_id(id)
    if not row:
        return "Not found", 404
    return render_template('data_edit.html', row=row)

@app.route('/credit')
def credit():
    return render_template('credit.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
