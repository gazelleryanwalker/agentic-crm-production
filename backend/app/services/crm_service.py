from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
from app.models.crm import Contact, Company, Deal, Activity, Task
from app.services.memory_service import UniversalMemoryService
from app.services.ai_service import AIIntelligenceService
import logging

logger = logging.getLogger(__name__)

class CRMService:
    """
    Comprehensive CRM service that provides autonomous customer relationship management
    with AI-driven insights and automation.
    """
    
    def __init__(self, db_session: Session, memory_service: UniversalMemoryService = None,
                 ai_service: AIIntelligenceService = None):
        self.db = db_session
        self.memory_service = memory_service
        self.ai_service = ai_service
    
    # Contact Management
    
    def create_contact(self, contact_data: Dict, user_id: int = 1) -> Contact:
        """Create new contact with automatic enrichment and deduplication"""
        
        # Check for existing contact by email
        existing_contact = self.db.query(Contact).filter(
            Contact.email == contact_data.get('email'),
            Contact.user_id == user_id
        ).first()
        
        if existing_contact:
            logger.info(f"Contact already exists: {contact_data.get('email')}")
            return existing_contact
        
        # Create company if provided and doesn't exist
        company_id = None
        if contact_data.get('company_name'):
            company = self.get_or_create_company(contact_data['company_name'], user_id)
            company_id = company.id
        
        contact = Contact(
            first_name=contact_data.get('first_name', ''),
            last_name=contact_data.get('last_name', ''),
            email=contact_data.get('email'),
            phone=contact_data.get('phone'),
            title=contact_data.get('title'),
            company_id=company_id,
            lead_status=contact_data.get('lead_status', 'new'),
            lead_score=self._calculate_initial_lead_score(contact_data),
            user_id=user_id
        )
        
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        
        # Store contact creation in memory
        if self.memory_service:
            self.memory_service.add_memory(
                content=f"Created contact: {contact.full_name} ({contact.email}) at {contact.company.name if contact.company else 'Unknown Company'}",
                memory_type='user',
                category='contact_management',
                tags=['contact', 'created', contact.lead_status],
                source_platform='crm_service',
                user_id=user_id
            )
        
        logger.info(f"Created new contact: {contact.full_name}")
        return contact
    
    def update_contact(self, contact_id: int, updates: Dict, user_id: int = 1) -> Optional[Contact]:
        """Update contact with intelligent field handling"""
        
        contact = self.db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.user_id == user_id
        ).first()
        
        if not contact:
            return None
        
        # Track changes for memory storage
        changes = []
        
        for field, value in updates.items():
            if hasattr(contact, field) and getattr(contact, field) != value:
                old_value = getattr(contact, field)
                setattr(contact, field, value)
                changes.append(f"{field}: {old_value} → {value}")
        
        # Update lead score if relevant fields changed
        if any(field in ['title', 'company_id', 'phone'] for field in updates.keys()):
            contact.lead_score = self._recalculate_lead_score(contact)
        
        contact.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Store changes in memory
        if changes and self.memory_service:
            self.memory_service.add_memory(
                content=f"Updated contact {contact.full_name}: {', '.join(changes)}",
                memory_type='user',
                category='contact_management',
                tags=['contact', 'updated'],
                source_platform='crm_service',
                user_id=user_id
            )
        
        logger.info(f"Updated contact: {contact.full_name}")
        return contact
    
    def search_contacts(self, query: str, filters: Dict = None, user_id: int = 1) -> List[Contact]:
        """Advanced contact search with AI-powered matching"""
        
        contacts_query = self.db.query(Contact).filter(Contact.user_id == user_id)
        
        # Apply text search
        if query:
            search_filter = or_(
                func.lower(Contact.first_name).contains(query.lower()),
                func.lower(Contact.last_name).contains(query.lower()),
                func.lower(Contact.email).contains(query.lower()),
                func.lower(Contact.title).contains(query.lower())
            )
            contacts_query = contacts_query.filter(search_filter)
        
        # Apply additional filters
        if filters:
            if filters.get('lead_status'):
                contacts_query = contacts_query.filter(Contact.lead_status == filters['lead_status'])
            if filters.get('company_id'):
                contacts_query = contacts_query.filter(Contact.company_id == filters['company_id'])
            if filters.get('min_lead_score'):
                contacts_query = contacts_query.filter(Contact.lead_score >= filters['min_lead_score'])
        
        contacts = contacts_query.order_by(desc(Contact.lead_score), desc(Contact.updated_at)).limit(50).all()
        
        # Use memory service for semantic search if available
        if self.memory_service and query:
            memory_results = self.memory_service.search_memories(
                query,
                category='contact_management',
                limit=10,
                user_id=user_id
            )
            
            # Enhance results with memory insights
            for contact in contacts[:5]:  # Top 5 contacts
                contact._memory_insights = [m for m in memory_results if contact.full_name.lower() in m['content'].lower()]
        
        return contacts
    
    # Company Management
    
    def get_or_create_company(self, company_name: str, user_id: int = 1, 
                             additional_data: Dict = None) -> Company:
        """Get existing company or create new one with enrichment"""
        
        existing_company = self.db.query(Company).filter(
            func.lower(Company.name) == company_name.lower(),
            Company.user_id == user_id
        ).first()
        
        if existing_company:
            return existing_company
        
        # Create new company
        company_data = additional_data or {}
        company = Company(
            name=company_name,
            domain=company_data.get('domain'),
            industry=company_data.get('industry'),
            size=company_data.get('size'),
            location=company_data.get('location'),
            annual_revenue=company_data.get('annual_revenue'),
            description=company_data.get('description'),
            user_id=user_id
        )
        
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        
        # Store company creation in memory
        if self.memory_service:
            self.memory_service.add_memory(
                content=f"Created company: {company.name} in {company.industry or 'Unknown'} industry",
                memory_type='user',
                category='company_management',
                tags=['company', 'created', company.industry.lower() if company.industry else 'unknown'],
                source_platform='crm_service',
                user_id=user_id
            )
        
        logger.info(f"Created new company: {company.name}")
        return company
    
    # Deal Management
    
    def create_deal(self, deal_data: Dict, user_id: int = 1) -> Deal:
        """Create new deal with AI-powered probability estimation"""
        
        deal = Deal(
            title=deal_data.get('title'),
            value=deal_data.get('value', 0),
            stage=deal_data.get('stage', 'prospecting'),
            probability=deal_data.get('probability') or self._estimate_deal_probability(deal_data),
            expected_close_date=self._parse_date(deal_data.get('expected_close_date')),
            contact_id=deal_data.get('contact_id'),
            company_id=deal_data.get('company_id'),
            description=deal_data.get('description'),
            user_id=user_id
        )
        
        self.db.add(deal)
        self.db.commit()
        self.db.refresh(deal)
        
        # Store deal creation in memory with context
        if self.memory_service:
            context = f"Created deal: {deal.title} (${deal.value:,}) for {deal.contact.full_name if deal.contact else 'Unknown Contact'}"
            if deal.company:
                context += f" at {deal.company.name}"
            
            self.memory_service.add_memory(
                content=context,
                memory_type='user',
                category='deal_management',
                tags=['deal', 'created', deal.stage.lower()],
                source_platform='crm_service',
                user_id=user_id
            )
        
        # Auto-create initial tasks for new deal
        self._create_initial_deal_tasks(deal, user_id)
        
        logger.info(f"Created new deal: {deal.title} (${deal.value:,})")
        return deal
    
    def update_deal_stage(self, deal_id: int, new_stage: str, user_id: int = 1) -> Optional[Deal]:
        """Update deal stage with automatic probability adjustment"""
        
        deal = self.db.query(Deal).filter(
            Deal.id == deal_id,
            Deal.user_id == user_id
        ).first()
        
        if not deal:
            return None
        
        old_stage = deal.stage
        deal.stage = new_stage
        deal.probability = self._get_stage_probability(new_stage)
        deal.updated_at = datetime.utcnow()
        
        # Set close date if deal is won/lost
        if new_stage.lower() in ['won', 'closed-won']:
            deal.status = 'won'
            deal.actual_close_date = datetime.utcnow()
        elif new_stage.lower() in ['lost', 'closed-lost']:
            deal.status = 'lost'
            deal.actual_close_date = datetime.utcnow()
        
        self.db.commit()
        
        # Store stage change in memory
        if self.memory_service:
            self.memory_service.add_memory(
                content=f"Deal stage updated: {deal.title} moved from {old_stage} to {new_stage} (${deal.value:,})",
                memory_type='user',
                category='deal_management',
                tags=['deal', 'stage_change', new_stage.lower()],
                source_platform='crm_service',
                user_id=user_id
            )
        
        # Create follow-up tasks based on new stage
        self._create_stage_specific_tasks(deal, new_stage, user_id)
        
        logger.info(f"Updated deal stage: {deal.title} → {new_stage}")
        return deal
    
    def get_pipeline_analytics(self, user_id: int = 1) -> Dict:
        """Get comprehensive pipeline analytics and insights"""
        
        # Basic pipeline metrics
        deals = self.db.query(Deal).filter(Deal.user_id == user_id).all()
        
        total_pipeline_value = sum(deal.value for deal in deals if deal.status == 'open')
        weighted_pipeline = sum(deal.value * (deal.probability / 100) for deal in deals if deal.status == 'open')
        
        # Stage distribution
        stage_stats = {}
        for deal in deals:
            if deal.status == 'open':
                stage_stats[deal.stage] = stage_stats.get(deal.stage, {'count': 0, 'value': 0})
                stage_stats[deal.stage]['count'] += 1
                stage_stats[deal.stage]['value'] += deal.value
        
        # Win/loss analysis
        won_deals = [d for d in deals if d.status == 'won']
        lost_deals = [d for d in deals if d.status == 'lost']
        
        win_rate = len(won_deals) / max(len(won_deals) + len(lost_deals), 1) * 100
        avg_deal_size = sum(d.value for d in won_deals) / max(len(won_deals), 1)
        
        # Time-based analysis
        current_month = datetime.utcnow().replace(day=1)
        monthly_won = sum(d.value for d in won_deals if d.actual_close_date and d.actual_close_date >= current_month)
        
        return {
            'total_pipeline_value': total_pipeline_value,
            'weighted_pipeline_value': weighted_pipeline,
            'open_deals_count': len([d for d in deals if d.status == 'open']),
            'stage_distribution': stage_stats,
            'win_rate': round(win_rate, 1),
            'average_deal_size': round(avg_deal_size, 2),
            'monthly_revenue': monthly_won,
            'deals_won_this_month': len([d for d in won_deals if d.actual_close_date and d.actual_close_date >= current_month]),
            'deals_lost_this_month': len([d for d in lost_deals if d.actual_close_date and d.actual_close_date >= current_month])
        }
    
    # Activity Management
    
    def log_activity(self, activity_data: Dict, user_id: int = 1) -> Activity:
        """Log customer activity with automatic insights"""
        
        activity = Activity(
            type=activity_data.get('type'),
            subject=activity_data.get('subject'),
            description=activity_data.get('description'),
            contact_id=activity_data.get('contact_id'),
            deal_id=activity_data.get('deal_id'),
            activity_date=activity_data.get('activity_date') or datetime.utcnow(),
            duration_minutes=activity_data.get('duration_minutes'),
            outcome=activity_data.get('outcome'),
            user_id=user_id
        )
        
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        
        # Update contact's last contact date
        if activity.contact:
            activity.contact.last_contact_date = activity.activity_date
            self.db.commit()
        
        # Analyze activity with AI if available
        if self.ai_service and activity.description:
            try:
                if activity.type == 'call' and len(activity.description) > 100:
                    # Analyze as conversation
                    analysis = self.ai_service.analyze_conversation(
                        activity.description,
                        contact_id=activity.contact_id,
                        deal_id=activity.deal_id,
                        user_id=user_id
                    )
                    activity.outcome = analysis.get('sentiment', {}).get('label', activity.outcome)
                    self.db.commit()
                    
            except Exception as e:
                logger.warning(f"Error analyzing activity: {e}")
        
        # Store activity in memory
        if self.memory_service:
            context = f"Logged {activity.type} activity: {activity.subject}"
            if activity.contact:
                context += f" with {activity.contact.full_name}"
            if activity.deal:
                context += f" regarding {activity.deal.title}"
            
            self.memory_service.add_memory(
                content=context,
                memory_type='user',
                category='activity_log',
                tags=['activity', activity.type, activity.outcome or 'unknown'],
                source_platform='crm_service',
                user_id=user_id
            )
        
        logger.info(f"Logged activity: {activity.type} - {activity.subject}")
        return activity
    
    # Task Management
    
    def create_task(self, task_data: Dict, user_id: int = 1) -> Task:
        """Create task with intelligent prioritization"""
        
        task = Task(
            title=task_data.get('title'),
            description=task_data.get('description'),
            priority=task_data.get('priority') or self._determine_task_priority(task_data),
            status='pending',
            due_date=self._parse_date(task_data.get('due_date')),
            contact_id=task_data.get('contact_id'),
            deal_id=task_data.get('deal_id'),
            assigned_to=task_data.get('assigned_to', user_id),
            created_by=user_id
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # Store task creation in memory
        if self.memory_service:
            context = f"Created task: {task.title} (Priority: {task.priority})"
            if task.contact:
                context += f" for {task.contact.full_name}"
            if task.deal:
                context += f" regarding {task.deal.title}"
            
            self.memory_service.add_memory(
                content=context,
                memory_type='user',
                category='task_management',
                tags=['task', 'created', task.priority],
                source_platform='crm_service',
                user_id=user_id
            )
        
        logger.info(f"Created task: {task.title}")
        return task
    
    def get_overdue_tasks(self, user_id: int = 1) -> List[Task]:
        """Get overdue tasks with context"""
        
        now = datetime.utcnow()
        overdue_tasks = self.db.query(Task).filter(
            Task.assigned_to == user_id,
            Task.status.in_(['pending', 'in_progress']),
            Task.due_date < now
        ).order_by(Task.due_date).all()
        
        return overdue_tasks
    
    def get_upcoming_tasks(self, days_ahead: int = 7, user_id: int = 1) -> List[Task]:
        """Get upcoming tasks within specified timeframe"""
        
        now = datetime.utcnow()
        future_date = now + timedelta(days=days_ahead)
        
        upcoming_tasks = self.db.query(Task).filter(
            Task.assigned_to == user_id,
            Task.status.in_(['pending', 'in_progress']),
            Task.due_date.between(now, future_date)
        ).order_by(Task.due_date, Task.priority).all()
        
        return upcoming_tasks
    
    # Utility Methods
    
    def _calculate_initial_lead_score(self, contact_data: Dict) -> int:
        """Calculate initial lead score based on available data"""
        
        score = 0
        
        # Title-based scoring
        title = (contact_data.get('title') or '').lower()
        if any(word in title for word in ['ceo', 'president', 'founder', 'owner']):
            score += 30
        elif any(word in title for word in ['director', 'vp', 'vice president', 'manager']):
            score += 20
        elif any(word in title for word in ['coordinator', 'specialist', 'analyst']):
            score += 10
        
        # Company-based scoring
        if contact_data.get('company_name'):
            score += 15
        
        # Contact information completeness
        if contact_data.get('phone'):
            score += 10
        if contact_data.get('title'):
            score += 5
        
        return min(score, 100)  # Cap at 100
    
    def _recalculate_lead_score(self, contact: Contact) -> int:
        """Recalculate lead score based on current contact data and activities"""
        
        base_score = self._calculate_initial_lead_score({
            'title': contact.title,
            'company_name': contact.company.name if contact.company else None,
            'phone': contact.phone
        })
        
        # Activity-based boost
        activity_count = len(contact.activities)
        activity_boost = min(activity_count * 5, 25)  # Max 25 points from activities
        
        # Deal-based boost
        deal_boost = 0
        if contact.deals:
            open_deals = [d for d in contact.deals if d.status == 'open']
            deal_boost = min(len(open_deals) * 15, 30)  # Max 30 points from deals
        
        # Recent activity boost
        if contact.last_contact_date:
            days_since_contact = (datetime.utcnow() - contact.last_contact_date).days
            if days_since_contact <= 7:
                recent_boost = 10
            elif days_since_contact <= 30:
                recent_boost = 5
            else:
                recent_boost = 0
        else:
            recent_boost = 0
        
        total_score = base_score + activity_boost + deal_boost + recent_boost
        return min(total_score, 100)  # Cap at 100
    
    def _estimate_deal_probability(self, deal_data: Dict) -> int:
        """Estimate deal probability based on stage and other factors"""
        
        stage = deal_data.get('stage', 'prospecting').lower()
        
        stage_probabilities = {
            'prospecting': 10,
            'qualification': 20,
            'needs analysis': 30,
            'proposal': 50,
            'negotiation': 70,
            'closing': 90,
            'won': 100,
            'lost': 0
        }
        
        base_probability = stage_probabilities.get(stage, 25)
        
        # Adjust based on deal value (higher value deals might be more complex)
        value = deal_data.get('value', 0)
        if value > 100000:
            base_probability = max(base_probability - 10, 0)
        elif value > 50000:
            base_probability = max(base_probability - 5, 0)
        
        return base_probability
    
    def _get_stage_probability(self, stage: str) -> int:
        """Get standard probability for a deal stage"""
        
        stage_probabilities = {
            'prospecting': 10,
            'qualification': 20,
            'needs analysis': 30,
            'proposal': 50,
            'negotiation': 70,
            'closing': 90,
            'won': 100,
            'closed-won': 100,
            'lost': 0,
            'closed-lost': 0
        }
        
        return stage_probabilities.get(stage.lower(), 25)
    
    def _create_initial_deal_tasks(self, deal: Deal, user_id: int):
        """Create initial tasks for a new deal"""
        
        initial_tasks = [
            {
                'title': f'Research {deal.company.name if deal.company else "prospect"}',
                'description': 'Research company background, needs, and decision makers',
                'priority': 'medium',
                'due_date': datetime.utcnow() + timedelta(days=2)
            },
            {
                'title': f'Initial outreach to {deal.contact.full_name if deal.contact else "contact"}',
                'description': 'Make initial contact to understand requirements',
                'priority': 'high',
                'due_date': datetime.utcnow() + timedelta(days=1)
            }
        ]
        
        for task_data in initial_tasks:
            task_data.update({
                'contact_id': deal.contact_id,
                'deal_id': deal.id,
                'assigned_to': user_id
            })
            self.create_task(task_data, user_id)
    
    def _create_stage_specific_tasks(self, deal: Deal, stage: str, user_id: int):
        """Create tasks specific to deal stage"""
        
        stage_tasks = {
            'proposal': [
                {
                    'title': f'Prepare proposal for {deal.title}',
                    'description': 'Create detailed proposal based on requirements',
                    'priority': 'high',
                    'due_date': datetime.utcnow() + timedelta(days=3)
                }
            ],
            'negotiation': [
                {
                    'title': f'Follow up on proposal for {deal.title}',
                    'description': 'Follow up on proposal and address any concerns',
                    'priority': 'high',
                    'due_date': datetime.utcnow() + timedelta(days=1)
                }
            ],
            'closing': [
                {
                    'title': f'Prepare contract for {deal.title}',
                    'description': 'Prepare final contract and closing documents',
                    'priority': 'urgent',
                    'due_date': datetime.utcnow() + timedelta(days=1)
                }
            ]
        }
        
        tasks_to_create = stage_tasks.get(stage.lower(), [])
        
        for task_data in tasks_to_create:
            task_data.update({
                'contact_id': deal.contact_id,
                'deal_id': deal.id,
                'assigned_to': user_id
            })
            self.create_task(task_data, user_id)
    
    def _determine_task_priority(self, task_data: Dict) -> str:
        """Determine task priority based on context"""
        
        # Check for urgent keywords
        title = (task_data.get('title') or '').lower()
        description = (task_data.get('description') or '').lower()
        content = title + ' ' + description
        
        if any(word in content for word in ['urgent', 'asap', 'critical', 'emergency']):
            return 'urgent'
        
        # Check due date proximity
        due_date = self._parse_date(task_data.get('due_date'))
        if due_date:
            days_until_due = (due_date - datetime.utcnow()).days
            if days_until_due <= 1:
                return 'urgent'
            elif days_until_due <= 3:
                return 'high'
        
        # Check if related to high-value deal
        deal_id = task_data.get('deal_id')
        if deal_id:
            deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
            if deal and deal.value > 50000:
                return 'high'
        
        return 'medium'
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        
        if not date_str:
            return None
        
        try:
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_str
        except:
            return None
