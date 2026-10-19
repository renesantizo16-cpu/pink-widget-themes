# Signed v5.1 feed preparation

This prefix is reserved for the separate owner-signed v5.1 feed. The existing unsigned content/v1 feed remains unchanged.

No manifest pointer or Christmas clock release is activated by this documentation. Client trust remains disabled until exact content review, local owner signing, HTTPS preflight, and explicit engine/build installation approval.

Selected pointer (not yet published):
https://raw.githubusercontent.com/renesantizo16-cpu/pink-widget-themes/main/content/v51/manifest.json

Clients are anonymous read-only HTTPS consumers. GitHub Pages is not required and is not enabled by this preparation. Owner publishing credentials and encrypted RSA private key stay on the owner's trusted signing computer, never in this repository, CI, or the browsing Mac. The signing tool uses a local terminal passphrase prompt without echo; never create a plaintext private-key file.

Protocol: the pointer envelope has format pink-approved-manifest-v1, a base64 manifest and RSA/SHA-256 signature. The pinned public key authenticates the original manifest bytes. Manifest and catalog JSON must satisfy the schema files in schemas/ and the engine's stricter validation. Only supported declarative widget configuration and bounded hash-checked PNG resources are accepted; no remote executable code.

After explicit approval, publish new release resources under content/v51/releases/<unique-version>/ first. Never overwrite a release path. Verify anonymous resource bytes and approved hashes, then publish the locally signed manifest pointer last. Main URLs are mutable; signed hashes detect changes. Retain commit-SHA raw URLs for immutable audit evidence. Rollback uses a separately reviewed/signed snapshot referencing preserved assets.

Before activation test anonymous HTTPS 200 without redirects, ETag/Cache-Control and conditional requests, pinned signature, catalog/PNG integrity and limits, offline cache and invalid-update retention. A missing pointer is not readiness. After signed-feed readiness and installation authorization, build/test the pinned activated engine; approve its exact package hash before side-by-side installation. Native Monterey acceptance and same-running-process clock/homepage refresh and independent rollbacks are separate gates. No automatic desktop Apply.
