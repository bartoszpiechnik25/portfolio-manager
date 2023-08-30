import unittest
import sys
import os

p = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join("/", *p.split("/")[:-1]))

from api.main.resources.sql_resource import app, CONFIG

test = """Given the SQL code.
CREATE TABLE department (creation VARCHAR, department_id VARCHAR);
CREATE TABLE management (department_id VARCHAR, head_id VARCHAR);
CREATE TABLE head (head_id VARCHAR, born_state VARCHAR)

Generate the SQL code to answer the following question.
What are the distinct creation years of the departments
managed by a secretary born in state 'Alabama'?
Answer:
"""


class TestLLMController(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_sql_post(self):
        response = self.app.post(CONFIG.TEX2SQL_ENDPOINT, json={"text": test})
        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_text", response.json)
        self.assertIsInstance(response.json["generated_text"], list)

    def test_shouldReturnErrorWhenIncorrectData(self):
        response = self.app.post(
            CONFIG.TEX2SQL_ENDPOINT, json={"text": test, "num_return_sequences": 3}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.json)


if __name__ == "__main__":
    unittest.main()
