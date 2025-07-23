from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.services.memory_service import UniversalMemoryService
from app.utils.validators import validate_memory_data, validate_search_query, format_validation_errors
from app.utils.helpers import sanitize_input
import logging

logger = logging.getLogger(__name__)

memory_bp = Blueprint('memory', __name__)

def get_memory_service():
    """Get initialized memory service"""
    return UniversalMemoryService(db.session)

@memory_bp.route('/memories', methods=['POST'])
@jwt_required()
def add_memory():
    """Add a new memory to the universal memory layer"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate memory data
        validation_errors = validate_memory_data(data)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize inputs
        content = sanitize_input(data['content'], 10000)
        memory_type = sanitize_input(data['memory_type'], 50)
        category = sanitize_input(data.get('category', ''), 100) if data.get('category') else None
        tags = data.get('tags', [])
        source_platform = sanitize_input(data.get('source_platform', ''), 100) if data.get('source_platform') else None
        
        # Add memory using service
        memory_service = get_memory_service()
        memory = memory_service.add_memory(
            content=content,
            memory_type=memory_type,
            category=category,
            tags=tags,
            source_platform=source_platform,
            user_id=user_id
        )
        
        logger.info(f"Added memory: {memory_type}/{category} for user {user_id}")
        
        return jsonify({
            'message': 'Memory added successfully',
            'memory': memory.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add memory'}), 500

@memory_bp.route('/memories/search', methods=['GET'])
@jwt_required()
def search_memories():
    """Search memories using semantic similarity"""
    
    try:
        user_id = get_jwt_identity()
        
        # Get and validate query
        query = request.args.get('q', '').strip()
        query_validation = validate_search_query(query)
        
        if query_validation['errors']:
            return jsonify({
                'error': 'Invalid search query',
                'details': query_validation['errors']
            }), 400
        
        query = query_validation['query']
        
        # Get optional filters
        memory_type = request.args.get('type')
        category = request.args.get('category')
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 results
        
        # Search memories
        memory_service = get_memory_service()
        memories = memory_service.search_memories(
            query=query,
            memory_type=memory_type,
            category=category,
            limit=limit,
            user_id=user_id
        )
        
        return jsonify({
            'memories': memories,
            'total': len(memories),
            'query': query
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        return jsonify({'error': 'Memory search failed'}), 500

@memory_bp.route('/memories/stats', methods=['GET'])
@jwt_required()
def get_memory_stats():
    """Get comprehensive memory statistics"""
    
    try:
        user_id = get_jwt_identity()
        
        memory_service = get_memory_service()
        stats = memory_service.get_memory_stats(user_id)
        
        return jsonify({
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching memory stats: {e}")
        return jsonify({'error': 'Failed to fetch memory statistics'}), 500

@memory_bp.route('/memories/optimize', methods=['POST'])
@jwt_required()
def optimize_memories():
    """Optimize memory storage by removing duplicates and low-relevance memories"""
    
    try:
        user_id = get_jwt_identity()
        
        memory_service = get_memory_service()
        optimization_result = memory_service.optimize_memories(user_id)
        
        logger.info(f"Memory optimization completed for user {user_id}: {optimization_result}")
        
        return jsonify({
            'message': 'Memory optimization completed',
            'result': optimization_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error optimizing memories: {e}")
        return jsonify({'error': 'Memory optimization failed'}), 500

@memory_bp.route('/memories/<int:memory_id>/related', methods=['GET'])
@jwt_required()
def get_related_memories(memory_id):
    """Get memories related to a specific memory"""
    
    try:
        user_id = get_jwt_identity()
        limit = min(int(request.args.get('limit', 5)), 20)  # Max 20 results
        
        memory_service = get_memory_service()
        related_memories = memory_service.get_related_memories(
            memory_id=memory_id,
            limit=limit,
            user_id=user_id
        )
        
        return jsonify({
            'related_memories': related_memories,
            'total': len(related_memories)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching related memories: {e}")
        return jsonify({'error': 'Failed to fetch related memories'}), 500

@memory_bp.route('/memories/<int:memory_id>/boost', methods=['POST'])
@jwt_required()
def boost_memory_relevance(memory_id):
    """Boost memory relevance score when accessed or referenced"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        boost = float(data.get('boost', 0.1))
        
        # Limit boost amount
        boost = max(0.01, min(boost, 1.0))
        
        memory_service = get_memory_service()
        success = memory_service.update_memory_relevance(memory_id, boost, user_id)
        
        if not success:
            return jsonify({'error': 'Memory not found'}), 404
        
        return jsonify({
            'message': 'Memory relevance updated',
            'boost_applied': boost
        }), 200
        
    except Exception as e:
        logger.error(f"Error boosting memory relevance: {e}")
        return jsonify({'error': 'Failed to update memory relevance'}), 500

@memory_bp.route('/memories/categories', methods=['GET'])
@jwt_required()
def get_memory_categories():
    """Get all memory categories for the user"""
    
    try:
        user_id = get_jwt_identity()
        
        from app.models.memory import Memory
        from sqlalchemy import func, distinct
        
        categories = db.session.query(distinct(Memory.category)).filter(
            Memory.user_id == user_id,
            Memory.category.isnot(None)
        ).all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({
            'categories': sorted(category_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching memory categories: {e}")
        return jsonify({'error': 'Failed to fetch categories'}), 500

@memory_bp.route('/memories/types', methods=['GET'])
@jwt_required()
def get_memory_types():
    """Get available memory types"""
    
    try:
        return jsonify({
            'types': [
                {
                    'value': 'user',
                    'label': 'User Memory',
                    'description': 'Personal context and preferences'
                },
                {
                    'value': 'session',
                    'label': 'Session Memory',
                    'description': 'Temporary interaction context'
                },
                {
                    'value': 'agent',
                    'label': 'Agent Memory',
                    'description': 'System-wide learning and insights'
                }
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching memory types: {e}")
        return jsonify({'error': 'Failed to fetch memory types'}), 500
