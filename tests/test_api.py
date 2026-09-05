"""Integration and unit tests for FastAPI endpoints."""

import unittest
from fastapi import HTTPException
from app import morning_briefing, chat, ChatRequest


class TestApiEndpoints(unittest.TestCase):
    """Verify API endpoint handlers and request validation."""

    def test_morning_briefing_handler(self):
        result = morning_briefing()
        self.assertIsInstance(result, dict)
        self.assertIn("stockout_risks", result)
        self.assertIn("dead_stock", result)
        self.assertIn("sales_anomalies", result)
        self.assertIsInstance(result["stockout_risks"], list)
        self.assertIsInstance(result["dead_stock"], list)
        self.assertIsInstance(result["sales_anomalies"], list)

    def test_chat_empty_message_validation(self):
        with self.assertRaises(HTTPException) as ctx:
            chat(ChatRequest(message="   "))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("cannot be empty", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
