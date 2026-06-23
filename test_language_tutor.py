
"""
Unit Tests for Neuro-Language-Tutor
"""
import unittest
from pathlib import Path
import os
import shutil

# Import modules
from neuro_language_tutor import LanguageChatHandler, LessonGenerator, ProgressTracker, SpeechHandler


class TestLessonGenerator(unittest.TestCase):
    """Test LessonGenerator functionality"""
    
    def setUp(self):
        """Set up test fixture"""
        self.test_path = Path("test_memory_storage")
        self.generator = LessonGenerator(storage_path=str(self.test_path))
        self.student_id = "test_student_123"
    
    def tearDown(self):
        """Clean up after test"""
        if self.test_path.exists():
            try:
                shutil.rmtree(self.test_path)
            except:
                pass
    
    def test_vocab_lesson_generation(self):
        """Test generate_vocab_lesson()"""
        vocab_list = self.generator.generate_vocab_lesson(
            student_id=self.student_id,
            topic="Animals",
            difficulty="beginner",
            count=5
        )
        
        self.assertIsNotNone(vocab_list)
        self.assertGreater(len(vocab_list), 0)
        for item in vocab_list:
            self.assertEqual(item.difficulty, "beginner")
            self.assertEqual(item.topic, "Animals")
        print(f"✅ Vocab Lesson Test Passed: Generated {len(vocab_list)} words for topic 'Animals'")
    
    def test_grammar_lesson_generation(self):
        """Test generate_grammar_lesson()"""
        exercises = self.generator.generate_grammar_lesson(
            student_id=self.student_id,
            difficulty="beginner",
            count=3
        )
        
        self.assertIsNotNone(exercises)
        self.assertGreater(len(exercises), 0)
        for exercise in exercises:
            self.assertIsNotNone(exercise.question)
            self.assertIsNotNone(exercise.correct_answer)
        print(f"✅ Grammar Lesson Test Passed: Generated {len(exercises)} exercises")


class TestProgressTracker(unittest.TestCase):
    """Test ProgressTracker functionality"""
    
    def setUp(self):
        """Set up test fixture"""
        # Use temporary test path
        self.test_path = Path("test_memory_storage")
        self.tracker = ProgressTracker(storage_path=str(self.test_path))
        self.student_id = "test_student_456"
    
    def tearDown(self):
        """Clean up after test"""
        if self.test_path.exists():
            try:
                shutil.rmtree(self.test_path)
            except:
                pass
    
    def test_student_progress_creation(self):
        """Test that student progress is created correctly"""
        progress = self.tracker.get_or_create_student_progress(self.student_id)
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress.student_id, self.student_id)
        self.assertEqual(progress.lessons_completed, 0)
        print("✅ Progress Creation Test Passed")
    
    def test_increment_lesson_completed(self):
        """Test incrementing lesson completed count"""
        self.tracker.increment_lesson_completed(self.student_id)
        progress = self.tracker.get_or_create_student_progress(self.student_id)
        
        self.assertEqual(progress.lessons_completed, 1)
        print("✅ Increment Lesson Test Passed")
    
    def test_update_vocab_progress(self):
        """Test updating vocabulary progress"""
        self.tracker.update_vocab_progress(
            student_id=self.student_id,
            word="hello",
            is_correct=True
        )
        progress = self.tracker.get_or_create_student_progress(self.student_id)
        
        self.assertIn("hello", progress.vocab_progress)
        self.assertEqual(progress.vocab_progress["hello"].correct_count, 1)
        print("✅ Vocab Progress Test Passed")


class TestChatHandler(unittest.TestCase):
    """Test LanguageChatHandler functionality"""
    
    def setUp(self):
        """Set up test fixture"""
        self.test_path = Path("test_memory_storage")
        self.chat_handler = LanguageChatHandler(storage_path=str(self.test_path))
        self.student_id = "test_student_789"
    
    def tearDown(self):
        """Clean up after test"""
        if self.test_path.exists():
            try:
                shutil.rmtree(self.test_path)
            except:
                pass
    
    def test_add_user_message(self):
        """Test adding user message to chat"""
        self.chat_handler.add_user_message(self.student_id, "Hello!")
        history = self.chat_handler.get_conversation_history(self.student_id)
        
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "Hello!")
        print("✅ Add User Message Test Passed")


if __name__ == "__main__":
    print("🧪 Running Neuro-Language-Tutor Unit Tests...")
    print("=" * 60)
    
    # Run all tests
    unittest.main(verbosity=2)

