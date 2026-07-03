# services/chat/rag_chat.py

import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from main import settings
from apps.db_models import ChatMessage
from services.search.semantic_search import semantic_search



# ---------------------------------------------------------------------------
# System prompt — instructs the LLM on its role and how to use context
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert code analyst assistant called GitRAG.
You have been given relevant code snippets from the user's repository to help answer their question (if applicable).

Guidelines:
1. RESPONSE STYLE & LENGTH: Structure your responses to be comprehensive, detailed, and thoroughly explained, matching a conversational ChatGPT-like style. Avoid extremely short, single-sentence, or abrupt responses. Expand on explanations by detailing the underlying logic, code architecture, step-by-step instructions, and background context.
2. GREETINGS & CASUAL CHAT: If the user greets you (e.g. "hi", "hello", "how are you?") or starts a general casual conversation, respond naturally, politely, and warmly as a friendly assistant. Do not say "there is no information about this in the provided context" for greetings.
3. CONTEXT-BASED QUESTIONS: If the user's question relates to the provided repository/code context, answer using the context. Explain the implementation details, reference specific file names/paths, and use formatted code blocks to highlight relevant parts of the code.
4. OUT OF CONTEXT QUESTIONS: If the user asks a general question that is not covered by or related to the provided repository context, you must still answer it fully, thoroughly, and accurately using your general knowledge, but you MUST prefix your response with: "*(Note: This answer is not from the provided repository context)*\n\n".

Code context retrieved from the repository:
{context}
"""

CONTEXT_TOP_K = 5
HISTORY_WINDOW = 10  # last N messages to include for conversation memory


def _load_history(
    session_id: str,
    session,
) -> list:
    """
    Load the last HISTORY_WINDOW messages for a session and convert them
    to LangChain message objects for the prompt.
    """
    rows = (
        session.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_WINDOW)
        .all()
    )

    # Reverse so oldest-first for correct conversation order
    rows = list(reversed(rows))

    history = []
    for row in rows:
        if row.role == "user":
            history.append(HumanMessage(content=row.content))
        else:
            history.append(AIMessage(content=row.content))

    return history


def _build_context_block(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a readable context string for the prompt.
    """
    if not chunks:
        return "No relevant code chunks were found in this repository."

    blocks = []
    for i, chunk in enumerate(chunks, 1):
        score_pct = round(chunk["score"] * 100)
        header = (
            f"--- Chunk {i} | File: {chunk['file']} "
            f"| Language: {chunk['language']} "
            f"| Relevance: {score_pct}% ---"
        )
        blocks.append(f"{header}\n{chunk['content']}")

    return "\n\n".join(blocks)


def rag_chat(
    query: str,
    repo_id: str,
    session_id: str,
    user_id: int,
) -> dict:
    """
    Core RAG pipeline:

    1. Retrieve top-k relevant code chunks from the selected repository.
    2. Load recent conversation history for context continuity.
    3. Build a LangChain prompt with system instructions + context + history.
    4. Call Gemini and return the answer + list of source file paths.

    Args:
        query:      The user's natural language question.
        repo_id:    UUID of the repository to search within.
        session_id: UUID of the active chat session (for history loading).
        user_id:    ID of the authenticated user (for scoping the search).

    Returns:
        dict with keys:
            "answer"  : str — the LLM's response
            "sources" : list[str] — unique file paths of retrieved chunks
    """

    # 1. Semantic search — retrieve relevant code chunks
    chunks = semantic_search(
        query=query,
        user_id=user_id,
        repo_id=repo_id,
        top_k=CONTEXT_TOP_K,
    )

    context_block = _build_context_block(chunks)

    unique_sources = list(
        dict.fromkeys(
            chunk["file"] for chunk in chunks
        )
    )

    # 2. Load conversation history from DB
    db_session = settings.db.SessionLocal()

    try:
        history = _load_history(session_id, db_session)
    finally:
        db_session.close()

    # 3. Build LangChain prompt
    #    We structure it as: system (with context) + history + current question
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            *[
                (
                    "human" if isinstance(msg, HumanMessage) else "ai",
                    msg.content,
                )
                for msg in history
            ],
            ("human", "{question}"),
        ]
    )

    # 4. Initialise the Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": context_block,
            "question": query,
        }
    )

    answer = response.content

    return {
        "answer": answer,
        "sources": unique_sources,
    }
