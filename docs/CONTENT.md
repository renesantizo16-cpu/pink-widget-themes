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

Both sample releases are unpublished PR fixtures and may be revised during review.
Once approved for public consumption, releases are immutable; never overwrite one. A manifest is the mutable
pointer; retain older releases for installed clients and rollback. Hashes detect
corruption, not authenticity: trust comes from the app's configured HTTPS origin.

## Families and palettes

| Family | Three palettes |
| --- | --- |
| Coquette Pink | Classic Coquette, Rose Petal, Champagne Blush |
| Soft Elegant | Warm Linen, Botanical Blush, Taupe Rose |
| Minimalist | Warm Minimal, Stone & Blush, Charcoal Contrast |
| Halloween | Pink Pumpkin Patch, Lavender Ghost, Midnight Witch |
| Christmas | Classic Christmas, Cozy Hearth, Snowy Tradition |
| Fall | Harvest Amber, Pumpkin Spice, Maple Rose |
| Winter | Frosted Blue, Silver Pine, Soft Snow |

Each family has exactly these three palettes. IDs are stable, globally unique,
family-prefixed slugs (for example `coquette-pink-classic-coquette` and
`minimalist-stone-and-blush`), distinct from legacy theme IDs. Validation enforces
the exact approved ID/name pairings. Each palette defines five sRGB `#RRGGBB`
roles: `bg` (background), `edge` (borders/detail), `ink` (text), `accent`
(highlights), and `soft` (secondary surfaces). These are proposed color values for
the approved palette names, not an assertion that finished artwork is approved.
Classic Christmas uses traditional red `accent: #B32735`, green `ink: #174C35`,
and gold `edge: #C5A04B`, with cream and pale gold surfaces.

Future premium widget artwork can bind to the same stable `familyId`/`paletteId`
and role tokens, referencing independently versioned PNG assets. Do not rename
palette IDs when adding artwork, tint an entire authored image automatically, or
infer entitlement from a family or palette name. This contract provides artwork
references, not licensing or purchase enforcement. Publish changed asset bytes
with a new hash in a new release; retain old assets for cached selections.

Legacy items keep their original IDs and exact embedded `legacyTheme` objects.
Their new `familyId`/`paletteId` references are catalog discovery associations;
**the embedded legacy palette remains authoritative for legacy rendering**.
Thanksgiving content is grouped under Fall and New Year under Winter. No new
palette is substituted into a legacy theme. The root `widget-themes.json` and its
baseline checksum remain unchanged. All five individual Blush examples and the
composite pack reference `coquette-pink-classic-coquette`.

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

`home.defaultBanner` is required and permanent: it cannot have `startsAt`,
`endsAt`, or `priority`. Both examples give its headline and compatibility message
the exact approved phrase **Make Your Desktop Beautiful.** Bundle that phrase
and a default image locally for network/image failures as well.

Every banner requires a unique `id` and plain-text `message` (the compatibility
text). It supports these separate optional presentation fields:

| Field | Meaning |
| --- | --- |
| `headline` | Independent headline; when absent, display `message` as the title. |
| `subtitle` | Independent secondary text; omit its UI space when absent. |
| `image` | `{ "assetId": "banner", "alt": "Accessible image description" }`; resolves to an asset and requires nonempty alt text. |
| `button` | `{ "label": "Explore", "action": { "type": "open-item", "itemId": "blush-studio-pack" } }`; label and action must both exist. |
| `startsAt` | Optional inclusive UTC start, only for entries in `home.banners`. |
| `endsAt` | Optional exclusive UTC end, only for entries in `home.banners`. |

Entries in `home.banners` additionally require `priority` (0–100). Missing start
means no lower bound; missing end means no upper bound; neither means always
eligible. If both dates exist the start must precede the end. Dates are ISO 8601
UTC ending in Z. Select eligible entries by highest priority, then ascending ASCII
`id` for ties; choose the permanent default when none are eligible. Re-evaluate
on resume, clock change and the next existing start/end boundary without network
polling. UTC schedules are not localized recurring dates. Sample Fall dates are
fixed test data and can legitimately expire.

A button action is `open-item` (`itemId`) or `open-url` (`url`). The label belongs
to the button, separately from the action. URLs must use HTTPS, have no user info
and use port 443 or no explicit port. Open them only after a user click, through
the system browser with an app-owned host allowlist. Unknown actions never run.
Text-only and buttonless banners are valid. Headline/subtitle are plain text,
never markup. Do not display `message` a second time when a headline is present.

The earlier draft's `imageId` (using the asset's `alt`) and `action` (including
`label`) are accepted compatibility aliases. A banner must not specify both
`image` and `imageId`, or both `button` and `action`. New content should use
`image` and `button`. On image failure show the bundled permanent fallback and
its message; never show a broken image or execute an action automatically.

## Announcement refresh policy

The manifest's configurable `refreshAfterSeconds` targets **900 seconds (about
15 minutes)**. The schema permits 300–604800 seconds, defaulting to 900 for
publishers; the field is required on the wire. A Mac app preference may override
it within the same bounds, with a bundled 900-second default when no remote
configuration exists. Treat this as an approximate foreground cadence, not a
strict delivery guarantee: suspension, offline state and error backoff delay it.

Use ETags/If-None-Match (or Last-Modified), disk and image caches, and fetch a
catalog only when its hash changes. Add small jitter, coalesce concurrent refreshes,
and exponentially back off errors (for example 15, 30, 60 minutes, capped at six
hours, honoring Retry-After). Do not wake a sleeping Mac to check announcements.
Provide an explicit **Refresh** option: conditionally revalidate immediately,
bypassing the normal freshness interval and local cached-response freshness,
while retaining ETags and verified cached assets. Coalesce repeated clicks;
honor server rate limits and Retry-After. A 304 without cached data needs one
unconditional retry. A failed refresh retains last-known-good content and shows
a lightweight status. Banner boundary timers operate independently of fetching.

## Limits

Schemas bound catalogs to 1,000 items, 500 assets and 50 scheduled banners;
publisher checks cap each catalog at 1 MiB and each resource at 8 MiB. Static
images are at most 2560×1600 pixels. These are upper bounds, not download targets.
The app must validate bounds before allocation and enforce decoded image limits.
