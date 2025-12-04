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
        except:
            font_titre = font_label = font_valeur = font_phrase = ImageFont.load_default()

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

        # Phrase finale selon le score brut
        try:
            t_val = float(t_score)
        except:
            t_val = 0

        if t_val <= 10:
            phrase = "Bravo à toi, tu n'es pas une tana."
        elif t_val <= 30:
            phrase = "Aïe… c’est pas que tu es une tana, c’est que tu aimes bien t’amuser."
        elif t_val <= 80:
            phrase = "Oula, on a affaire à une tana timide, mais une tana quand même."
        elif t_val <= 220:
            phrase = "Une tana moyenne."
        elif t_val <= 500:
            phrase = "On rentre dans une catégorie de tana qui nous dépasse."
        elif t_val <= 1000:
            phrase = "Tu vis pour t’amuser. Une vie de péché."
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

# --- Route crédit ---
@app.route('/credit')
def credit():
    return render_template('credit.html')
if __name__ == '__main__':
    app.run(debug=True, port=5002)
