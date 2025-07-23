from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app import db

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    title = Column(String(200))
    company_id = Column(Integer, ForeignKey('companies.id'))
    lead_status = Column(String(50), default='new')
    lead_score = Column(Integer, default=0)
    last_contact_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="contacts")
    deals = relationship("Deal", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")
    tasks = relationship("Task", back_populates="contact")
    user = relationship("User", back_populates="contacts")
    
    # Indexes
    __table_args__ = (
        Index('idx_contact_email', 'email'),
        Index('idx_contact_company', 'company_id'),
        Index('idx_contact_user', 'user_id'),
        Index('idx_lead_status', 'lead_status'),
    )
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'title': self.title,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'lead_status': self.lead_status,
            'lead_score': self.lead_score,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    domain = Column(String(255))
    industry = Column(String(100))
    size = Column(String(50))
    location = Column(String(200))
    annual_revenue = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    contacts = relationship("Contact", back_populates="company")
    deals = relationship("Deal", back_populates="company")
    user = relationship("User", back_populates="companies")
    
    # Indexes
    __table_args__ = (
        Index('idx_company_name', 'name'),
        Index('idx_company_domain', 'domain'),
        Index('idx_company_user', 'user_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'industry': self.industry,
            'size': self.size,
            'location': self.location,
            'annual_revenue': self.annual_revenue,
            'description': self.description,
            'contact_count': len(self.contacts),
            'deal_count': len(self.deals),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Deal(db.Model):
    __tablename__ = 'deals'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    value = Column(Float, nullable=False)
    stage = Column(String(100), nullable=False)
    probability = Column(Integer, default=0)
    expected_close_date = Column(DateTime)
    actual_close_date = Column(DateTime)
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    company_id = Column(Integer, ForeignKey('companies.id'))
    status = Column(String(50), default='open')  # open, won, lost
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="deals")
    company = relationship("Company", back_populates="deals")
    activities = relationship("Activity", back_populates="deal")
    tasks = relationship("Task", back_populates="deal")
    user = relationship("User", back_populates="deals")
    
    # Indexes
    __table_args__ = (
        Index('idx_deal_stage', 'stage'),
        Index('idx_deal_status', 'status'),
        Index('idx_deal_contact', 'contact_id'),
        Index('idx_deal_company', 'company_id'),
        Index('idx_deal_user', 'user_id'),
        Index('idx_deal_close_date', 'expected_close_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'value': self.value,
            'stage': self.stage,
            'probability': self.probability,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'actual_close_date': self.actual_close_date.isoformat() if self.actual_close_date else None,
            'contact_id': self.contact_id,
            'contact_name': self.contact.full_name if self.contact else None,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # email, call, meeting, note
    subject = Column(String(200))
    description = Column(Text)
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    deal_id = Column(Integer, ForeignKey('deals.id'))
    activity_date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer)
    outcome = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="activities")
    deal = relationship("Deal", back_populates="activities")
    user = relationship("User", back_populates="activities")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_type', 'type'),
        Index('idx_activity_contact', 'contact_id'),
        Index('idx_activity_deal', 'deal_id'),
        Index('idx_activity_date', 'activity_date'),
        Index('idx_activity_user', 'user_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'subject': self.subject,
            'description': self.description,
            'contact_id': self.contact_id,
            'contact_name': self.contact.full_name if self.contact else None,
            'deal_id': self.deal_id,
            'deal_title': self.deal.title if self.deal else None,
            'activity_date': self.activity_date.isoformat() if self.activity_date else None,
            'duration_minutes': self.duration_minutes,
            'outcome': self.outcome,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    status = Column(String(20), default='pending')  # pending, in_progress, completed, cancelled
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    deal_id = Column(Integer, ForeignKey('deals.id'))
    assigned_to = Column(Integer, ForeignKey('users.id'))
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact", back_populates="tasks")
    deal = relationship("Deal", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_task_status', 'status'),
        Index('idx_task_priority', 'priority'),
        Index('idx_task_due_date', 'due_date'),
        Index('idx_task_assigned', 'assigned_to'),
        Index('idx_task_contact', 'contact_id'),
        Index('idx_task_deal', 'deal_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'contact_id': self.contact_id,
            'contact_name': self.contact.full_name if self.contact else None,
            'deal_id': self.deal_id,
            'deal_title': self.deal.title if self.deal else None,
            'assigned_to': self.assigned_to,
            'assignee_name': self.assignee.username if self.assignee else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
