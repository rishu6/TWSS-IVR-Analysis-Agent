# Render Free + Neon Free deployment

This deployment keeps the existing call history and staff accounts in a dedicated Neon PostgreSQL database. The Render service hosts the API and built frontend over HTTPS. No paid compute or disk is selected.

## Private local setup

Create `.env.render` locally with mode 600. It is ignored by Git and Docker:

```env
RENDER_API_KEY=your_render_api_key
DATABASE_URL=your_neon_postgresql_connection_string
```

Keep the existing four provider credentials in `.env.integrations`. Configure the same credentials as private environment variables on the Render service. Never copy either private file into Git or a Docker image.

Neon: create a **Free** project, open **Connect**, and copy its PostgreSQL connection string into DATABASE_URL. Use a dedicated empty database for this project. The app uses the psycopg driver; the cloud entrypoint converts standard postgres/postgresql connection URLs automatically.

## Build and start

`Dockerfile` builds the React frontend in a Node stage and packages it with Python/FastAPI. It does not seed demo records. `scripts/cloud.py` binds to `0.0.0.0:$PORT`, derives the HTTPS origin from `RENDER_EXTERNAL_URL`, forces Secure cookies, applies migrations and preserves existing admin accounts.

The `render.yaml` Blueprint selects a **Free** Docker web service in Singapore, with one instance, `/healthz` readiness checks and auto-deploy disabled. DATABASE_URL and provider credentials are dashboard/API secrets, not source values. Runtime files are ephemeral under `/tmp/twss`; the PostgreSQL database is the durable source of record.

## Move the Mac data

1. Deploy with `MIGRATION_PENDING=true` and `AUTO_SYNC=false`. Readiness remains available while user routes show setup mode.
2. Ensure the dedicated PostgreSQL database has been migrated to the current schema by the cloud startup.
3. Run `.venv/bin/python scripts/migrate_to_postgres.py` locally. It creates a consistent private SQLite backup in `.runtime/render/`, imports records in dependency order inside one PostgreSQL transaction, verifies row counts and reseeds integer IDs. Browser sessions are omitted; staff password hashes and accounts are preserved. Existing destination call/lead records or unexpected staff accounts cause refusal rather than overwrite.
4. Validate imported counts and account login, then change `MIGRATION_PENDING=false`, `AUTO_SYNC=true` and redeploy. Existing Mac staff sign-in details remain valid; users sign in again on the new URL.
5. Use the Render URL for staff activity after cutover. Retain the Mac database/backup for recovery; it is not deleted by migration.

Render Free does not provide persistent disks or SSH. The generated SSH migration key is not needed for this PostgreSQL deployment. Do not register it unless a future paid-disk deployment specifically requires SSH.

## Free-plan limits

Render Free can sleep after 15 minutes without inbound traffic; synchronization runs only while the service is awake. Startup can therefore take longer after idle. Render's free PostgreSQL database expires after 30 days, so this setup uses Neon instead. Neon Free has its own storage/compute limits. Keep both services on Free; do not enable an automatic paid upgrade.

Local SQLite backups remain on the Mac. The app's SQLite-file backup routine does not create PostgreSQL backups. Use the database provider's available recovery features and keep an off-service export appropriate to your data policy. No production availability or load certification is claimed.

Official references: [Render Free](https://render.com/docs/free), [Blueprint reference](https://render.com/docs/blueprint-spec), [Render environment variables](https://render.com/docs/environment-variables), [Neon pricing](https://neon.com/pricing).
