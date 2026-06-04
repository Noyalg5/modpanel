# Switching to PostgreSQL

ModPanel AI Platform uses SQLAlchemy with async drivers, so switching databases requires only a single environment variable change. No code changes are needed.

## Local PostgreSQL setup

1. **Install PostgreSQL** on your machine (version 13+).

2. **Create a database and user:**
   ```bash
   createdb modpanel
   createuser modpanel_user
   psql -c "ALTER USER modpanel_user WITH PASSWORD 'your_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE modpanel TO modpanel_user;"
   ```

3. **Update your `.env` file:**
   ```
   DATABASE_URL=postgresql+asyncpg://modpanel_user:your_password@localhost:5432/modpanel
   ```

4. **Restart the server** — tables are created automatically on startup:
   ```bash
   uvicorn main:app --reload
   ```
   You will see a log line confirming the database type:
   ```
   INFO: Database: postgresql — postgresql+asyncpg://modpanel_user:...
   ```

## Docker option (quickest)

```bash
docker run --name modpanel-pg \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=modpanel \
  -p 5432:5432 \
  -d postgres:15
```

Then set in `.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/modpanel
```

## Switching back to SQLite

```
DATABASE_URL=sqlite+aiosqlite:///./modpanel.db
```

## Notes

- Tests always run against SQLite regardless of your `.env` setting.
- The `asyncpg` driver is used for PostgreSQL; `aiosqlite` is used for SQLite.
- Both drivers are installed via `requirements.txt`.
- All DateTime columns store timezone-aware values (`TIMESTAMPTZ` in PostgreSQL).
