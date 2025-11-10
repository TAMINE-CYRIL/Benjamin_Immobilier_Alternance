import regex as re

def normalisation_language(text):
    """
    Normalise le nombre selon l'insertion des virgules/points dans le paramètre.
    """
    if ',' in text and '.' in text:
        if text.find(',') < text.find('.'):
            text = text.replace(',', '')
        else:
            text = text.replace('.', '')
            text = text.replace(',', '.')
    elif '.' in text:
        if text.count('.') > 1:
            text = text.replace('.', '')
        elif text.count('.') == 1:
            if re.match(r'\d+\.\d{3}$', text):
                text = text.replace('.', '')  
    elif ',' in text:
        if text.count(',') > 1:
            text = text.replace(',', '')
        else:
            text = text.replace(',', '.')
    return text

def extract_number(text, as_int=False):
    """
    Extrait un nombre depuis une chaîne de caractères.
    Gère les formats avec k/K (milliers) et m/M (millions).
    """
    if not text or text == "N/A":
        return None
    if isinstance(text, (int, float)):
        return int(text) if as_int else float(text)

    text = text.strip()

    # Détection du multiplicateur k/K ou M/m (juste avant symbole ou fin)
    multiplier = 1
    m = re.search(r'([kK]|M|m)(?=[^\d²]|$)', text)
    if m:
        if m.group(1).lower() == 'k':
            multiplier = 1_000
        else:
            multiplier = 1_000_000
        # retirer uniquement le multiplicateur
        text = text[:m.start()] + text[m.end():]

    # Nettoyage : retirer €, m², m2, M2, /, espaces
    text_cleaned = re.sub(r'M2|m2|m²|M²|€|EUR|/|\s+', '', text)

    # Normalisation format européen / US
    text_cleaned = normalisation_language(text_cleaned)

    # Extraction du nombre
    match = re.search(r'\d+(\.\d+)?', text_cleaned)
    if not match:
        return None

    value = float(match.group()) * multiplier
    return int(value) if as_int else value

def normalization(annonces):
    """
    Normalise les champs, afin de récupérer des nombres pour certaines valeurs de nos annonces. (ou None).
    """
    clean_annonces = []
    
    for annonce in annonces:
        annonce["price"] = extract_number(annonce.get("price"))
        annonce["surface"] = extract_number(annonce.get("surface"))
        annonce["price_square_meter"] = extract_number(annonce.get("price_square_meter"))
        annonce["adjuged_price"] = extract_number(annonce.get("adjuged_price"))
        annonce["rooms"] = extract_number(annonce.get("rooms"), as_int=True)
        annonce["zip_code"] = extract_number(annonce.get("zip_code"), as_int=True)
        clean_annonces.append(annonce)
    return clean_annonces


def filter_annonces(annonces):
    """
    Filtre les annonces pour ne garder que celles avec un prix et une surface valides.
    """
    clean_annonces = normalization(annonces)
    return clean_annonces
