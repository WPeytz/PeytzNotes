# PeytzNotes demo deployment

The public demo shows only notes whose `is_public` flag has been explicitly enabled. Existing notes become private when the backend first starts with the visibility migration. Uploads also start private.

Set a strong, random `PEYTZNOTES_ADMIN_KEY` on the Railway backend before deploying this version. Without it, management endpoints return 503 and no one can publish, upload, or delete notes. Keep the key out of source control and out of `NEXT_PUBLIC_*` variables.

The owner can visit `/admin`, enter the key, preview notes, and publish individual notes. The key stays in that page's memory and is cleared on reload. Public browsing, search, chat, and study generation use only published notes. The public AI endpoints have a shared per-client hourly budget controlled by `PEYTZNOTES_DEMO_HOURLY_LIMIT` (default 30).

Before publishing any note, review its full content for private data and third-party material. Unpublishing removes it from new public reads and retrieval. Previously generated chat answers are retained in the chat database.
