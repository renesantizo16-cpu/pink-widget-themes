import copy
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from jsonschema import ValidationError
from scripts.validate_content import (ROOT, load, validate, validate_catalog,
                                      resource_check, schema_check, select_banner)


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.base = ROOT / 'content/v1/releases/1.0.0'
        self.catalog = load(self.base / 'catalog.json')
        self.legacy = load(ROOT / 'widget-themes.json')

    def invalid(self, mutate):
        data = copy.deepcopy(self.catalog)
        mutate(data)
        with self.assertRaises((ValueError, ValidationError)):
            validate_catalog(data, self.base, self.legacy)

    def test_repository(self):
        self.assertIn('13 unchanged', validate())

    def test_all_six_content_types(self):
        self.assertEqual({i['type'] for i in self.catalog['items']},
                         {'clock', 'calendar', 'note', 'wallpaper', 'sticker', 'theme-pack'})

    def test_unknown_major(self):
        self.invalid(lambda c: c.update(schemaVersion=2))

    def test_missing_family(self):
        self.invalid(lambda c: c['families'].pop())

    def test_fourth_palette(self):
        self.invalid(lambda c: c['families'][0]['palettes'].append(c['families'][0]['palettes'][0]))

    def test_duplicate_palette(self):
        self.invalid(lambda c: c['families'][0]['palettes'].__setitem__(1, c['families'][0]['palettes'][0]))

    def test_family_name(self):
        self.invalid(lambda c: c['families'][0].update(name='Winter'))

    def test_missing_palette(self):
        self.invalid(lambda c: c['items'][0].update(paletteId='absent'))

    def test_duplicate_item(self):
        self.invalid(lambda c: c['items'].append(c['items'][0]))

    def test_changed_legacy(self):
        self.invalid(lambda c: c['items'][0]['legacyTheme'].update(note='Changed'))

    def test_missing_legacy(self):
        self.invalid(lambda c: c['items'].pop(0))

    def test_bad_color(self):
        self.invalid(lambda c: c['families'][0]['palettes'][0]['colors'].update(bg='pink'))

    def test_missing_asset(self):
        self.invalid(lambda c: c['items'][-2]['config'].update(assetId='absent'))

    def test_unknown_config(self):
        self.invalid(lambda c: c['items'][-6]['config'].update(script='run'))

    def test_missing_pack_member(self):
        self.invalid(lambda c: c['items'][-1]['components'].append('absent'))

    def test_nested_pack_cycle(self):
        self.invalid(lambda c: c['items'][-1]['components'].append(c['items'][-1]['id']))

    def test_hash_and_size(self):
        for field, value in [('sha256', '0'*64), ('bytes', 1)]:
            with self.subTest(field=field):
                self.invalid(lambda c: c['assets'][0]['resource'].update({field: value}))

    def test_dimensions(self):
        self.invalid(lambda c: c['assets'][0].update(width=12))

    def test_traversal(self):
        for path in ['../widget-themes.json', '/etc/passwd', 'https://example.com/a.png', 'assets/../banner.png']:
            with self.subTest(path=path):
                self.invalid(lambda c: c['assets'][0]['resource'].update(path=path))

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'release'
            base.mkdir()
            (base / 'escape.png').symlink_to(ROOT / 'widget-themes.json')
            with self.assertRaises(ValueError):
                resource_check({'path':'escape.png'}, base, '.png')

    def test_schedule(self):
        b = self.catalog['home']['banners'][0]
        for value in [b['startsAt'], '2026-09-01T00:00:00Z', 'not-a-date', '2026-10-01T00:00:00']:
            with self.subTest(value=value):
                self.invalid(lambda c: c['home']['banners'][0].update(endsAt=value))

    def test_fallback_cannot_expire(self):
        self.invalid(lambda c: c['home']['defaultBanner'].update(endsAt='2026-12-01T00:00:00Z'))

    def test_banner_references(self):
        self.invalid(lambda c: c['home']['defaultBanner']['image'].update(assetId='absent'))
        self.invalid(lambda c: c['home']['banners'][0]['button']['action'].update(itemId='absent'))

    def test_url_action(self):
        action = {'type':'open-url', 'url':'https://example.com/themes', 'label':'Explore'}
        c = copy.deepcopy(self.catalog)
        c['home']['defaultBanner']['action'] = action
        validate_catalog(c, self.base, self.legacy)
        for url in ['http://example.com', 'file:///etc/passwd', 'javascript:alert(1)', 'https://user:pass@example.com/', 'https://example.com:444/']:
            with self.subTest(url=url):
                self.invalid(lambda c: c['home']['defaultBanner'].update(action=dict(action, url=url)))

    def test_schedule_boundaries_and_ties(self):
        home = copy.deepcopy(self.catalog['home'])
        def at(value):
            return select_banner(home, datetime.fromisoformat(value.replace('Z', '+00:00')))['id']
        self.assertEqual(at('2026-09-30T23:59:59Z'), 'welcome')
        self.assertEqual(at('2026-10-01T00:00:00Z'), 'fall-example')
        self.assertEqual(at('2026-12-01T00:00:00Z'), 'welcome')
        second = dict(home['banners'][0], id='another', priority=11)
        home['banners'].append(second)
        self.assertEqual(at('2026-10-01T00:00:00Z'), 'another')
        second['priority'] = 10
        self.assertEqual(at('2026-10-01T00:00:00Z'), 'another')

    def test_exact_approved_palette_lineup(self):
        expected = {
            'Coquette Pink': ['Classic Coquette', 'Rose Petal', 'Champagne Blush'],
            'Soft Elegant': ['Warm Linen', 'Botanical Blush', 'Taupe Rose'],
            'Minimalist': ['Warm Minimal', 'Stone & Blush', 'Charcoal Contrast'],
            'Halloween': ['Pink Pumpkin Patch', 'Lavender Ghost', 'Midnight Witch'],
            'Christmas': ['Classic Christmas', 'Cozy Hearth', 'Snowy Tradition'],
            'Fall': ['Harvest Amber', 'Pumpkin Spice', 'Maple Rose'],
            'Winter': ['Frosted Blue', 'Silver Pine', 'Soft Snow'],
        }
        self.assertEqual({f['name']: [p['name'] for p in f['palettes']]
                          for f in self.catalog['families']}, expected)
        palettes = [p for f in self.catalog['families'] for p in f['palettes']]
        self.assertEqual(len({p['id'] for p in palettes}), 21)
        self.assertTrue(set(p['id'] for p in palettes).isdisjoint(
            t['id'] for t in self.legacy['themes']))
        self.assertEqual(len({tuple(p['colors'].values()) for p in palettes}), 21)

    def test_unapproved_palette_name_or_id(self):
        self.invalid(lambda c: c['families'][0]['palettes'][0].update(name='Strawberry Milk'))
        self.invalid(lambda c: c['families'][0]['palettes'][0].update(id='strawberry-milk'))

    def test_classic_christmas_traditional_colors(self):
        colors = next(p['colors'] for f in self.catalog['families']
                      for p in f['palettes'] if p['name'] == 'Classic Christmas')
        rgb = lambda color: tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        red, green, gold = (rgb(colors[k]) for k in ['accent', 'ink', 'edge'])
        self.assertGreater(red[0], max(red[1:]))
        self.assertGreater(green[1], max(green[0], green[2]))
        self.assertGreater(gold[0], gold[1])
        self.assertGreater(gold[1], gold[2])

    def test_legacy_rendering_is_independent_of_new_palettes(self):
        originals = {t['id']: t for t in self.legacy['themes']}
        families = {f['id']: f for f in self.catalog['families']}
        differences = 0
        for item in self.catalog['items']:
            if 'legacyTheme' not in item:
                continue
            self.assertEqual(item['legacyTheme'], originals[item['id']])
            colors = next(p['colors'] for p in families[item['familyId']]['palettes']
                          if p['id'] == item['paletteId'])
            differences += colors != item['legacyTheme']['palette']
        self.assertGreater(differences, 0)

    def test_refresh_target_and_configurable_bounds(self):
        manifest = load(ROOT / 'content/v1/manifest.json')
        self.assertEqual(manifest['refreshAfterSeconds'], 900)
        for interval in [300, 600, 900, 1800, 604800]:
            schema_check(dict(manifest, refreshAfterSeconds=interval), 'manifest')
        for interval in [0, 299, 604801, 900.5, '900']:
            with self.subTest(interval=interval), self.assertRaises(ValidationError):
                schema_check(dict(manifest, refreshAfterSeconds=interval), 'manifest')

    def test_permanent_fallback_phrase(self):
        home = self.catalog['home']
        self.assertEqual(home['defaultBanner']['headline'], 'Make Your Desktop Beautiful.')
        self.assertEqual(home['defaultBanner']['message'], 'Make Your Desktop Beautiful.')
        for key, value in [('startsAt', '2026-01-01T00:00:00Z'),
                           ('endsAt', '2027-01-01T00:00:00Z'), ('priority', 100)]:
            self.invalid(lambda c: c['home']['defaultBanner'].update({key:value}))
        for year in [2000, 2100]:
            self.assertEqual(select_banner(home, datetime(year, 1, 1, tzinfo=timezone.utc))['id'], 'welcome')

    def test_optional_banner_fields_and_date_bounds(self):
        for bounds in [{}, {'startsAt':'2026-10-01T00:00:00Z'},
                       {'endsAt':'2026-12-01T00:00:00Z'}]:
            with self.subTest(bounds=bounds):
                c = copy.deepcopy(self.catalog)
                c['home']['banners'] = [dict(id='optional', message='Text only', priority=10, **bounds)]
                c['home']['defaultBanner'] = {'id':'welcome', 'message':'Make Your Desktop Beautiful.'}
                validate_catalog(c, self.base, self.legacy)
                for value, active in [('2026-09-01T00:00:00+00:00', 'startsAt' not in bounds),
                                      ('2026-10-01T00:00:00+00:00', True),
                                      ('2026-12-01T00:00:00+00:00', 'endsAt' not in bounds)]:
                    result = select_banner(c['home'], datetime.fromisoformat(value))['id']
                    self.assertEqual(result, 'optional' if active else 'welcome')

    def test_accessible_image_and_button_validation(self):
        self.invalid(lambda c: c['home']['defaultBanner']['image'].pop('alt'))
        self.invalid(lambda c: c['home']['defaultBanner']['image'].update(alt=''))
        self.invalid(lambda c: c['home']['banners'][0]['button'].pop('label'))
        self.invalid(lambda c: c['home']['banners'][0]['button'].pop('action'))
        self.invalid(lambda c: c['home']['banners'][0]['button']['action'].update(type='run-script'))
        self.invalid(lambda c: c['home']['defaultBanner'].update(headline=''))
        self.invalid(lambda c: c['home']['defaultBanner'].update(subtitle=12))

    def test_banner_aliases_are_unambiguous(self):
        self.invalid(lambda c: c['home']['defaultBanner'].update(imageId='banner'))
        self.invalid(lambda c: c['home']['banners'][0].update(
            action={'type':'open-item', 'itemId':'blush-studio-pack', 'label':'Explore'}))
        c = copy.deepcopy(self.catalog)
        banner = c['home']['banners'][0]
        banner['imageId'] = banner.pop('image')['assetId']
        button = banner.pop('button')
        banner['action'] = dict(button['action'], label=button['label'])
        validate_catalog(c, self.base, self.legacy)

    def test_new_button_https_action(self):
        c = copy.deepcopy(self.catalog)
        c['home']['banners'][0]['button']['action'] = {'type':'open-url', 'url':'https://example.com/themes'}
        validate_catalog(c, self.base, self.legacy)
        for url in ['javascript:alert(1)', 'https://user:pass@example.com/', 'http://example.com/']:
            self.invalid(lambda c: c['home']['banners'][0]['button'].update(
                action={'type':'open-url', 'url':url}))

    def test_placeholder_artwork_labels(self):
        for asset in self.catalog['assets']:
            self.assertIn('Placeholder', asset['alt'])
            self.assertIn('not a finished approved widget', asset['alt'])

    def test_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'duplicate.json'
            path.write_text('{"schemaVersion":1,"schemaVersion":2}')
            with self.assertRaises(ValueError):
                load(path)

    def test_mutated_repository(self):
        def alter_legacy(root):
            path = root / 'widget-themes.json'
            path.write_bytes(path.read_bytes() + b' ')
        def alter_manifest(root, **change):
            path = root / 'content/v1/manifest.json'
            value = load(path)
            value.update(change)
            path.write_text(json.dumps(value))
        def corrupt_catalog(root):
            path = root / 'content/v1/releases/1.0.1/catalog.json'
            path.write_bytes(path.read_bytes() + b' ')
        for mutation in [alter_legacy, corrupt_catalog,
                         lambda root: alter_manifest(root, release='9.0.0')]:
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    for folder in ['content', 'schemas', 'tests']:
                        shutil.copytree(ROOT / folder, root / folder,
                                        ignore=shutil.ignore_patterns('__pycache__'))
                    shutil.copy2(ROOT / 'widget-themes.json', root)
                    mutation(root)
                    with self.assertRaises(ValueError):
                        validate(root)

    def test_manifest_constraints(self):
        manifest = load(ROOT / 'content/v1/manifest.json')
        for key, value in [('schemaVersion', 2), ('refreshAfterSeconds', 1), ('minimumOSVersion', '13.0')]:
            with self.subTest(key=key):
                bad = dict(manifest, **{key:value})
                with self.assertRaises(ValidationError):
                    schema_check(bad, 'manifest')


if __name__ == '__main__':
    unittest.main()
