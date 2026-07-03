# services/search/semantic_search.py

from main import settings
from apps.db_models import RepositoryChunk, Repository
from services.repo.embeddings.embedding_model import embedding_model


def semantic_search(
    query: str,
    user_id: int,
    repo_id: str = None,
    top_k: int = 5,
):
    """
    Embed the query using the same model used at indexing time,
    then retrieve the top-k most similar chunks from the vector store
    using pgvector cosine distance.

    Args:
        query:   Natural-language search query.
        user_id: ID of the authenticated user (used to scope results
                 to repositories the user owns).
        repo_id: Optional UUID string — when supplied, search is
                 restricted to that single repository.
        top_k:   Maximum number of results to return.

    Returns:
        List of dicts, each containing:
            file, path, language, extension,
            chunk_index, content, score, repo_id
    """

    # 1. Embed the query (returns a list of floats)
    query_embedding = embedding_model.embed_query(query)

    session = settings.db.SessionLocal()

    try:

        # 2. Build the base query joining chunks → repositories so we
        #    can filter by user_id and (optionally) by repo_id.
        base_query = (
            session.query(
                RepositoryChunk,
                (
                    RepositoryChunk.embedding.cosine_distance(query_embedding)
                ).label("distance"),
            )
            .join(
                Repository,
                Repository.id == RepositoryChunk.repo_id,
            )
            .filter(Repository.user_id == user_id)
        )

        if repo_id:
            base_query = base_query.filter(
                RepositoryChunk.repo_id == repo_id
            )

        # 3. Order by distance ascending (closest = most similar)
        #    and limit to top_k results.
        rows = (
            base_query
            .order_by("distance")
            .limit(top_k)
            .all()
        )

        # 4. Convert distance (0 = identical, 2 = opposite) to a
        #    similarity score in [0, 1] that is intuitive for the UI.
        results = []

        for chunk, distance in rows:

            similarity = round(
                1.0 - (distance / 2.0),
                4,
            )

            results.append(
                {
                    "file": chunk.path,
                    "path": chunk.path,
                    "filename": chunk.filename,
                    "language": chunk.language or "unknown",
                    "extension": chunk.extension or "",
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "score": similarity,
                    "repo_id": str(chunk.repo_id),
                }
            )

        return results

    finally:
        session.close()
