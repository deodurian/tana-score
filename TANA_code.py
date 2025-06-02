from math import *

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
        age_vieux = int(donnees.get("age_vieux", 0)) if bodyc != 0 else 0
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

    maquillage = donnees.get("maquillage")  # full/juste fond/eyeliner/creme
    potes_vs_relation = donnees.get("potes_relation")  # 1/2/3/4
    # age_vieux already converted above
    demi_famille = donnees.get("demi_famille")  # oui/non

    T = 0
    if sexe == "f":
        T = 1

    if premier != 0:
        if (age - premier) == 0:
            n = bodyc
        else:
            n = bodyc / (age - premier)
        T = bodyc * 2
        if bodyc != 0 and n > 1:
            T += 2 + n
    else:
        bodyc = 0

    if premier >= 16:
        T = 4
    elif premier == 0:
        T = 0
    else:
        T += 4 + abs(16 - premier)

    if score > 1_000_000:
        T += log(score)
    elif score > 500_000:
        T += log(score) - 1
    elif score > 200_000:
        T += log(score) - 2
    elif score > 100_000:
        T += 2
    elif score > 50_000:
        T += 1

    if abo != 0:
        ratio = insta / abo
        if ratio >= 10 and insta > 10_000:
            T += ratio - 3
        elif ratio >= 4 or insta > 900:
            T += ratio - 1
        elif ratio >= 1 or insta > 400 or abo > insta:
            T += ratio
        elif ratio < 1:
            T += 1
        elif ratio < 0.5:
            T -= ratio
    else:
        ratio = 1

    if chien == "c":
        T += (ratio + bodyc + ex + date) * 3
    elif chien == "b" and (age - premier + 1) > 0 and bodyc / (age - premier + 1) > 1.2:
        T += bodyc * n
    elif chien == "b":
        T -= exp(-1.3)

    if (ami == "f" and sexe == "f") or (ami == "g" and sexe == "h"):
        T -= 1
    elif (ami == "f" and sexe == "g") or (ami == "g" and sexe == "f"):
        T += 2

    if date != 0:
        D = (date * 2) / age
        if D > 10 or date > 20:
            T += D * 1.3
        if D > 6:
            T += D
        elif D > 2:
            T += (date / D) + 1
        else:
            T += 1
    else:
        T -= 0.3

    if bodyc != 0:
        exbody = ex / bodyc
    else:
        exbody = 0

    

    # --- Nouvelles influences ---
    if trompe == "oui":
        T += 2
        if plaisir == "oui":
            T += bodyc*1.5
        if refaire == "oui":
            T *= 1.4 
        else:
            T -= 1

    if maquillage == "full":
        T += 5
    elif maquillage == "juste fond":
        T += 3
    elif maquillage == "eyeliner":
        T += 1
    elif maquillage == "creme":
        T -= 3

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
        T += 10

    if ex > 7 or (exbody < 1 and exbody != 0):
            T += ex * bodyc
    elif ex > 4:
        T += ex
    elif ex >= 1:
            T += 1
    else:
            T -= 0.3
    
    if bz == "o":
            T *= 1.7
    if T<0: 
        T=0

    def sigmoid_percent(T, x0=70, k=0.009):
        return round(100 / (1 + exp(-k * (T - x0))))
    
    pourcentage = sigmoid_percent(T)
    return T, pourcentage
