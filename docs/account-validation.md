# Account validation — 2026-10-28

- Local credential configuration: all four required values present; no values printed.
- LeadSquared configured host independently matched the official India Mumbai API host (`api-in21.leadsquared.com`) in [official API host documentation](https://apidocs.leadsquared.com/api-host/).
- One HTTPS GET to the documented `/v2/LeadManagement.svc/LeadsMetaData.Get` endpoint succeeded with HTTP 200. Response contained 138 metadata definitions; Phone and Mobile were present. [Metadata contract](https://apidocs.leadsquared.com/meta-data/).
- Credentials sent in documented headers, never query parameters. Redirects disabled; exact official hostname allowlist enforced. Raw provider payloads were not printed or persisted.
- Initial network access was restricted and automatic approval rejected an unverified destination. After independently matching the exact host against official documentation and adding an enforced allowlist, the request was approved and succeeded.
- Acefone token presence checked only. No Acefone request made; CDR method/path, response schema, pagination and linkage remain unverified.
- No customer records imported; no provider records modified. Dashboard remains synthetic and live mode remains disabled.

The verification script is `scripts/verify_leadsquared_connection.py`. Eight tests cover request contract, error redaction, response validation and unverified-host rejection; seven existing local setup tests cover configuration parsing and privacy.

## Internal integration follow-up

The official Acefone index exposed the exact CDR reference at `https://docs.acefone.in/reference/call-detail-records-2.md`. One account request to `GET https://api.acefone.in/v1/call/records` returned HTTP 200 with actual inbound call-flow data. LeadSquared criteria-search pages of 1,000 rows also succeeded, including page 100; the account-wide phone index therefore uses durable resumable scans. The internal app now imports real data into `.runtime/internal.db`. This supersedes the earlier “no customer records imported” milestone above. No keys or customer values were printed during validation.

The initial default-lead-type index subsequently completed with 206,156 leads. At verification the app held 196 Acefone calls and preserved four unknown-caller records without fabricating numbers. Actual enrichment produced single matches and multiple matches while retaining ambiguity; provider states were healthy between scheduled poll cycles. The real localhost API also passed an ephemeral-Viewer masking and authorization check; no customer values or credentials were printed.
