# zalo-intake connector

Receive-only `zca-js@2.1.2` listener process for the zalo-intake module. It never
sends Zalo messages. Downloaded media goes to the module media root
(`ZALO_INBOX_STORAGE_ROOT`); signed JSON events are persisted in the local file
outbox before publication to the module's internal connector API.

Wire contract: the connector talks to the module over loopback HTTP under the
`/connector/v1` prefix (internal control plane — **not** the public
`/intake/v1` contract API):

- `POST /connector/v1/connectors/onboard` — header `x-zalo-bootstrap` →
  `{connector_account_id}`
- `POST /connector/v1/events` — `x-zalo-timestamp` + `x-zalo-signature`,
  HMAC-SHA256 over `{timestamp}.{body}`
- `GET /connector/v1/connectors/{id}/config` — signature over an empty body
- `GET /connector/v1/connectors/{id}/commands/next` — derived key
  `HMAC(webhook_secret, account_id)`; 204 means no pending command

The full wire protocol (event shapes, ACK semantics, env names) is specified in
[`../docs/connector-protocol.md`](../docs/connector-protocol.md). That document
is the connector↔module source of truth once MIN-103 slice D lands; this README
is only the runbook.

## Required environment

Set these in the process environment (secrets are intentionally not stored in
this repository; see `.env.example` in the repo root):

- `ZALO_INBOX_BACKEND_URL` — module base URL, e.g. `http://127.0.0.1:8790`
- `ZALO_INBOX_BOOTSTRAP_SECRET` — must match the module process
- `ZALO_INBOX_WEBHOOK_SECRET` — must match the module process
- `ZALO_INBOX_STORAGE_ROOT` — media storage root shared with the module
- `ZALO_CONNECTOR_QUOTA_BYTES` — media quota, e.g. `5368709120` (5 GiB)
- `ZALO_CONNECTOR_RETENTION_HOURS` — media retention, e.g. `168` (7 days)

Optional:

- `ZALO_CONNECTOR_STATE_ROOT` — session/outbox location; defaults to
  `runtime/zalo_connector`
- `ZALO_CONNECTOR_FORCE_QR` — set to `1` to skip session restore and force a
  fresh QR login
- `ZALO_CONNECTOR_PARENT_PID` — set by the module process manager when it
  spawns this process; the connector exits when the parent dies
- `ZALO_DATA_SYNC_TIMEOUT_SECONDS` — data-sync deadline budget enforced by the
  module side (default `900`)

## Run and verify

```sh
npm ci
npm test
npm run check
npm start
```

Normally the module starts this process via `POST /connector/v1/connectors/start`
(the module process manager spawns `node connector/bin/run.mjs` with the
environment above). `npm start` remains the operator/debug path. The first run
publishes a browser-safe QR login state and writes the QR image under
`ZALO_CONNECTOR_STATE_ROOT`; the module binds the first successful QR account.

A real Zalo account is required to complete the QR scan and to smoke-test
restored session, source discovery, image/PDF payloads, and CDN downloads;
offline tests mock those external boundaries.

## Secrets — never commit

`ZALO_CONNECTOR_STATE_ROOT` holds `session.json` (Zalo cookie/imei/userAgent —
full account takeover if leaked), `account.json`, `generation.json`,
`login-qr.png`, and three file-outbox queues (`webhook-outbox`,
`download-queue`, `unknown-source-queue`) containing raw private message JSON
and CDN URLs. `ZALO_INBOX_STORAGE_ROOT` holds downloaded media. Both are
runtime directories: never commit their contents, never log session payloads or
signed URLs.
