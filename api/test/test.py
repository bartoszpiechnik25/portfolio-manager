import unittest
from api.main.app import create_app, CONFIG

table = """CREATE TABLE department (creation VARCHAR, department_id VARCHAR);
CREATE TABLE management (department_id VARCHAR, head_id VARCHAR);
CREATE TABLE head (head_id VARCHAR, born_state VARCHAR)"""

question = """
What are the distinct creation years of the departments
managed by a secretary born in state 'Alabama'?
Answer:
"""

article = """
Do not use this command to run your application in production.
Only use the development server during development.
The development server is provided for convenience,
but is not designed to be particularly secure, stable, or efficient.
See Deploying to Production for how to run in production.
"""


class TestLLMController(unittest.TestCase):
    def setUp(self):
        self.app = create_app().test_client()

    def test_sql_post(self):
        response = self.app.post(
            CONFIG.TEX2SQL_ENDPOINT, json={"sql_table": table, "question": question}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_sequence", response.json)
        self.assertIsInstance(response.json["generated_sequence"], list)

    def test_shouldReturnErrorWhenIncorrectData(self):
        response = self.app.post(
            CONFIG.TEX2SQL_ENDPOINT,
            json={"sql_table": table, "question": question, "num_return_sequences": 3},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.json)

    def test_summary_post(self):
        response = self.app.post(CONFIG.SUMMARY_ENDPOINT, json={"text": article})
        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_sequence", response.json)
        self.assertIsInstance(response.json["generated_sequence"], list)


if __name__ == "__main__":
    unittest.main()
