
"""
LessonGenerator: Menghasilkan latihan bahasa personal (kosa kata, tata bahasa, dll).
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import random
from pathlib import Path
import json


@dataclass
class VocabularyItem:
    word: str
    translation: str
    example_sentence: str
    difficulty: str  # "beginner", "intermediate", "advanced"
    topic: str


@dataclass
class GrammarExercise:
    rule: str
    question: str
    correct_answer: str
    options: List[str]
    explanation: str


@dataclass
class Lesson:
    lesson_id: str
    student_id: str
    language: str
    topic: str
    vocabulary: List[VocabularyItem]
    grammar: List[GrammarExercise]
    difficulty: str


class LessonGenerator:
    def __init__(self, storage_path: str = "./neuro_memory_storage"):
        self.storage_path = Path(storage_path) / "language_tutor"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load default vocabulary database
        self._init_default_vocab()

    def _init_default_vocab(self):
        """Inisialisasi database kosa kata default (contoh Inggris)."""
        vocab_file = self.storage_path / "default_vocab.json"
        if not vocab_file.exists():
            # Contoh default vocab untuk Inggris Beginner, Intermediate, Advanced
            default_vocab = [
                # --- Beginner: Greetings ---
                VocabularyItem(
                    word="Hello",
                    translation="Halo",
                    example_sentence="Hello, how are you today?",
                    difficulty="beginner",
                    topic="Greetings"
                ),
                VocabularyItem(
                    word="Goodbye",
                    translation="Selamat tinggal",
                    example_sentence="Goodbye, see you next week!",
                    difficulty="beginner",
                    topic="Greetings"
                ),
                VocabularyItem(
                    word="Thank you",
                    translation="Terima kasih",
                    example_sentence="Thank you very much for your help!",
                    difficulty="beginner",
                    topic="Greetings"
                ),
                VocabularyItem(
                    word="Please",
                    translation="Silakan",
                    example_sentence="Please sit down.",
                    difficulty="beginner",
                    topic="Greetings"
                ),
                VocabularyItem(
                    word="Sorry",
                    translation="Maaf",
                    example_sentence="I'm sorry, I'm late.",
                    difficulty="beginner",
                    topic="Greetings"
                ),
                
                # --- Beginner: Animals ---
                VocabularyItem(
                    word="Cat",
                    translation="Kucing",
                    example_sentence="The cat is sleeping on the sofa.",
                    difficulty="beginner",
                    topic="Animals"
                ),
                VocabularyItem(
                    word="Dog",
                    translation="Anjing",
                    example_sentence="My dog loves playing in the park.",
                    difficulty="beginner",
                    topic="Animals"
                ),
                VocabularyItem(
                    word="Bird",
                    translation="Burung",
                    example_sentence="A small bird is singing in the tree.",
                    difficulty="beginner",
                    topic="Animals"
                ),
                VocabularyItem(
                    word="Fish",
                    translation="Ikan",
                    example_sentence="There are many fish in the aquarium.",
                    difficulty="beginner",
                    topic="Animals"
                ),
                VocabularyItem(
                    word="Rabbit",
                    translation="Kelinci",
                    example_sentence="The rabbit has long ears.",
                    difficulty="beginner",
                    topic="Animals"
                ),
                
                # --- Beginner: Numbers ---
                VocabularyItem(
                    word="One",
                    translation="Satu",
                    example_sentence="I have one apple.",
                    difficulty="beginner",
                    topic="Numbers"
                ),
                VocabularyItem(
                    word="Two",
                    translation="Dua",
                    example_sentence="She has two sisters.",
                    difficulty="beginner",
                    topic="Numbers"
                ),
                VocabularyItem(
                    word="Three",
                    translation="Tiga",
                    example_sentence="We need three chairs.",
                    difficulty="beginner",
                    topic="Numbers"
                ),
                VocabularyItem(
                    word="Four",
                    translation="Empat",
                    example_sentence="The table has four legs.",
                    difficulty="beginner",
                    topic="Numbers"
                ),
                VocabularyItem(
                    word="Five",
                    translation="Lima",
                    example_sentence="I wake up at five o'clock.",
                    difficulty="beginner",
                    topic="Numbers"
                ),
                
                # --- Beginner: Colors ---
                VocabularyItem(
                    word="Red",
                    translation="Merah",
                    example_sentence="The red flower is beautiful.",
                    difficulty="beginner",
                    topic="Colors"
                ),
                VocabularyItem(
                    word="Blue",
                    translation="Biru",
                    example_sentence="The sky is blue today.",
                    difficulty="beginner",
                    topic="Colors"
                ),
                VocabularyItem(
                    word="Green",
                    translation="Hijau",
                    example_sentence="The grass is green in spring.",
                    difficulty="beginner",
                    topic="Colors"
                ),
                VocabularyItem(
                    word="Yellow",
                    translation="Kuning",
                    example_sentence="Bananas are yellow.",
                    difficulty="beginner",
                    topic="Colors"
                ),
                
                # --- Beginner: Food & Drink ---
                VocabularyItem(
                    word="Water",
                    translation="Air",
                    example_sentence="I drink water every day.",
                    difficulty="beginner",
                    topic="Food & Drink"
                ),
                VocabularyItem(
                    word="Apple",
                    translation="Apel",
                    example_sentence="An apple a day keeps the doctor away.",
                    difficulty="beginner",
                    topic="Food & Drink"
                ),
                VocabularyItem(
                    word="Bread",
                    translation="Roti",
                    example_sentence="I eat bread for breakfast.",
                    difficulty="beginner",
                    topic="Food & Drink"
                ),
                VocabularyItem(
                    word="Milk",
                    translation="Susu",
                    example_sentence="Children should drink milk.",
                    difficulty="beginner",
                    topic="Food & Drink"
                ),
                
                # --- Intermediate: Daily Activities ---
                VocabularyItem(
                    word="Wake up",
                    translation="Bangun tidur",
                    example_sentence="I usually wake up at 6 AM.",
                    difficulty="intermediate",
                    topic="Daily Activities"
                ),
                VocabularyItem(
                    word="Brush teeth",
                    translation="Gosok gigi",
                    example_sentence="Brush your teeth twice a day.",
                    difficulty="intermediate",
                    topic="Daily Activities"
                ),
                VocabularyItem(
                    word="Take a shower",
                    translation="Mandi",
                    example_sentence="I take a shower every morning.",
                    difficulty="intermediate",
                    topic="Daily Activities"
                ),
                VocabularyItem(
                    word="Have breakfast",
                    translation="Sarapan",
                    example_sentence="We have breakfast at 7.",
                    difficulty="intermediate",
                    topic="Daily Activities"
                ),
                
                # --- Intermediate: School/Work ---
                VocabularyItem(
                    word="Study",
                    translation="Belajar",
                    example_sentence="I study English every evening.",
                    difficulty="intermediate",
                    topic="School & Work"
                ),
                VocabularyItem(
                    word="Work",
                    translation="Bekerja",
                    example_sentence="My father works in an office.",
                    difficulty="intermediate",
                    topic="School & Work"
                ),
                VocabularyItem(
                    word="Teach",
                    translation="Mengajar",
                    example_sentence="She teaches math at a high school.",
                    difficulty="intermediate",
                    topic="School & Work"
                ),
                
                # --- Advanced: Emotions & Feelings ---
                VocabularyItem(
                    word="Ecstatic",
                    translation="Sangat gembira",
                    example_sentence="She was ecstatic when she heard the good news.",
                    difficulty="advanced",
                    topic="Emotions"
                ),
                VocabularyItem(
                    word="Melancholy",
                    translation="Sedih mendalam",
                    example_sentence="He felt melancholy on a rainy day.",
                    difficulty="advanced",
                    topic="Emotions"
                ),
                VocabularyItem(
                    word="Ambivalent",
                    translation="Ragu-ragu",
                    example_sentence="I'm ambivalent about this decision.",
                    difficulty="advanced",
                    topic="Emotions"
                )
            ]
            
            # Simpan ke JSON
            data = [item.__dict__ for item in default_vocab]
            with open(vocab_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Load vocab
        with open(vocab_file, "r", encoding="utf-8") as f:
            self.vocab_database = [VocabularyItem(**item) for item in json.load(f)]

    def generate_vocab_lesson(
        self, 
        student_id: str, 
        language: str = "English", 
        topic: Optional[str] = None, 
        difficulty: str = "beginner",
        count: int = 5
    ) -> List[VocabularyItem]:
        """Generate latihan kosa kata personal."""
        # Filter vocab berdasarkan difficulty dan topic
        filtered = [
            v for v in self.vocab_database 
            if v.difficulty == difficulty
            and (topic is None or v.topic == topic)
        ]
        
        # Pilih secara acak
        if len(filtered) > count:
            return random.sample(filtered, count)
        return filtered

    def generate_grammar_lesson(
        self, 
        student_id: str, 
        language: str = "English", 
        difficulty: str = "beginner",
        count: int = 3
    ) -> List[GrammarExercise]:
        """Generate latihan tata bahasa personal."""
        
        # Latihan berdasarkan difficulty
        beginner_exercises = [
            # --- Beginner: Simple Present Tense ---
            GrammarExercise(
                rule="Simple Present Tense",
                question="She ___ (play) football every weekend.",
                correct_answer="plays",
                options=["play", "plays", "playing", "played"],
                explanation="Untuk subjek she/he/it, tambahkan -s di akhir kata kerja."
            ),
            GrammarExercise(
                rule="Simple Present Tense",
                question="I ___ (like) eating pizza.",
                correct_answer="like",
                options=["likes", "like", "liked", "liking"],
                explanation="Untuk subjek I/you/we/they, gunakan kata kerja dasar tanpa -s."
            ),
            GrammarExercise(
                rule="Simple Present Tense",
                question="They ___ (watch) TV in the evening.",
                correct_answer="watch",
                options=["watch", "watches", "watching", "watched"],
                explanation="Untuk subjek they, gunakan kata kerja dasar."
            ),
            
            # --- Beginner: To Be (Am/Is/Are) ---
            GrammarExercise(
                rule="To Be Verbs",
                question="He ___ a doctor.",
                correct_answer="is",
                options=["is", "am", "are", "be"],
                explanation="Untuk subjek he/she/it, gunakan 'is'."
            ),
            GrammarExercise(
                rule="To Be Verbs",
                question="I ___ from Indonesia.",
                correct_answer="am",
                options=["is", "am", "are", "be"],
                explanation="Untuk subjek I, gunakan 'am'."
            ),
            GrammarExercise(
                rule="To Be Verbs",
                question="You ___ my best friend.",
                correct_answer="are",
                options=["is", "am", "are", "be"],
                explanation="Untuk subjek you, gunakan 'are'."
            ),
            
            # --- Beginner: Articles (A/An/The) ---
            GrammarExercise(
                rule="Articles (A/An)",
                question="I have ___ apple.",
                correct_answer="an",
                options=["a", "an", "the", "some"],
                explanation="Gunakan 'an' sebelum kata yang dimulai dengan vokal (a, i, u, e, o)."
            ),
            GrammarExercise(
                rule="Articles (A/An)",
                question="She is ___ teacher.",
                correct_answer="a",
                options=["a", "an", "the", "some"],
                explanation="Gunakan 'a' sebelum kata yang dimulai dengan konsonan."
            ),
            
            # --- Beginner: Plural Nouns ---
            GrammarExercise(
                rule="Plural Nouns",
                question="I have two ___ (cat).",
                correct_answer="cats",
                options=["cat", "cats", "cates", "caties"],
                explanation="Untuk sebagian besar kata benda, tambahkan -s untuk bentuk jamak."
            ),
            GrammarExercise(
                rule="Plural Nouns",
                question="There are three ___ (dog) in the park.",
                correct_answer="dogs",
                options=["dog", "dogs", "doges", "dogies"],
                explanation="Tambahkan -s di akhir kata benda untuk jamak."
            )
        ]
        
        intermediate_exercises = [
            # --- Intermediate: Simple Past Tense ---
            GrammarExercise(
                rule="Simple Past Tense",
                question="We ___ (visit) Paris last year.",
                correct_answer="visited",
                options=["visit", "visits", "visited", "visiting"],
                explanation="Untuk Simple Past, tambahkan -ed di akhir kata kerja biasa."
            ),
            GrammarExercise(
                rule="Simple Past Tense",
                question="She ___ (go) to school yesterday.",
                correct_answer="went",
                options=["go", "goes", "went", "going"],
                explanation="'Go' adalah kata kerja tidak beraturan, bentuk pastnya adalah 'went'."
            ),
            
            # --- Intermediate: Present Continuous Tense ---
            GrammarExercise(
                rule="Present Continuous Tense",
                question="Look! They ___ (play) basketball.",
                correct_answer="are playing",
                options=["play", "plays", "are playing", "played"],
                explanation="Present Continuous: am/is/are + verb-ing, untuk aksi yang sedang terjadi."
            ),
            GrammarExercise(
                rule="Present Continuous Tense",
                question="I ___ (study) for the exam now.",
                correct_answer="am studying",
                options=["study", "studies", "am studying", "studied"],
                explanation="Untuk subjek I: am + verb-ing."
            ),
            
            # --- Intermediate: Comparative Adjectives ---
            GrammarExercise(
                rule="Comparative Adjectives",
                question="My house is ___ (big) than yours.",
                correct_answer="bigger",
                options=["big", "bigger", "biggest", "more big"],
                explanation="Untuk kata sifat pendek (1-2 suku kata), tambahkan -er untuk comparative."
            ),
            GrammarExercise(
                rule="Comparative Adjectives",
                question="This book is ___ (interesting) than that one.",
                correct_answer="more interesting",
                options=["interesting", "more interesting", "most interesting", "interestinger"],
                explanation="Untuk kata sifat panjang (3+ suku kata), gunakan 'more' sebelum kata sifat."
            )
        ]
        
        advanced_exercises = [
            # --- Advanced: Present Perfect Tense ---
            GrammarExercise(
                rule="Present Perfect Tense",
                question="I ___ (finish) my homework already.",
                correct_answer="have finished",
                options=["finish", "finished", "have finished", "finishing"],
                explanation="Present Perfect: have/has + past participle, untuk aksi yang selesai baru-baru ini."
            ),
            GrammarExercise(
                rule="Present Perfect Tense",
                question="She ___ (never/visit) Japan before.",
                correct_answer="has never visited",
                options=["never visits", "never visited", "has never visited", "never visit"],
                explanation="Untuk pengalaman hidup, gunakan Present Perfect."
            ),
            
            # --- Advanced: Conditional Sentences ---
            GrammarExercise(
                rule="First Conditional",
                question="If it rains, we ___ (stay) at home.",
                correct_answer="will stay",
                options=["stay", "stayed", "will stay", "staying"],
                explanation="First Conditional: If + Simple Present, ... + will + verb (untuk situasi yang mungkin terjadi)."
            ),
            GrammarExercise(
                rule="Second Conditional",
                question="If I ___ (have) more money, I would buy a new car.",
                correct_answer="had",
                options=["have", "had", "have had", "having"],
                explanation="Second Conditional: If + Simple Past, ... + would + verb (untuk situasi yang tidak realistis)."
            ),
            
            # --- Advanced: Passive Voice ---
            GrammarExercise(
                rule="Passive Voice",
                question="The book ___ (write) by a famous author.",
                correct_answer="was written",
                options=["wrote", "was written", "writes", "is writing"],
                explanation="Passive Voice: be + past participle, ketika fokus pada objek yang dikenai aksi."
            )
        ]
        
        # Pilih exercises berdasarkan difficulty
        if difficulty == "beginner":
            selected = beginner_exercises
        elif difficulty == "intermediate":
            selected = intermediate_exercises
        elif difficulty == "advanced":
            selected = advanced_exercises
        else:
            selected = beginner_exercises
        
        # Random sampling
        if len(selected) > count:
            return random.sample(selected, count)
        return selected

    def save_lesson(self, lesson: Lesson):
        """Simpan lesson ke file JSON."""
        lesson_file = self.storage_path / f"lesson_{lesson.lesson_id}.json"
        with open(lesson_file, "w", encoding="utf-8") as f:
            # Convert dataclass ke dict
            data = lesson.__dict__
            data["vocabulary"] = [v.__dict__ for v in lesson.vocabulary]
            data["grammar"] = [g.__dict__ for g in lesson.grammar]
            json.dump(data, f, ensure_ascii=False, indent=2)

