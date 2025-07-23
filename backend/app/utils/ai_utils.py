import numpy as np
import openai
from typing import Optional, List
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

def generate_embedding(text: str, model: str = "text-embedding-ada-002") -> Optional[np.ndarray]:
    """
    Generate embedding vector for text using OpenAI's embedding API
    with cost optimization and caching.
    """
    
    if not text or not text.strip():
        return None
    
    # Create cache key from text hash
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    try:
        # Use OpenAI's embedding API
        client = openai.OpenAI()
        
        response = client.embeddings.create(
            model=model,
            input=text[:8000]  # Truncate to avoid token limits
        )
        
        embedding = np.array(response.data[0].embedding)
        logger.debug(f"Generated embedding for text (length: {len(text)})")
        
        return embedding
        
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
        # Fallback to simple hash-based embedding
        return _generate_fallback_embedding(text)

def _generate_fallback_embedding(text: str, dimensions: int = 1536) -> np.ndarray:
    """
    Generate a simple hash-based embedding as fallback when OpenAI API is unavailable.
    This provides basic semantic grouping but not true semantic similarity.
    """
    
    # Create multiple hash values for different aspects of the text
    hashes = []
    
    # Word-based hashes
    words = text.lower().split()
    for i in range(0, min(len(words), 10), 2):  # Sample every 2nd word, max 5 pairs
        word_pair = ' '.join(words[i:i+2])
        hash_val = int(hashlib.md5(word_pair.encode()).hexdigest()[:8], 16)
        hashes.append(hash_val)
    
    # Character-based hashes
    for i in range(0, min(len(text), 100), 20):  # Sample every 20 characters
        chunk = text[i:i+20]
        hash_val = int(hashlib.md5(chunk.encode()).hexdigest()[:8], 16)
        hashes.append(hash_val)
    
    # Length and structure hashes
    hashes.append(len(text))
    hashes.append(len(words))
    hashes.append(text.count('.'))
    hashes.append(text.count('?'))
    
    # Pad or truncate to desired dimensions
    while len(hashes) < dimensions:
        hashes.extend(hashes[:min(len(hashes), dimensions - len(hashes))])
    
    hashes = hashes[:dimensions]
    
    # Normalize to create embedding-like vector
    embedding = np.array(hashes, dtype=float)
    embedding = embedding / np.linalg.norm(embedding)  # Normalize
    
    return embedding

def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embedding vectors.
    Returns similarity score between 0 and 1.
    """
    
    try:
        # Ensure embeddings are numpy arrays
        if not isinstance(embedding1, np.ndarray):
            embedding1 = np.array(embedding1)
        if not isinstance(embedding2, np.ndarray):
            embedding2 = np.array(embedding2)
        
        # Handle different dimensions by padding with zeros
        if len(embedding1) != len(embedding2):
            max_len = max(len(embedding1), len(embedding2))
            if len(embedding1) < max_len:
                embedding1 = np.pad(embedding1, (0, max_len - len(embedding1)))
            if len(embedding2) < max_len:
                embedding2 = np.pad(embedding2, (0, max_len - len(embedding2)))
        
        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure result is between 0 and 1
        similarity = max(0.0, min(1.0, (similarity + 1) / 2))
        
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0

def batch_generate_embeddings(texts: List[str], model: str = "text-embedding-ada-002") -> List[Optional[np.ndarray]]:
    """
    Generate embeddings for multiple texts in batch for cost efficiency.
    """
    
    if not texts:
        return []
    
    try:
        client = openai.OpenAI()
        
        # Truncate texts to avoid token limits
        truncated_texts = [text[:8000] if text else "" for text in texts]
        
        response = client.embeddings.create(
            model=model,
            input=truncated_texts
        )
        
        embeddings = []
        for data in response.data:
            embeddings.append(np.array(data.embedding))
        
        logger.info(f"Generated {len(embeddings)} embeddings in batch")
        return embeddings
        
    except Exception as e:
        logger.warning(f"Batch embedding generation failed: {e}")
        # Fallback to individual generation
        return [generate_embedding(text) for text in texts]

def find_most_similar(query_embedding: np.ndarray, candidate_embeddings: List[np.ndarray], 
                     top_k: int = 5) -> List[tuple]:
    """
    Find the most similar embeddings to a query embedding.
    Returns list of (index, similarity_score) tuples.
    """
    
    similarities = []
    
    for i, candidate in enumerate(candidate_embeddings):
        if candidate is not None:
            similarity = calculate_similarity(query_embedding, candidate)
            similarities.append((i, similarity))
    
    # Sort by similarity score (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:top_k]

def semantic_search(query: str, documents: List[str], top_k: int = 5) -> List[dict]:
    """
    Perform semantic search over a collection of documents.
    Returns list of documents with similarity scores.
    """
    
    if not query or not documents:
        return []
    
    # Generate query embedding
    query_embedding = generate_embedding(query)
    if query_embedding is None:
        return []
    
    # Generate document embeddings
    doc_embeddings = batch_generate_embeddings(documents)
    
    # Find most similar documents
    similar_indices = find_most_similar(query_embedding, doc_embeddings, top_k)
    
    results = []
    for idx, score in similar_indices:
        results.append({
            'document': documents[idx],
            'similarity_score': score,
            'index': idx
        })
    
    return results

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text using simple frequency analysis.
    This is a fallback when more sophisticated NLP tools aren't available.
    """
    
    if not text:
        return []
    
    # Simple keyword extraction
    import re
    from collections import Counter
    
    # Remove punctuation and convert to lowercase
    clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = clean_text.split()
    
    # Filter out common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Filter words
    filtered_words = [
        word for word in words 
        if len(word) > 2 and word not in stop_words and word.isalpha()
    ]
    
    # Count frequency
    word_counts = Counter(filtered_words)
    
    # Return most common words
    keywords = [word for word, count in word_counts.most_common(max_keywords)]
    
    return keywords

def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    Create a simple extractive summary of text.
    This is a basic implementation for when advanced NLP isn't available.
    """
    
    if not text or len(text) < 100:
        return text
    
    # Split into sentences
    import re
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return text
    
    # Simple scoring based on sentence length and position
    scored_sentences = []
    
    for i, sentence in enumerate(sentences):
        score = 0
        
        # Length score (prefer medium-length sentences)
        length = len(sentence.split())
        if 10 <= length <= 30:
            score += 2
        elif 5 <= length <= 40:
            score += 1
        
        # Position score (prefer earlier sentences)
        if i < len(sentences) * 0.3:
            score += 2
        elif i < len(sentences) * 0.6:
            score += 1
        
        # Keyword score (prefer sentences with important words)
        important_words = ['important', 'key', 'main', 'primary', 'significant', 'critical']
        for word in important_words:
            if word in sentence.lower():
                score += 1
        
        scored_sentences.append((sentence, score))
    
    # Sort by score and take top sentences
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    top_sentences = scored_sentences[:max_sentences]
    
    # Sort by original order
    top_sentences.sort(key=lambda x: sentences.index(x[0]))
    
    summary = '. '.join([s[0] for s in top_sentences])
    return summary + '.' if not summary.endswith('.') else summary
