import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DB_PATH = BACKEND_DIR / "test_app.db"

sys.path.insert(0, str(BACKEND_DIR))

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from fastapi.testclient import TestClient

from database import Base, engine
from main import app
from routes import chat as chat_routes


class FakeGeminiResponse:
    def __init__(self, text):
        self.text = text


class FakeGeminiChat:
    def send_message(self, message):
        return FakeGeminiResponse(f"Support reply: {message}")


class FakeGeminiModel:
    def start_chat(self, history=None):
        return FakeGeminiChat()


class MentalHealthAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_model = chat_routes.model
        chat_routes.model = FakeGeminiModel()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        chat_routes.model = cls.original_model
        Base.metadata.drop_all(bind=engine)
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def signup_and_login(self):
        signup_response = self.client.post(
            "/signup",
            json={
                "email": "test@example.com",
                "password": "Password123!",
                "name": "Test User",
                "username": "test_user",
            },
        )
        self.assertEqual(signup_response.status_code, 200)

        login_response = self.client.post(
            "/login",
            json={"email": "test@example.com", "password": "Password123!"},
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def test_auth_flow(self):
        headers = self.signup_and_login()

        profile_response = self.client.put(
            "/profile",
            json={
                "name": "Updated User",
                "email": "updated@example.com",
                "current_password": "Password123!",
            },
            headers=headers,
        )

        self.assertEqual(profile_response.status_code, 200)
        body = profile_response.json()
        self.assertEqual(body["user"]["name"], "Updated User")
        self.assertEqual(body["user"]["email"], "updated@example.com")
        self.assertTrue(body["user"]["has_password"])
        self.assertFalse(body["user"]["dark_mode"])
        self.assertEqual(body["user"]["language"], "English")

    def test_preference_persistence_flow(self):
        headers = self.signup_and_login()

        preference_response = self.client.put(
            "/profile",
            json={
                "dark_mode": True,
                "email_notifications": False,
                "push_notifications": False,
                "language": "Spanish",
            },
            headers=headers,
        )

        self.assertEqual(preference_response.status_code, 200)
        user = preference_response.json()["user"]
        self.assertTrue(user["dark_mode"])
        self.assertFalse(user["email_notifications"])
        self.assertFalse(user["push_notifications"])
        self.assertEqual(user["language"], "Spanish")

        privacy_summary = self.client.get("/privacy-summary", headers=headers)
        self.assertEqual(privacy_summary.status_code, 200)
        self.assertTrue(privacy_summary.json()["preferences"]["dark_mode"])

    def test_chat_and_history_flow(self):
        headers = self.signup_and_login()

        chat_response = self.client.post(
            "/chat",
            json={"message": "I feel anxious about work lately."},
            headers=headers,
        )
        self.assertEqual(chat_response.status_code, 200)
        chat_body = chat_response.json()
        self.assertIn("Support reply", chat_body["response"])
        session_id = chat_body["session_id"]

        history_response = self.client.get("/history/", headers=headers)
        self.assertEqual(history_response.status_code, 200)
        sessions = history_response.json()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["tag"], "Anxiety")
        self.assertEqual(sessions[0]["title"], "Work Anxiety Support")

        messages_response = self.client.get(f"/history/{session_id}", headers=headers)
        self.assertEqual(messages_response.status_code, 200)
        messages = messages_response.json()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["sender"], "user")
        self.assertEqual(messages[1]["sender"], "ai")

    def test_chat_title_generation_for_general_topics(self):
        headers = self.signup_and_login()

        response = self.client.post(
            "/chat",
            json={"message": "I keep overthinking conversations and confidence at social events lately."},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)

        history_response = self.client.get("/history/", headers=headers)
        self.assertEqual(history_response.status_code, 200)
        sessions = history_response.json()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["title"], "Overthinking Conversations Confidence")

    def test_history_management_flow(self):
        headers = self.signup_and_login()

        first_chat = self.client.post(
            "/chat",
            json={"message": "I need help with my goals."},
            headers=headers,
        )
        second_chat = self.client.post(
            "/chat",
            json={"message": "My sleep has been difficult."},
            headers=headers,
        )
        first_session_id = first_chat.json()["session_id"]
        second_session_id = second_chat.json()["session_id"]

        rename_response = self.client.put(
            f"/history/{first_session_id}",
            json={"title": "Goals Session"},
            headers=headers,
        )
        self.assertEqual(rename_response.status_code, 200)
        self.assertEqual(rename_response.json()["title"], "Goals Session")

        delete_one_response = self.client.delete(
            f"/history/{second_session_id}",
            headers=headers,
        )
        self.assertEqual(delete_one_response.status_code, 200)

        delete_all_response = self.client.delete("/history/", headers=headers)
        self.assertEqual(delete_all_response.status_code, 200)
        self.assertEqual(delete_all_response.json()["message"], "All conversation history deleted successfully")

    def test_history_search_flow(self):
        headers = self.signup_and_login()

        self.client.post(
            "/chat",
            json={"message": "I feel anxious about an upcoming presentation."},
            headers=headers,
        )
        self.client.post(
            "/chat",
            json={"message": "My relationship has been feeling distant lately."},
            headers=headers,
        )

        anxiety_search = self.client.get("/history/?q=anxious", headers=headers)
        self.assertEqual(anxiety_search.status_code, 200)
        anxiety_sessions = anxiety_search.json()
        self.assertEqual(len(anxiety_sessions), 1)
        self.assertEqual(anxiety_sessions[0]["tag"], "Anxiety")

        relationship_search = self.client.get("/history/?q=relationship", headers=headers)
        self.assertEqual(relationship_search.status_code, 200)
        relationship_sessions = relationship_search.json()
        self.assertEqual(len(relationship_sessions), 1)
        self.assertEqual(relationship_sessions[0]["tag"], "Relationships")

    def test_history_bulk_delete_flow(self):
        headers = self.signup_and_login()

        first_chat = self.client.post(
            "/chat",
            json={"message": "I feel anxious about work lately."},
            headers=headers,
        )
        second_chat = self.client.post(
            "/chat",
            json={"message": "My relationship has been feeling distant lately."},
            headers=headers,
        )
        third_chat = self.client.post(
            "/chat",
            json={"message": "I want to reflect on my week."},
            headers=headers,
        )

        bulk_delete_response = self.client.request(
            "DELETE",
            "/history/bulk",
            json={
                "session_ids": [
                    first_chat.json()["session_id"],
                    second_chat.json()["session_id"],
                ]
            },
            headers=headers,
        )
        self.assertEqual(bulk_delete_response.status_code, 200)
        self.assertEqual(bulk_delete_response.json()["deleted_sessions"], 2)

        remaining_history = self.client.get("/history/", headers=headers)
        self.assertEqual(remaining_history.status_code, 200)
        remaining_sessions = remaining_history.json()
        self.assertEqual(len(remaining_sessions), 1)
        self.assertEqual(remaining_sessions[0]["id"], third_chat.json()["session_id"])

    def test_history_status_flow(self):
        headers = self.signup_and_login()

        first_chat = self.client.post(
            "/chat",
            json={"message": "I feel anxious about work lately."},
            headers=headers,
        )
        second_chat = self.client.post(
            "/chat",
            json={"message": "My relationship has been feeling distant lately."},
            headers=headers,
        )

        first_session_id = first_chat.json()["session_id"]
        second_session_id = second_chat.json()["session_id"]

        pin_response = self.client.patch(
            f"/history/{second_session_id}/status",
            json={"is_pinned": True},
            headers=headers,
        )
        self.assertEqual(pin_response.status_code, 200)
        self.assertTrue(pin_response.json()["is_pinned"])

        archive_response = self.client.patch(
            f"/history/{first_session_id}/status",
            json={"is_archived": True},
            headers=headers,
        )
        self.assertEqual(archive_response.status_code, 200)
        self.assertTrue(archive_response.json()["is_archived"])
        self.assertFalse(archive_response.json()["is_pinned"])

        active_history = self.client.get("/history/", headers=headers)
        self.assertEqual(active_history.status_code, 200)
        active_sessions = active_history.json()
        self.assertEqual(len(active_sessions), 1)
        self.assertEqual(active_sessions[0]["id"], second_session_id)
        self.assertTrue(active_sessions[0]["is_pinned"])

        archived_history = self.client.get("/history/?include_archived=true", headers=headers)
        self.assertEqual(archived_history.status_code, 200)
        archived_sessions = archived_history.json()
        self.assertEqual(len(archived_sessions), 2)
        self.assertTrue(any(session["is_archived"] for session in archived_sessions))

    def test_export_data_includes_preferences_and_session_metadata(self):
        headers = self.signup_and_login()

        preference_response = self.client.put(
            "/profile",
            json={
                "dark_mode": True,
                "email_notifications": False,
                "push_notifications": True,
                "language": "French",
            },
            headers=headers,
        )
        self.assertEqual(preference_response.status_code, 200)

        chat_response = self.client.post(
            "/chat",
            json={"message": "I feel anxious about work lately."},
            headers=headers,
        )
        session_id = chat_response.json()["session_id"]

        status_response = self.client.patch(
            f"/history/{session_id}/status",
            json={"is_pinned": True},
            headers=headers,
        )
        self.assertEqual(status_response.status_code, 200)

        export_response = self.client.get("/export", headers=headers)
        self.assertEqual(export_response.status_code, 200)
        export_data = export_response.json()
        self.assertTrue(export_data["user"]["preferences"]["dark_mode"])
        self.assertEqual(export_data["user"]["preferences"]["language"], "French")
        self.assertEqual(len(export_data["sessions"]), 1)
        self.assertTrue(export_data["sessions"][0]["is_pinned"])

    def test_insights_flow(self):
        headers = self.signup_and_login()

        for payload in [
            {"mood_score": 7, "energy_level": 6, "stress_level": 4},
            {"mood_score": 8, "energy_level": 7, "stress_level": 3},
            {"mood_score": 6, "energy_level": 5, "stress_level": 5},
        ]:
            response = self.client.post("/insights/mood", json=payload, headers=headers)
            self.assertEqual(response.status_code, 200)

        self.client.post(
            "/chat",
            json={"message": "I feel stress at work and some anxiety."},
            headers=headers,
        )

        stats_response = self.client.get("/insights/stats", headers=headers)
        self.assertEqual(stats_response.status_code, 200)
        self.assertIn("total_sessions", stats_response.json())

        summary_response = self.client.get("/insights/summary?days=7", headers=headers)
        self.assertEqual(summary_response.status_code, 200)
        self.assertEqual(len(summary_response.json()["insights"]), 4)

        topics_response = self.client.get("/insights/topics", headers=headers)
        self.assertEqual(topics_response.status_code, 200)
        self.assertGreaterEqual(len(topics_response.json()["topics"]), 1)

        patterns_response = self.client.get("/insights/patterns?days=7", headers=headers)
        self.assertEqual(patterns_response.status_code, 200)
        self.assertIn("current_streak", patterns_response.json())
        self.assertIn("correlations", patterns_response.json())

        achievements_response = self.client.get("/insights/achievements", headers=headers)
        self.assertEqual(achievements_response.status_code, 200)
        self.assertEqual(len(achievements_response.json()["achievements"]), 4)


if __name__ == "__main__":
    unittest.main()
