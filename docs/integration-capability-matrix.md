# Integration capability matrix

Reviewed 2026-10-27 against official public documentation. User confirmed **Acefone India**, with no account-specific documentation available. Public documentation validation is not runtime or tenant verification. The separate internal Mac app now uses real read-only CDR polling and a resumable CRM index. Both account connections were verified on 2026-10-28; the demo remains synthetic. See [account validation](account-validation.md) and [internal deployment](internal-deployment.md).

| Capability | Verified public contract / source | Unknown / implementation gate |
|---|---|---|
| Acefone authentication | [API tokens](https://docs.acefone.in/docs/using-managing-api-tokens): Authorization: Bearer token, portal-managed scopes, restrictions and expiry. | Confirm read-only tenant scopes; no token generation or rotation calls implemented. |
| Acefone webhooks | [India webhook guide](https://docs.acefone.in/docs/web-hooks): configurable method, body, triggers, timestamp format and timezone. Two delivery attempts described. | Need exact configured payloads, authentication mechanism, stable delivery ID and ordering. No invented signature header or live parser. |
| Acefone history/CDR | [Official CDR reference](https://docs.acefone.in/reference/call-detail-records-2.md), discovered via official llms.txt: GET `https://api.acefone.in/v1/call/records`; from_date, to_date, page, limit; results array and count/size/page metadata. Account request returned HTTP 200. | Polling/backfill implemented with configured IST date parameters and epoch precedence. Provider quotas remain unverified; conservative pacing and bounded retry apply. |
| Acefone call identity | CDR reference identifies call_id as unique call identity; actual account rows contain it. | CDRs correlate only by call_id. Exact transfer/leg linkage is unverified; no phone/time merging. |
| Acefone agent evidence | Tenant CDRs verified Agent entries with name, id, num/number, dialst (Dialed/Answered) and time; missed_agents entries contain name/number. | Detailed Call Flow now exposes this evidence. Missed-summary timestamps, exhaustive ring counts and exact leg IDs remain unavailable; no attempt count is inferred. |
| Acefone portal evidence | [India CDR UI guide](https://docs.acefone.in/docs/call-detail-records-cdr-1) describes call flow, trace logs, DTMF and agent ring time in the portal. | Portal features do not prove equivalent API fields or exhaustive ring-event delivery. Request an API export contract before mapping. |
| Acefone historical retention | [Retention policy](https://docs.acefone.in/docs/data-retention-policy) describes UI CDR availability for months 1–3, archive batch files for months 4–12 and deletion after month 12. | This is not an API pagination or recording retrieval contract; confirm account applicability and archival access. |
| Acefone recording | Documented recording_url is supplied by the account. | Access/expiry/retention remain unverified. Signed URLs are stripped before persistence and never exposed; playback disabled. |
| LeadSquared phone lookup | [Phone lookup](https://apidocs.leadsquared.com/get-lead-by-phone/): GET `https://{host}/v2/LeadManagement.svc/RetrieveLeadByPhoneNumber?phone={number}`. Searches Phone/Mobile. Returns the most recently active lead if duplicates exist. Response fields include ProspectID, FirstName, LastName, Phone, Mobile, CreatedOn, ProspectStage, OwnerId, Source. | Cannot enumerate all duplicate candidates with this endpoint. No pagination established for it. |
| LeadSquared candidate enumeration | [Criteria search](https://apidocs.leadsquared.com/search-by-lead-criteria/): POST `https://{host}/v2/LeadManagement.svc/Leads.Get`. Parameter, Columns, Sorting, Paging; array response. PageIndex starts at 1, PageSize max 1000. | Proposed Phone and Mobile searches must be validated against actual stored formats and object types before claiming exhaustive normalized matching. |
| LeadSquared authentication | [Authentication](https://apidocs.leadsquared.com/authentication/): HTTPS, x-LSQ-AccessKey and x-LSQ-SecretKey headers supported and preferred. | Tenant API host and read-only scope needed. Secrets stay in environment. |
| LeadSquared metadata / account check | [Get Metadata](https://apidocs.leadsquared.com/meta-data/): GET `/v2/LeadManagement.svc/LeadsMetaData.Get`. On 2026-10-28 the saved account credentials returned HTTP 200 with 138 schema fields, including Phone and Mobile. | Verifies authentication and metadata access only; customer lookup, duplicate enumeration and live dashboard access remain unverified. |
| LeadSquared quotas | [Rate limits](https://apidocs.leadsquared.com/rate-limits/): plan-specific quotas (10 or 20 calls/5 seconds in general table). | Phone lookup error table mentions 25/5s. Confirm account quota; no universal limit assumed. |
| LeadSquared history/time | [Overview](https://apidocs.leadsquared.com/overview/): API datetime format is UTC. | Current stage/owner do not establish historical values. Demo labels **current only**; history capabilities unverified. |

## Documented examples (redacted shapes, not tenant captures)

```http
GET /v2/LeadManagement.svc/RetrieveLeadByPhoneNumber?phone=919876543210
Host: <tenant-verified-api-host>
x-LSQ-AccessKey: <environment-only>
x-LSQ-SecretKey: <environment-only>
```

```json
[{"ProspectID":"<id>","FirstName":"<redacted>","CreatedOn":"2026-01-01 00:00:00","ProspectStage":"<current>","OwnerId":"<owner>"}]
```

Criteria request shape:

```json
{"Parameter":{"LookupName":"Phone","LookupValue":"<stored-phone-format>","SqlOperator":"="},"Columns":{"Include_CSV":"ProspectID,Phone,Mobile"},"Sorting":{"ColumnName":"CreatedOn","Direction":"0"},"Paging":{"PageIndex":1,"PageSize":100}}
```

No Acefone payload is represented as verified. Fixtures implement our **internal synthetic contract**, never guessed vendor fields. Demo mode calls no live vendor endpoints. Internal mode calls only documented read-only Acefone CDR and LeadSquared criteria-search endpoints, with credentials in headers and exact trusted-host restrictions.

## Request for Acefone India support

Provide the account's official CDR/history API contract (method, URL, auth, quotas, pagination, retention), enabled webhook trigger definitions and redacted payloads for: four sequential agent attempts, simultaneous rings, IVR exit, cross-department transfer, duplicate delivery and delayed hangup. Confirm root/leg IDs, event IDs, signature or equivalent authentication, timezone, individual missed-ring coverage and recording URL access/expiry. These are questions about availability, not assertions that the APIs support them.

For LeadSquared obtain API host, phone field metadata/formats, object type scope, duplicate examples and read-only sandbox access. Never send credentials in chat. CDR history and basic CRM access are now verified. Detailed per-agent linkage, webhook authentication and recording playback still require this evidence; those capabilities remain disabled or unavailable.
