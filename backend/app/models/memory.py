from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from app import db

class Memory(db.Model):
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    memory_type = Column(String(50), nullable=False)  # user, session, agent
    category = Column(String(100))
    tags = Column(JSON)
    source_platform = Column(String(100))
    embedding_vector = Column(JSON)  # Store as JSON for simplicity
    relevance_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_memory_type_user', 'memory_type', 'user_id'),
        Index('idx_category_user', 'category', 'user_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_relevance_score', 'relevance_score'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type,
            'category': self.category,
            'tags': self.tags,
            'source_platform': self.source_platform,
            'relevance_score': self.relevance_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }
    
    @classmethod
    def create_memory(cls, content, memory_type, user_id, category=None, tags=None, source_platform=None):
        """Factory method to create a new memory with proper validation"""
        memory = cls(
            content=content,
            memory_type=memory_type,
            user_id=user_id,
            category=category,
            tags=tags or [],
            source_platform=source_platform
        )
        return memory
