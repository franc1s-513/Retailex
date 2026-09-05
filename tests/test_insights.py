"""Unit tests for the deterministic Morning Briefing analytics engine."""

import unittest
from backend.insights import (
    get_stockout_risks,
    get_dead_stock,
    get_sales_anomalies,
)


class TestInsightsEngine(unittest.TestCase):
    """Verify deterministic retail calculations without LLM dependency."""

    def test_stockout_risks_structure_and_detection(self):
        risks = get_stockout_risks()
        self.assertIsInstance(risks, list)
        self.assertGreater(len(risks), 0, "Expected at least one stockout/velocity risk.")

        # Check required fields
        required_fields = {
            "store_id", "product_id", "name", "category",
            "current_stock", "reorder_level", "avg_daily_velocity", "status", "severity"
        }
        for item in risks:
            self.assertTrue(required_fields.issubset(item.keys()))
            self.assertIn(item["status"], {"out_of_stock", "below_reorder", "velocity_risk"})

        # Product P008 (Espresso Machine) is engineered to be out of stock
        out_of_stock_products = {item["product_id"] for item in risks if item["status"] == "out_of_stock"}
        self.assertIn("P008", out_of_stock_products, "P008 must be identified as out of stock.")

    def test_dead_stock_detection(self):
        dead_stock = get_dead_stock()
        self.assertIsInstance(dead_stock, list)
        self.assertGreater(len(dead_stock), 0, "Expected dead stock items in dataset.")

        # Product P011 (Cast Iron Skillet) is engineered with high stock and 0 sales
        dead_product_ids = {item["product_id"] for item in dead_stock}
        self.assertIn("P011", dead_product_ids, "P011 must be identified as dead stock.")

        p011_item = next(item for item in dead_stock if item["product_id"] == "P011")
        self.assertEqual(p011_item["current_stock"], 150)
        self.assertGreater(p011_item["dead_stock_value"], 0)

    def test_sales_anomalies_detection(self):
        anomalies = get_sales_anomalies()
        self.assertIsInstance(anomalies, list)
        self.assertGreater(len(anomalies), 0, "Expected sales anomalies in dataset.")

        # Product P005 (Bluetooth Speaker) has an engineered promo spike on Day 16
        spikes = [item for item in anomalies if item["product_id"] == "P005" and item["type"] == "spike"]
        self.assertGreater(len(spikes), 0, "Expected a detected spike for product P005.")
        self.assertGreater(spikes[0]["change_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
