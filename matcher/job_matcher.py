from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from matcher.model_utils import get_embeddings  # moved here


def compute_cosine_similarity(embedding1, embedding2):
    """Compute the cosine similarity between two embeddings."""
    # Flatten embeddings to 1D arrays for cosine similarity
    embedding1 = np.array(embedding1).flatten().reshape(1, -1)
    embedding2 = np.array(embedding2).flatten().reshape(1, -1)

    similarity = cosine_similarity(embedding1, embedding2)
    return similarity[0][0] * 100  # Return as percentage


def match_resume_to_job(resume_text, job_description_text):
    """Compare resume against job description using cosine similarity."""
    # Get embeddings for the resume and job description
    resume_embeddings = get_embeddings(resume_text)
    job_description_embeddings = get_embeddings(job_description_text)

    # Compute similarity score
    similarity_score = compute_cosine_similarity(
        resume_embeddings, job_description_embeddings
    )

    return similarity_score
