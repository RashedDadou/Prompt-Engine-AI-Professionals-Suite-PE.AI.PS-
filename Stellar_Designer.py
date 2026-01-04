# advanced_knowledge.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class MemoryEntry(Base):
    __tablename__ = 'long_term_memory'
    
    id = Column(Integer, primary_key=True)
    input_text = Column(String, nullable=False)      # النص المخزن (مثل: spacecraft/engines/thrust:10.0)
    timestamp = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    category = Column(String, default="general")     # space, philosophy, engineering, etc.
    priority = Column(Integer, default=5)            # كل ما أعلى كل ما أهم

class AdvancedKnowledgeLibrary:
    def __init__(self, db_path="stellar_advanced_knowledge.db"):
        db_url = f'sqlite:///{db_path}'
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def calculate_priority(self, key: str) -> int:
        """نظام أولويات بسيط لكن فعال"""
        high_priority = ['plasma', 'engine', 'thruster', 'shield', 'laser', 'weapon', 'commander', 'nebula']
        medium_priority = ['angle', 'thrust', 'material', 'design', 'glow', 'trail']
        
        key_lower = key.lower()
        if any(word in key_lower for word in high_priority):
            return 20
        elif any(word in key_lower for word in medium_priority):
            return 10
        return 5

    def update_knowledge(self, category: str, subcategory: str, key: str, value: str, specialization: str = "space"):
        session = self.Session()
        entry_text = f"{category}/{subcategory}/{key}:{value}"
        priority = self.calculate_priority(key)
        
        new_entry = MemoryEntry(
            input_text=entry_text,
            category=specialization,
            priority=priority
        )
        session.add(new_entry)
        session.commit()
        session.close()
        
        print(f"🧠 معرفة محفوظة: {entry_text} | الأولوية: {priority} | التخصص: {specialization}")

    def get_long_term_memory(self, limit: int = 20, category: str = None) -> list[str]:
        session = self.Session()
        query = session.query(MemoryEntry.input_text).order_by(desc(MemoryEntry.priority), desc(MemoryEntry.id))
        if category:
            query = query.filter(MemoryEntry.category == category)
        if limit:
            query = query.limit(limit)
        
        results = [row[0] for row in query.all()]
        session.close()
        return results

    def get_recent_knowledge(self, limit: int = 10) -> list[str]:
        session = self.Session()
        results = [row[0] for row in session.query(MemoryEntry.input_text)
                  .order_by(desc(MemoryEntry.id)).limit(limit).all()]
        session.close()
        return results


# ==================== التخصصات العلمية الذكية ====================
class SpecializedEnhancer:
    """مساعد متخصص يضيف لمسات حسب السياق"""
    
    def __init__(self):
        self.helpers = {
            'space': "delivering immense plasma thrust, angled auxiliary engines for perfect maneuverability, glowing energy trails",
            'engineering': "advanced cross-linked cooling pipes, reinforced titanium-alloy hull, precision-engineered components",
            'creativity': "In the silent void, a lone commander pilots destiny, stars weeping light upon the hull.",
            'history': "inspired by legendary 21st-century interstellar combat designs, echoing the golden age of space exploration",
            'nature': "surrounded by ethereal nebula glow, trailed by cosmic dust and ancient asteroid fragments",
            'philosophy': "A symbol of human ambition piercing the infinite cosmos, carrying dreams beyond gravity's grasp"
        }

    def enhance(self, prompt: str, specialization: str = "space") -> str:
        if specialization not in self.helpers:
            specialization = "space"
        
        addition = self.helpers[specialization]
        
        # نضيف حسب السياق عشان ما يتكررش
        if addition.lower() not in prompt.lower():
            return prompt + ", " + addition
        return prompt

    def get_random_enhancement(self) -> str:
        import random
        return random.choice(list(self.helpers.values()))