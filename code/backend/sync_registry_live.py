# /backend/sync_registry_live.py
"""
Fetch live Registry entries from Masumi official API and upsert into SQLite.

NOTE (2025-04-19): This synchronization functionality is currently DISABLED
                   via comments in `backend/main.py`. The code remains here
                   for future use. To re-enable, follow the instructions
                   within the `start_scheduler` function in `main.py` and
                   ensure the correct API endpoint URL (MASUMI_REGISTRY_URL)
                   and token (MASUMI_API_TOKEN) are configured in the .env
                   file at the project root. The target API endpoint also
                   needs to be verified (e.g., via Swagger UI) to ensure
                   the path and method (POST/GET) are correct.

Run once (for testing, if enabled):
    python -m backend.sync_registry_live

To schedule (if enabled via main.py):
    import backend.sync_registry_live as s; s.run_sync()
"""

