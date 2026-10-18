# Authoring, review and publishing

Nothing here deploys or modifies the live root feed. All release files are public
examples: never include credentials, account identifiers, personal notes or other
private information. Do not store secrets in JSON, assets, tests or workflow files.
Original sample artwork has no third-party dependencies. Every sample asset's alt
text labels it as placeholder artwork, not a finished approved widget. The two
release directories are unpublished fixtures within PR #1 and are revised here
before approval; the immutability rule applies after approval/public consumption.

## Prepare a release

1. Create a feature branch from current main. Leave `widget-themes.json` unchanged;
   `tests/legacy-baseline.json` pins its exact bytes and ID order. Preserve the
   embedded legacy copies in every v1 catalog. Do not update the baseline merely
   to make a failing preservation check pass.
2. Copy the latest release directory into a new unused semantic-version directory.
   Edit `catalog.json`, including its `release`, item metadata, banners and assets.
   Never modify a release that has already been approved and published. A release
   is self-contained: asset paths stay inside its own directory.
3. For each changed asset record exact byte length, SHA-256, actual PNG pixel
   dimensions and alt text. Keep artwork small; use the approved seven families
   and the exact three approved palettes for each in CONTENT.md. Keep palette IDs
   stable for future premium artwork and never recolor embedded legacy themes.
   Keep announcement refreshAfterSeconds at the proposed 900-second target unless
   deliberately configuring a different interval within schema bounds. Review
   separate headline/subtitle, accessible image alt, button label/action and UTC
   date bounds; the fallback must stay permanent with the approved phrase.
   Add images only when you own their publishing rights.
4. Print a candidate manifest with the offline helper, then review its diff:

   ```sh
   python scripts/prepare_manifest.py 1.0.1 --published-at 2026-10-18T00:00:00Z > work/manifest-candidate.json
   ```

   Create `work/` first if needed. The helper validates the selected release and
   prints JSON only; it does not write the live pointer. After review, copy the
   candidate to `content/v1/manifest.json`. Use the intended publication timestamp,
   not the sample timestamp, for a future release. `publishedAt` is informational;
   banner start/end control scheduling.
5. Run the validation and unittest commands in README. Both schema constraints and
   cross-document semantic checks are required. Tests include corruption, unsafe
   paths, missing references, legacy preservation and banner boundary selection.
6. Open a PR containing the complete immutable release plus pointer change. Review
   artwork, messages, schedules, actions, app compatibility, sizes and test output.
   Owner approval is required before merge or deployment. No automatic publication,
   GitHub Release creation, tagging, Pages configuration or hosting change is
   performed by this foundation.

## Publish only after approval

Choose a static HTTPS origin with stable relative paths and correct JSON/PNG MIME
types. If using GitHub raw hosting after approval, the proposed manifest URL is
`https://raw.githubusercontent.com/renesantizo16-cpu/pink-widget-themes/main/content/v1/manifest.json`.
This is a proposed location, not a verified or enabled v5 endpoint in this PR.
The existing legacy URL remains unchanged.

Upload immutable release directories first, verify their bytes/hashes through the
public origin, then update the manifest last. Serve immutable release files with
long-lived caching and the mutable manifest with short caching/revalidation;
suggest `max-age=31536000, immutable` and `max-age=300` respectively when hosting
allows header control. Use HTTPS, no authentication, and no client credentials.
Verify the public origin and run Mac consumer acceptance tests before distributing
an application configured to use it.

## Example history and rollback

- **1.0.0**: initial 13 legacy packs, 5 individual items, 1 full pack, 21 palettes,
  a scheduled Fall banner and a permanent default.
- **1.0.1**: same content with revised default banner subtitle; selected by the
  example manifest. Both directories are checked in for offline review.

For rollback, use the helper with an older retained release and a new publication
timestamp; commit the resulting manifest through a reviewed PR. Do not edit the
older catalog or assets. Consumers must accept a valid older release pointer:
release versions identify content and are not an anti-rollback counter. Retain
cached current selections during a failed rollback fetch. Remove stale files only
under a separate retention policy that protects clients using an older catalog.
