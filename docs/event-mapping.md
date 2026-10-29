# Event mapping and reporting policy

All fields below are **internal**, not Acefone wire fields. A live mapping cannot be approved without provider payloads.

| Internal target | Required live evidence | Demo source |
|---|---|---|
| call_id | Stable root ID or verified linked-leg graph | Explicit fixture root |
| event_id | Stable event ID or reviewed dedupe hash rules | Unique synthetic ID |
| at | Offset-aware provider time with documented format | ISO 8601 with offset, normalized UTC |
| received_at | Our receipt clock | Server UTC clock |
| leg_id, agent, department | Per-leg identifiers and routing evidence | Explicit fixture values |
| INBOUND, IVR, DTMF, QUEUED | Trigger/payload examples | Typed internal events |
| RING, NO_ANSWER, ANSWER, LEG_END | Complete ring and leg lifecycle evidence | Typed internal events and leg_id |
| TRANSFER | Verified source/target leg linkage | Explicit source_leg_id/target_leg_id |
| END | Termination reason and call scope | Explicit reason: missed, ivr_exit, abandoned, unknown |

Reduction sorts by provider time, sequence, event ID. All normalized events and original payload timestamps are retained. Duplicates are ignored; reuse of an event ID with a conflicting payload is rejected. Receipt time does not determine journey order. Identity is provider + root ID; callers sharing a number never merge.

Demo status policy: any explicit answer => ANSWERED. Otherwise no END => IN_PROGRESS. END missed => MISSED; ivr_exit without legs => IVR_ONLY; abandoned => ABANDONED; insufficient evidence => UNKNOWN. Agent NO_ANSWER never implies customer MISSED. Absent ring coverage produces null attempt metrics, never zero or inferred names. Clock contradictions produce a partial-data warning rather than negative durations.

Department primary attribution uses the first explicit routing/leg department: each call counted once. Department involvement counts distinct calls touching each department; involvement counts are not additive. All transfer legs remain attached to the root. First response is first answer minus inbound start. Final answering agent is the last explicit answer. Talk time requires leg answer and leg end evidence; no ring duration is included.

Overview and department call counts include inbound calls only. Agent reports and the explorer include both directions by default, so outbound callbacks remain visible; the API supports an explicit direction filter. Date ranges are inclusive start / exclusive end, with UI calendar boundaries converted from Asia/Kolkata to UTC. Hourly buckets align to Asia/Kolkata hours.

CRM snapshots are current only unless verified history exists. First observed caller is relative to this dataset; it is not proof of a first-ever customer call or a newly created CRM lead.

Recovery matches are **candidates**, not confirmed recovery: explicit later answer after missed termination, same normalized caller and DID within configurable window. Each connected call can serve at most one candidate. This never merges calls or establishes identity from a shared phone.
