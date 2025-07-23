from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.services.ai_service import AIIntelligenceService
from app.services.memory_service import UniversalMemoryService
from app.utils.validators import validate_required_fields, format_validation_errors
from app.utils.helpers import sanitize_input
import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__)

def get_ai_service():
    """Get initialized AI service"""
    memory_service = UniversalMemoryService(db.session)
    return AIIntelligenceService(db.session, memory_service)

@ai_bp.route('/analyze/conversation', methods=['POST'])
@jwt_required()
def analyze_conversation():
    """Analyze conversation transcript for insights"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['transcript']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize inputs
        transcript = sanitize_input(data['transcript'], 10000)
        participants = data.get('participants', [])
        contact_id = data.get('contact_id')
        deal_id = data.get('deal_id')
        
        if len(transcript) < 50:
            return jsonify({'error': 'Transcript too short for meaningful analysis'}), 400
        
        # Analyze conversation
        ai_service = get_ai_service()
        analysis = ai_service.analyze_conversation(
            transcript=transcript,
            participants=participants,
            contact_id=contact_id,
            deal_id=deal_id,
            user_id=user_id
        )
        
        logger.info(f"Analyzed conversation for user {user_id}")
        
        return jsonify({
            'message': 'Conversation analyzed successfully',
            'analysis': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing conversation: {e}")
        return jsonify({'error': 'Conversation analysis failed'}), 500

@ai_bp.route('/analyze/email', methods=['POST'])
@jwt_required()
def analyze_email():
    """Analyze email for sentiment, intent, and urgency"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['subject', 'body']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize inputs
        subject = sanitize_input(data['subject'], 500)
        body = sanitize_input(data['body'], 5000)
        sender = sanitize_input(data.get('sender', ''), 255)
        recipient = sanitize_input(data.get('recipient', ''), 255)
        contact_id = data.get('contact_id')
        deal_id = data.get('deal_id')
        
        # Analyze email
        ai_service = get_ai_service()
        analysis = ai_service.analyze_email(
            subject=subject,
            body=body,
            sender=sender,
            recipient=recipient,
            contact_id=contact_id,
            deal_id=deal_id,
            user_id=user_id
        )
        
        logger.info(f"Analyzed email for user {user_id}")
        
        return jsonify({
            'message': 'Email analyzed successfully',
            'analysis': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing email: {e}")
        return jsonify({'error': 'Email analysis failed'}), 500

@ai_bp.route('/generate/proposal', methods=['POST'])
@jwt_required()
def generate_proposal():
    """Generate personalized proposal based on contact and deal information"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['contact_info', 'deal_info']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        contact_info = data['contact_info']
        deal_info = data['deal_info']
        conversation_history = data.get('conversation_history', [])
        
        # Generate proposal
        ai_service = get_ai_service()
        proposal = ai_service.generate_proposal(
            contact_info=contact_info,
            deal_info=deal_info,
            conversation_history=conversation_history,
            user_id=user_id
        )
        
        logger.info(f"Generated proposal for user {user_id}")
        
        return jsonify({
            'message': 'Proposal generated successfully',
            'proposal': proposal
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating proposal: {e}")
        return jsonify({'error': 'Proposal generation failed'}), 500

@ai_bp.route('/generate/email-response', methods=['POST'])
@jwt_required()
def generate_email_response():
    """Generate intelligent email response"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['original_email']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        original_email = data['original_email']
        context = data.get('context', {})
        tone = data.get('tone', 'professional')
        
        # Validate tone
        valid_tones = ['professional', 'friendly', 'formal', 'casual']
        if tone not in valid_tones:
            tone = 'professional'
        
        # Generate email response
        ai_service = get_ai_service()
        response = ai_service.generate_email_response(
            original_email=original_email,
            context=context,
            tone=tone,
            user_id=user_id
        )
        
        logger.info(f"Generated email response for user {user_id}")
        
        return jsonify({
            'message': 'Email response generated successfully',
            'response': response,
            'tone': tone
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating email response: {e}")
        return jsonify({'error': 'Email response generation failed'}), 500

@ai_bp.route('/predict/deal/<int:deal_id>', methods=['GET'])
@jwt_required()
def predict_deal_outcome(deal_id):
    """Predict deal outcome based on historical data and current signals"""
    
    try:
        user_id = get_jwt_identity()
        
        # Predict deal outcome
        ai_service = get_ai_service()
        prediction = ai_service.predict_deal_outcome(deal_id, user_id)
        
        if 'error' in prediction:
            return jsonify(prediction), 404
        
        logger.info(f"Generated deal prediction for deal {deal_id}")
        
        return jsonify({
            'message': 'Deal prediction generated successfully',
            'prediction': prediction
        }), 200
        
    except Exception as e:
        logger.error(f"Error predicting deal outcome: {e}")
        return jsonify({'error': 'Deal prediction failed'}), 500

@ai_bp.route('/insights/contact/<int:contact_id>', methods=['GET'])
@jwt_required()
def get_contact_insights():
    """Get AI-generated insights for a specific contact"""
    
    try:
        user_id = get_jwt_identity()
        contact_id = request.view_args['contact_id']
        
        # Get contact
        from app.models.crm import Contact
        contact = db.session.query(Contact).filter(
            Contact.id == contact_id,
            Contact.user_id == user_id
        ).first()
        
        if not contact:
            return jsonify({'error': 'Contact not found'}), 404
        
        # Get contact-related memories and analyses
        memory_service = UniversalMemoryService(db.session)
        insights = memory_service.search_memories(
            query=f"{contact.full_name} {contact.email}",
            limit=10,
            user_id=user_id
        )
        
        # Format insights
        formatted_insights = []
        for insight in insights:
            if insight['similarity_score'] > 0.5:  # Only high-relevance insights
                formatted_insights.append({
                    'content': insight['content'],
                    'category': insight.get('category', 'general'),
                    'relevance': insight['similarity_score'],
                    'created_at': insight.get('created_at')
                })
        
        return jsonify({
            'contact_id': contact_id,
            'contact_name': contact.full_name,
            'insights': formatted_insights,
            'total': len(formatted_insights)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching contact insights: {e}")
        return jsonify({'error': 'Failed to fetch contact insights'}), 500

@ai_bp.route('/insights/deal/<int:deal_id>', methods=['GET'])
@jwt_required()
def get_deal_insights(deal_id):
    """Get AI-generated insights for a specific deal"""
    
    try:
        user_id = get_jwt_identity()
        
        # Get deal
        from app.models.crm import Deal
        deal = db.session.query(Deal).filter(
            Deal.id == deal_id,
            Deal.user_id == user_id
        ).first()
        
        if not deal:
            return jsonify({'error': 'Deal not found'}), 404
        
        # Get deal-related memories and analyses
        memory_service = UniversalMemoryService(db.session)
        insights = memory_service.search_memories(
            query=f"{deal.title} {deal.company.name if deal.company else ''}",
            limit=10,
            user_id=user_id
        )
        
        # Get deal prediction
        ai_service = get_ai_service()
        prediction = ai_service.predict_deal_outcome(deal_id, user_id)
        
        # Format insights
        formatted_insights = []
        for insight in insights:
            if insight['similarity_score'] > 0.5:
                formatted_insights.append({
                    'content': insight['content'],
                    'category': insight.get('category', 'general'),
                    'relevance': insight['similarity_score'],
                    'created_at': insight.get('created_at')
                })
        
        return jsonify({
            'deal_id': deal_id,
            'deal_title': deal.title,
            'prediction': prediction if 'error' not in prediction else None,
            'insights': formatted_insights,
            'total': len(formatted_insights)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching deal insights: {e}")
        return jsonify({'error': 'Failed to fetch deal insights'}), 500

@ai_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get AI-powered recommendations for the user"""
    
    try:
        user_id = get_jwt_identity()
        
        recommendations = []
        
        # Get overdue tasks recommendation
        from app.models.crm import Task
        from datetime import datetime
        
        overdue_tasks = db.session.query(Task).filter(
            Task.assigned_to == user_id,
            Task.status.in_(['pending', 'in_progress']),
            Task.due_date < datetime.utcnow()
        ).count()
        
        if overdue_tasks > 0:
            recommendations.append({
                'type': 'task_management',
                'priority': 'high',
                'title': 'Address Overdue Tasks',
                'description': f'You have {overdue_tasks} overdue tasks that need attention.',
                'action': 'Review and complete overdue tasks',
                'url': '/tasks?overdue=true'
            })
        
        # Get stale deals recommendation
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        stale_deals = db.session.query(Deal).filter(
            Deal.user_id == user_id,
            Deal.status == 'open',
            Deal.updated_at < week_ago
        ).count()
        
        if stale_deals > 0:
            recommendations.append({
                'type': 'deal_management',
                'priority': 'medium',
                'title': 'Follow Up on Stale Deals',
                'description': f'{stale_deals} deals haven\'t been updated in over a week.',
                'action': 'Review and update deal status',
                'url': '/deals?stale=true'
            })
        
        # Get high-value lead recommendation
        from app.models.crm import Contact
        
        hot_leads = db.session.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.lead_score >= 80,
            Contact.last_contact_date < datetime.utcnow() - timedelta(days=3)
        ).count()
        
        if hot_leads > 0:
            recommendations.append({
                'type': 'lead_nurturing',
                'priority': 'high',
                'title': 'Engage High-Value Leads',
                'description': f'{hot_leads} high-scoring leads haven\'t been contacted recently.',
                'action': 'Reach out to hot leads',
                'url': '/contacts?hot_leads=true'
            })
        
        return jsonify({
            'recommendations': recommendations,
            'total': len(recommendations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching recommendations: {e}")
        return jsonify({'error': 'Failed to fetch recommendations'}), 500
