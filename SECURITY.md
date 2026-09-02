# Security

## cryptography CVE-2026-69247 (Dependabot #13)

**Package:** `cryptography` (via `presidio-anonymizer` → `swiss-pii-anonymizer`)  
**Fix:** `cryptography>=50.0.0`  
**Upstream blocker:** `presidio-anonymizer` 2.2.364 pins `cryptography<49` ([presidio#2229](https://github.com/data-privacy-stack/presidio/issues/2229)).

**Our mitigation:** `backend/Dockerfile` installs with `pip --override 'cryptography>=50.0.0,<51'`.  
Runtime use is Presidio AES operators only — we do not expose PKCS#7 `EnvelopedData` decryption to untrusted input.

After `presidio-anonymizer` releases a compatible version, remove the override.
