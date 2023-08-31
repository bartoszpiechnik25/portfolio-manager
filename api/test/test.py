import unittest
from api.main.resources.sql_resource import app, CONFIG

table = """CREATE TABLE department (creation VARCHAR, department_id VARCHAR);
CREATE TABLE management (department_id VARCHAR, head_id VARCHAR);
CREATE TABLE head (head_id VARCHAR, born_state VARCHAR)"""

question = """
What are the distinct creation years of the departments
managed by a secretary born in state 'Alabama'?
Answer:
"""


class TestLLMController(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_sql_post(self):
        response = self.app.post(
            CONFIG.TEX2SQL_ENDPOINT, json={"sql_table": table, "question": question}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_text", response.json)
        self.assertIsInstance(response.json["generated_text"], list)

    def test_shouldReturnErrorWhenIncorrectData(self):
        response = self.app.post(
            CONFIG.TEX2SQL_ENDPOINT,
            json={"sql_table": table, "question": question, "num_return_sequences": 3},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.json)


if __name__ == "__main__":
    unittest.main()
