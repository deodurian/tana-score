from flask import Flask, render_template, request, send_from_directory
import json
import os
from TANA_code import calculer_T
from google_sheets_utils import enregistrer_dans_google_sheet
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from flask import send_file

app = Flask(__name__)

DATA_FILE = "données.json"

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

# --- Validation des données ---

def validate_form(form):
    """
    Valide toutes les données du formulaire côté serveur.
    PREND EN COMPTE LES QUESTIONS CONDITIONNELLES.
    
    POURQUOI C'EST IMPORTANT :
    1. Sécurité : Empêche l'injection de données malveillantes
    2. Intégrité : Garantit que les calculs sont corrects
    3. Statistiques fiables : Évite les données aberrantes
    4. Logique conditionnelle : Ne valide que les champs qui devraient être présents
    
    Retourne (is_valid, error_message)
    """
    errors = []
    
    # 1. CHAMPS TOUJOURS OBLIGATOIRES (peu importe les réponses)
    always_required = ['sexe', 'age', 'premier', 'date', 'ex', 'score', 'insta', 'abo', 
                      'chien', 'ami', 'bz', 'demi_famille']
    
    for field in always_required:
        if field not in form or form.get(field) == '':
            errors.append(f"Le champ '{field}' est obligatoire")
    
    if errors:
        return False, " | ".join(errors)
    
    # 2. VALIDATION DES CHAMPS NUMÉRIQUES OBLIGATOIRES
    try:
        age = int(form.get('age', 0))
        if not (13 <= age <= 100):
            errors.append("L'âge doit être entre 13 et 100 ans")
    except ValueError:
        errors.append("L'âge doit être un nombre")
    
    premier = -1 # Initialisation pour la validation conditionnelle
    try:
        premier = int(form.get('premier', 0))
        if not (0 <= premier <= 100):
            errors.append("L'âge de la première fois doit être entre 0 et 100")
    except ValueError:
        errors.append("L'âge de la première fois doit être un nombre")
        premier = -1  # Valeur invalide pour éviter les erreurs plus tard
    
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
    
    # 3. VALIDATION CONDITIONNELLE - Bodycount (seulement si premier > 0)
    bodyc = -1 # Initialisation pour la validation conditionnelle
    if premier > 0:
        # Si la personne a déjà eu une première fois, bodycount est obligatoire
        if 'bodyc' not in form or form.get('bodyc') == '':
            errors.append("Le bodycount est obligatoire si vous avez déjà eu une première fois")
        else:
            try:
                bodyc = int(form.get('bodyc', 0))
                if bodyc < 0:
                    errors.append("Le bodycount ne peut pas être négatif")
            except ValueError:
                errors.append("Le bodycount doit être un nombre")
    
    # 4. VALIDATION CONDITIONNELLE - Age plus vieux (seulement si bodycount > 0)
    if bodyc > 0: # Use the validated bodyc
        if 'age_plus_vieux' not in form or form.get('age_plus_vieux') == '':
            errors.append("L'âge de la personne la plus vieille est obligatoire si le bodycount est supérieur à 0")
        else:
            try:
                age_vieux = int(form.get('age_plus_vieux', 0))
                if age_vieux < 0:
                    errors.append("L'âge ne peut pas être négatif")
            except ValueError:
                errors.append("L'âge de la personne la plus vieille doit être un nombre")
    
    # 5. VALIDATION DES CHOIX MULTIPLES (toujours obligatoires)
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
    
    # 6. VALIDATION DES CHAMPS CONDITIONNELS (optionnels)
    # Ces champs ne sont présents que dans certains cas, donc on ne les valide que s'ils existent
    
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

# --- Statistiques ---

def get_stats(user_score=None):
    """
    Calcule les statistiques globales depuis Google Sheets
    
    Retourne un dictionnaire avec:
    - total: nombre total de participants
    - moyenne: score moyen
    - mediane: score médian
    - percentile: position de l'utilisateur (si user_score fourni)
    """
    from google_sheets_utils import get_all_data_from_sheets
    
    # Lire les données depuis Google Sheets au lieu de données.json
    data = get_all_data_from_sheets()
    
    if not data:
        return {
            'total': 0,
            'moyenne': 0,
            'mediane': 0,
            'percentile': 0
        }
    
    # Extraire tous les scores T
    scores = []
    for entry in data:
        try:
            if 'T' in entry and entry['T']:
                scores.append(float(entry['T']))
        except (ValueError, TypeError):
            continue
    
    if not scores:
        return {
            'total': len(data),
            'moyenne': 0,
            'mediane': 0,
            'percentile': 0
        }
    
    # Calculer moyenne
    moyenne = sum(scores) / len(scores)
    
    # Calculer médiane
    scores_sorted = sorted(scores)
    n = len(scores_sorted)
    if n % 2 == 0:
        mediane = (scores_sorted[n//2 - 1] + scores_sorted[n//2]) / 2
    else:
        mediane = scores_sorted[n//2]
    
    # Calculer percentile de l'utilisateur
    percentile = 0
    if user_score is not None:
        # Combien de personnes ont un score inférieur ?
        lower_count = sum(1 for s in scores if s < user_score)
        percentile = (lower_count / len(scores)) * 100
    
    return {
        'total': len(data),
        'moyenne': round(moyenne, 1),
        'mediane': round(mediane, 1),
        'percentile': round(percentile, 0)
    }

# --- Routes ---



@app.route("/")
def accueil():
    return render_template("acceuil.html")

@app.route("/quiz", methods=["GET"])
def quiz():
    return render_template('tana.html')

@app.route('/submit', methods=['POST'])
def submit():
    form = request.form
    
    # VALIDATION CÔTÉ SERVEUR - Étape critique !
    is_valid, error_message = validate_form(form)
    if not is_valid:
        # Si les données sont invalides, afficher une page d'erreur
        return render_template('error.html', error=error_message), 400
    
    # Les données sont valides, on peut continuer
    save_data(dict(form))
    t_score, pourcentage = calculer_T(dict(form))
    
    # Préparer les données pour Google Sheets
    all_data = {key: form.get(key, "") for key in form.keys()}
    all_data["T"] = t_score
    all_data["pourcentage"] = pourcentage
    
    # Envoyer à Google Sheets en arrière-plan (non bloquant)
    def send_to_sheets():
        try:
            enregistrer_dans_google_sheet(all_data)
        except Exception as e:
            print("Erreur envoi Google Sheets:", e)
    
    import threading
    thread = threading.Thread(target=send_to_sheets)
    thread.start()
    
    # Calculer les statistiques pour comparaison
    stats = get_stats(user_score=t_score)
    
    # Récupérer le temps de complétion
    completion_time = form.get('completion_time', 'N/A')
    
    # Afficher immédiatement les résultats avec les stats
    return render_template('resultat.html', 
                         T=t_score, 
                         pourcentage=pourcentage,
                         stats=stats,
                         completion_time=completion_time)



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



# Nouvelle version propre et cohérente de la route /telecharger_image
@app.route('/telecharger_image')
def telecharger_image():
    try:
        from PIL import Image
        t_score = request.args.get('T', default='0')
        pourcentage = request.args.get('pourcentage', default='0')
        percentile = request.args.get('percentile', default='0')

        # Dimensions carrées
        largeur, hauteur = 1080, 1080

        # Créer fond uni
        fond = Image.new('RGBA', (largeur, hauteur), "#fcaec0")

        # Ajouter image décorative par-dessus le fond rose
        try:
            decor_path = os.path.join('static', 'image fond.png')
            decor = Image.open(decor_path).convert("RGBA").resize((largeur, hauteur))
            fond.paste(decor, (0, 0), decor)
        except Exception as e:
            print("Erreur chargement décor :", e)

        # Ajouter image de fond
        image_path = os.path.join('static', 'tana logo chrome rose.webp')
        try:
            image_fond = Image.open(image_path).convert("RGBA").resize((largeur, hauteur))
            fond.paste(image_fond, (0, 0), image_fond)
        except Exception as e:
            print("Erreur chargement fond :", e)

        draw = ImageDraw.Draw(fond)

        # Polices
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font_titre = ImageFont.truetype(font_path, 80)
            font_label = ImageFont.truetype(font_path, 40)
            font_valeur = ImageFont.truetype(font_path, 80)
            font_phrase = ImageFont.truetype(font_path, 30)
            font_classement = ImageFont.truetype(font_path, 35)
        except:
            font_titre = font_label = font_valeur = font_phrase = font_classement = ImageFont.load_default()

        # Logo en haut à gauche
        try:
            logo_path = os.path.join("static", "tana logo noir.png")
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((120, 120))
            fond.paste(logo, (35, 35), logo)
        except Exception as e:
            print("Logo introuvable :", e)

        x_center = largeur // 2

        # Titre Score TANA
        texte_titre = "Score TANA"
        w_titre = draw.textbbox((0, 0), texte_titre, font=font_titre)[2]
        draw.text(((largeur - w_titre) / 2, 80), texte_titre, fill="purple", font=font_titre)
        draw.line(((largeur - w_titre) / 2, 160, (largeur + w_titre) / 2, 160), fill="purple", width=4)

        # Score brut
        label_score = "Score brut"
        val_score = f"{float(t_score):.1f}"
        w_label = draw.textbbox((0, 0), label_score, font=font_label)[2]
        w_val = draw.textbbox((0, 0), val_score, font=font_valeur)[2]

        draw.text((x_center - w_label / 2, 200), label_score, fill="black", font=font_label)
        draw.text((x_center - w_val / 2, 250), val_score, fill="darkred", font=font_valeur)

        # Pourcentage
        label_pct = "Pourcentage"
        val_pct = f"{pourcentage}%"
        w_label2 = draw.textbbox((0, 0), label_pct, font=font_label)[2]
        w_val2 = draw.textbbox((0, 0), val_pct, font=font_valeur)[2]

        draw.text((x_center - w_label2 / 2, 400), label_pct, fill="black", font=font_label)
        draw.text((x_center - w_val2 / 2, 450), val_pct, fill="darkred", font=font_valeur)

        # Classement (nouveau)
        try:
            percentile_val = float(percentile)
            top_percent = 100 - percentile_val
            classement_text = f"Top {top_percent:.0f}%"
            w_classement = draw.textbbox((0, 0), classement_text, font=font_classement)[2]
            draw.text((x_center - w_classement / 2, 560), classement_text, fill="purple", font=font_classement)
        except:
            pass

        # Phrase finale selon le score brut
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

        # Envoi image
        buf = BytesIO()
        fond.save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype='image/png', as_attachment=True, download_name='score_tana.png')

    except Exception as e:
        print("Erreur génération image :", e)
        return "Erreur lors de la génération de l'image", 500

# --- Route Dashboard (Protégée) ---
@app.route('/dashboard/<secret_token>', methods=['GET', 'POST'])
def dashboard(secret_token):
    """
    Dashboard privé avec double sécurité:
    1. URL secrète (secret_token)
    2. Mot de passe
    
    Variables d'environnement requises:
    - DASHBOARD_SECRET_URL: le token dans l'URL
    - DASHBOARD_PASSWORD: le mot de passe
    """
    # Vérification 1: Token dans l'URL
    expected_token = os.environ.get('DASHBOARD_SECRET_URL', 'change-me-in-production')
    if secret_token != expected_token:
        return "404 Not Found", 404  # Faire croire que la page n'existe pas
    
    # Vérification 2: Mot de passe
    if request.method == 'POST':
        password = request.form.get('password', '')
        expected_password = os.environ.get('DASHBOARD_PASSWORD', 'admin123')
        
        if password == expected_password:
            # Mot de passe correct, afficher le dashboard
            from google_sheets_utils import get_all_data_from_sheets
            
            try:
                # Lire les données depuis Google Sheets
                data = get_all_data_from_sheets()
                stats = get_stats()
                
                # Calculer distribution des scores
                scores = []
                for entry in data:
                    try:
                        if 'T' in entry and entry['T']:
                            scores.append(float(entry['T']))
                    except (ValueError, TypeError):
                        continue
                
                # Grouper par tranches
                distribution = {
                    '0-10': sum(1 for s in scores if s <= 10),
                    '11-30': sum(1 for s in scores if 10 < s <= 30),
                    '31-80': sum(1 for s in scores if 30 < s <= 80),
                    '81-220': sum(1 for s in scores if 80 < s <= 220),
                    '221-500': sum(1 for s in scores if 220 < s <= 500),
                    '501+': sum(1 for s in scores if s > 500)
                }
                
                # 10 dernières soumissions
                recent = data[-10:][::-1]  # Inverser pour avoir les plus récentes en premier
                
                return render_template('dashboard.html', 
                                     stats=stats, 
                                     distribution=distribution,
                                     recent=recent,
                                     total_scores=len(scores))
            except Exception as e:
                # Si erreur lors de la lecture de Google Sheets
                print(f"Erreur dashboard: {e}")
                return render_template('error.html', 
                                     error=f"Impossible de charger les données depuis Google Sheets. Erreur: {str(e)}"), 500
        else:
            return render_template('dashboard_login.html', error="Mot de passe incorrect")
    
    # GET request: afficher le formulaire de connexion
    return render_template('dashboard_login.html', error=None)

# --- Route crédit ---
@app.route('/credit')
def credit():
    return render_template('credit.html')
if __name__ == '__main__':
    app.run(debug=True, port=5002)
