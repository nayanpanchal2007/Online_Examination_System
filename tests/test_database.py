import tempfile
import unittest
from pathlib import Path

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        database.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_seeded_users_can_authenticate(self):
        student = database.authenticate("alice", "alice123", self.db_path)
        self.assertEqual(student["role"], "student")
        self.assertIsNone(database.authenticate("alice", "wrong", self.db_path))

    def test_exam_submission_scores_answers_and_records_attempt(self):
        student = database.authenticate("alice", "alice123", self.db_path)
        exam = database.list_exams(self.db_path)[0]
        questions = database.get_questions(exam["id"], self.db_path)
        answers = {question["id"]: question["options"][0] for question in questions}

        result = database.submit_attempt(student["id"], exam["id"], answers, self.db_path)

        self.assertEqual(result, {"score": 1, "total": 4})
        attempts = database.get_attempts(student["id"], self.db_path)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["total"], 4)

    def test_admin_can_create_exam_and_question(self):
        exam_id = database.add_exam("Test", "Python", "A test exam", self.db_path)
        database.add_question(exam_id, "Pick one", ["yes", "no"], "yes", self.db_path)

        self.assertEqual(database.list_exams(self.db_path)[-1]["question_count"], 1)
        self.assertEqual(len(database.get_questions(exam_id, self.db_path)), 1)

    def test_admin_can_manage_students(self):
        student_id = database.add_student("nina", "Nina Lopez", "nina123", self.db_path)

        self.assertEqual(database.authenticate("nina", "nina123", self.db_path)["full_name"], "Nina Lopez")
        self.assertIn("nina", [item["username"] for item in database.list_students(self.db_path)])

        database.update_student(student_id, db_path=self.db_path, full_name="Nina Patel", password="newsecret")
        self.assertEqual(database.authenticate("nina", "newsecret", self.db_path)["full_name"], "Nina Patel")

        database.delete_student(student_id, self.db_path)
        self.assertIsNone(database.authenticate("nina", "newsecret", self.db_path))

    def test_invalid_database_inputs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "title and subject"):
            database.add_exam(" ", "Python", "", self.db_path)

        exam_id = database.add_exam("Validation", "Python", "", self.db_path)
        with self.assertRaisesRegex(ValueError, "Question text"):
            database.add_question(exam_id, " ", ["yes", "no"], "yes", self.db_path)
        with self.assertRaisesRegex(ValueError, "unique"):
            database.add_question(exam_id, "Pick one", ["yes", "yes"], "yes", self.db_path)

        with self.assertRaisesRegex(ValueError, "already in use"):
            database.add_student("alice", "Another Alice", "password", self.db_path)

        nina_id = database.add_student("nina", "Nina Lopez", "password", self.db_path)
        with self.assertRaisesRegex(ValueError, "already in use"):
            database.update_student(nina_id, username="alice", db_path=self.db_path)

    def test_submission_rejects_answers_from_another_exam(self):
        student = database.authenticate("alice", "alice123", self.db_path)
        exams = database.list_exams(self.db_path)
        question = database.get_questions(exams[0]["id"], self.db_path)[0]
        other_questions = database.get_questions(exams[1]["id"], self.db_path)
        answers = {item["id"]: item["options"][0] for item in other_questions}
        answers[question["id"]] = "tuple"

        with self.assertRaisesRegex(ValueError, "do not match"):
            database.submit_attempt(student["id"], exams[1]["id"], answers, self.db_path)

    def test_malformed_password_hash_fails_authentication(self):
        with database.connect(self.db_path) as connection:
            connection.execute("UPDATE users SET password_hash = 'not-a-valid-hash' WHERE username = 'alice'")

        self.assertIsNone(database.authenticate("alice", "alice123", self.db_path))

    def test_submission_rejects_unknown_accounts_and_incomplete_answers(self):
        exam = database.list_exams(self.db_path)[0]
        questions = database.get_questions(exam["id"], self.db_path)
        student = database.authenticate("alice", "alice123", self.db_path)
        answers = {question["id"]: question["options"][0] for question in questions}

        with self.assertRaisesRegex(ValueError, "Answer every question"):
            database.submit_attempt(student["id"], exam["id"], {}, self.db_path)
        with self.assertRaisesRegex(ValueError, "Student account"):
            database.submit_attempt(99999, exam["id"], answers, self.db_path)
        with self.assertRaisesRegex(ValueError, "Assessment not found"):
            database.submit_attempt(student["id"], 99999, answers, self.db_path)

    def test_corrupt_question_options_are_reported_as_validation_errors(self):
        exam = database.list_exams(self.db_path)[0]
        question_id = database.get_questions(exam["id"], self.db_path)[0]["id"]
        with database.connect(self.db_path) as connection:
            connection.execute(
                "UPDATE questions SET options_json = ? WHERE id = ?",
                ("not-json", question_id),
            )

        with self.assertRaisesRegex(ValueError, "invalid question data"):
            database.get_questions(exam["id"], self.db_path)


if __name__ == "__main__":
    unittest.main()