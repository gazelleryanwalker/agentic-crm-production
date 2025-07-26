from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.user import User
from ..models.seo import SEOProject, SEORule, SEOOptimization, SEOAnalysis
from .. import db
import openai
import json
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import logging

seo_bp = Blueprint('seo', __name__)

# Configure OpenAI
def get_openai_client():
    """Get OpenAI client with API key from environment"""
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    return openai.OpenAI(api_key=api_key)

@seo_bp.route('/projects', methods=['GET'])
@jwt_required()
def get_seo_projects():
    """Get all SEO projects for the current user"""
    try:
        user_id = get_jwt_identity()
        projects = SEOProject.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'success': True,
            'projects': [{
                'id': project.id,
                'name': project.name,
                'domain': project.domain,
                'status': project.status,
                'created_at': project.created_at.isoformat(),
                'last_analysis': project.last_analysis.isoformat() if project.last_analysis else None,
                'total_pages': project.total_pages,
                'optimized_pages': project.optimized_pages
            } for project in projects]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching SEO projects: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch SEO projects'}), 500

@seo_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_seo_project():
    """Create a new SEO project"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('domain'):
            return jsonify({'success': False, 'message': 'Name and domain are required'}), 400
        
        # Validate domain format
        domain = data['domain'].strip()
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        try:
            parsed = urlparse(domain)
            if not parsed.netloc:
                raise ValueError("Invalid domain")
        except:
            return jsonify({'success': False, 'message': 'Invalid domain format'}), 400
        
        # Create new SEO project
        project = SEOProject(
            user_id=user_id,
            name=data['name'],
            domain=domain,
            status='active'
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'SEO project created successfully',
            'project': {
                'id': project.id,
                'name': project.name,
                'domain': project.domain,
                'status': project.status,
                'created_at': project.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating SEO project: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to create SEO project'}), 500

@seo_bp.route('/projects/<int:project_id>/analyze', methods=['POST'])
@jwt_required()
def analyze_website(project_id):
    """Analyze a website for SEO opportunities"""
    try:
        user_id = get_jwt_identity()
        project = SEOProject.query.filter_by(id=project_id, user_id=user_id).first()
        
        if not project:
            return jsonify({'success': False, 'message': 'SEO project not found'}), 404
        
        data = request.get_json()
        urls = data.get('urls', [project.domain])  # Default to domain if no URLs provided
        
        analysis_results = []
        
        for url in urls:
            try:
                # Fetch page content
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; AgenticCRM-SEO/1.0)'
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract current SEO elements
                current_seo = extract_seo_elements(soup, url)
                
                # Generate AI-powered recommendations
                recommendations = generate_seo_recommendations(current_seo, url)
                
                # Save analysis to database
                analysis = SEOAnalysis(
                    project_id=project.id,
                    url=url,
                    current_title=current_seo.get('title'),
                    current_description=current_seo.get('description'),
                    current_h1=current_seo.get('h1'),
                    recommendations=json.dumps(recommendations),
                    status='pending'
                )
                
                db.session.add(analysis)
                analysis_results.append({
                    'url': url,
                    'current_seo': current_seo,
                    'recommendations': recommendations
                })
                
            except Exception as e:
                current_app.logger.error(f"Error analyzing URL {url}: {str(e)}")
                analysis_results.append({
                    'url': url,
                    'error': f"Failed to analyze: {str(e)}"
                })
        
        # Update project stats
        project.last_analysis = db.func.now()
        project.total_pages = len(urls)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Website analysis completed',
            'results': analysis_results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error analyzing website: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to analyze website'}), 500

def extract_seo_elements(soup, url):
    """Extract current SEO elements from a webpage"""
    seo_data = {
        'url': url,
        'title': '',
        'description': '',
        'h1': '',
        'h2_tags': [],
        'internal_links': [],
        'external_links': [],
        'images_without_alt': 0,
        'schema_markup': [],
        'word_count': 0
    }
    
    # Extract title
    title_tag = soup.find('title')
    if title_tag:
        seo_data['title'] = title_tag.get_text().strip()
    
    # Extract meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        seo_data['description'] = meta_desc.get('content', '').strip()
    
    # Extract H1 tags
    h1_tags = soup.find_all('h1')
    if h1_tags:
        seo_data['h1'] = h1_tags[0].get_text().strip()
    
    # Extract H2 tags
    h2_tags = soup.find_all('h2')
    seo_data['h2_tags'] = [h2.get_text().strip() for h2 in h2_tags[:5]]  # Limit to first 5
    
    # Extract links
    links = soup.find_all('a', href=True)
    domain = urlparse(url).netloc
    
    for link in links:
        href = link.get('href')
        if href.startswith('http'):
            link_domain = urlparse(href).netloc
            if link_domain == domain:
                seo_data['internal_links'].append(href)
            else:
                seo_data['external_links'].append(href)
        elif href.startswith('/'):
            seo_data['internal_links'].append(href)
    
    # Count images without alt text
    images = soup.find_all('img')
    seo_data['images_without_alt'] = len([img for img in images if not img.get('alt')])
    
    # Extract schema markup
    schema_scripts = soup.find_all('script', type='application/ld+json')
    for script in schema_scripts:
        try:
            schema_data = json.loads(script.string)
            seo_data['schema_markup'].append(schema_data)
        except:
            pass
    
    # Calculate word count
    text_content = soup.get_text()
    words = re.findall(r'\b\w+\b', text_content.lower())
    seo_data['word_count'] = len(words)
    
    return seo_data

def generate_seo_recommendations(current_seo, url):
    """Generate AI-powered SEO recommendations"""
    try:
        client = get_openai_client()
        
        prompt = f"""
        Analyze the following SEO data for the URL: {url}
        
        Current SEO Elements:
        - Title: "{current_seo.get('title', 'No title')}"
        - Meta Description: "{current_seo.get('description', 'No description')}"
        - H1: "{current_seo.get('h1', 'No H1')}"
        - H2 Tags: {current_seo.get('h2_tags', [])}
        - Word Count: {current_seo.get('word_count', 0)}
        - Internal Links: {len(current_seo.get('internal_links', []))}
        - External Links: {len(current_seo.get('external_links', []))}
        - Images without Alt: {current_seo.get('images_without_alt', 0)}
        - Schema Markup: {len(current_seo.get('schema_markup', []))} items
        
        Provide specific SEO recommendations in JSON format with the following structure:
        {{
            "title_optimization": {{
                "current_issues": ["list of issues"],
                "recommended_title": "optimized title",
                "reasoning": "why this title is better"
            }},
            "meta_description": {{
                "current_issues": ["list of issues"],
                "recommended_description": "optimized description",
                "reasoning": "why this description is better"
            }},
            "h1_optimization": {{
                "current_issues": ["list of issues"],
                "recommended_h1": "optimized H1",
                "reasoning": "why this H1 is better"
            }},
            "internal_linking": {{
                "opportunities": ["suggested internal linking opportunities"],
                "anchor_text_suggestions": ["list of anchor text suggestions"]
            }},
            "schema_markup": {{
                "recommended_schemas": ["list of recommended schema types"],
                "implementation_priority": "high/medium/low"
            }},
            "overall_score": 85,
            "priority_actions": ["top 3 priority actions"]
        }}
        
        Focus on practical, actionable recommendations that will improve search engine rankings.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert SEO analyst. Provide detailed, actionable SEO recommendations in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse the JSON response
        recommendations = json.loads(response.choices[0].message.content)
        return recommendations
        
    except Exception as e:
        current_app.logger.error(f"Error generating SEO recommendations: {str(e)}")
        return {
            "error": "Failed to generate recommendations",
            "overall_score": 0,
            "priority_actions": ["Manual review required"]
        }

@seo_bp.route('/projects/<int:project_id>/optimizations', methods=['GET'])
@jwt_required()
def get_optimizations(project_id):
    """Get all optimizations for a project"""
    try:
        user_id = get_jwt_identity()
        project = SEOProject.query.filter_by(id=project_id, user_id=user_id).first()
        
        if not project:
            return jsonify({'success': False, 'message': 'SEO project not found'}), 404
        
        analyses = SEOAnalysis.query.filter_by(project_id=project_id).all()
        
        results = []
        for analysis in analyses:
            recommendations = json.loads(analysis.recommendations) if analysis.recommendations else {}
            results.append({
                'id': analysis.id,
                'url': analysis.url,
                'current_title': analysis.current_title,
                'current_description': analysis.current_description,
                'current_h1': analysis.current_h1,
                'recommendations': recommendations,
                'status': analysis.status,
                'created_at': analysis.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'optimizations': results
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching optimizations: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch optimizations'}), 500

@seo_bp.route('/projects/<int:project_id>/generate-snippet', methods=['POST'])
@jwt_required()
def generate_seo_snippet(project_id):
    """Generate JavaScript snippet for SEO automation"""
    try:
        user_id = get_jwt_identity()
        project = SEOProject.query.filter_by(id=project_id, user_id=user_id).first()
        
        if not project:
            return jsonify({'success': False, 'message': 'SEO project not found'}), 404
        
        # Generate unique project token
        import secrets
        project_token = secrets.token_urlsafe(32)
        project.snippet_token = project_token
        db.session.commit()
        
        # Generate JavaScript snippet
        snippet = f"""
<!-- Agentic CRM SEO Automation -->
<script>
(function() {{
    var script = document.createElement('script');
    script.src = '{request.host_url}api/seo/snippet.js';
    script.setAttribute('data-project-token', '{project_token}');
    script.setAttribute('data-project-id', '{project_id}');
    script.async = true;
    document.head.appendChild(script);
}})();
</script>
<!-- End Agentic CRM SEO Automation -->
        """.strip()
        
        return jsonify({
            'success': True,
            'snippet': snippet,
            'token': project_token,
            'instructions': [
                'Copy the above JavaScript snippet',
                'Paste it in the <head> section of your website',
                'The snippet will automatically optimize your SEO elements',
                'Monitor changes from your CRM dashboard'
            ]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error generating SEO snippet: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to generate snippet'}), 500

@seo_bp.route('/snippet.js', methods=['GET'])
def serve_seo_snippet():
    """Serve the SEO automation JavaScript snippet"""
    project_token = request.args.get('token')
    project_id = request.args.get('project_id')
    
    if not project_token or not project_id:
        return "// Invalid parameters", 400, {'Content-Type': 'application/javascript'}
    
    # Verify project exists and token is valid
    project = SEOProject.query.filter_by(id=project_id, snippet_token=project_token).first()
    if not project:
        return "// Invalid project or token", 403, {'Content-Type': 'application/javascript'}
    
    # Generate the JavaScript code
    js_code = f"""
// Agentic CRM SEO Automation Script
(function() {{
    'use strict';
    
    const PROJECT_ID = '{project_id}';
    const PROJECT_TOKEN = '{project_token}';
    const API_BASE = '{request.host_url}api/seo';
    
    // Initialize SEO automation
    function initSEOAutomation() {{
        console.log('Agentic CRM SEO Automation initialized');
        
        // Get current page optimizations
        fetchOptimizations();
        
        // Set up mutation observer for dynamic content
        setupMutationObserver();
    }}
    
    // Fetch optimizations for current page
    function fetchOptimizations() {{
        const currentUrl = window.location.href;
        
        fetch(`${{API_BASE}}/apply-optimizations`, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify({{
                project_token: PROJECT_TOKEN,
                project_id: PROJECT_ID,
                url: currentUrl,
                user_agent: navigator.userAgent
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.success && data.optimizations) {{
                applyOptimizations(data.optimizations);
            }}
        }})
        .catch(error => {{
            console.warn('SEO optimization fetch failed:', error);
        }});
    }}
    
    // Apply SEO optimizations to the page
    function applyOptimizations(optimizations) {{
        // Apply title optimization
        if (optimizations.title) {{
            document.title = optimizations.title;
        }}
        
        // Apply meta description
        if (optimizations.meta_description) {{
            let metaDesc = document.querySelector('meta[name="description"]');
            if (!metaDesc) {{
                metaDesc = document.createElement('meta');
                metaDesc.setAttribute('name', 'description');
                document.head.appendChild(metaDesc);
            }}
            metaDesc.setAttribute('content', optimizations.meta_description);
        }}
        
        // Apply H1 optimization
        if (optimizations.h1) {{
            const h1 = document.querySelector('h1');
            if (h1) {{
                h1.textContent = optimizations.h1;
            }}
        }}
        
        // Apply schema markup
        if (optimizations.schema_markup) {{
            optimizations.schema_markup.forEach(schema => {{
                const script = document.createElement('script');
                script.type = 'application/ld+json';
                script.textContent = JSON.stringify(schema);
                document.head.appendChild(script);
            }});
        }}
        
        // Apply internal links
        if (optimizations.internal_links) {{
            applyInternalLinks(optimizations.internal_links);
        }}
        
        console.log('SEO optimizations applied');
    }}
    
    // Apply internal linking suggestions
    function applyInternalLinks(linkSuggestions) {{
        linkSuggestions.forEach(suggestion => {{
            const elements = document.querySelectorAll(suggestion.selector);
            elements.forEach(element => {{
                if (element.textContent.includes(suggestion.keyword)) {{
                    const link = document.createElement('a');
                    link.href = suggestion.url;
                    link.textContent = suggestion.anchor_text;
                    link.style.color = 'inherit';
                    link.style.textDecoration = 'underline';
                    
                    // Replace keyword with link
                    element.innerHTML = element.innerHTML.replace(
                        new RegExp(suggestion.keyword, 'gi'),
                        link.outerHTML
                    );
                }}
            }});
        }});
    }}
    
    // Set up mutation observer for dynamic content
    function setupMutationObserver() {{
        const observer = new MutationObserver(function(mutations) {{
            mutations.forEach(function(mutation) {{
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {{
                    // Re-apply optimizations when new content is added
                    setTimeout(fetchOptimizations, 1000);
                }}
            }});
        }});
        
        observer.observe(document.body, {{
            childList: true,
            subtree: true
        }});
    }}
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initSEOAutomation);
    }} else {{
        initSEOAutomation();
    }}
    
}})();
    """
    
    return js_code, 200, {'Content-Type': 'application/javascript'}

@seo_bp.route('/apply-optimizations', methods=['POST'])
def apply_optimizations():
    """API endpoint called by the JavaScript snippet to get optimizations"""
    try:
        data = request.get_json()
        project_token = data.get('project_token')
        project_id = data.get('project_id')
        url = data.get('url')
        
        if not all([project_token, project_id, url]):
            return jsonify({'success': False, 'message': 'Missing required parameters'}), 400
        
        # Verify project and token
        project = SEOProject.query.filter_by(id=project_id, snippet_token=project_token).first()
        if not project:
            return jsonify({'success': False, 'message': 'Invalid project or token'}), 403
        
        # Find existing analysis for this URL
        analysis = SEOAnalysis.query.filter_by(project_id=project_id, url=url).first()
        
        if not analysis:
            return jsonify({'success': False, 'message': 'No analysis found for this URL'}), 404
        
        # Parse recommendations
        recommendations = json.loads(analysis.recommendations) if analysis.recommendations else {}
        
        # Format optimizations for JavaScript application
        optimizations = {}
        
        if 'title_optimization' in recommendations:
            optimizations['title'] = recommendations['title_optimization'].get('recommended_title')
        
        if 'meta_description' in recommendations:
            optimizations['meta_description'] = recommendations['meta_description'].get('recommended_description')
        
        if 'h1_optimization' in recommendations:
            optimizations['h1'] = recommendations['h1_optimization'].get('recommended_h1')
        
        if 'schema_markup' in recommendations:
            optimizations['schema_markup'] = recommendations['schema_markup'].get('recommended_schemas', [])
        
        if 'internal_linking' in recommendations:
            optimizations['internal_links'] = recommendations['internal_linking'].get('opportunities', [])
        
        return jsonify({
            'success': True,
            'optimizations': optimizations
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error applying optimizations: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to apply optimizations'}), 500
