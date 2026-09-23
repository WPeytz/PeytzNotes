"""Access checks for the public demo and owner management routes."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.routes import search as search_routes, study as study_routes
from app.services import retrieval
from app.services import chat as chat_service


class EmptyResult:
    def mappings(self):
        return self

    def all(self):
        return []

    def first(self):
        return None

    def scalar_one_or_none(self):
        return None

    def __iter__(self):
        return iter(())


class RecordingSession:
    def __init__(self):
        self.queries = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def execute(self, statement, *_):
        self.queries.append(str(statement))
        return EmptyResult()


class OwnerAccessTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.note_id = "00000000-0000-0000-0000-000000000000"

    def test_management_routes_require_owner_key(self):
        with patch.dict(os.environ, {"PEYTZNOTES_ADMIN_KEY": "test-owner-key"}):
            requests = [
                self.client.get("/admin/notes"),
                self.client.get(f"/admin/notes/{self.note_id}"),
                self.client.patch(
                    f"/admin/notes/{self.note_id}/visibility",
                    json={"is_public": True},
                ),
                self.client.delete(f"/notes/{self.note_id}"),
                self.client.get(f"/chats/{self.note_id}/messages"),
                self.client.get("/admin/notes", headers={"X-Admin-Key": "wrong"}),
            ]
        self.assertTrue(all(response.status_code == 401 for response in requests))

    def test_management_fails_closed_without_configured_key(self):
        with patch.dict(os.environ, {"PEYTZNOTES_ADMIN_KEY": ""}):
            response = self.client.get("/admin/notes")
        self.assertEqual(response.status_code, 503)


class PublicVisibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_full_note_read_requires_public_flag(self):
        session = RecordingSession()
        with patch.object(search_routes, "async_session", return_value=session):
            with self.assertRaises(HTTPException):
                await search_routes.get_note("00000000-0000-0000-0000-000000000000")
        self.assertIn("is_public = TRUE", session.queries[0])

    async def test_note_and_course_lists_require_public_flag(self):
        notes_session = RecordingSession()
        with patch.object(search_routes, "async_session", return_value=notes_session):
            await search_routes.list_notes(course=None)
        self.assertIn("is_public = TRUE", notes_session.queries[0])

        courses_session = RecordingSession()
        with patch.object(study_routes, "async_session", return_value=courses_session):
            await study_routes.list_courses()
        self.assertIn("is_public = TRUE", courses_session.queries[0])

    async def test_retrieval_requires_public_flag(self):
        session = RecordingSession()
        with patch.object(retrieval, "async_session", return_value=session):
            with patch.object(retrieval, "embed_query", return_value=[0.0] * 1536):
                await retrieval.search_chunks("test")
        self.assertIn("n.is_public = TRUE", session.queries[0])
        self.assertIn("position(lower(:query) in lower(c.text))", session.queries[0])

    async def test_legacy_chat_cannot_reuse_private_history(self):
        session = RecordingSession()
        with patch.object(chat_service, "async_session", return_value=session):
            with self.assertRaises(HTTPException) as error:
                await chat_service.chat("00000000-0000-0000-0000-000000000000", "hello")
        self.assertEqual(error.exception.status_code, 404)
        self.assertIn("public_demo", session.queries[0])


if __name__ == "__main__":
    unittest.main()
