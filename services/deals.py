import re
import unicodedata

from database.connection import get_connection


SCORE_VERSION = "2.1"
COMPONENT_WEIGHTS = {
    "market_discount": 40,
    "land_potential": 30,
    "liquidity": 10,
    "listing_signals": 15,
    "energy": 5,
}

POSITIVE_SIGNALS = {
    "terrain divisible": 3,
    "parcelle divisible": 3,
    "division parcellaire": 3,
    "fort potentiel": 2,
    "a renover": 2,
    "travaux a prevoir": 1.5,
    "dependance": 1.5,
    "permis accorde": 2,
    "succession": 1.5,
    "vente urgente": 1,
    "demolition": 1,
}

RISK_SIGNALS = {
    "viager": "Vente en viager",
    "occupe": "Bien potentiellement occupé",
    "indivision": "Situation d'indivision mentionnée",
    "servitude": "Servitude mentionnée dans l'annonce",
    "non constructible": "Terrain annoncé comme non constructible",
}


NB_TRANSACTION_STATS = None


def load_nb_transaction_stats(force_reload=False):
    """
    Charge les statistiques globales du nombre de transactions à partir de la table dvf_nb_transactions_stats.
    """
    global NB_TRANSACTION_STATS

    if NB_TRANSACTION_STATS is not None and not force_reload:
        return NB_TRANSACTION_STATS

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT q1, median, q3
            FROM dvf_nb_transactions_stats
            WHERE scope = 'global'
            """
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not row:
        raise RuntimeError("Quartiles nb_transactions non initialises")

    NB_TRANSACTION_STATS = {
        "q1": row[0],
        "median": row[1],
        "q3": row[2],
    }
    return NB_TRANSACTION_STATS


def evaluate_annonce(
    prix_annonce_m2,
    prix_m2_med,
    prix_m2_q1,
    prix_m2_q3,
    nb_transactions,
    nb_transaction_stats=None,
):
    """
    Evalue une annonce en calculant un score de 0 à 100 basé sur l'écart de son prix au m2 par rapport à la médiane,
    ajusté par la position de son prix dans les quartiles et le nombre de transactions dans
    """
    if not all([prix_annonce_m2, prix_m2_med, prix_m2_q1, prix_m2_q3]):
        return None

    ecart = (prix_annonce_m2 - prix_m2_med) / prix_m2_med

    if ecart <= -0.30:
        score_decote = 80
    elif ecart <= -0.20:
        score_decote = 72
    elif ecart <= -0.10:
        score_decote = 64
    elif ecart <= -0.05:
        score_decote = 58
    elif ecart <= 0.05:
        score_decote = 50
    elif ecart <= 0.15:
        score_decote = 35
    else:
        score_decote = 20

    bonus_quartile = 0
    if prix_m2_q3 > prix_m2_q1:
        position = (prix_annonce_m2 - prix_m2_q1) / (prix_m2_q3 - prix_m2_q1)

        if position < 0:
            bonus_quartile = 15
        elif position < 0.5:
            bonus_quartile = 8
        elif position < 1:
            bonus_quartile = 0
        elif position < 1.5:
            bonus_quartile = -10
        else:
            bonus_quartile = -20

    stats = nb_transaction_stats or load_nb_transaction_stats()
    q1 = stats["q1"]
    median = stats["median"]
    q3 = stats["q3"]

    if nb_transactions <= q1:
        confidence = 0.6
    elif nb_transactions <= median:
        confidence = 0.8
    elif nb_transactions <= q3:
        confidence = 1.0
    else:
        confidence = 1.1

    score = 50 + (score_decote - 50) * confidence
    score += bonus_quartile * confidence

    return max(0, min(100, round(score, 1)))


def _number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _canonical_text(*values):
    text = " ".join(str(value) for value in values if value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text.lower()).strip()


def _market_component(price_m2, median):
    price_m2 = _number(price_m2)
    median = _number(median)
    if not price_m2 or not median:
        return 20.0, None, "Référence de prix indisponible"

    discount = (median - price_m2) / median
    score = max(0, min(40, 20 + discount * 66))
    percentage = round(discount * 100)
    if percentage > 0:
        reason = f"Prix au m² inférieur de {percentage} % à la médiane DVF"
    elif percentage < 0:
        reason = f"Prix au m² supérieur de {abs(percentage)} % à la médiane DVF"
    else:
        reason = "Prix au m² proche de la médiane DVF"
    return round(score, 1), discount, reason


def _land_component(annonce):
    parcel_surface = _number(annonce.get("parcel_surface"))
    built_surface = _number(annonce.get("surface"))
    property_type = _canonical_text(annonce.get("type_bien"))
    text = _canonical_text(annonce.get("title"), annonce.get("description"))
    score = 15.0
    reasons = []

    if parcel_surface:
        if parcel_surface >= 1500:
            score = 25
        elif parcel_surface >= 800:
            score = 21
        elif parcel_surface >= 400:
            score = 16
        elif parcel_surface >= 200:
            score = 12
        else:
            score = 8
        reasons.append(f"Parcelle cadastrale de {round(parcel_surface):,} m²".replace(",", " "))

        if built_surface and parcel_surface >= built_surface * 4:
            score += 3
            reasons.append("Emprise bâtie faible par rapport à la parcelle")
    else:
        reasons.append("Surface cadastrale non disponible")

    if "terrain" in property_type:
        score += 2
        reasons.append("Bien de type terrain")
    if any(signal in text for signal in ("terrain divisible", "parcelle divisible", "division parcellaire")):
        score += 3
        reasons.append("Potentiel de division mentionné")

    return round(max(0, min(30, score)), 1), reasons, parcel_surface is not None


def _liquidity_component(nb_transactions, stats):
    transactions = _number(nb_transactions)
    if transactions is None or not stats:
        return 5.0, "Volume de transactions comparable indisponible", False

    q1 = _number(stats.get("q1")) or 0
    median = _number(stats.get("median")) or q1
    q3 = _number(stats.get("q3")) or median
    if transactions <= q1:
        score = 3
        label = "Marché local peu liquide"
    elif transactions <= median:
        score = 5
        label = "Liquidité locale modérée"
    elif transactions <= q3:
        score = 8
        label = "Marché local actif"
    else:
        score = 10
        label = "Marché local très actif"
    return score, f"{label} ({round(transactions)} transactions comparables)", True


def _listing_component(annonce):
    text = _canonical_text(annonce.get("title"), annonce.get("description"))
    score = 7.5
    reasons = []
    risks = []

    for signal, bonus in POSITIVE_SIGNALS.items():
        if signal in text:
            score += bonus
            reasons.append(f"Signal détecté : « {signal} »")
    for signal, label in RISK_SIGNALS.items():
        if signal in text:
            score -= 2
            risks.append(label)

    if not text:
        reasons.append("Texte d'annonce indisponible")
    elif not reasons:
        reasons.append("Aucun signal textuel fort détecté")
    return round(max(0, min(15, score)), 1), reasons, risks, bool(text)


def _energy_component(energy_class):
    energy_class = (energy_class or "").strip().upper()
    mapping = {"A": 5, "B": 4.5, "C": 4, "D": 3, "E": 2, "F": 1.5, "G": 1}
    if energy_class not in mapping:
        return 2.5, "DPE non disponible", False
    return mapping[energy_class], f"Performance énergétique classée {energy_class}", True


def evaluate_opportunity(annonce, dvf_reference=None, transaction_stats=None):
    """
    Calcule un score V2 explicable. Les valeurs inconnues reçoivent une base
    neutre et réduisent le score de confiance plutôt que de pénaliser le bien.
    """
    reference = dvf_reference or {}
    components = {}
    reasons = []
    risks = []
    available_weight = 0

    market_score, discount, market_reason = _market_component(
        annonce.get("price_square_meter"),
        reference.get("prix_m2_med"),
    )
    components["market_discount"] = market_score
    reasons.append(market_reason)
    if discount is not None:
        available_weight += COMPONENT_WEIGHTS["market_discount"]
        if discount < -0.5:
            risks.append("Prix très supérieur au marché local")
        elif discount > 0.55:
            risks.append("Décote extrême à vérifier")

    land_score, land_reasons, land_known = _land_component(annonce)
    components["land_potential"] = land_score
    reasons.extend(land_reasons)
    if land_known:
        available_weight += COMPONENT_WEIGHTS["land_potential"]

    liquidity_score, liquidity_reason, liquidity_known = _liquidity_component(
        reference.get("nb_transactions"),
        transaction_stats,
    )
    components["liquidity"] = liquidity_score
    reasons.append(liquidity_reason)
    if liquidity_known:
        available_weight += COMPONENT_WEIGHTS["liquidity"]

    listing_score, listing_reasons, listing_risks, listing_known = _listing_component(annonce)
    components["listing_signals"] = listing_score
    reasons.extend(listing_reasons)
    risks.extend(listing_risks)
    if listing_known:
        available_weight += COMPONENT_WEIGHTS["listing_signals"]

    energy_score, energy_reason, energy_known = _energy_component(annonce.get("energy_class"))
    components["energy"] = energy_score
    reasons.append(energy_reason)
    if energy_known:
        available_weight += COMPONENT_WEIGHTS["energy"]

    total = round(sum(components.values()), 1)
    confidence = round(min(100, available_weight + (10 if reference.get("nb_transactions") else 0)))
    if any("non constructible" in risk.lower() for risk in risks):
        risk_level = "high"
    elif len(risks) >= 2 or confidence < 50:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "total": total,
        "confidence": confidence,
        "risk_level": risk_level,
        "components": components,
        "reasons": reasons,
        "risks": list(dict.fromkeys(risks)),
        "version": SCORE_VERSION,
        "market": {
            "price_m2": _number(annonce.get("price_square_meter")),
            "median_price_m2": _number(reference.get("prix_m2_med")),
            "discount_ratio": round(discount, 4) if discount is not None else None,
            "transactions": _number(reference.get("nb_transactions")),
        },
    }
