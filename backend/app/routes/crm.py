from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.crm import Contact, Company, Deal, Activity, Task
from app.services.crm_service import CRMService
from app.services.memory_service import UniversalMemoryService
from app.services.ai_service import AIIntelligenceService
from app.utils.validators import (
    validate_contact_data, validate_company_data, validate_deal_data,
    validate_task_data, validate_activity_data, validate_pagination_params,
    format_validation_errors, sanitize_input_data
)
from app.utils.helpers import create_pagination_info
import logging

logger = logging.getLogger(__name__)

crm_bp = Blueprint('crm', __name__)

def get_services():
    """Get initialized CRM services"""
    memory_service = UniversalMemoryService(db.session)
    ai_service = AIIntelligenceService(db.session, memory_service)
    crm_service = CRMService(db.session, memory_service, ai_service)
    return crm_service, memory_service, ai_service

# Contact Management Routes

@crm_bp.route('/contacts', methods=['GET'])
@jwt_required()
def get_contacts():
    """Get contacts with pagination and filtering"""
    
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        page = request.args.get('page', 1)
        per_page = request.args.get('per_page', 20)
        
        pagination_result = validate_pagination_params(page, per_page)
        if pagination_result['errors']:
            return jsonify({'error': 'Invalid pagination parameters'}), 400
        
        page = pagination_result['params']['page']
        per_page = pagination_result['params']['per_page']
        
        # Get filters
        search = request.args.get('search', '').strip()
        lead_status = request.args.get('lead_status')
        company_id = request.args.get('company_id')
        
        # Build query
        query = db.session.query(Contact).filter(Contact.user_id == user_id)
        
        if search:
            from sqlalchemy import or_, func
            search_filter = or_(
                func.lower(Contact.first_name).contains(search.lower()),
                func.lower(Contact.last_name).contains(search.lower()),
                func.lower(Contact.email).contains(search.lower())
            )
            query = query.filter(search_filter)
        
        if lead_status:
            query = query.filter(Contact.lead_status == lead_status)
        
        if company_id:
            query = query.filter(Contact.company_id == company_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        contacts = query.order_by(Contact.lead_score.desc(), Contact.updated_at.desc())\
                       .offset((page - 1) * per_page)\
                       .limit(per_page)\
                       .all()
        
        # Create pagination info
        pagination_info = create_pagination_info(page, per_page, total_count)
        
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts],
            'pagination': pagination_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}")
        return jsonify({'error': 'Failed to fetch contacts'}), 500

@crm_bp.route('/contacts', methods=['POST'])
@jwt_required()
def create_contact():
    """Create a new contact"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate contact data
        validation_errors = validate_contact_data(data)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize input data
        allowed_fields = ['first_name', 'last_name', 'email', 'phone', 'title', 
                         'company_name', 'lead_status', 'lead_score']
        sanitized_data = sanitize_input_data(data, allowed_fields)
        
        # Create contact using CRM service
        crm_service, _, _ = get_services()
        contact = crm_service.create_contact(sanitized_data, user_id)
        
        logger.info(f"Created contact: {contact.full_name}")
        
        return jsonify({
            'message': 'Contact created successfully',
            'contact': contact.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create contact'}), 500

@crm_bp.route('/contacts/<int:contact_id>', methods=['GET'])
@jwt_required()
def get_contact(contact_id):
    """Get specific contact with related data"""
    
    try:
        user_id = get_jwt_identity()
        
        contact = db.session.query(Contact).filter(
            Contact.id == contact_id,
            Contact.user_id == user_id
        ).first()
        
        if not contact:
            return jsonify({'error': 'Contact not found'}), 404
        
        # Get related data
        recent_activities = db.session.query(Activity).filter(
            Activity.contact_id == contact_id
        ).order_by(Activity.activity_date.desc()).limit(10).all()
        
        open_deals = db.session.query(Deal).filter(
            Deal.contact_id == contact_id,
            Deal.status == 'open'
        ).all()
        
        pending_tasks = db.session.query(Task).filter(
            Task.contact_id == contact_id,
            Task.status.in_(['pending', 'in_progress'])
        ).order_by(Task.due_date).all()
        
        contact_data = contact.to_dict()
        contact_data['recent_activities'] = [activity.to_dict() for activity in recent_activities]
        contact_data['open_deals'] = [deal.to_dict() for deal in open_deals]
        contact_data['pending_tasks'] = [task.to_dict() for task in pending_tasks]
        
        return jsonify({'contact': contact_data}), 200
        
    except Exception as e:
        logger.error(f"Error fetching contact: {e}")
        return jsonify({'error': 'Failed to fetch contact'}), 500

@crm_bp.route('/contacts/<int:contact_id>', methods=['PUT'])
@jwt_required()
def update_contact(contact_id):
    """Update contact"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate contact data
        validation_errors = validate_contact_data(data)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize input data
        allowed_fields = ['first_name', 'last_name', 'email', 'phone', 'title', 
                         'lead_status', 'lead_score']
        sanitized_data = sanitize_input_data(data, allowed_fields)
        
        # Update contact using CRM service
        crm_service, _, _ = get_services()
        contact = crm_service.update_contact(contact_id, sanitized_data, user_id)
        
        if not contact:
            return jsonify({'error': 'Contact not found'}), 404
        
        logger.info(f"Updated contact: {contact.full_name}")
        
        return jsonify({
            'message': 'Contact updated successfully',
            'contact': contact.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating contact: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update contact'}), 500

# Deal Management Routes

@crm_bp.route('/deals', methods=['GET'])
@jwt_required()
def get_deals():
    """Get deals with pagination and filtering"""
    
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        page = request.args.get('page', 1)
        per_page = request.args.get('per_page', 20)
        
        pagination_result = validate_pagination_params(page, per_page)
        if pagination_result['errors']:
            return jsonify({'error': 'Invalid pagination parameters'}), 400
        
        page = pagination_result['params']['page']
        per_page = pagination_result['params']['per_page']
        
        # Get filters
        stage = request.args.get('stage')
        status = request.args.get('status', 'open')
        
        # Build query
        query = db.session.query(Deal).filter(Deal.user_id == user_id)
        
        if stage:
            query = query.filter(Deal.stage == stage)
        
        if status:
            query = query.filter(Deal.status == status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        deals = query.order_by(Deal.value.desc(), Deal.updated_at.desc())\
                    .offset((page - 1) * per_page)\
                    .limit(per_page)\
                    .all()
        
        # Create pagination info
        pagination_info = create_pagination_info(page, per_page, total_count)
        
        return jsonify({
            'deals': [deal.to_dict() for deal in deals],
            'pagination': pagination_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        return jsonify({'error': 'Failed to fetch deals'}), 500

@crm_bp.route('/deals', methods=['POST'])
@jwt_required()
def create_deal():
    """Create a new deal"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate deal data
        validation_errors = validate_deal_data(data)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize input data
        allowed_fields = ['title', 'value', 'stage', 'probability', 'expected_close_date',
                         'contact_id', 'company_id', 'description']
        sanitized_data = sanitize_input_data(data, allowed_fields)
        
        # Create deal using CRM service
        crm_service, _, _ = get_services()
        deal = crm_service.create_deal(sanitized_data, user_id)
        
        logger.info(f"Created deal: {deal.title}")
        
        return jsonify({
            'message': 'Deal created successfully',
            'deal': deal.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create deal'}), 500

@crm_bp.route('/deals/<int:deal_id>/stage', methods=['PUT'])
@jwt_required()
def update_deal_stage(deal_id):
    """Update deal stage"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'stage' not in data:
            return jsonify({'error': 'Stage is required'}), 400
        
        new_stage = data['stage']
        
        # Update deal stage using CRM service
        crm_service, _, _ = get_services()
        deal = crm_service.update_deal_stage(deal_id, new_stage, user_id)
        
        if not deal:
            return jsonify({'error': 'Deal not found'}), 404
        
        logger.info(f"Updated deal stage: {deal.title} → {new_stage}")
        
        return jsonify({
            'message': 'Deal stage updated successfully',
            'deal': deal.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating deal stage: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update deal stage'}), 500

# Activity Management Routes

@crm_bp.route('/activities', methods=['POST'])
@jwt_required()
def log_activity():
    """Log a new activity"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate activity data
        validation_errors = validate_activity_data(data)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize input data
        allowed_fields = ['type', 'subject', 'description', 'contact_id', 'deal_id',
                         'activity_date', 'duration_minutes', 'outcome']
        sanitized_data = sanitize_input_data(data, allowed_fields)
        
        # Log activity using CRM service
        crm_service, _, _ = get_services()
        activity = crm_service.log_activity(sanitized_data, user_id)
        
        logger.info(f"Logged activity: {activity.type} - {activity.subject}")
        
        return jsonify({
            'message': 'Activity logged successfully',
            'activity': activity.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to log activity'}), 500

# Task Management Routes

@crm_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get tasks with filtering"""
    
    try:
        user_id = get_jwt_identity()
        
        # Get filters
        status = request.args.get('status')
        priority = request.args.get('priority')
        overdue = request.args.get('overdue', '').lower() == 'true'
        upcoming = request.args.get('upcoming', '').lower() == 'true'
        
        # Get tasks using CRM service
        crm_service, _, _ = get_services()
        
        if overdue:
            tasks = crm_service.get_overdue_tasks(user_id)
        elif upcoming:
            days_ahead = int(request.args.get('days_ahead', 7))
            tasks = crm_service.get_upcoming_tasks(days_ahead, user_id)
        else:
            # Build query
            query = db.session.query(Task).filter(Task.assigned_to == user_id)
            
            if status:
                query = query.filter(Task.status == status)
            
            if priority:
                query = query.filter(Task.priority == priority)
            
            tasks = query.order_by(Task.due_date, Task.priority).limit(50).all()
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return jsonify({'error': 'Failed to fetch tasks'}), 500

@crm_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """Create a new task"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate task data
        validation_errors = validate_task_data(data)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize input data
        allowed_fields = ['title', 'description', 'priority', 'due_date',
                         'contact_id', 'deal_id', 'assigned_to']
        sanitized_data = sanitize_input_data(data, allowed_fields)
        
        # Create task using CRM service
        crm_service, _, _ = get_services()
        task = crm_service.create_task(sanitized_data, user_id)
        
        logger.info(f"Created task: {task.title}")
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create task'}), 500

@crm_bp.route('/tasks/<int:task_id>/complete', methods=['PUT'])
@jwt_required()
def complete_task(task_id):
    """Mark task as completed"""
    
    try:
        user_id = get_jwt_identity()
        
        task = db.session.query(Task).filter(
            Task.id == task_id,
            Task.assigned_to == user_id
        ).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        from datetime import datetime
        task.status = 'completed'
        task.completed_date = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Completed task: {task.title}")
        
        return jsonify({
            'message': 'Task completed successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to complete task'}), 500

# Analytics Routes

@crm_bp.route('/analytics/pipeline', methods=['GET'])
@jwt_required()
def get_pipeline_analytics():
    """Get pipeline analytics"""
    
    try:
        user_id = get_jwt_identity()
        
        crm_service, _, _ = get_services()
        analytics = crm_service.get_pipeline_analytics(user_id)
        
        return jsonify({
            'analytics': analytics
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching pipeline analytics: {e}")
        return jsonify({'error': 'Failed to fetch analytics'}), 500

# Search Routes

@crm_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    """Universal search across CRM entities"""
    
    try:
        user_id = get_jwt_identity()
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        if len(query) < 2:
            return jsonify({'error': 'Search query must be at least 2 characters'}), 400
        
        # Search contacts
        crm_service, _, _ = get_services()
        contacts = crm_service.search_contacts(query, user_id=user_id)
        
        # Search deals
        from sqlalchemy import or_, func
        deals = db.session.query(Deal).filter(
            Deal.user_id == user_id,
            or_(
                func.lower(Deal.title).contains(query.lower()),
                func.lower(Deal.description).contains(query.lower())
            )
        ).limit(10).all()
        
        # Search companies
        companies = db.session.query(Company).filter(
            Company.user_id == user_id,
            func.lower(Company.name).contains(query.lower())
        ).limit(10).all()
        
        results = []
        
        # Format results
        for contact in contacts[:5]:
            results.append({
                'type': 'contact',
                'id': contact.id,
                'title': contact.full_name,
                'subtitle': f"{contact.title} at {contact.company.name if contact.company else 'Unknown Company'}",
                'url': f'/contacts/{contact.id}'
            })
        
        for deal in deals[:5]:
            results.append({
                'type': 'deal',
                'id': deal.id,
                'title': deal.title,
                'subtitle': f"${deal.value:,} - {deal.stage}",
                'url': f'/deals/{deal.id}'
            })
        
        for company in companies[:5]:
            results.append({
                'type': 'company',
                'id': company.id,
                'title': company.name,
                'subtitle': f"{company.industry or 'Unknown Industry'} - {len(company.contacts)} contacts",
                'url': f'/companies/{company.id}'
            })
        
        return jsonify({
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({'error': 'Search failed'}), 500
