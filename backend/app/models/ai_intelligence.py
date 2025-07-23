from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from app import db

class ConversationAnalysis(db.Model):
    __tablename__ = 'conversation_analyses'
    
    id = Column(Integer, primary_key=True)
    transcript = Column(Text, nullable=False)
    participants = Column(JSON)  # List of participant names/emails
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))  # positive, neutral, negative
    topics = Column(JSON)  # List of main topics discussed
    action_items = Column(JSON)  # List of action items identified
    next_steps = Column(JSON)  # Suggested next steps
    deal_signals = Column(JSON)  # Buying signals or concerns
    talk_time_ratio = Column(JSON)  # Speaking time distribution
    key_insights = Column(JSON)  # Important insights
    urgency_level = Column(String(20))  # low, medium, high
    follow_up_required = Column(String(10))  # true/false as string
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    deal_id = Column(Integer, ForeignKey('deals.id'))
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    contact = relationship("Contact")
    deal = relationship("Deal")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_contact', 'contact_id'),
        Index('idx_analysis_deal', 'deal_id'),
        Index('idx_analysis_date', 'analyzed_at'),
        Index('idx_analysis_sentiment', 'sentiment_label'),
        Index('idx_analysis_urgency', 'urgency_level'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'participants': self.participants,
            'sentiment': {
                'score': self.sentiment_score,
                'label': self.sentiment_label
            },
            'topics': self.topics,
            'action_items': self.action_items,
            'next_steps': self.next_steps,
            'deal_signals': self.deal_signals,
            'talk_time_ratio': self.talk_time_ratio,
            'key_insights': self.key_insights,
            'urgency_level': self.urgency_level,
            'follow_up_required': self.follow_up_required == 'true',
            'contact_id': self.contact_id,
            'deal_id': self.deal_id,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }

class EmailAnalysis(db.Model):
    __tablename__ = 'email_analyses'
    
    id = Column(Integer, primary_key=True)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    sender = Column(String(255))
    recipient = Column(String(255))
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))  # positive, neutral, negative
    intent = Column(String(100))  # meeting_request, pricing_inquiry, support_request, etc.
    urgency = Column(String(20))  # low, medium, high, urgent
    priority_score = Column(Integer)  # 1-5 scale
    key_points = Column(JSON)  # Main points from the email
    suggested_response = Column(Text)  # AI-generated response suggestion
    action_required = Column(String(10))  # true/false as string
    follow_up_date = Column(DateTime)  # Suggested follow-up date
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    deal_id = Column(Integer, ForeignKey('deals.id'))
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    contact = relationship("Contact")
    deal = relationship("Deal")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_email_contact', 'contact_id'),
        Index('idx_email_deal', 'deal_id'),
        Index('idx_email_date', 'analyzed_at'),
        Index('idx_email_sentiment', 'sentiment_label'),
        Index('idx_email_urgency', 'urgency'),
        Index('idx_email_priority', 'priority_score'),
        Index('idx_email_sender', 'sender'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'sender': self.sender,
            'recipient': self.recipient,
            'sentiment': {
                'score': self.sentiment_score,
                'label': self.sentiment_label
            },
            'intent': self.intent,
            'urgency': self.urgency,
            'priority_score': self.priority_score,
            'key_points': self.key_points,
            'suggested_response': self.suggested_response,
            'action_required': self.action_required == 'true',
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'contact_id': self.contact_id,
            'deal_id': self.deal_id,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }
