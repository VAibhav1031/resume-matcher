from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
import io
import base64
import logging
import re
import seaborn as sns
from typing import Dict, List, Optional, Tuple


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#  model  is here  brooo !!!!
MODEL = SentenceTransformer("all-mpnet-base-v2")  # Best general-purpose model


def get_embeddings(text: str) -> np.ndarray:
    """Get embeddings using Sentence Transformer"""
    try:
        return MODEL.encode(text)
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise


#  main thing here also where we do cosine similarity  for  things to  compre
def compute_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    # compute Cosine similarity is mostly used, her we are  doing simple  things is to compare the embeddings value from jon description to resume 
    try:
        similarity = cosine_similarity(
            np.array(embedding1).reshape(
                1, -1), np.array(embedding2).reshape(1, -1)
        )
        return round(similarity[0][0] * 100, 2)
    except Exception as e:
        logger.error(f"Error computing similarity: {str(e)}")
        raise



# extraction of the Keyword 
def extract_keywords(text: str, n: int = 10) -> List[str]:
    """Extract top keywords using TF-IDF
    Mostly you see this  
    """
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        sorted_indices = np.argsort(tfidf.toarray()).flatten()[::-1]
        return [feature_names[i] for i in sorted_indices[:n]]
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return []


def extract_section(text: str, section_name: str) -> Optional[str]:
    """Extract specific section from resume text with improved parsing"""
    try:
        match = re.search(
            rf"(?i)\b{
                section_name}\b[:\-]*\s*(.*?)(?=\n\s*\n|\Z)", text, re.DOTALL
        )
        return match.group(1).strip() if match else None
    except Exception as e:
        logger.error(f"Error extracting section {section_name}: {str(e)}")
        return None


# main visualization part
def generate_visualization(
    overall_score: float, section_scores: Dict[str, float], matched_keywords: List[str]
) -> str:
    """
    Generate professional visualization with:
    - Gauge chart for overall score
    - Bar chart for section scores
    - Returns base64 encoded image
    """
    # Set modern seaborn style
    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.figure(figsize=(14, 6))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#f8f9fa")

    # Gauge Chart
    def create_gauge(ax, score):
        ax.set_title("Overall Match Score", fontsize=14, pad=20)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        # Draw outer circle
        outer = Circle((0.5, 0.5), 0.4, color="lightgray",
                       fill=False, linewidth=10)
        ax.add_patch(outer)

        # Draw colored wedge
        color = "#FF5A5F" if score < 33 else "#FFB400" if score < 66 else "#00A699"
        wedge = Wedge(
            (0.5, 0.5), 0.4, 90, 90 - (score * 3.6), width=0.2, color=color, alpha=0.7
        )
        ax.add_patch(wedge)

        # Add score text
        ax.text(
            0.5,
            0.5,
            f"{score:.1f}%",
            ha="center",
            va="center",
            fontsize=24,
            fontweight="bold",
        )

        # Add labels
        ax.text(0.15, 0.2, "Low", fontsize=10)
        ax.text(0.5, 0.1, "Medium", fontsize=10)
        ax.text(0.8, 0.2, "High", fontsize=10)

    create_gauge(ax1, overall_score)

    # Bar Chart
    if section_scores:
        names = [name.capitalize() for name in section_scores.keys()]
        values = list(section_scores.values())

        bars = ax2.bar(
            names, values, color=["#4C72B0", "#DD8452", "#55A868", "#C44E52"], alpha=0.7
        )
        ax2.set_title("Section-wise Matching", fontsize=14, pad=20)
        ax2.set_ylim(0, 100)
        ax2.grid(axis="y", alpha=0.3)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f}%",
                ha="center",
                va="bottom",
            )

    plt.tight_layout()

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(
        buf, format="png", dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor()
    )
    plt.close(fig)
    buf.seek(0)

    return base64.b64encode(buf.read()).decode("utf-8")


def match_resume_to_job(resume_text: str, job_text: str) -> Dict[str, any]:
    """
    Compare resume against job description with detailed analysis
    Returns:
        {
            'overall_score': float,
            'section_scores': dict,
            'matched_keywords': list,
            'visualization': str (base64 image)
        }
    """
    try:
        # Get embeddings
        resume_emb = get_embeddings(resume_text)
        job_emb = get_embeddings(job_text)

        # Calculate similarity
        overall_score = compute_cosine_similarity(resume_emb, job_emb)

        # Section-wise analysis
        sections = {
            "skills": extract_section(resume_text, "skills"),
            "experience": extract_section(resume_text, "experience"),
            "education": extract_section(resume_text, "education"),
        }

        section_scores = {}
        for name, section_text in sections.items():
            if section_text:
                section_emb = get_embeddings(section_text)
                section_scores[name] = compute_cosine_similarity(
                    section_emb, job_emb)

        # Keyword matching
        resume_keywords = set(extract_keywords(resume_text, n=20))
        job_keywords = set(extract_keywords(job_text, n=20))
        matched_keywords = sorted(
            resume_keywords & job_keywords, key=lambda x: (len(x), x), reverse=True
        )[:15]  # Limit to top 15

        # Generate visualization
        viz_image = generate_visualization(
            overall_score, section_scores, matched_keywords
        )

        return {
            "overall_score": overall_score,
            "section_scores": section_scores,
            "matched_keywords": matched_keywords,
            "visualization": viz_image,
        }

    except Exception as e:
        logger.error(f"Error in resume matching: {str(e)}", exc_info=True)
        raise RuntimeError("Failed to process resume matching") from e
