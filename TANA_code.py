import subprocess
from math import log2
from math import *
from google_sheets_utils import enregistrer_dans_google_sheet

def calculer_T(donnees):
    sexe = donnees["sexe"]
    try:
        age = int(donnees["age"])
    except (ValueError, TypeError):
        age = 0

    try:
        bodyc = int(donnees.get("bodyc", 0))
    except (ValueError, TypeError):
        bodyc = 0

    try:
        score = float(donnees.get("score", 0))
    except (ValueError, TypeError):
        score = 0.0

    try:
        insta = int(donnees.get("insta", 0))
    except (ValueError, TypeError):
        insta = 0

    try:
        abo = int(donnees.get("abo", 0))
    except (ValueError, TypeError):
        abo = 0

    try:
        ex = int(donnees.get("ex", 0))
    except (ValueError, TypeError):
        ex = 0

    try:
        date = int(donnees.get("date", 0))
    except (ValueError, TypeError):
        date = 0

    try:
        age_vieux = int(donnees.get("age_plus_vieux", 0)) if bodyc != 0 else 0
    except (ValueError, TypeError):
        age_vieux = 0
    try:
        premier = int(donnees["premier"])
    except (ValueError, TypeError):
        premier = 0
    # Si premier vaut 0, forcer les réponses à "tromper", "plaisir", "refaire" à "non"
    if premier == 0:
        donnees["trompe"] = "non"
        donnees["plaisir"] = "non"
        donnees["refaire"] = "non"

    # Nouvelles questions (tarte tropezienne)
    trompe = donnees.get("trompe", "non")  # oui/non
    plaisir = donnees.get("plaisir", "non")  # oui/non
    refaire = donnees.get("refaire", "non")  # oui/non
    # date, ex, bodyc, score, insta, abo already converted above
    chien = donnees["chien"]
    ami = donnees["ami"]
    bz = donnees["bz"]

    maquillage = donnees.get("maquillage")  # full/fond/eyeliner/creme
    
    # Mapper les valeurs textuelles de "laisser_potes" vers des valeurs numériques
    laisser_potes_raw = donnees.get("laisser_potes", "")
    if laisser_potes_raw == "oui_bien":
        potes_vs_relation = "1"
    elif laisser_potes_raw == "depend":
        potes_vs_relation = "2"
    elif laisser_potes_raw == "peut_etre":
        potes_vs_relation = "3"
    elif laisser_potes_raw == "non_potes_dabord":
        potes_vs_relation = "4"
    else:
        potes_vs_relation = None
    # age_vieux already converted above
    demi_famille = donnees.get("demi_famille")  # oui/non

    T = 0
    n = 0  # Initialisation pour éviter NameError si premier == 0
    if sexe == "f":
        T = 1

    if premier != 0:
        if (age - premier) == 0:
            n = bodyc + 1 
        else:
            n = bodyc / (age - premier)
        T += bodyc * 2
        if bodyc != 0 and n > 1:
            T += 2 + n
    else:
        T += 0

    if premier >= 16:
        T += 4
    elif premier == 0:
        T += 0
    else:
        T += 4 + abs(16 - premier)

    # Récompenser les scores faibles et punir les scores élevés de manière continue (formule racine carrée).
    # Un score de 50 000 est neutre (aucun effet sur T). Les scores inférieurs réduisent T, les scores supérieurs l'augmentent.
    T += 0.02 * (sqrt(max(0.0, score)) - sqrt(50000.0))


    # Calculer le ratio d'abonnés / abonnements de manière sécurisée
    ratio = insta / abo if abo != 0 else 1.0

    # Punir continûment les ratios élevés et les grands comptes d'abonnés (formule Log-Log)
    # Les ratios inférieurs à 1.0 agissent comme une récompense (diminuent T).
    if insta > 0 and abo > 0:
        T += 3.0 * log10(ratio) * log10(insta + 1)

    if chien == "c":
        T += (ratio + bodyc + ex + date) * 3
    elif chien == "b" and (age - premier + 1) > 0 and bodyc  > 20:
        T += 2 * bodyc * (n+1+ ex + date)
    elif chien == "b":
        if sexe == "h" :
            T -= exp(1.3)
        else:
            T += exp(1.5)

    if (ami == "f" and sexe == "f") or (ami == "g" and sexe == "h"):
        T -= 1
    elif (ami == "f" and sexe == "g") or (ami == "g" and sexe == "f"):
        T += 2 * ex 

    if date != 0:
        D = (date * 2) / age
        if D > 10 or date > 20:
            T += D * age
        if D > 6:
            T += 2 * D
        elif D > 2:
            T += (date / 2) + 1
        else:
            T += date
    else:
        T -= 3

    if bodyc != 0:
        exbody = ex / bodyc
    else:
        exbody = 0

    

    # --- Nouvelles influences ---
    if trompe == "oui":
        T += bodyc * 2
        if plaisir == "oui":
            T += bodyc**2
        if refaire == "oui":
            T += exp(bodyc) 
    else:
        T -= date

    if maquillage == "full":
        T += ex * 2
    elif maquillage == "fond":
        T += ex
    elif maquillage == "eyeliner":
        T += 0
    elif maquillage == "creme":
        T -= 1

    if potes_vs_relation == "1":
        T += 2
    elif potes_vs_relation == "2":
        T += 1
    elif potes_vs_relation == "3":
        T += 0.5
    elif potes_vs_relation == "4":
        T -= 1

    if bodyc != 0 and age_vieux != 0:
        if age_vieux - age > 10:
            T += 5 + bodyc/2
        elif age_vieux - age > 5:
            T += 2
        elif age_vieux - age < 5:
            T += 1 

    if demi_famille == "oui":
        T += 100

    if ex > 7 or (exbody < 1 and exbody != 0):
            T += ex * bodyc
    elif ex > 4:
        T += ex
    elif ex >= 1:
            T += 6.7 
    else:
            T -= 0.3 
    
    if bz == "o":
            T *= 2.7
    

    def sigmoid_percent(T):
        if T <= 0:
            return round(-10 * log1p(abs(T)))  # pourcentage négatif progressif

        s = 100  # centre de la courbe à T = 100
        j = 1.02  # pour que T=3000 donne environ 97%
        return round(100 * (T**j) / (T**j + s**j), 2)
    
    pourcentage = sigmoid_percent(T)
    return T, pourcentage
