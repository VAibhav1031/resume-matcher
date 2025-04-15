from sentence_transformers import SentenceTransformer

# Load model once at import
model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embeddings(text):
    """Generate sentence embeddings using the loaded model."""
    embeddings = model.encode([text])
    return embeddings
