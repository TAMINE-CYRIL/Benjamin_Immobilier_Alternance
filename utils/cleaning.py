import regex as re


def normalisation_language(text):
    """
    Normalise le nombre donnée selon l'insertion des virgules/points dans le paramètre.
    """
    # Dans le cas où nous avons des virgules et des points
    if ',' in text and '.' in text:
        
        # Si on a la virgule avant le point : Format US
        if text.find(',') < text.find('.'):
            text = text.replace(',', '')
            
            
        # Sinon format européen
        else:
            text = text.replace('.', '')
            text = text.replace(',', '.')
            
    # Si on a que des points
    elif '.' in text:
        if text.count('.') > 1:
            text = text.replace('.', '')
        elif text.count('.') == 1:
            if re.match(r'\d+\.\d{3}$', text):
                text = text.replace('.', '')  
            
            
    # Si on a que des virgules
    elif ',' in text:
        if text.count(',') > 1:
            text = text.replace(',', '')
            

        else:
            text = text.replace(',', '.')

    return text


def extract_number(text, as_int=False):
    if not text or text == "N/A":
        return None
    if isinstance(text, (int, float)):
        value = float(text)
        return int(text) if as_int else value
    
    # Nettoyage initial
    text_cleaned = re.sub(r'M2|m2|m²|M²|€|EUR|/|\s+', '', text)

    # Gestion des multiplicateurs
    multiplier = 1
    if re.search(r'[kK]', text_cleaned):
        multiplier = 1000
        text_cleaned = re.sub(r'[kK]', '', text_cleaned)
    elif re.search(r'[mM](?!\d)', text_cleaned):
        multiplier = 1000000
        text_cleaned = re.sub(r'[mM](?!\d)', '', text_cleaned)


    # Détection et normalisation du format numérique
    text_cleaned = normalisation_language(text_cleaned)

    # Extraction finale du nombre
    match = re.search(r'\d*\.?\d+', text_cleaned)
    if not match:
        return None

    value = float(match.group()) * multiplier
    return int(value) if as_int else value


def calculation_price_square_meter(annonces):
    clean_annonces = []
    for annonce in annonces:
        if annonce.get("price_square_meter"):
            continue

        price = annonce.get("price")
        surface = annonce.get("surface")

        if price is None or surface is None or surface == 0:
            continue

        annonce["price_square_meter"] = round(price / surface, 2)
        clean_annonces.append(annonce)

    return clean_annonces



def normalization(annonces):
    """
    Normalise les champs prix et surface en entiers (ou None).
    """
    clean_annonces = []
    for annonce in annonces:
        annonce["price"] = extract_number(annonce.get("price"))
        annonce["surface"] = extract_number(annonce.get("surface"))
        annonce["bedrooms"] = extract_number(annonce.get("bedrooms"), as_int=True)
        annonce["zip_code"] = extract_number(annonce.get("zip_code"), as_int=True)
        clean_annonces.append(annonce)

    return clean_annonces







def filter_annonces(annonces):
    """
    Filtre les annonces pour ne garder que celles avec un prix et une surface valides.
    """
    filtrage = []
    clean_annonces = normalization(annonces)
    clean_annonces = calculation_price_square_meter(clean_annonces) 
    for annonce in clean_annonces:
        price = annonce.get("price")
        surface = annonce.get("surface")
        if price is None or surface is None :
            continue
        filtrage.append(annonce)
    return filtrage

