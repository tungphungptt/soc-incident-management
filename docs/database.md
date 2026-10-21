# Database compatibility notes

The source archive includes:
- `seed_soc_incident_management.sql`
- `verify_soc_incident_management.sql`
- `queries_18_soc_incident_management.sql`
- `README_seed_report.md`
- `generate_seed.py`

The seed file states that it only performs INSERT operations and expects the schema to exist. It does not contain the complete CREATE TABLE definitions. The app therefore introspects these existing tables at runtime.

Before using:
1. Confirm database `soc_incident_management` exists.
2. Confirm all 14 expected tables exist.
3. Review the supplied verification SQL and seed README.
4. Back up the database.
5. Use a least-privilege MySQL account for the application.
6. Do not run seed scripts twice unless duplicate handling has been deliberately planned.

The application intentionally avoids automatically altering schema to fit the code.
