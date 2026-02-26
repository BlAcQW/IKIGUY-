# Active Rules

Rules extracted from error learning records. Scanned before every code generation pass.

---

RULE-1 | Architectural | When adding a new execution path that creates a database record, check every non-nullable FK on that model — if the new path doesn't have a valid FK target, the FK must be made nullable (and all downstream type references updated) before the feature ships.
