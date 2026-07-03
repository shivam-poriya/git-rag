# services/repo/embeddings/embedding_model.py

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Singleton embedding model — uses Google's gemini-embedding-001 API.
# Same Gemini API key as the LLM; no local model download, no torch required.
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY", ""),
)