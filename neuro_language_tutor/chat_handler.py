
"""
LanguageChatHandler: Mengelola percakapan bahasa dengan AI, koreksi otomatis, dan feedback.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
from .llm_handler import LLMHandler


@dataclass
class ChatMessage:
    role: str  # "user" atau "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correction: Optional[str] = None  # Koreksi jika ada kesalahan
    explanation: Optional[str] = None  # Penjelasan koreksi


class LanguageChatHandler:
    def __init__(
        self, 
        storage_path: str = "./neuro_memory_storage",
        target_language: str = "English"
    ):
        self.storage_path = Path(storage_path) / "language_tutor"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.target_language = target_language
        self.conversations: Dict[str, List[ChatMessage]] = {}  # key: student_id
        
        # Inisialisasi LLM Handler
        self.llm = LLMHandler()
        
        # Load saved conversations
        self._load_conversations()

    def _load_conversations(self):
        """Load riwayat percakapan dari file JSON."""
        conv_file = self.storage_path / "conversations.json"
        if conv_file.exists():
            with open(conv_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for student_id, conv_list in data.items():
                    self.conversations[student_id] = [
                        ChatMessage(**msg) for msg in conv_list
                    ]

    def _save_conversations(self):
        """Simpan riwayat percakapan ke file JSON."""
        conv_file = self.storage_path / "conversations.json"
        data = {}
        for student_id, conv_list in self.conversations.items():
            data[student_id] = [msg.__dict__ for msg in conv_list]
        with open(conv_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_user_message(self, student_id: str, content: str, timestamp: Optional[str] = None):
        """Tambahkan pesan user ke riwayat."""
        if student_id not in self.conversations:
            self.conversations[student_id] = []
        
        self.conversations[student_id].append(
            ChatMessage(
                role="user", 
                content=content, 
                timestamp=timestamp or datetime.now().isoformat()
            )
        )
        self._save_conversations()

    def generate_assistant_response(
        self,
        student_id: str,
        teacher_context: Optional[str] = None,
        teacher_persona: str = "strict_warm",
        correction_mode: str = "fluency_first",
        llm_mode: str = "auto",
        llm_profile: Optional[str] = None,
        llm_model: Optional[str] = None
    ) -> ChatMessage:
        """
        Generate response AI menggunakan LLM, beserta koreksi dan penjelasan.
        """
        history = self.get_conversation_history(student_id, limit=10)
        user_message = history[-1].content if history else ""
        
        # Generate response dari LLM
        assistant_content, correction, explanation = self.llm.generate_response(
            user_message=user_message,
            conversation_history=history,
            teacher_context=teacher_context,
            teacher_persona=teacher_persona,
            correction_mode=correction_mode,
            llm_mode=llm_mode,
            llm_profile=llm_profile,
            llm_model=llm_model
        )
        
        # Tambahkan ke riwayat dan kembalikan
        self.add_assistant_message(
            student_id=student_id,
            content=assistant_content,
            correction=correction,
            explanation=explanation
        )
        
        # Dapatkan message terakhir (yang baru ditambahkan)
        return self.conversations[student_id][-1]

    def add_assistant_message(
        self, 
        student_id: str, 
        content: str, 
        timestamp: Optional[str] = None,
        correction: Optional[str] = None,
        explanation: Optional[str] = None
    ):
        """Tambahkan pesan assistant beserta koreksi dan penjelasan."""
        if student_id not in self.conversations:
            self.conversations[student_id] = []
        
        self.conversations[student_id].append(
            ChatMessage(
                role="assistant", 
                content=content, 
                timestamp=timestamp or datetime.now().isoformat(),
                correction=correction,
                explanation=explanation
            )
        )
        self._save_conversations()

    def get_conversation_history(self, student_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Dapatkan riwayat percakapan siswa (opsional batasi jumlah pesan terakhir)."""
        if student_id not in self.conversations:
            return []
        conv = self.conversations[student_id]
        if limit:
            return conv[-limit:]
        return conv

    def clear_conversation(self, student_id: str):
        """Hapus riwayat percakapan siswa."""
        if student_id in self.conversations:
            del self.conversations[student_id]
            self._save_conversations()
