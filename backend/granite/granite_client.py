import time
import requests
from typing import List
try:
    from backend.config import settings
except ImportError:
    from config import settings
from langchain_core.embeddings import Embeddings

# Use local embeddings to avoid API quota issues
LOCAL_EMBEDDINGS_AVAILABLE = True
embedding_model = None  # Lazy load only when needed


def _get_embedding_model():
    """Lazy load the embedding model only when first needed"""
    global embedding_model
    
    if embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use a lightweight, fast model for embeddings
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded local embedding model: all-MiniLM-L6-v2")
        except ImportError:
            print("⚠️ sentence-transformers not available. Install with: pip install sentence-transformers")
            embedding_model = False
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            embedding_model = False
    
    return embedding_model if embedding_model is not False else None


class GraniteClient(Embeddings):
    """Simple, reliable IBM Granite client for chat and embeddings"""

    def __init__(self):
        self.api_key = settings.IBM_CLOUD_API_KEY
        self.project_id = settings.IBM_PROJECT_ID
        self.base_url = "https://us-south.ml.cloud.ibm.com"
        self._access_token = None
        self._token_expiry = 0

    def _get_iam_token(self):
        """Get IBM Cloud IAM access token"""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        response = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        self._token_expiry = time.time() + int(data["expires_in"]) - 60

        return self._access_token

    def generate_embedding(self, text: str):
        """Generate high-quality embeddings using local model"""
        if LOCAL_EMBEDDINGS_AVAILABLE:
            try:
                model = _get_embedding_model()
                if model is not None:
                    # Normalize text for better embeddings
                    normalized_text = text.strip().lower()
                    embedding = model.encode(normalized_text, convert_to_tensor=False, normalize_embeddings=True)
                    return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            except Exception as e:
                print(f"Local embedding error: {e}")
        
        # Fallback to dummy embedding
        return [0.0] * 384
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents (required by Embeddings interface)"""
        return [self.generate_embedding(text) for text in texts]

    def generate_chat_response(self, prompt: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Simple, reliable chat response using IBM Granite"""
        try:
            access_token = self._get_iam_token()
            
            chat_url = f"{self.base_url}/ml/v1/text/generation?version=2024-05-01"
            
            payload = {
                "model_id": "ibm/granite-3-8b-instruct",
                "input": prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "stop_sequences": ["\n\n", "User:", "Human:"]
                },
                "project_id": self.project_id
            }
            
            response = requests.post(
                chat_url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('results', [{}])[0].get('generated_text', '')
                return generated_text.strip()
            else:
                print(f"Granite API error: {response.status_code} - {response.text}")
                return self._simple_fallback_response(prompt)
                
        except Exception as e:
            print(f"Granite chat error: {e}")
            return self._simple_fallback_response(prompt)

    def _simple_fallback_response(self, prompt: str) -> str:
        """Simple, helpful fallback responses"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["hi", "hello", "hey", "namaste"]):
            return "Hello! I'm here to help you with questions about Vishwakarma University. What would you like to know?"
        elif "fee" in prompt_lower or "cost" in prompt_lower:
            return "For current fee information, please contact the Vishwakarma University admissions office or visit the official website for accurate details."
        elif "admission" in prompt_lower:
            return "For admission requirements and procedures, please visit the Vishwakarma University website or contact the admissions office directly."
        elif "program" in prompt_lower or "course" in prompt_lower:
            return "Vishwakarma University offers various undergraduate and postgraduate programs. Please check the official website or contact the university for detailed program information."
        else:
            return "I'm here to help with questions about Vishwakarma University! Could you please be more specific about what you'd like to know? I can help with programs, admissions, facilities, and more."

    def generate_chat_stream(self, prompt: str, max_tokens: int = 1500):
        """Generate streaming chat response for real-time user experience"""
        try:
            # Try Granite API first
            response = self.generate_chat_response(prompt, max_tokens)
            
            # Simulate streaming by breaking response into tokens
            if response:
                words = response.split()
                for i, word in enumerate(words):
                    if i == 0:
                        yield word
                    else:
                        yield " " + word
            
        except Exception as e:
            print(f"Streaming error: {e}")
            fallback = self._simple_fallback_response(prompt)
            words = fallback.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield " " + word
    
    def embed_query(self, text: str) -> List[float]:
        """Alias for generate_embedding for compatibility"""
        return self.generate_embedding(text)

    def __call__(self, text: str) -> List[float]:
        return self.embed_query(text)


# Backward compatibility 
granite_embeddings = GraniteClient()
granite_client = GraniteClient()