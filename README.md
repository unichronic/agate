# AGATE: Unified AI Agent Security Gateway (Composable Stack)

Yes — you can make this feel like **one cohesive tool** instead of separate products.

This repo now provides a practical composition approach:

- A single **AGATE gateway API** as the entrypoint (`/v1/agent/guard`)
- **OPA** for tool policy decisions
- **Presidio** for output DLP checks
- **Lakera** as an optional external prompt-injection adapter
- Vendor/bootstrap script for open-source dependencies you want in local folders

## Architecture (single-tool control plane)

```text
Agent/App -> AGATE Gateway -> [Input Scan + Optional Lakera]
                         -> [OPA Tool Policy]
                         -> [Presidio DLP]
                         -> Allow/Deny + unified audit response
```

Treat AGATE as the orchestration layer and the only endpoint agents talk to.

## What is included

- `gateway/main.py`: unified policy gateway API
- `policies/agate.rego`: sample RBAC+argument-level controls
- `docker-compose.yml`: local stack (gateway + OPA + Presidio)
- `scripts/bootstrap_vendors.sh`: clones OSS repos into `vendor/`
- `scripts/demo_requests.sh`: before/after-style request simulation

## Quick start

1. Start services:

```bash
docker compose up
```

2. Run demo calls:

```bash
./scripts/demo_requests.sh
```

## Vendor clone strategy

Run:

```bash
./scripts/bootstrap_vendors.sh
```

This clones open repositories into `vendor/` (Bifrost, OPA, Presidio, llm-guard).

Notes:

- **Lakera** is API-first/commercial in this setup; configure it via `LAKERA_URL` and `LAKERA_API_KEY`.
- **Bifrost** is cloned locally into `vendor/bifrost` and can be run upstream or alongside AGATE.
- **Cisco A2A** is best integrated as an identity/intent check adapter at agent-to-agent boundaries.

## Why this answers your ask

This gives you a single packaged tool experience:

- one endpoint
- one policy decision surface
- one deployment bundle
- pluggable best-of-breed engines behind it

So yes — not “just separate tools,” but a unified **Agent Security Gateway product shell**.
