"""Offline publishing checks. Run with Python 3.11+ and requirements-dev.txt."""
import hashlib
import json
from pathlib import Path
import struct
import sys
from datetime import datetime
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = dict(zip(
    ['coquette-pink', 'soft-elegant', 'minimalist', 'halloween', 'christmas', 'fall', 'winter'],
    ['Coquette Pink', 'Soft Elegant', 'Minimalist', 'Halloween', 'Christmas', 'Fall', 'Winter']))


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def schema_check(data, name, root=ROOT):
    schema = load(root / 'schemas' / (name + '.schema.json'))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)


def indexed(values):
    result = {v['id']: v for v in values}
    require(len(result) == len(values), 'duplicate IDs')
    return result


def resource_check(value, base, suffix):
    # All remote references are relative to a trusted HTTPS feed origin.
    path = value['path']
    parts = path.split('/')
    require(all(p not in ('', '.', '..') for p in parts), 'unsafe resource path')
    target = (base / path).resolve()
    require(target.is_relative_to(base.resolve()), 'resource escapes release')
    require(target.suffix == suffix, 'wrong resource extension')
    data = target.read_bytes()
    require(len(data) == value['bytes'], 'resource byte count mismatch')
    require(hashlib.sha256(data).hexdigest() == value['sha256'], 'resource hash mismatch')
    return target, data


def utc(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def select_banner(home, now):
    """UTC start inclusive/end exclusive; highest priority then ascending ID."""
    active = [b for b in home['banners'] if utc(b['startsAt']) <= now < utc(b['endsAt'])]
    return sorted(active, key=lambda b: (-b['priority'], b['id']))[0] if active else home['defaultBanner']


def validate_catalog(catalog, base, legacy, root=ROOT):
    schema_check(catalog, 'catalog', root)
    families = indexed(catalog['families'])
    require(set(families) == set(FAMILIES), 'must contain exactly seven approved families')
    palettes = {}
    for fid, family in families.items():
        require(family['name'] == FAMILIES[fid], 'family name does not match ID')
        palettes[fid] = indexed(family['palettes'])
    assets = indexed(catalog['assets'])
    for asset in assets.values():
        _, data = resource_check(asset['resource'], base, '.png')
        require(data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR', 'invalid PNG header')
        require(struct.unpack('!II', data[16:24]) == (asset['width'], asset['height']), 'PNG dimensions mismatch')
    items = indexed(catalog['items'])
    for item in items.values():
        require(item['paletteId'] in palettes[item['familyId']], 'unknown palette')
        typ = item['type']
        if typ in ('wallpaper', 'sticker'):
            require(item['config']['assetId'] in assets, 'missing item asset')
        if typ == 'theme-pack' and 'components' in item:
            children = [items.get(cid) for cid in item['components']]
            require(all(child and child['type'] != 'theme-pack' for child in children), 'pack must reference individual items; cycles/nested packs prohibited')
            require(all(child['familyId'] == item['familyId'] and child['paletteId'] == item['paletteId'] for child in children), 'pack palette/family mismatch')
    originals = {t['id']: t for t in legacy['themes']}
    embedded = {i['id']: i['legacyTheme'] for i in items.values() if 'legacyTheme' in i}
    require(embedded == originals, 'all 13 legacy themes must be preserved exactly')
    require(all(i['legacyTheme']['id'] == i['id'] and i['legacyTheme']['palette'] == palettes[i['familyId']][i['paletteId']]['colors'] for i in items.values() if 'legacyTheme' in i), 'legacy identity/palette mismatch')
    home = catalog['home']
    indexed([home['defaultBanner']] + home['banners'])
    for banner in [home['defaultBanner']] + home['banners']:
        require(banner['imageId'] in assets, 'missing banner image')
        if 'startsAt' in banner:
            require(utc(banner['startsAt']) < utc(banner['endsAt']), 'banner schedule must have start before end')
        action = banner.get('action', {})
        if action.get('type') == 'open-item':
            require(action['itemId'] in items, 'missing banner action target')
        if action.get('type') == 'open-url':
            url = urlsplit(action['url'])
            require(url.scheme == 'https' and bool(url.hostname) and not url.username and not url.password and url.port in (None, 443), 'unsafe banner URL')


def validate(root=ROOT):
    legacy = load(root / 'widget-themes.json')
    schema_check(legacy, 'legacy', root)
    baseline = load(root / 'tests/legacy-baseline.json')
    require(hashlib.sha256((root / 'widget-themes.json').read_bytes()).hexdigest() == baseline['sha256'], 'legacy feed changed')
    require([t['id'] for t in legacy['themes']] == baseline['themeIds'], 'legacy theme IDs/order changed')
    base = root / 'content/v1'
    manifest = load(base / 'manifest.json')
    schema_check(manifest, 'manifest', root)
    path, data = resource_check(manifest['catalog'], base, '.json')
    require(len(data) <= 1048576, 'catalog exceeds 1 MiB')
    require(manifest['catalog']['path'] == 'releases/' + manifest['release'] + '/catalog.json', 'manifest release/path mismatch')
    # Validate all immutable releases, including those no longer selected.
    releases = sorted((base / 'releases').glob('*/catalog.json'))
    require(bool(releases), 'no releases')
    for release in releases:
        catalog = load(release)
        require(catalog['release'] == release.parent.name, 'catalog release/directory mismatch')
        require(release.stat().st_size <= 1048576, 'catalog exceeds 1 MiB')
        validate_catalog(catalog, release.parent, legacy, root)
    require(load(path)['release'] == manifest['release'], 'manifest/catalog release mismatch')
    return f'Validated {len(releases)} release(s), 13 unchanged legacy themes, 7 families / 21 palettes.'


if __name__ == '__main__':
    try:
        print(validate())
    except Exception as error:
        print('Validation failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
