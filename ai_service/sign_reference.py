import os

BASE_DIR = os.path.dirname(__file__)
SIGNS_DIR = os.path.join(BASE_DIR, 'signs')
EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
SIGN_ORDER = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]


def normalize_letter(label):
    if label is None or label == '':
        return None
    value = str(label).strip().upper()
    if len(value) == 1 and (value.isdigit() or 'A' <= value <= 'Z'):
        return value
    return None


def get_sign_image_path(label):
    letter = normalize_letter(label)
    if not letter:
        return None

    for ext in EXTENSIONS:
        file_path = os.path.join(SIGNS_DIR, f'{letter}{ext}')
        if os.path.exists(file_path):
            return f'signs/{letter}{ext}'
    return None


def list_sign_files():
    if not os.path.isdir(SIGNS_DIR):
        return []

    signs = []
    for letter in SIGN_ORDER:
        image_url = get_sign_image_path(letter)
        if image_url:
            signs.append({'letter': letter, 'imageUrl': image_url})
    return signs


def attach_sign_reference(payload):
    if not isinstance(payload, dict):
        return payload

    label = payload.get('translation') or payload.get('result')
    sign_image_url = get_sign_image_path(label)

    result = dict(payload)
    result['signImageUrl'] = sign_image_url
    result['referenceSign'] = (
        {'letter': normalize_letter(label), 'imageUrl': sign_image_url}
        if sign_image_url
        else None
    )
    return result
