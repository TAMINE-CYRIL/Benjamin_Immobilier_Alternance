import regex as re


def extract_number(text):
    """
    Extrait un nombre d'une chaîne de caractères.
    Retourne None si 'N/A' ou pas de chiffre.
    """
    if not text or text == "N/A":
        return None
    if isinstance(text, (int, float)):
        return float(text)
    
    if re.search(r'k|K', text):
        multiplier = 1000
        text = re.sub(r'k|K', '', text)
    else:
        multiplier = 1
    
    text_cleaned = re.sub(r'M2|m2|m²|M²|€|EUR|/', '', text)
    text_cleaned = text_cleaned.replace(',', '.')
    text_cleaned = text_cleaned.replace(' ', '')
    part_text = ''
    
    parts = text_cleaned.split('.')    
    if len(parts) > 2:
        text_cleaned = part_text.join(parts[:-1]) + '.' + parts[-1]
    elif len(parts) == 2 and len(parts[1]) > 2:
        text_cleaned = part_text.join(parts)
    
    # Extraire tous les chiffres et le point décimal
    digits = re.sub(r'[^\d.]', '', text_cleaned)
    if not digits or digits == '.':
        return None
    
    return float(digits) * multiplier



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
        if price is None or surface is None :
            continue
        filtrage.append(annonce)
    return filtrage
