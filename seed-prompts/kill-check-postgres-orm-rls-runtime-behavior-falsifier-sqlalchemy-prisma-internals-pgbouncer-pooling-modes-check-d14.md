# Success Pattern: kill-check — Postgres ORM + RLS runtime behavior falsifier (SQLAlchemy/Prisma internals, pgbouncer pooling modes, CHECK constraint transport semantics)

## Strategy
Expert type "Postgres ORM + RLS runtime behavior falsifier (SQLAlchemy/Prisma internals, pgbouncer pooling modes, CHECK constraint transport semantics)" for kill-check question.
Question: Does the chosen ORM (SQLAlchemy or Prisma) honor CHECK constraints plus RLS round-trip without silently stripping hints or issuing pre-SET-ROLE SELECTs during flush, and if adversarial, is pgbouncer session mode sufficient to restore F922 J1-J3 guarantees?

## When It Works
- Question type: kill-check
- Converged in 2/5 iterations

## Evidence
- Dispatch: D14
- Question: JQ073
- Findings produced: 12
- Iterations: 2/5
- Status: answered

## Key Decisions
JQ073 resolved: SQLAlchemy is correct ORM conditional on three rules — raw-SQL CHECK constraints + J3 pg_constraint audit (Alembic autogenerate gap), exclusive after_begin wiring for SET ROLE (eliminates pre-SET-ROLE SELECTs at flush), and pgbouncer session mode in prod (transaction mode is adversarial regardless of 1.21 prepared-statement support). Prisma rejected: raw-SQL CHECK only, generic error surface, no after_begin analogue. One residual audit deferred to a new question.