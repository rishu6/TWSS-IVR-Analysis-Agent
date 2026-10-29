# Connect your own accounts

Account setup started 2026-10-28. Credentials alone do not enable live mode. The running demo still uses synthetic data, selectable demo roles and a synthetic database.

## Enter credentials locally

Open `.env.integrations` in your editor and fill the four empty settings. The file is ignored by Git and created with owner-only permissions. Never send its contents to chat. If it already existed, its contents and permissions were left untouched.

- Acefone India: API Connect → API Tokens. Use a token with the read scope needed for the documented endpoints. [Official token guide](https://docs.acefone.in/docs/using-managing-api-tokens).
- LeadSquared: My Account → Settings → API and Webhooks. Copy the actual account API host and access/secret keys. The CRM host depends on account region; do not infer it from Acefone's India region. [API host guide](https://apidocs.leadsquared.com/api-host/) and [authentication](https://apidocs.leadsquared.com/authentication/).

Check that settings are present without printing them:

```bash
.venv/bin/python scripts/check_integration_config.py
```

This check makes no network requests and does not verify credentials. The demo startup script does not load this credential file.

LeadSquared authentication and metadata access were subsequently verified on 2026-10-28 using `scripts/verify_leadsquared_connection.py`; see [account validation](account-validation.md). This does not enable the live dashboard or verify Acefone.

## Next implementation gates

1. Confirm account hosts and official Acefone CDR/history documentation; inspect one redacted response. Never guess a CDR URL or its call/leg fields.
2. Implement isolated read-only connection tests, then provider adapters with contract tests, timeouts, quota controls and bounded retries. Verify LeadSquared duplicate enumeration and stored phone formats.
3. Import a small approved date range into a separate live database. Keep all synthetic data separate and report unavailable capabilities explicitly.
4. Replace selectable demo roles with authenticated user identities and appropriate permissions before displaying real customer records. Ensure secrets never enter frontend bundles, database rows or logs.
5. Verify Acefone webhook authentication and delivery/root/leg semantics before enabling intake. Decide on an HTTPS callback address; localhost alone is not a public provider callback endpoint.

No lead creation, call placement or provider configuration changes are part of the initial read-only connection stage.
