# Recruitment Buddy - Technical Documentation

## Overview
The **Recruitment Buddy** module (`routes/recruitment_buddy.py`) is an AI-powered service designed to automate and enhance the candidate screening process. It analyzes resumes against job descriptions to provide a match score, extracted skills, and personalized interview questions.

## Technology Stack & Rationale

We chose a hybrid approach combining **Classical NLP**, **Statistical ML**, and **Generative AI** to balance performance, cost, and accuracy.

| Library | Purpose | Why we used it? |
|---------|---------|-----------------|
| **FastAPI** | Web Framework | High performance, native async support, and automatic OpenAPI documentation. |
| **Scikit-Learn** | Machine Learning | Used for `TfidfVectorizer` and `cosine_similarity`. It provides a robust, mathematical way to calculate text similarity without needing heavy deep learning models for every comparison. |
| **NLTK & Spacy** | NLP Preprocessing | `NLTK` handles efficient tokenization and stopword removal. `Spacy` provides industrial-strength NLP capabilities. |
| **PyPDF2 / docx2txt** | File Parsing | Robust extraction of raw text from user-uploaded PDF and DOCX resumes. |
| **Google Gemini** | Generative AI | Used for **Contextual Question Generation**. Unlike static templates, Gemini generates unique, deep technical questions based on the candidate's specific strengths. |

## Core Logic & Algorithms

### 1. Resume Parsing
- **Input**: Accepts PDF, DOCX, or plain text.
- **Process**: 
  - `extract_text_from_file` identifies the file type.
  - Converts binary content into a raw text string for analysis.
- **Why**: Standardizes all inputs into a common format for the NLP pipeline.

### 2. Skill Extraction (`extract_skills`)
- **Method**: Hybrid keyword matching + Regex.
- **Logic**: 
  - We maintain a curated list of high-value tech terms (`Python`, `React`, `AWS`, etc.).
  - The text is tokenized and lemmatized using `NLTK`.
  - We scan for exact matches and variations (e.g., "React.js" vs "React") to ensure improved recall.

### 3. Match Scoring Algorithm (`calculate_similarity`)
The final match score (0-100%) is a weighted average of two metrics:

1.  **Skill-Based Similarity (70% Weight)**: 
    - $\frac{\text{Matching Skills}}{\text{Total Required Skills}}$
    - *Rationale*: A candidate MUST have the core hard skills required for the job. This is the most critical factor.

2.  **Semantic Text Similarity (30% Weight)**:
    - Uses **TF-IDF (Term Frequency-Inverse Document Frequency)** to vectorize the Job Description and Resume.
    - Calculates the **Cosine Similarity** between these vectors.
    - *Rationale*: Captures the overall "vibe" and context (e.g., seniority, soft skills, domain language) that specific keywords might miss.

### 4. Interview Question Generation
- **Old Approach**: Static templates or simple NLP echoes (Removed).
- **New Approach**: **Generative AI (Gemini 2.5 Flash)**.
- **Workflow**:
  1. Identify candidate's **Strengths** (Intersection of Resume Skills & JD Skills).
  2. Send a prompt to Gemini: *"Generate a specific, technical interview question about {Skill}..."*
  3. **Result**: The team lead gets a unique, high-quality question that challenges the candidate's specific expertise, rather than a generic "Tell me about yourself."

## Future Improvements
- **Vector Database**: For searching through thousands of resumes instantly using embeddings (e.g., FAISS or PGVector).
- **Entity Recognition (NER)**: Training a custom Spacy model to extract "Years of Experience" or "University Names" more accurately.


