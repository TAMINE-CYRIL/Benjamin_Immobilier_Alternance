import math

import regex as re


ANNONCE_FIELDS = [
    "title",
    "url",
    "city",
    "zip_code",
    "department",
    "price",
    "surface",
    "rooms",
    "price_square_meter",
    "adjuged_price",
    "agency",
    "source_site",
    "type_bien",
    "energy_class",
    "sale_date",
    "visit_date",
    "description",
    "photos",
    "address",
    "publication_date",
    "location",
]

SCORING_REQUIRED_FIELDS = ("zip_code", "type_bien", "price_square_meter")


def blank_to_none(value):
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned or cleaned.upper() == "N/A":
            return None
        return cleaned
    return value


def extract_department(zip_code: str) -> str | None:
    zip_code = blank_to_none(zip_code)
    if not zip_code:
        return None

    zip_code = str(zip_code)
    if re.match(r"^\d{5}$", zip_code):
        return zip_code[:2]
    return None


def normalisation_language(text):
    if "," in text and "." in text:
        if text.find(",") < text.find("."):
            text = text.replace(",", "")
        else:
            text = text.replace(".", "")
            text = text.replace(",", ".")
    elif "." in text:
        if text.count(".") > 1:
            text = text.replace(".", "")
        elif text.count(".") == 1 and re.match(r"\d+\.\d{3}$", text):
            text = text.replace(".", "")
    elif "," in text:
        if text.count(",") > 1:
            text = text.replace(",", "")
        else:
            text = text.replace(",", ".")
    return text


def extract_number(text, as_int=False):
    text = blank_to_none(text)
    if text is None:
        return None
    if isinstance(text, (int, float)):
        if isinstance(text, float) and (math.isnan(text) or math.isinf(text)):
            return None
        return int(text) if as_int else float(text)

    text = str(text).strip()

    multiplier = 1
    multiplier_match = re.search(r"([kK]|M|m)(?=[^\d\u00b2]|$)", text)
    if multiplier_match:
        multiplier = 1_000 if multiplier_match.group(1).lower() == "k" else 1_000_000
        text = text[:multiplier_match.start()] + text[multiplier_match.end():]

    text_cleaned = re.sub(r"M2|m2|m\u00b2|M\u00b2|\u20ac|EUR|/|\s+", "", text)
    text_cleaned = normalisation_language(text_cleaned)

    match = re.search(r"[+-]?\d+(\.\d+)?", text_cleaned)
    if not match:
        return None

    value = float(match.group()) * multiplier
    return int(value) if as_int else value


def _normalize_text(value):
    value = blank_to_none(value)
    if isinstance(value, str):
        return value.strip()
    return value


def _normalize_list(value):
    value = blank_to_none(value)
    if value is None:
        return None
    if isinstance(value, list):
        cleaned = [item for item in (_normalize_text(item) for item in value) if item is not None]
        return cleaned or None

    normalized_value = _normalize_text(value)
    return [normalized_value] if normalized_value is not None else None


def _is_valid_zip_code(zip_code):
    return bool(zip_code and re.match(r"^\d{5}$", str(zip_code)))


def _extract_zip_code_from_text(*values):
    for value in values:
        value = blank_to_none(value)
        if value is None:
            continue

        match = re.search(r"\b(\d{5})\b", str(value))
        if match:
            return match.group(1)

    return None


def _sanitize_positive_number(value):
    if value is None:
        return None
    return value if value > 0 else None


def _compute_surface(price, price_square_meter):
    if not price or not price_square_meter or price_square_meter <= 0:
        return None
    surface = round(float(price) / float(price_square_meter), 2)
    return surface if surface > 0 else None


def _compute_price_square_meter(price, surface):
    if not price or not surface or surface <= 0:
        return None
    price_square_meter = round(float(price) / float(surface), 2)
    return price_square_meter if price_square_meter > 0 else None


def normalize_annonce(raw_annonce):
    annonce = {field: None for field in ANNONCE_FIELDS}

    for key, value in (raw_annonce or {}).items():
        if key in annonce:
            annonce[key] = value

    annonce["title"] = _normalize_text(annonce.get("title"))
    annonce["url"] = _normalize_text(annonce.get("url"))
    annonce["city"] = _normalize_text(annonce.get("city"))
    annonce["zip_code"] = _normalize_text(annonce.get("zip_code"))
    annonce["agency"] = _normalize_text(annonce.get("agency"))
    annonce["source_site"] = _normalize_text(annonce.get("source_site"))
    annonce["type_bien"] = _normalize_text(annonce.get("type_bien"))
    annonce["energy_class"] = _normalize_text(annonce.get("energy_class"))
    annonce["sale_date"] = _normalize_text(annonce.get("sale_date"))
    annonce["visit_date"] = _normalize_text(annonce.get("visit_date"))
    annonce["description"] = _normalize_text(annonce.get("description"))
    annonce["address"] = _normalize_text(annonce.get("address"))
    annonce["publication_date"] = _normalize_text(annonce.get("publication_date"))
    annonce["location"] = annonce.get("location")
    annonce["photos"] = _normalize_list(annonce.get("photos"))

    annonce["price"] = _sanitize_positive_number(extract_number(annonce.get("price")))
    annonce["surface"] = _sanitize_positive_number(extract_number(annonce.get("surface")))
    annonce["price_square_meter"] = _sanitize_positive_number(extract_number(annonce.get("price_square_meter")))
    annonce["adjuged_price"] = _sanitize_positive_number(extract_number(annonce.get("adjuged_price")))
    annonce["rooms"] = _sanitize_positive_number(extract_number(annonce.get("rooms"), as_int=True))

    if not _is_valid_zip_code(annonce.get("zip_code")):
        annonce["zip_code"] = _extract_zip_code_from_text(
            annonce.get("zip_code"),
            annonce.get("city"),
            annonce.get("address"),
        )

    if not _is_valid_zip_code(annonce.get("zip_code")):
        annonce["zip_code"] = None

    if annonce["surface"] is None:
        annonce["surface"] = _compute_surface(annonce["price"], annonce["price_square_meter"])

    if annonce["price_square_meter"] is None:
        annonce["price_square_meter"] = _compute_price_square_meter(annonce["price"], annonce["surface"])

    annonce["department"] = extract_department(annonce.get("zip_code"))
    return annonce


def classify_annonce(annonce):
    if not annonce.get("url"):
        return "skipped"

    missing_scoring_fields = [
        field for field in SCORING_REQUIRED_FIELDS
        if annonce.get(field) in (None, "")
    ]
    if not missing_scoring_fields:
        return "valid_scoring"

    useful_fields = ("price", "surface", "city", "zip_code", "type_bien", "description")
    if any(annonce.get(field) not in (None, "", []) for field in useful_fields):
        return "valid_no_scoring"

    return "partial"


def normalize_annonces(annonces):
    normalized = []
    summary = {
        "total": 0,
        "valid_scoring": 0,
        "valid_no_scoring": 0,
        "partial": 0,
        "skipped": 0,
        "eligible_for_scoring": 0,
        "not_scored_missing_fields": 0,
    }

    for raw_annonce in annonces or []:
        summary["total"] += 1
        annonce = normalize_annonce(raw_annonce)
        status = classify_annonce(annonce)
        annonce["_validation_status"] = status
        normalized.append(annonce)
        summary[status] += 1

    summary["eligible_for_scoring"] = summary["valid_scoring"]
    summary["not_scored_missing_fields"] = (
        summary["valid_no_scoring"] + summary["partial"] + summary["skipped"]
    )
    return normalized, summary


def normalization(annonces):
    normalized, _ = normalize_annonces(annonces)
    return normalized


def filter_annonces(annonces):
    normalized, _ = normalize_annonces(annonces)
    return normalized
