from sentence_transformers import SentenceTransformer

# Initialize the model
model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embeddings(text):
    # Generate the sentence embeddings
    embeddings = model.encode([text])
    return embeddings
