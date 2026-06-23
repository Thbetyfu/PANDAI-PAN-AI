
"""
ProgressTracker: Melacak perkembangan belajar bahasa siswa (kosa kata, tata bahasa, dll).
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime


@dataclass
class VocabProgress:
    word: str
    correct_count: int = 0
    wrong_count: int = 0
    last_reviewed: Optional[str] = None
    mastery_level: float = 0.0  # 0.0 - 1.0


@dataclass
class StudentProgress:
    student_id: str
    language: str
    total_words_learned: int = 0
    lessons_completed: int = 0
    streak_days: int = 0
    vocab_progress: Dict[str, VocabProgress] = None


class ProgressTracker:
    def __init__(self, storage_path: str = "./neuro_memory_storage"):
        self.storage_path = Path(storage_path) / "language_tutor"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.student_progress: Dict[str, StudentProgress] = {}  # key: student_id
        self._load_progress()

    def _load_progress(self):
        """Load progress dari file JSON."""
        progress_file = self.storage_path / "progress.json"
        if progress_file.exists():
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for student_id, prog_data in data.items():
                    vocab_dict = {}
                    for word, vocab_prog in prog_data.get("vocab_progress", {}).items():
                        vocab_dict[word] = VocabProgress(**vocab_prog)
                    self.student_progress[student_id] = StudentProgress(
                        student_id=student_id,
                        language=prog_data.get("language", "English"),
                        total_words_learned=prog_data.get("total_words_learned", 0),
                        lessons_completed=prog_data.get("lessons_completed", 0),
                        streak_days=prog_data.get("streak_days", 0),
                        vocab_progress=vocab_dict
                    )

    def _save_progress(self):
        """Simpan progress ke file JSON."""
        progress_file = self.storage_path / "progress.json"
        data = {}
        for student_id, prog in self.student_progress.items():
            vocab_dict = {}
            for word, vocab_prog in prog.vocab_progress.items():
                vocab_dict[word] = vocab_prog.__dict__
            data[student_id] = {
                "student_id": prog.student_id,
                "language": prog.language,
                "total_words_learned": prog.total_words_learned,
                "lessons_completed": prog.lessons_completed,
                "streak_days": prog.streak_days,
                "vocab_progress": vocab_dict
            }
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_or_create_student_progress(self, student_id: str, language: str = "English") -> StudentProgress:
        """Dapatkan atau buat progress siswa baru."""
        if student_id not in self.student_progress:
            self.student_progress[student_id] = StudentProgress(
                student_id=student_id,
                language=language,
                vocab_progress={}
            )
            self._save_progress()
        return self.student_progress[student_id]

    def update_vocab_progress(
        self, 
        student_id: str, 
        word: str, 
        is_correct: bool
    ):
        """Update progress kosa kata siswa."""
        prog = self.get_or_create_student_progress(student_id)
        
        if word not in prog.vocab_progress:
            prog.vocab_progress[word] = VocabProgress(word=word)
            prog.total_words_learned += 1
        
        vocab_prog = prog.vocab_progress[word]
        if is_correct:
            vocab_prog.correct_count += 1
            vocab_prog.mastery_level = min(1.0, vocab_prog.mastery_level + 0.1)
        else:
            vocab_prog.wrong_count += 1
            vocab_prog.mastery_level = max(0.0, vocab_prog.mastery_level - 0.05)
        
        vocab_prog.last_reviewed = datetime.now().isoformat()
        self._save_progress()

    def increment_lesson_completed(self, student_id: str):
        """Tambahkan jumlah lesson yang selesai."""
        prog = self.get_or_create_student_progress(student_id)
        prog.lessons_completed += 1
        self._save_progress()

    def get_student_summary(self, student_id: str) -> Optional[Dict]:
        """Dapatkan ringkasan progress siswa."""
        if student_id not in self.student_progress:
            return None
        prog = self.student_progress[student_id]
        return {
            "student_id": prog.student_id,
            "language": prog.language,
            "total_words_learned": prog.total_words_learned,
            "lessons_completed": prog.lessons_completed,
            "streak_days": prog.streak_days,
            "vocab_count": len(prog.vocab_progress)
        }

