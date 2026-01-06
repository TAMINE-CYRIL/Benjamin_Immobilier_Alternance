def evaluate_annonce(prix_annonce_m2, prix_marche_m2, nb_transactions):
    if not prix_annonce_m2 or not prix_marche_m2:
        return None

    ecart = (prix_annonce_m2 - prix_marche_m2) / prix_marche_m2

    # score de base
    if ecart <= -0.30:
        score = 100
    elif ecart <= -0.20:
        score = 90
    elif ecart <= -0.10:
        score = 75
    elif ecart <= -0.05:
        score = 65
    elif ecart <= 0.05:
        score = 50
    elif ecart <= 0.15:
        score = 30
    else:
        score = 10

    if nb_transactions >= 100:
        score += 10
    elif nb_transactions >= 50:
        score += 5
    elif nb_transactions < 20:
        score -= 10

    return max(0, min(100, score))

