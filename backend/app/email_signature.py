"""Build signatures from account data and verified public brand contacts, never model guesses."""
import json
from pathlib import Path

path = Path(__file__).resolve().parents[2] / 'shared/message_catalog.json'
if not path.is_file():
    path = Path(__file__).with_name('_vercel_data') / 'message_catalog.json'
BRAND_CONTACTS = json.loads(path.read_text(encoding='utf-8'))['brandContacts']


def contact_for(code: str) -> dict:
    return BRAND_CONTACTS.get(code.upper(), {})


def signature(sender: dict, *, english: bool = False) -> str:
    brand = contact_for(sender.get('organization_code') or sender.get('organization', ''))
    return '\n'.join(str(value).strip() for value in [
        sender.get('name'),
        sender.get('organization'),
        sender.get('phone') or ('[Add phone number in My profile]' if english else '[Dopunite telefon u Moj profil]'),
        brand.get('website'),
        brand.get('address'),
    ] if value and str(value).strip())
