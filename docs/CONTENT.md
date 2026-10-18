# Content contract v1

The product version is v5; the new wire protocol starts at integer
`schemaVersion: 1` under `content/v1`. It is separate from the legacy root
`schema: 1`. Breaking changes require a new schema version and directory.
Release versions are three nonnegative integers, compared numerically, never
lexicographically. IDs are stable lowercase slugs. Schemas reject unknown fields;
new required fields, new types or changed semantics require a protocol bump.
The `.invalid` schema IDs are identifiers, not endpoints to fetch.

## Manifest and releases

Fetch a configured HTTPS URL ending in `content/v1/manifest.json`. The manifest
contains `release`, UTC `publishedAt`, `minimumAppVersion`, `minimumOSVersion`,
`refreshAfterSeconds` and `catalog` (`path`, exact UTF-8 `bytes`, lowercase hex
`sha256`). Resolve the catalog against the manifest directory. Resolve every
asset resource against the catalog directory. Hash exact downloaded bytes before
JSON decoding or image decoding. Do not reserialize before hashing.

`legacyPath` is the fixed compatibility path `../../widget-themes.json`, relative
to the manifest. It is the sole allowed parent-directory reference. Resource
paths otherwise forbid absolute URLs, `.` and `..` segments, encoded separators,
queries, fragments and backslashes. No resource may escape its release directory.
HTTPS hosting is configured by the app; no production endpoint is activated here.

Both sample releases are self-contained and immutable once approved for public
consumption. Never overwrite an existing release. A manifest is the mutable
pointer; retain older releases for installed clients and rollback. Hashes detect
corruption, not authenticity: trust comes from the app's configured HTTPS origin.

## Families and palettes

| Family | Three palettes |
| --- | --- |
| Coquette Pink | Strawberry Milk, Pink Moonlight, Rose Garden |
| Soft Elegant | Pearl, Rose Silk, Lavender Mist |
| Minimalist | Paper, Sand, Slate |
| Halloween | Pink Pumpkin Patch, Lavender Ghost Party, Midnight Witch |
| Christmas | Pink Christmas, Candy Cane Cutie, Sugarplum Snow |
| Fall | Pumpkin Spice Cozy, Thankful Hearts, Rose Gold Harvest |
| Winter | New Year Sparkle, Frost, Snow Rose |

This maps Thanksgiving content into Fall and New Year content into Winter while
preserving all original IDs, wording, colors and countdowns in `legacyTheme`.
Each family has exactly three unique palettes with `bg`, `edge`, `ink`, `accent`
and `soft` colors in `#RRGGBB` form. Palette IDs are scoped to a family.
New family mappings and the eight new palettes are proposed by this PR; the
original feed has no family field and remains byte-for-byte unchanged.

## Items

Every item has `id`, `name`, `type`, `familyId`, and `paletteId`. IDs are unique
within a release. Every family/palette reference must resolve.

| Type | Payload and app behavior |
| --- | --- |
| `clock` | `config.style`: digital/analog; `hourCycle`: system/12/24; `showSeconds`: boolean. Use the user's local time zone. |
| `calendar` | `firstWeekday`: system/monday/sunday; `showWeekNumbers`: boolean. System calendar and locale remain local. |
| `note` | Placeholder and bounded `maxCharacters`; actual personal note text stays on device. |
| `wallpaper` | PNG `assetId`; `fit`: fill (aspect fill/crop) or fit (aspect fit). Apply only after user selection. |
| `sticker` | PNG `assetId` and logical point `defaultWidth`; preserve image aspect ratio and alpha. |
| `theme-pack` | Either `components` (IDs of individual items) or an exact `legacyTheme`, never both. |

Composite packs cannot contain packs, duplicate members or cycles. Components
share the pack family and palette. The Blush Studio Pack demonstrates all five
individual types together. Legacy packs use the existing widget renderer,
including quote and countdown support; do not reinterpret those as new types.
Applying a remote note must never overwrite a user's text. Pack application
should be one reversible local operation. Download failure leaves the current
selection intact.

## Assets and banners

Assets have a unique `id`, `resource`, `mediaType: image/png`, pixel `width`,
`height` and accessible `alt` text. Only static PNG is supported. Sample assets
are simple original pink gradients and a transparent circle, not finished designs.
No SVG, JavaScript, HTML, fonts, video, animated files or executable payloads.

`home.defaultBanner` is required and has no schedule or priority. `home.banners`
contains scheduled banners with `startsAt`, `endsAt` (ISO 8601 UTC ending in Z),
`priority` (0–100), `imageId`, plain-text `message`, and optional `action`.
The start must precede the end. Select banners for which `start <= now < end`;
highest priority wins, then ascending ASCII `id` for ties. Select the default
when none are active. Re-evaluate on resume, clock change and the next start/end
boundary without network polling. UTC schedules are not localized recurring dates.

An action is either `open-item` (`itemId`, `label`) or `open-url` (`url`, `label`).
URLs must use HTTPS, have no user info and use port 443 or no explicit port.
Open URLs only after a user click, through the system browser with an app-owned
host allowlist. Unknown actions never run. On failed image download show the
bundled default image/message; actionless banners render without a button.
Default and scheduled banner IDs must be unique. Dates shown in the examples
are fixed test data and can legitimately expire.

## Limits

Schemas bound catalogs to 1,000 items, 500 assets and 50 scheduled banners;
publisher checks cap each catalog at 1 MiB and each resource at 8 MiB. Static
images are at most 2560×1600 pixels. These are upper bounds, not download targets.
The app must validate bounds before allocation and enforce decoded image limits.
