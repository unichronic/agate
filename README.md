# AGATE Vendor Bootstrap

This repository has been minimized to keep only vendor-related assets.

## What remains

- `scripts/bootstrap_vendors.sh` to clone/update third-party dependencies into `vendor/`
- `README.md`

## Bootstrap vendors

```bash
./scripts/bootstrap_vendors.sh
```

This will clone/update:

- Bifrost
- OPA
- Presidio
- llm-guard

into the local `vendor/` directory.
