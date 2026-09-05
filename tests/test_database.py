"""Unit tests for database read-only operations and safety guards."""

import unittest
from backend.database_ops import execute_query, get_db_schema


class TestDatabaseOps(unittest.TestCase):
    """Verify read-only SQL enforcement and database schema retrieval."""

    def test_valid_select_query(self):
        rows = execute_query("SELECT product_id, name, selling_price FROM Products LIMIT 5;")
        self.assertIsInstance(rows, list)
        self.assertEqual(len(rows), 5)
        self.assertIn("product_id", rows[0])
        self.assertIn("name", rows[0])
        self.assertIn("selling_price", rows[0])

    def test_read_only_blocks_insert(self):
        with self.assertRaises(ValueError) as ctx:
            execute_query("INSERT INTO Products (product_id, name) VALUES ('P999', 'Fake');")
        self.assertIn("Only read-only SQL is allowed", str(ctx.exception))

    def test_read_only_blocks_drop(self):
        with self.assertRaises(ValueError) as ctx:
            execute_query("DROP TABLE Products;")
        self.assertIn("Only read-only SQL is allowed", str(ctx.exception))

    def test_read_only_blocks_delete(self):
        with self.assertRaises(ValueError) as ctx:
            execute_query("DELETE FROM Products WHERE product_id = 'P001';")
        self.assertIn("Only read-only SQL is allowed", str(ctx.exception))

    def test_empty_query_raises(self):
        with self.assertRaises(ValueError):
            execute_query("   ")

    def test_get_db_schema_contains_all_tables(self):
        schema = get_db_schema()
        self.assertIsInstance(schema, str)
        self.assertIn("Table: Products", schema)
        self.assertIn("Table: Inventory", schema)
        self.assertIn("Table: Sales", schema)
        self.assertIn("product_id", schema)
        self.assertIn("current_stock", schema)
        self.assertIn("quantity_sold", schema)


if __name__ == "__main__":
    unittest.main()
