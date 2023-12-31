import unittest
from api.main import db, ENDPOINTS_CONFIG, create_app
from api.main.database import Users

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
app = create_app("test")


class TestLLMController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()

    def test_sql_post(self):
        response = self.app.post(
            ENDPOINTS_CONFIG.TEX2SQL_ENDPOINT, json={"sql_table": table, "question": question}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_sequence", response.json)
        self.assertIsInstance(response.json["generated_sequence"], list)

    def test_shouldReturnErrorWhenIncorrectData(self):
        response = self.app.post(
            ENDPOINTS_CONFIG.TEX2SQL_ENDPOINT,
            json={
                "sql_table": table,
                "question": question,
                "num_return_sequences": 3,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.json)

    def test_summary_post(self):
        response = self.app.post(ENDPOINTS_CONFIG.SUMMARY_ENDPOINT, json={"text": article})
        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_sequence", response.json)
        self.assertIsInstance(response.json["generated_sequence"], list)


class TestUserController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        with cls.app.application.app_context():
            db.create_all()
            cls.user1 = {"username": "test", "email": "sjdsfdf@gmail.com", "password": "test"}
            cls.user2 = {
                "username": "test2",
                "email": "askldfjas@example.com",
                "password": "test2",
                "name": "test2",
                "surname": "test2",
            }
            cls.app.post(
                ENDPOINTS_CONFIG.USER_ENDPOINT,
                json=cls.user1,
            )
            cls.app.post(
                ENDPOINTS_CONFIG.USER_ENDPOINT,
                json=cls.user2,
            )
            db.session.commit()

    @classmethod
    def tearDownClass(cls):
        with cls.app.application.app_context():
            db.metadata.drop_all(db.engine)
            db.session.commit()

    def test_add_existing_user(self):
        response = self.app.post(ENDPOINTS_CONFIG.USER_ENDPOINT, json=self.user1)
        self.assertEqual(response.status_code, 400)

    def test_get_all_users(self):
        response = self.app.get(ENDPOINTS_CONFIG.USERS_ENDPOINT)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertEqual(len(response.json), 8)

    def test_get_user1(self):
        response = self.app.get(f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/{self.user1['username']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["email"], self.user1["email"])

    def test_get_user2(self):
        response = self.app.get(f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/{self.user2['username']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["username"], self.user2["username"])

    def test_get_non_existing_user(self):
        response = self.app.get(f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/non_existing_user")
        self.assertEqual(response.status_code, 404)

    def test_delete_non_existing_user(self):
        response = self.app.delete(f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/non_existing_user")
        self.assertEqual(response.status_code, 404)

    def test_delete_user1(self):
        response = self.app.delete(f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/{self.user1['username']}")
        self.assertEqual(response.status_code, 204)
        self.app.post(
            ENDPOINTS_CONFIG.USER_ENDPOINT,
            json=self.user1,
        )

    def test_modify_user2(self):
        response = self.app.put(
            f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/{self.user2['username']}", json={"name": "test3"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "test3")

    def test_modify_non_existing_user(self):
        response = self.app.put(
            f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/non_existing_user", json={"name": "test3"}
        )
        self.assertEqual(response.status_code, 400)

    def test_create_user_with_put(self):
        response = self.app.put(
            f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/test4",
            json={"email": "sadlfsadf@sldf.com", "password": "test4", "username": "test4"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["username"], "test4")


class TestPasswordHashing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user1 = {"username": "test", "email": "something@example.com", "password": "testPasswd"}

    def test_no_password_getter(self):
        with self.assertRaises(AttributeError):
            self.user1.password

    def test_password_setter(self):
        user = Users(**self.user1)
        self.assertTrue(user.password_hash is not None)

    def test_verify_valid_password(self):
        user = Users(**self.user1)
        self.assertTrue(user.verify_password(self.user1["password"]))

    def test_verify_invalid_password(self):
        user = Users(**self.user1)
        self.assertFalse(user.verify_password("somepasswd"))


if __name__ == "__main__":
    unittest.main()
