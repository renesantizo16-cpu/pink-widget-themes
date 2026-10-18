"""Print a validated candidate manifest. Does not write, upload, tag or deploy."""
import argparse
import hashlib
import json
from validate_content import ROOT, load, require, schema_check, validate_catalog


def prepare(release, published_at):
    # Validate input before using it as part of a filesystem path.
    schema_check(dict(load(ROOT / 'content/v1/manifest.json'),
                      release=release, publishedAt=published_at), 'manifest')
    base = ROOT / 'content/v1'
    path = base / 'releases' / release / 'catalog.json'
    catalog = load(path)
    require(catalog['release'] == release, 'release mismatch')
    validate_catalog(catalog, path.parent, load(ROOT / 'widget-themes.json'))
    data = path.read_bytes()
    require(len(data) <= 1048576, 'catalog exceeds 1 MiB')
    manifest = dict(load(base / 'manifest.json'), release=release, publishedAt=published_at,
                    catalog={'path':path.relative_to(base).as_posix(), 'bytes':len(data),
                             'sha256':hashlib.sha256(data).hexdigest()})
    schema_check(manifest, 'manifest')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release')
    parser.add_argument('--published-at', required=True, help='UTC ISO 8601 timestamp ending in Z')
    args = parser.parse_args()
    print(json.dumps(prepare(args.release, args.published_at), indent=2))
