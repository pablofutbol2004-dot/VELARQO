from lib.normalization.normalize import normalize_email, normalize_phone, normalize_postcode


def normalize_name(name: str) -> str:
    if not name:
        return ""
    return " ".join(part.capitalize() for part in name.strip().split())


def normalize_record(raw: dict) -> dict:
    return {
        **raw,
        "name": normalize_name(raw.get("name", "")),
        "email": normalize_email(raw.get("email", "")),
        "phone": normalize_phone(raw.get("phone", "")),
        "postcode": normalize_postcode(raw.get("postcode", "")),
        "normalized": True,
    }
