import regex as re


def extract_number(text):
    """
    Extrait un nombre entier d'une chaîne de caractères.
    Retourne None si 'N/A' ou pas de chiffre.
    """
    if not text or text == "N/A":
        return None
    
    # Condition de sécurité au cas où la fonction est déjà utilisée sur un entier (BienIci).
    if isinstance(text, int):
        return text
    
    digits = ""

    # Supprimer les unités courantes
    text_cleaned = re.sub(r'M2|m2|m²|M²', '', text)
    

    for c in text_cleaned:
        if c in "0123456789":
            digits += c
    if digits == "":
        return None
    return int(digits)


def normalization(annonces):
    """
    Normalise les champs prix et surface en entiers (ou None).
    """
    clean_annonces = []
    for annonce in annonces:
        annonce["price"] = extract_number(annonce.get("price"))
        annonce["surface"] = extract_number(annonce.get("surface"))
        
        clean_annonces.append(annonce)

    return clean_annonces

def filter_annonces(annonces):
    filtrage = []
    clean_annonces=normalization(annonces)
    for annonce in clean_annonces:
        price = annonce.get("price")
        surface = annonce.get("surface")
        if price is None and surface is None :
            continue
        filtrage.append(annonce)
    return filtrage
