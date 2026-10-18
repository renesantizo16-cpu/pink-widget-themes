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
        self.invalid(lambda c: c['home']['defaultBanner'].update(imageId='absent'))
        self.invalid(lambda c: c['home']['banners'][0]['action'].update(itemId='absent'))

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
