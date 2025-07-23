import openai
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.models.ai_intelligence import ConversationAnalysis, EmailAnalysis
from app.models.crm import Contact, Deal
from app.services.memory_service import UniversalMemoryService
import logging

logger = logging.getLogger(__name__)

class AIIntelligenceService:
    """
    Comprehensive AI service for conversation analysis, email intelligence,
    and autonomous customer relationship insights.
    """
    
    def __init__(self, db_session, memory_service: UniversalMemoryService):
        self.db = db_session
        self.memory_service = memory_service
        self.openai_client = openai.OpenAI() if openai.api_key else None
        
        # Cost optimization: Use different models for different tasks
        self.models = {
            'analysis': 'gpt-3.5-turbo',  # Cost-effective for analysis
            'generation': 'gpt-4',        # Higher quality for generation
            'simple': 'gpt-3.5-turbo'     # Simple tasks
        }
    
    def analyze_conversation(self, transcript: str, participants: List[str] = None,
                           contact_id: int = None, deal_id: int = None, 
                           user_id: int = 1) -> Dict:
        """Analyze conversation transcript for comprehensive insights"""
        
        if not self.openai_client:
            return self._fallback_conversation_analysis(transcript)
        
        # Check if we've analyzed similar content recently (cost optimization)
        recent_analysis = self._check_recent_analysis(transcript, 'conversation', user_id)
        if recent_analysis:
            logger.info("Using cached conversation analysis")
            return recent_analysis
        
        prompt = self._build_conversation_analysis_prompt(transcript, participants)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.models['analysis'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis_data = json.loads(response.choices[0].message.content)
            
            # Store analysis in database
            analysis = ConversationAnalysis(
                transcript=transcript[:5000],  # Truncate for storage
                participants=participants or [],
                sentiment_score=analysis_data.get('sentiment', {}).get('score', 0.0),
                sentiment_label=analysis_data.get('sentiment', {}).get('label', 'neutral'),
                topics=analysis_data.get('topics', []),
                action_items=analysis_data.get('action_items', []),
                next_steps=analysis_data.get('next_steps', []),
                deal_signals=analysis_data.get('deal_signals', []),
                talk_time_ratio=analysis_data.get('talk_time_ratio', {}),
                key_insights=analysis_data.get('key_insights', []),
                urgency_level=analysis_data.get('urgency_level', 'medium'),
                follow_up_required=str(analysis_data.get('follow_up_required', False)).lower(),
                contact_id=contact_id,
                deal_id=deal_id,
                user_id=user_id
            )
            
            self.db.add(analysis)
            self.db.commit()
            
            # Add insights to memory for future reference
            self._store_conversation_insights(analysis_data, user_id)
            
            # Auto-create tasks based on action items
            self._create_tasks_from_analysis(analysis_data, contact_id, deal_id, user_id)
            
            result = analysis.to_dict()
            result['analysis_id'] = analysis.id
            
            logger.info(f"Completed conversation analysis for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in conversation analysis: {e}")
            return self._fallback_conversation_analysis(transcript)
    
    def analyze_email(self, subject: str, body: str, sender: str = None,
                     recipient: str = None, contact_id: int = None, 
                     deal_id: int = None, user_id: int = 1) -> Dict:
        """Analyze email for sentiment, intent, urgency, and generate response suggestions"""
        
        if not self.openai_client:
            return self._fallback_email_analysis(subject, body)
        
        # Check for recent similar analysis
        email_content = f"{subject}\n{body}"
        recent_analysis = self._check_recent_analysis(email_content, 'email', user_id)
        if recent_analysis:
            logger.info("Using cached email analysis")
            return recent_analysis
        
        prompt = self._build_email_analysis_prompt(subject, body, sender)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.models['analysis'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            analysis_data = json.loads(response.choices[0].message.content)
            
            # Store analysis in database
            analysis = EmailAnalysis(
                subject=subject,
                body=body[:5000],  # Truncate for storage
                sender=sender,
                recipient=recipient,
                sentiment_score=analysis_data.get('sentiment', {}).get('score', 0.0),
                sentiment_label=analysis_data.get('sentiment', {}).get('label', 'neutral'),
                intent=analysis_data.get('intent', 'other'),
                urgency=analysis_data.get('urgency', 'medium'),
                priority_score=analysis_data.get('priority_score', 3),
                key_points=analysis_data.get('key_points', []),
                suggested_response=analysis_data.get('suggested_response', ''),
                action_required=str(analysis_data.get('action_required', False)).lower(),
                follow_up_date=self._parse_follow_up_date(analysis_data.get('follow_up_date')),
                contact_id=contact_id,
                deal_id=deal_id,
                user_id=user_id
            )
            
            self.db.add(analysis)
            self.db.commit()
            
            # Store email insights in memory
            self._store_email_insights(analysis_data, sender, user_id)
            
            result = analysis.to_dict()
            result['analysis_id'] = analysis.id
            
            logger.info(f"Completed email analysis for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in email analysis: {e}")
            return self._fallback_email_analysis(subject, body)
    
    def generate_proposal(self, contact_info: Dict, deal_info: Dict, 
                         conversation_history: List[Dict] = None,
                         user_id: int = 1) -> str:
        """Generate personalized proposal based on contact and deal information"""
        
        if not self.openai_client:
            return self._fallback_proposal(contact_info, deal_info)
        
        # Gather relevant memories for context
        relevant_memories = self.memory_service.search_memories(
            f"{contact_info.get('name', '')} {deal_info.get('title', '')}",
            category='proposal',
            limit=5,
            user_id=user_id
        )
        
        context = self._build_proposal_context(contact_info, deal_info, conversation_history, relevant_memories)
        prompt = self._build_proposal_prompt(context)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.models['generation'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500
            )
            
            proposal = response.choices[0].message.content
            
            # Store proposal in memory for future reference
            self.memory_service.add_memory(
                content=f"Generated proposal for {contact_info.get('name', 'Unknown')} - {deal_info.get('title', 'Unknown Deal')}",
                memory_type='agent',
                category='proposal',
                tags=['proposal', 'generated', contact_info.get('company', '').lower()],
                source_platform='ai_service',
                user_id=user_id
            )
            
            logger.info(f"Generated proposal for deal {deal_info.get('id', 'unknown')}")
            return proposal
            
        except Exception as e:
            logger.error(f"Error generating proposal: {e}")
            return self._fallback_proposal(contact_info, deal_info)
    
    def generate_email_response(self, original_email: Dict, context: Dict = None,
                               tone: str = 'professional', user_id: int = 1) -> str:
        """Generate intelligent email response based on analysis and context"""
        
        if not self.openai_client:
            return "Thank you for your email. I'll review this and get back to you soon."
        
        prompt = self._build_email_response_prompt(original_email, context, tone)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.models['simple'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=500
            )
            
            email_response = response.choices[0].message.content
            
            # Store response pattern in memory
            self.memory_service.add_memory(
                content=f"Email response pattern for {original_email.get('intent', 'general')} intent",
                memory_type='agent',
                category='email_patterns',
                tags=['email', 'response', original_email.get('intent', 'general')],
                source_platform='ai_service',
                user_id=user_id
            )
            
            return email_response
            
        except Exception as e:
            logger.error(f"Error generating email response: {e}")
            return "Thank you for your email. I'll review this and get back to you soon."
    
    def predict_deal_outcome(self, deal_id: int, user_id: int = 1) -> Dict:
        """Predict deal outcome based on historical data and current signals"""
        
        deal = self.db.query(Deal).filter(Deal.id == deal_id, Deal.user_id == user_id).first()
        if not deal:
            return {'error': 'Deal not found'}
        
        # Gather deal-related analyses
        conversation_analyses = self.db.query(ConversationAnalysis).filter(
            ConversationAnalysis.deal_id == deal_id
        ).all()
        
        email_analyses = self.db.query(EmailAnalysis).filter(
            EmailAnalysis.deal_id == deal_id
        ).all()
        
        # Calculate prediction based on multiple factors
        prediction = self._calculate_deal_prediction(deal, conversation_analyses, email_analyses)
        
        # Store prediction insights in memory
        self.memory_service.add_memory(
            content=f"Deal prediction for {deal.title}: {prediction['outcome']} ({prediction['confidence']}% confidence)",
            memory_type='agent',
            category='predictions',
            tags=['deal', 'prediction', deal.stage.lower()],
            source_platform='ai_service',
            user_id=user_id
        )
        
        return prediction
    
    def _build_conversation_analysis_prompt(self, transcript: str, participants: List[str] = None) -> str:
        """Build optimized prompt for conversation analysis"""
        
        participants_str = ', '.join(participants) if participants else 'Unknown participants'
        
        return f"""
        Analyze the following conversation transcript and provide comprehensive insights:
        
        Participants: {participants_str}
        Transcript: {transcript}
        
        Provide analysis in this exact JSON format:
        {{
            "sentiment": {{"score": float between -1 and 1, "label": "positive/neutral/negative"}},
            "topics": ["list", "of", "main", "topics"],
            "action_items": ["specific", "action", "items", "identified"],
            "next_steps": ["suggested", "next", "steps"],
            "deal_signals": ["buying", "signals", "or", "concerns"],
            "talk_time_ratio": {{"speaker1": percentage, "speaker2": percentage}},
            "key_insights": ["important", "insights", "from", "conversation"],
            "urgency_level": "low/medium/high",
            "follow_up_required": true/false
        }}
        
        Focus on actionable insights and business-relevant information.
        """
    
    def _build_email_analysis_prompt(self, subject: str, body: str, sender: str = None) -> str:
        """Build optimized prompt for email analysis"""
        
        return f"""
        Analyze the following email for business intelligence:
        
        From: {sender or 'Unknown'}
        Subject: {subject}
        Body: {body}
        
        Provide analysis in this exact JSON format:
        {{
            "sentiment": {{"score": float between -1 and 1, "label": "positive/neutral/negative"}},
            "intent": "meeting_request/pricing_inquiry/support_request/sales_inquiry/follow_up/other",
            "urgency": "low/medium/high/urgent",
            "priority_score": integer 1-5,
            "key_points": ["main", "points", "from", "email"],
            "suggested_response": "brief professional response suggestion",
            "action_required": true/false,
            "follow_up_date": "YYYY-MM-DD or null"
        }}
        
        Focus on business context and actionable insights.
        """
    
    def _build_proposal_prompt(self, context: str) -> str:
        """Build prompt for proposal generation"""
        
        return f"""
        Generate a comprehensive, professional business proposal based on the following context:
        
        {context}
        
        Create a proposal that includes:
        1. Executive Summary
        2. Understanding of Requirements
        3. Proposed Solution
        4. Timeline and Deliverables
        5. Investment and Terms
        6. Next Steps
        
        Make it personalized, professional, and compelling. Use a confident but consultative tone.
        """
    
    def _build_email_response_prompt(self, original_email: Dict, context: Dict = None, tone: str = 'professional') -> str:
        """Build prompt for email response generation"""
        
        context_str = ""
        if context:
            context_str = f"Additional context: {json.dumps(context, indent=2)}"
        
        return f"""
        Generate a {tone} email response to the following email:
        
        Original Email:
        Subject: {original_email.get('subject', '')}
        From: {original_email.get('sender', '')}
        Content: {original_email.get('body', '')}
        
        Email Analysis:
        Intent: {original_email.get('intent', 'unknown')}
        Urgency: {original_email.get('urgency', 'medium')}
        Key Points: {', '.join(original_email.get('key_points', []))}
        
        {context_str}
        
        Generate a response that:
        - Addresses the sender's main points
        - Maintains a {tone} tone
        - Provides clear next steps if applicable
        - Is concise but complete
        
        Return only the email body, no subject line.
        """
    
    def _check_recent_analysis(self, content: str, analysis_type: str, user_id: int) -> Optional[Dict]:
        """Check if similar content was analyzed recently to avoid redundant API calls"""
        
        # Use memory service to find similar analyses
        similar_memories = self.memory_service.search_memories(
            content[:200],  # Use first 200 chars for similarity check
            category=f'{analysis_type}_analysis',
            limit=1,
            user_id=user_id
        )
        
        if similar_memories and similar_memories[0]['similarity_score'] > 0.8:
            # Return cached analysis if very similar
            return json.loads(similar_memories[0]['content'])
        
        return None
    
    def _store_conversation_insights(self, analysis_data: Dict, user_id: int):
        """Store conversation insights in memory for future reference"""
        
        insights = analysis_data.get('key_insights', [])
        for insight in insights:
            self.memory_service.add_memory(
                content=insight,
                memory_type='agent',
                category='conversation_insights',
                tags=['conversation', 'insight'],
                source_platform='ai_service',
                user_id=user_id
            )
    
    def _store_email_insights(self, analysis_data: Dict, sender: str, user_id: int):
        """Store email insights in memory"""
        
        key_points = analysis_data.get('key_points', [])
        for point in key_points:
            self.memory_service.add_memory(
                content=f"Email from {sender}: {point}",
                memory_type='agent',
                category='email_insights',
                tags=['email', 'insight', sender.split('@')[1] if '@' in sender else 'unknown'],
                source_platform='ai_service',
                user_id=user_id
            )
    
    def _create_tasks_from_analysis(self, analysis_data: Dict, contact_id: int, deal_id: int, user_id: int):
        """Auto-create tasks based on conversation analysis"""
        
        from app.models.crm import Task
        
        action_items = analysis_data.get('action_items', [])
        for item in action_items:
            task = Task(
                title=item,
                description=f"Auto-generated from conversation analysis",
                priority='medium',
                status='pending',
                contact_id=contact_id,
                deal_id=deal_id,
                assigned_to=user_id,
                created_by=user_id
            )
            self.db.add(task)
        
        if action_items:
            self.db.commit()
            logger.info(f"Created {len(action_items)} tasks from conversation analysis")
    
    def _calculate_deal_prediction(self, deal: Deal, conversation_analyses: List, email_analyses: List) -> Dict:
        """Calculate deal outcome prediction based on multiple signals"""
        
        # Base prediction on current stage and probability
        base_score = deal.probability / 100.0
        
        # Analyze sentiment trends
        sentiment_scores = []
        for analysis in conversation_analyses + email_analyses:
            if hasattr(analysis, 'sentiment_score') and analysis.sentiment_score:
                sentiment_scores.append(analysis.sentiment_score)
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        sentiment_boost = avg_sentiment * 0.2  # Max 20% boost from sentiment
        
        # Analyze engagement level
        engagement_score = len(conversation_analyses + email_analyses) * 0.05  # 5% per interaction
        engagement_score = min(engagement_score, 0.3)  # Cap at 30%
        
        # Calculate final prediction
        final_score = min(1.0, base_score + sentiment_boost + engagement_score)
        
        # Determine outcome and confidence
        if final_score >= 0.8:
            outcome = 'win'
            confidence = int(final_score * 100)
        elif final_score >= 0.5:
            outcome = 'likely_win'
            confidence = int(final_score * 100)
        elif final_score >= 0.3:
            outcome = 'uncertain'
            confidence = int(final_score * 100)
        else:
            outcome = 'at_risk'
            confidence = int((1 - final_score) * 100)
        
        return {
            'outcome': outcome,
            'confidence': confidence,
            'probability': int(final_score * 100),
            'factors': {
                'base_probability': deal.probability,
                'sentiment_impact': round(sentiment_boost * 100, 1),
                'engagement_impact': round(engagement_score * 100, 1),
                'interaction_count': len(conversation_analyses + email_analyses)
            }
        }
    
    def _parse_follow_up_date(self, date_str: str) -> Optional[datetime]:
        """Parse follow-up date from AI response"""
        
        if not date_str or date_str.lower() == 'null':
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            # If parsing fails, suggest tomorrow
            return datetime.utcnow() + timedelta(days=1)
    
    def _build_proposal_context(self, contact_info: Dict, deal_info: Dict, 
                               conversation_history: List[Dict], relevant_memories: List[Dict]) -> str:
        """Build comprehensive context for proposal generation"""
        
        context_parts = [
            f"Contact: {contact_info.get('name', 'Unknown')} at {contact_info.get('company', 'Unknown Company')}",
            f"Title: {contact_info.get('title', 'Unknown Title')}",
            f"Deal: {deal_info.get('title', 'Unknown Deal')} - ${deal_info.get('value', 0):,}",
            f"Stage: {deal_info.get('stage', 'Unknown Stage')}",
            f"Requirements: {deal_info.get('description', 'Not specified')}"
        ]
        
        if conversation_history:
            context_parts.append("Recent Conversations:")
            for conv in conversation_history[-3:]:  # Last 3 conversations
                context_parts.append(f"- {conv.get('summary', 'No summary available')}")
        
        if relevant_memories:
            context_parts.append("Relevant Context:")
            for memory in relevant_memories[:3]:  # Top 3 relevant memories
                context_parts.append(f"- {memory.get('content', '')}")
        
        return '\n'.join(context_parts)
    
    def _fallback_conversation_analysis(self, transcript: str) -> Dict:
        """Fallback analysis when AI service is unavailable"""
        
        word_count = len(transcript.split())
        positive_words = ['great', 'excellent', 'perfect', 'love', 'amazing', 'interested', 'yes']
        negative_words = ['problem', 'issue', 'concern', 'difficult', 'expensive', 'no', 'cannot']
        
        positive_count = sum(1 for word in positive_words if word.lower() in transcript.lower())
        negative_count = sum(1 for word in negative_words if word.lower() in transcript.lower())
        
        sentiment_score = (positive_count - negative_count) / max(word_count / 100, 1)
        sentiment_score = max(-1, min(1, sentiment_score))
        
        return {
            "sentiment": {
                "score": sentiment_score,
                "label": "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral"
            },
            "topics": ["general discussion"],
            "action_items": ["Follow up on conversation"],
            "next_steps": ["Schedule next meeting"],
            "deal_signals": [],
            "talk_time_ratio": {"speaker1": 50, "speaker2": 50},
            "key_insights": ["Conversation analyzed with basic sentiment detection"],
            "urgency_level": "medium",
            "follow_up_required": True,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _fallback_email_analysis(self, subject: str, body: str) -> Dict:
        """Fallback email analysis when AI service is unavailable"""
        
        # Simple keyword-based analysis
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency']
        meeting_keywords = ['meeting', 'call', 'schedule', 'appointment']
        pricing_keywords = ['price', 'cost', 'quote', 'proposal', 'budget']
        
        urgency = 'urgent' if any(word in (subject + body).lower() for word in urgent_keywords) else 'medium'
        
        if any(word in (subject + body).lower() for word in meeting_keywords):
            intent = 'meeting_request'
        elif any(word in (subject + body).lower() for word in pricing_keywords):
            intent = 'pricing_inquiry'
        else:
            intent = 'other'
        
        return {
            "sentiment": {"score": 0.0, "label": "neutral"},
            "intent": intent,
            "urgency": urgency,
            "priority_score": 3,
            "key_points": ["Email analyzed with basic keyword detection"],
            "suggested_response": "Thank you for your email. I'll review this and get back to you soon.",
            "action_required": True,
            "follow_up_date": (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        }
    
    def _fallback_proposal(self, contact_info: Dict, deal_info: Dict) -> str:
        """Fallback proposal when AI service is unavailable"""
        
        return f"""
        PROPOSAL FOR {contact_info.get('company', 'Your Company').upper()}
        
        Dear {contact_info.get('name', 'Valued Client')},
        
        Thank you for considering our services for {deal_info.get('title', 'your project')}. 
        
        EXECUTIVE SUMMARY
        We understand your need for a comprehensive solution that delivers value and meets your business objectives.
        
        PROPOSED SOLUTION
        Our team will work closely with you to deliver a customized solution that addresses your specific requirements.
        
        INVESTMENT
        Total Investment: ${deal_info.get('value', 0):,}
        
        NEXT STEPS
        1. Review and approve this proposal
        2. Schedule kickoff meeting
        3. Begin project implementation
        
        We look forward to partnering with you on this exciting opportunity.
        
        Best regards,
        Your Agentic CRM Team
        """
