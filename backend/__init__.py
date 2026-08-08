"""SYJ LeadForge REST API — thin FastAPI wrapper around the `leadforge`
core modules (importer, audit, scoring, exporters, db).

The API never re-implements business logic; it calls straight into the
same functions the CLI uses, so the CLI, API, and (future) dashboard
always agree on how a lead is scored.
"""
