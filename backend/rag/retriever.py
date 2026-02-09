from backend.rag.vector_store import VectorStore
from backend.granite.granite_client import granite_embeddings
from functools import lru_cache
from typing import List
import asyncio


vector_store = VectorStore()


# Query expansion for better retrieval
def expand_query(question: str) -> List[str]:
    """Expand query with synonyms and related terms"""
    expansions = [question.lower().strip()]
    
    # Add common synonyms and variations
    synonyms = {
        'fee': ['cost', 'price', 'tuition', 'charges', 'expenses'],
        'admission': ['enrollment', 'entry', 'application', 'selection'],
        'program': ['course', 'degree', 'curriculum', 'major'],
        'placement': ['job', 'employment', 'career', 'recruitment'],
        'facility': ['infrastructure', 'amenity', 'resource']
    }
    
    words = question.lower().split()
    for word in words:
        if word in synonyms:
            for synonym in synonyms[word]:
                variant = question.lower().replace(word, synonym)
                if variant not in expansions:
                    expansions.append(variant)
    
    return expansions[:3]  # Limit to top 3 variations

@lru_cache(maxsize=512)  # Increased cache size
def _cached_embed_query(question: str):
    """Cache query embeddings to avoid redundant API calls"""
    return tuple(granite_embeddings.embed_query(question))

def rerank_documents(question: str, docs, top_k: int = 5):
    """Rerank documents based on relevance and diversity"""
    if not docs or len(docs) <= top_k:
        return docs
    
    # Score documents based on multiple factors
    scored_docs = []
    for i, doc in enumerate(docs):
        score = 1.0 / (i + 1)  # Base ranking score
        
        # Boost score for documents with question keywords
        content_lower = doc.page_content.lower()
        question_words = question.lower().split()
        keyword_matches = sum(1 for word in question_words if word in content_lower)
        score += keyword_matches * 0.1
        
        # Boost score for longer, more informative content
        if len(doc.page_content) > 200:
            score += 0.05
            
        scored_docs.append((score, doc))
    
    # Sort by score and return top k
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored_docs[:top_k]]

async def retrieve_context_async(question: str, k: int = 6):
    """
    Enhanced async version with query expansion and reranking
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, retrieve_context, question, k)

def retrieve_context(question: str, k: int = 6):
    """
    Enhanced retrieval with query expansion, reranking, and better context assembly
    """
    if vector_store.store is None:
        return {"context": "", "sources": []}

    try:
        # Expand query for better retrieval
        query_variants = expand_query(question)
        all_docs = []
        
        # Search with multiple query variants
        for variant in query_variants:
            docs = vector_store.similarity_search(variant, k=k*2)  # Get more candidates
            all_docs.extend(docs)
        
        # Remove duplicates based on content
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            content_hash = hash(doc.page_content[:100])  # Hash first 100 chars
            if content_hash not in seen_content:
                unique_docs.append(doc)
                seen_content.add(content_hash)
        
        # Rerank and select best documents
        docs = rerank_documents(question, unique_docs, k)
        
    except Exception as e:
        print(f"Error in enhanced similarity search: {e}")
        return {
            "context": "I apologize, but I'm having trouble accessing the knowledge base right now.",
            "sources": []
        }
    
    # Extract context text with better formatting
    context_parts = []
    for doc in docs:
        content = doc.page_content.strip()
        if content and len(content) > 20:  # Skip very short chunks
            context_parts.append(content)
    
    context = "\n\n".join(context_parts)
    
    # Extract enhanced source information with deduplication
    sources = []
    seen_sources = set()
    
    for doc in docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        source_name = metadata.get('source', 'Unknown')
        
        # Skip duplicate sources
        if source_name in seen_sources:
            continue
        seen_sources.add(source_name)
        
        # Extract category from path (e.g., "backend/data/fees/tuition_fees.txt" -> "fees")
        path_parts = source_name.split('/')
        category = path_parts[-2] if len(path_parts) >= 2 else "general"
        filename = path_parts[-1] if path_parts else source_name
        
        # Create more informative snippet
        snippet = doc.page_content[:200].strip()
        if len(doc.page_content) > 200:
            last_period = snippet.rfind('.')
            if last_period > 100:  # Only truncate at sentence boundary if reasonable
                snippet = snippet[:last_period + 1]
            else:
                snippet += "..."
        
        sources.append({
            "category": category.title(),
            "filename": filename.replace('.txt', '').replace('_', ' ').title(),
            "snippet": snippet
        })
    
    return {"context": context, "sources": sources}
