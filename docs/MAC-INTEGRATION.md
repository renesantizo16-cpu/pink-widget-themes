# Mac application integration checklist

This repository is content and publisher tooling. The Swift application must
implement the consumer; these changes alone do not add remote publishing to an
installed app. Target Intel x86_64 and macOS 12 Monterey, including a 2015
MacBook Air. Use Foundation, URLSession, Codable, CryptoKit SHA256, ImageIO and
AppKit/SwiftUI APIs available on macOS 12. No WebView, Node, database server,
Python runtime or image animation is needed in the shipping app.

1. Bundle the existing 13 themes, a compatible catalog and a default banner/image
   as offline resources, including “Make Your Desktop Beautiful.” Configure the final HTTPS manifest URL in app-owned
   settings after publishing approval. Until then use bundled data or a local
   fixture server in development. Do not hardcode a feature-branch URL in a release.
2. Decode separate legacy and v1 DTOs. Check `schemaVersion` before decoding a
   catalog. Compare numeric app/OS versions, enforce all documented bounds and
   semantic references, and reject unsupported versions without erasing the cache.
   Port the validator's checks; Codable alone does not enforce the JSON Schema.
3. Fetch the manifest with URLSession in the background; timeout after 15 seconds,
   cap it at 64 KiB while streaming, and use ETag/If-None-Match or Last-Modified.
   Use a configurable 900-second (~15-minute) announcement target, constrained
   to 300–604800 seconds, from refreshAfterSeconds or an app preference. Refresh
   on launch/resume when stale, add jitter, coalesce requests, and exponentially
   back off on errors while honoring Retry-After. Pause automatic fetching while
   asleep; keep at most two requests active. Add an explicit Refresh option that
   conditionally revalidates immediately (bypasses freshness TTL, keeps ETags and
   asset caches), coalesces repeated clicks, and preserves content on failure.
   Implement the detailed policy in CONTENT.md; no busy polling.
4. Resolve only validated relative resource paths against the configured HTTPS
   origin. Forbid path traversal, encoded separators, credentials and origin changes;
   validate every redirect or reject redirects. Require HTTPS and default port.
   Fetch the catalog (1 MiB cap) only when its hash changes. Verify exact length
   and SHA-256 before decoding. Validate catalog release against the manifest.
5. Stage catalog metadata atomically on disk. Keep a last-known-good catalog and
   its originating manifest/base URL. Do not replace it until version, schema,
   bounds and references pass. Cache on-demand image bytes by SHA-256, verify
   length/hash before decoding, and use ImageIO thumbnail downsampling before
   drawing. A required selected-pack asset failure must abort that application,
   preserving the current local state. Banner asset failure uses bundled fallback.
6. Implement individual clock, calendar, note, wallpaper and sticker renderers;
   implement atomic, reversible component pack selection. Adapt `legacyTheme` to
   the current renderer without changing its quote, note or countdown behavior.
   Resolve approved family-prefixed palette IDs for new artwork, but render each
   legacy pack with its embedded original palette. Its family/palette reference
   is for catalog discovery and must never recolor an existing legacy theme.
   Keep all user content and preferences local. Legacy countdown dates are fixed,
   not annually recurring; preserve existing behavior after they pass.
7. Implement UTC banner selection and boundary timers as specified in CONTENT.md.
   Decode optional headline, subtitle, image {assetId, alt}, and button
   {label, action} independently. Use message as title when headline is absent;
   omit missing subtitle, image or button. Accept earlier imageId/action aliases
   only when the corresponding new field is absent. Missing start/end means an
   open schedule boundary; the permanent fallback forbids both. Show plain text
   and VoiceOver alt text, enforce permitted actions, and require an explicit
   click to open an HTTPS URL through NSWorkspace. Use a reviewed host allowlist;
   default to disabling external URL actions until one is configured.
8. On offline, corrupt data, incompatible versions or failed assets, retain the
   last good selection; if none exists use bundled content. Do not blank the home
   screen or delete user notes. Optionally adapt a validated legacy feed when v1
   is unavailable. Never interpret a malformed v1 document as a legacy document.

## Performance targets and verification

Use lazy image loading, a 50 MiB disk asset cache (LRU; pin selected assets), and
roughly 24 MiB decoded thumbnail cache. Evict unselected images under memory
pressure; do not preload every wallpaper. Decode away from the main thread.
Default clock updates once per minute; use a one-second timer only for a visible
clock with seconds explicitly enabled. Stop timers when hidden or asleep.

The examples use 960×240 banners, a 1440×900 wallpaper and a 128×128 sticker. PNG
compression keeps network bytes small; decoded RGBA wallpaper memory is still
about 5 MiB. Validate dimensions before decoding to prevent memory exhaustion.

Before shipping, test on an Intel MacBook Air running Monterey: cold launch,
airplane mode, first-launch offline, 304 responses with/without cache, TLS and
redirect failures, truncated files, corrupt hashes, unknown protocol, newer app
requirements, expired/overlapping schedules, sleep/resume and clock changes,
image decode failure, disk full, interrupted download and pack application,
rollback to an older release, local note preservation, VoiceOver and memory
pressure. Also test the explicit Refresh action, adjustable 15-minute cadence,
backoff/Retry-After, optional banner fields and open date bounds, the permanent
approved fallback phrase, and unchanged legacy colors after approved palette
associations are loaded. Python tests here verify publishing contracts and banner rules; they
do not establish native UI performance or macOS runtime compatibility.
