from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.crm import Contact, Company, Deal, Activity, Task
from app.models.memory import Memory
from app.services.crm_service import CRMService
from app.services.memory_service import UniversalMemoryService
from app.services.ai_service import AIIntelligenceService
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

def get_services():
    """Get initialized services"""
    memory_service = UniversalMemoryService(db.session)
    ai_service = AIIntelligenceService(db.session, memory_service)
    crm_service = CRMService(db.session, memory_service, ai_service)
    return crm_service, memory_service, ai_service

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    
    try:
        user_id = get_jwt_identity()
        
        # Get date ranges
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Contact statistics
        total_contacts = db.session.query(Contact).filter(Contact.user_id == user_id).count()
        new_contacts_week = db.session.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.created_at >= week_ago
        ).count()
        
        # Deal statistics
        open_deals = db.session.query(Deal).filter(
            Deal.user_id == user_id,
            Deal.status == 'open'
        ).all()
        
        total_pipeline_value = sum(deal.value for deal in open_deals)
        weighted_pipeline = sum(deal.value * (deal.probability / 100) for deal in open_deals)
        
        won_deals_month = db.session.query(Deal).filter(
            Deal.user_id == user_id,
            Deal.status == 'won',
            Deal.actual_close_date >= month_ago
        ).all()
        
        monthly_revenue = sum(deal.value for deal in won_deals_month)
        
        # Activity statistics
        activities_week = db.session.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.activity_date >= week_ago
        ).count()
        
        # Task statistics
        overdue_tasks = db.session.query(Task).filter(
            Task.assigned_to == user_id,
            Task.status.in_(['pending', 'in_progress']),
            Task.due_date < now
        ).count()
        
        upcoming_tasks = db.session.query(Task).filter(
            Task.assigned_to == user_id,
            Task.status.in_(['pending', 'in_progress']),
            Task.due_date.between(now, now + timedelta(days=7))
        ).count()
        
        # Memory statistics
        memory_service = get_memory_service()
        memory_stats = memory_service.get_memory_stats(user_id)
        
        # Calculate percentage changes (mock data for now)
        contacts_change = 15.2  # Would calculate from historical data
        pipeline_change = 8.7
        deals_change = 12.3
        
        return jsonify({
            'total_contacts': total_contacts,
            'new_contacts_week': new_contacts_week,
            'contacts_change': contacts_change,
            'pipeline_value': total_pipeline_value,
            'weighted_pipeline': weighted_pipeline,
            'pipeline_change': pipeline_change,
            'deals_won': len(won_deals_month),
            'deals_change': deals_change,
            'monthly_revenue': monthly_revenue,
            'activities_week': activities_week,
            'overdue_tasks': overdue_tasks,
            'upcoming_tasks': upcoming_tasks,
            'ai_insights': memory_stats.get('total_memories', 0),
            'insights_today': memory_stats.get('recent_memories_7d', 0)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({'error': 'Failed to fetch dashboard statistics'}), 500

@dashboard_bp.route('/recent-activities', methods=['GET'])
@jwt_required()
def get_recent_activities():
    """Get recent activities for dashboard"""
    
    try:
        user_id = get_jwt_identity()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        activities = db.session.query(Activity).filter(
            Activity.user_id == user_id
        ).order_by(desc(Activity.activity_date)).limit(limit).all()
        
        return jsonify({
            'activities': [activity.to_dict() for activity in activities]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")
        return jsonify({'error': 'Failed to fetch recent activities'}), 500

@dashboard_bp.route('/upcoming-tasks', methods=['GET'])
@jwt_required()
def get_upcoming_tasks():
    """Get upcoming tasks for dashboard"""
    
    try:
        user_id = get_jwt_identity()
        days_ahead = int(request.args.get('days_ahead', 7))
        
        crm_service, _, _ = get_services()
        tasks = crm_service.get_upcoming_tasks(days_ahead, user_id)
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching upcoming tasks: {e}")
        return jsonify({'error': 'Failed to fetch upcoming tasks'}), 500

@dashboard_bp.route('/pipeline-overview', methods=['GET'])
@jwt_required()
def get_pipeline_overview():
    """Get pipeline overview for dashboard"""
    
    try:
        user_id = get_jwt_identity()
        
        crm_service, _, _ = get_services()
        pipeline_analytics = crm_service.get_pipeline_analytics(user_id)
        
        # Get deals by stage for pipeline visualization
        deals_by_stage = db.session.query(
            Deal.stage,
            func.count(Deal.id).label('count'),
            func.sum(Deal.value).label('total_value')
        ).filter(
            Deal.user_id == user_id,
            Deal.status == 'open'
        ).group_by(Deal.stage).all()
        
        stage_data = []
        for stage, count, total_value in deals_by_stage:
            stage_data.append({
                'stage': stage,
                'count': count,
                'total_value': float(total_value or 0)
            })
        
        pipeline_analytics['stage_breakdown'] = stage_data
        
        return jsonify({
            'pipeline': pipeline_analytics
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching pipeline overview: {e}")
        return jsonify({'error': 'Failed to fetch pipeline overview'}), 500

@dashboard_bp.route('/top-deals', methods=['GET'])
@jwt_required()
def get_top_deals():
    """Get top deals by value for dashboard"""
    
    try:
        user_id = get_jwt_identity()
        limit = min(int(request.args.get('limit', 5)), 20)
        
        top_deals = db.session.query(Deal).filter(
            Deal.user_id == user_id,
            Deal.status == 'open'
        ).order_by(desc(Deal.value)).limit(limit).all()
        
        return jsonify({
            'deals': [deal.to_dict() for deal in top_deals]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching top deals: {e}")
        return jsonify({'error': 'Failed to fetch top deals'}), 500

@dashboard_bp.route('/hot-leads', methods=['GET'])
@jwt_required()
def get_hot_leads():
    """Get hot leads (high lead score contacts) for dashboard"""
    
    try:
        user_id = get_jwt_identity()
        limit = min(int(request.args.get('limit', 5)), 20)
        min_score = int(request.args.get('min_score', 70))
        
        hot_leads = db.session.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.lead_score >= min_score
        ).order_by(desc(Contact.lead_score), desc(Contact.updated_at)).limit(limit).all()
        
        return jsonify({
            'leads': [contact.to_dict() for contact in hot_leads]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching hot leads: {e}")
        return jsonify({'error': 'Failed to fetch hot leads'}), 500

@dashboard_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_ai_insights():
    """Get AI-generated insights for dashboard"""
    
    try:
        user_id = get_jwt_identity()
        limit = min(int(request.args.get('limit', 5)), 20)
        
        # Get recent AI insights from memory
        memory_service = get_memory_service()
        insights = memory_service.search_memories(
            query="insight recommendation analysis",
            memory_type="agent",
            category="insights",
            limit=limit,
            user_id=user_id
        )
        
        # If no insights found, generate some basic ones
        if not insights:
            insights = generate_basic_insights(user_id)
        
        return jsonify({
            'insights': insights
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching AI insights: {e}")
        return jsonify({'error': 'Failed to fetch AI insights'}), 500

@dashboard_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for dashboard"""
    
    try:
        user_id = get_jwt_identity()
        
        notifications = []
        
        # Overdue tasks notification
        overdue_count = db.session.query(Task).filter(
            Task.assigned_to == user_id,
            Task.status.in_(['pending', 'in_progress']),
            Task.due_date < datetime.utcnow()
        ).count()
        
        if overdue_count > 0:
            notifications.append({
                'type': 'warning',
                'title': 'Overdue Tasks',
                'message': f'You have {overdue_count} overdue task{"s" if overdue_count != 1 else ""}',
                'action_url': '/tasks?overdue=true'
            })
        
        # Stale deals notification
        week_ago = datetime.utcnow() - timedelta(days=7)
        stale_deals = db.session.query(Deal).filter(
            Deal.user_id == user_id,
            Deal.status == 'open',
            Deal.updated_at < week_ago
        ).count()
        
        if stale_deals > 0:
            notifications.append({
                'type': 'info',
                'title': 'Stale Deals',
                'message': f'{stale_deals} deal{"s" if stale_deals != 1 else ""} haven\'t been updated in a week',
                'action_url': '/deals?stale=true'
            })
        
        # High-value deals closing soon
        next_week = datetime.utcnow() + timedelta(days=7)
        closing_soon = db.session.query(Deal).filter(
            Deal.user_id == user_id,
            Deal.status == 'open',
            Deal.expected_close_date <= next_week,
            Deal.value >= 10000
        ).count()
        
        if closing_soon > 0:
            notifications.append({
                'type': 'success',
                'title': 'Deals Closing Soon',
                'message': f'{closing_soon} high-value deal{"s" if closing_soon != 1 else ""} closing within a week',
                'action_url': '/deals?closing_soon=true'
            })
        
        return jsonify({
            'notifications': notifications
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        return jsonify({'error': 'Failed to fetch notifications'}), 500

def get_memory_service():
    """Get memory service instance"""
    return UniversalMemoryService(db.session)

async def generate_basic_insights(user_id: int) -> list:
    """Generate basic insights when AI insights are not available"""
    
    insights = []
    
    try:
        # Contact growth insight
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_contacts = db.session.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.created_at >= week_ago
        ).count()
        
        if new_contacts > 0:
            insights.append({
                'content': f'Added {new_contacts} new contacts this week - great momentum!',
                'category': 'growth',
                'similarity_score': 0.9
            })
        
        # Deal velocity insight
        open_deals = db.session.query(Deal).filter(
            Deal.user_id == user_id,
            Deal.status == 'open'
        ).count()
        
        if open_deals > 5:
            insights.append({
                'content': f'You have {open_deals} active deals. Consider prioritizing the highest-value opportunities.',
                'category': 'strategy',
                'similarity_score': 0.8
            })
        
        # Activity insight
        activities_week = db.session.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.activity_date >= week_ago
        ).count()
        
        if activities_week < 5:
            insights.append({
                'content': 'Low activity this week. Consider scheduling more customer touchpoints.',
                'category': 'engagement',
                'similarity_score': 0.7
            })
        
    except Exception as e:
        logger.error(f"Error generating basic insights: {e}")
    
    return insights
