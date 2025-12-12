from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, status
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any, List, Union
import json
import os
import uuid
import tempfile
import re
import spacy
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import PyPDF2
import docx2txt
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Optional
from auth.jwt_bearer import JWTBearer
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from services.ai_service import generate_interview_question_gemini

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
try:
    nltk.download('punkt_tab')
except:
    print("punkt_tab not found, but continuing with standard tokenizer")
# Initialize spaCy for NLP
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # If the model is not found, download it
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")



# Initialize NLTK components
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

executor = ThreadPoolExecutor(max_workers=4), Optional

router = APIRouter()

# In-memory storage for demonstration
# In production, use a database
recruitment_data = {}

# ML Models and Vectorizers
class MLModels:
    def __init__(self):
        self.jd_vectorizer = TfidfVectorizer(stop_words='english')
        self.resume_vectorizer = TfidfVectorizer(stop_words='english')
        self.job_categories = [
            "Data Science", "Software Engineering", "DevOps", "Product Management",
            "UX/UI Design", "Data Engineering", "Machine Learning", "Cybersecurity"
        ]
        self.tech_skills = [
            # Languages
            "Python", "JavaScript", 
            # Frameworks
            "Node.js", "React", "Next.js", "Flask", "FastAPI", "LLM", "LLMs",
            # Databases
            "MySQL", "MongoDB",
            # Tools
            "Git", "JIRA", "Google Colab",
            # Technologies
            "Machine Learning", "API Development", "NLP"
        ]
        
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for ML processing."""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords and lemmatize
        tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
        return ' '.join(tokens)

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using flexible matching."""
        text_lower = text.lower()
        found_skills = []
        
        # Check for each skill with flexible matching
        for skill in self.tech_skills:
            # Convert skill to lowercase for case-insensitive matching
            skill_lower = skill.lower()
            
            # Check for exact match or word boundary match
            if (f" {skill_lower} " in f" {text_lower} " or  # Word boundary
                f"{skill_lower}," in text_lower or          # Followed by comma
                f"{skill_lower}." in text_lower or          # Followed by period
                f" {skill_lower}" in f" {text_lower}"):     # At end of text
                found_skills.append(skill)  # Add the original case version
                continue
                
            # Check for framework/library names (e.g., "React" in "React.js")
            if any(term in text_lower for term in [f"{skill_lower}.", f"{skill_lower} ", f" {skill_lower}"]):
                found_skills.append(skill)
                continue
                
        # Additional handling for common variations
        skill_variations = {
            "node": "Node.js",
            "react": "React",
            "next": "Next.js",
            "fastapi": "FastAPI",
            "flask": "Flask",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "git": "Git",
            "jira": "JIRA",
            "nlp": "NLP",
            "llm": "LLM",
            "llms": "LLM"
        }
        
        for variation, skill_name in skill_variations.items():
            if (variation in text_lower and 
                skill_name not in found_skills and 
                skill_name in self.tech_skills):
                found_skills.append(skill_name)
        
        return list(set(found_skills))  # Remove duplicates
    
    def extract_skills_bkp(self, text: str) -> List[str]:
        """Extract skills from text using keyword matching."""
        text = text.lower()
        return [skill for skill in self.tech_skills if skill.lower() in text]
    
    def calculate_similarity_BKP(self, jd_text: str, resume_text: str) -> float:
        """Calculate similarity between job description and resume."""
        # Preprocess texts
        jd_processed = self.preprocess_text(jd_text)
        resume_processed = self.preprocess_text(resume_text)
        
        # Create TF-IDF vectors
        try:
            jd_vector = self.jd_vectorizer.fit_transform([jd_processed])
            resume_vector = self.resume_vectorizer.fit_transform([resume_processed])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(jd_vector, resume_vector)[0][0]
            return min(1.0, max(0.0, similarity)) * 100  # Convert to percentage
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def calculate_similarity(self, jd_text: str, resume_text: str) -> float:
        """Calculate similarity between job description and resume."""
        # Extract skills from both texts
        jd_skills = set(self.extract_skills(jd_text))
        resume_skills = set(self.extract_skills(resume_text))
        
        # If no skills found in either text, fall back to text similarity
        if not jd_skills or not resume_skills:
            return self._calculate_text_similarity(jd_text, resume_text)
        
        # Calculate skill-based similarity
        if not jd_skills:  # Avoid division by zero
            return 0.0
            
        matching_skills = jd_skills.intersection(resume_skills)
        skill_similarity = (len(matching_skills) / len(jd_skills)) * 100
        
        # Also calculate text similarity and combine both
        text_similarity = self._calculate_text_similarity(jd_text, resume_text)
        
        # Weighted average (70% skill match, 30% text match)
        return (skill_similarity * 0.7) + (text_similarity * 0.3)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Helper method to calculate text similarity using TF-IDF."""
        try:
            # Preprocess texts
            text1_processed = self.preprocess_text(text1)
            text2_processed = self.preprocess_text(text2)
            
            # Create TF-IDF vectors
            jd_vector = self.jd_vectorizer.fit_transform([text1_processed])
            resume_vector = self.resume_vectorizer.fit_transform([text2_processed])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(jd_vector, resume_vector)[0][0]
            return min(1.0, max(0.0, similarity)) * 100  # Convert to percentage
        except Exception as e:
            print(f"Error calculating text similarity: {e}")
            return 0.0

    def generate_questions(self, jd_text: str, resume_text: str, num_questions: int = 5) -> List[str]:
        """Generate interview questions based on candidate's strengths and skills using AI."""
        try:
            # Extract skills from both texts
            jd_skills = set(self.extract_skills(jd_text))
            resume_skills = set(self.extract_skills(resume_text))
            
            # Get matching skills (strengths)
            strengths = list(jd_skills.intersection(resume_skills))
            
            # If no strengths found, return empty list
            if not strengths:
                return []
                
            # Get context from resume (first 1000 chars) for better questions
            context = ' '.join(resume_text[:1000].split())
            
            questions = []
            
            # Generate questions for each strength
            # Shuffle strengths to get variety if we have more strengths than needed
            import random
            random.shuffle(strengths)
            
            for skill in strengths[:num_questions]:
                try:
                    question = generate_interview_question_gemini(skill, context)
                    questions.append(question)
                except Exception as e:
                    print(f"Error generating question for {skill}: {e}")
                    questions.append(f"Can you describe a challenging {skill} problem you've solved and how you approached it?")

            return questions[:num_questions]

        except Exception as e:
            print(f"Error in generate_questions: {e}")
            # Fallback to simple questions if there's an error
            return [f"Can you tell me about your experience with {skill}?" for skill in strengths[:num_questions]] if 'strengths' in locals() else []

    def generate_questions1(self, jd_text: str, resume_text: str, num_questions: int = 5) -> List[str]:
        """Generate interview questions based on candidate's strengths and skills."""
        # Extract skills from both texts
        jd_skills = set(self.extract_skills(jd_text))
        resume_skills = set(self.extract_skills(resume_text))
        
        # Get matching skills (strengths)
        strengths = list(jd_skills.intersection(resume_skills))
        
        # If no strengths found, return empty list
        if not strengths:
            return []
            
        # Question templates specific to skills/strengths
        skill_question_templates = [
            "Can you walk us through a challenging {0} project you've worked on?",
            "How do you stay current with the latest developments in {0}?",
            "Can you describe a time when you had to solve a complex problem using {0}?",
            "What {0} best practices do you follow in your development workflow?",
            "How would you explain {0} to a non-technical stakeholder?",
            "What's your approach to debugging issues in {0}?",
            "Can you compare different tools or frameworks you've used for {0}?",
            "How do you ensure code quality when working with {0}?"
        ]
        
        # Generate questions based on strengths
        questions = []
        for i in range(min(num_questions, len(strengths))):
            for template in skill_question_templates:
                if len(questions) >= num_questions:
                    break
                questions.append(template.format(strengths[i]))
        
        # If we still need more questions, use the remaining strengths with general templates
        if len(questions) < num_questions:
            remaining_templates = [
                "What's your experience with {0}?",
                "How would you approach learning a new aspect of {0}?",
                "What resources would you recommend for someone starting with {0}?"
            ]
            
            for strength in strengths:
                for template in remaining_templates:
                    if len(questions) >= num_questions:
                        break
                    question = template.format(strength)
                    if question not in questions:  # Avoid duplicates
                        questions.append(question)
        
        return questions[:num_questions]

# Initialize ML models
ml_models = MLModels()

class JobDescription(BaseModel):
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Detailed job description")
    requirements: List[str] = Field(..., description="List of required skills and qualifications")
    responsibilities: List[str] = Field(default_factory=list, description="List of job responsibilities")
    location: str = Field(..., description="Job location")
    job_type: str = Field("Full-time", description="Type of employment (Full-time, Part-time, Contract, etc.)")
    salary_range: Optional[str] = Field(None, description="Salary range for the position")
    experience_required: Optional[str] = Field(None, description="Required years of experience")
    company_name: Optional[str] = Field(None, description="Name of the hiring company")
    industry: Optional[str] = Field(None, description="Industry of the company")
    remote_work: bool = Field(False, description="Whether remote work is available")

class ResumeAnalysisRequest(BaseModel):
    job_description: JobDescription
    resume_text: Optional[str] = Field(None, description="Text content of the resume")
    resume_file: Optional[UploadFile] = Field(None, description="Resume file (PDF, DOCX, or TXT)")

class MatchResult(BaseModel):
    match_score: float = Field(..., description="Overall match score (0-100)")
    skills_match: Dict[str, float] = Field(..., description="Match score for each skill")
    strengths: List[str] = Field(..., description="Candidate's strengths based on the job requirements")
    weaknesses: List[str] = Field(..., description="Areas where the candidate may be lacking")
    missing_skills: List[str] = Field(..., description="Required skills not found in the resume")
    recommended_questions: List[str] = Field(..., description="Customized interview questions")
    suggested_pitch: str = Field(..., description="Personalized pitch for the candidate")
    job_fit: str = Field(..., description="Summary of how well the candidate fits the role")
    red_flags: List[str] = Field(default_factory=list, description="Potential concerns about the candidate")
    experience_match: float = Field(..., description="How well the candidate's experience matches the requirements (0-100)")
    skill_gaps: Dict[str, str] = Field(..., description="Areas where additional training might be needed")

class ResumeData(BaseModel):
    text: str = Field(..., description="Extracted text from resume")
    skills: List[str] = Field(default_factory=list, description="List of skills found in resume")
    experience: List[Dict[str, str]] = Field(default_factory=list, description="List of work experiences")
    education: List[Dict[str, str]] = Field(default_factory=list, description="List of education entries")

class JobAnalysis(BaseModel):
    skills: List[str] = Field(..., description="List of required skills")
    experience_level: str = Field(..., description="Inferred experience level (junior/mid/senior)")
    key_responsibilities: List[str] = Field(..., description="Key responsibilities")
    technical_terms: List[str] = Field(..., description="Technical terms and technologies mentioned")

class SkillsMatchRequest(BaseModel):
    required_skills: List[str] = Field(..., description="List of required skills")
    candidate_skills: List[str] = Field(..., description="List of candidate's skills")

class SkillsMatchResult(BaseModel):
    match_score: float = Field(..., description="Overall match score (0-100)")
    matching_skills: List[str] = Field(..., description="Skills that match")
    missing_skills: List[str] = Field(..., description="Skills that are missing")
    match_percentage: float = Field(..., description="Percentage of required skills matched")

class SkillGapAnalysis(BaseModel):
    gaps: Dict[str, str] = Field(..., description="Skill gaps with suggested training resources")
    improvement_areas: List[str] = Field(..., description="Areas for skill development")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in the gap analysis (0-100)")
    recommendations: List[str] = Field(..., description="Specific recommendations for skill development")
    priority_areas: List[str] = Field(..., description="High-priority areas for immediate attention")
    timeline: str = Field(..., description="Estimated timeline for skill development (e.g., 3-6 months)")

async def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from uploaded file (PDF, DOCX, or TXT)."""
    content = await file.read()
    file_extension = file.filename.split('.')[-1].lower()
    
    try:
        if file_extension == 'pdf':
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        elif file_extension == 'docx':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                text = docx2txt.process(temp_file_path)
                return text
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        else:  # Assume plain text
            return content.decode('utf-8')
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

class MatchResult(BaseModel):
    match_score: float
    strengths: List[str]
    weaknesses: List[str]
    missing_skills: List[str]
    recommended_questions: List[str]
    suggested_pitch: str



@router.post("/analyze-resume", response_model=MatchResult, tags=["Recruitment Buddy"])
async def analyze_resume(
    job_description: str = Form(..., description="Job description text"),
    resume_file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    token: str = Depends(JWTBearer())
):
    try:
        # Extract text from resume
        resume_text = await extract_text_from_file(resume_file)
        
        # Extract skills from both job description and resume
        jd_skills = set(ml_models.extract_skills(job_description))
        resume_skills = set(ml_models.extract_skills(resume_text))
        
        # Calculate matching and missing skills
        matching_skills = list(jd_skills.intersection(resume_skills))
        missing_skills = list(jd_skills - resume_skills)
        
        # Calculate match score
        match_score = ml_models.calculate_similarity(job_description, resume_text)
        
        # Generate strengths and weaknesses
        strengths = matching_skills[:3] if matching_skills else ["Strong educational background"]
        weaknesses = [f"Could benefit from more experience with {skill}" for skill in missing_skills[:2]]
        
        # Generate interview questions
        questions = ml_models.generate_questions(job_description, resume_text, num_questions=5)
        
        # Generate personalized pitch
        pitch = (
            f"We're impressed with your background in {', '.join(strengths[:2]) if strengths else 'relevant technologies'}. "
            "Your experience aligns well with this position. "
            "We'd love to discuss how your skills can contribute to our team."
        )
        
        # Calculate skill match percentages
        skills_match = {skill: 100.0 if skill in matching_skills else 0.0 
                       for skill in jd_skills}
        
        # Generate job fit summary
        job_fit = (
            f"The candidate shows a {match_score:.1f}% match with the job requirements. "
            f"{'They have strong experience in ' + ', '.join(strengths[:2]) + '.' if strengths else ''} "
            f"{'They could benefit from additional experience in ' + ', '.join(missing_skills[:2]) + '.' if missing_skills else ''}"
        )
        
        # Identify potential red flags
        red_flags = []
        if len(missing_skills) > len(jd_skills) * 0.7:  # More than 70% skills missing
            red_flags.append("Significant number of required skills are missing")
        
        # Calculate experience match
        experience_match = min(100, (len(matching_skills) / max(1, len(jd_skills))) * 100)
        
        # Identify skill gaps
        skill_gaps = {
            skill: "Consider additional training or certification" 
            for skill in missing_skills
        }
        
        return {
            "match_score": round(match_score, 2),
            "skills_match": skills_match,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_skills": missing_skills,
            "recommended_questions": questions,
            "suggested_pitch": pitch,
            "job_fit": job_fit,
            "red_flags": red_flags,
            "experience_match": round(experience_match, 2),
            "skill_gaps": skill_gaps
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        
@router.post("/analyze-resume1", response_model=MatchResult, tags=["Recruitment Buddy"])
async def analyze_resume(
    job_description: str = Form(..., description="Job description text"),
    resume_file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    token: str = Depends(JWTBearer())
):
    """
    Analyze a resume against a job description using ML and provide detailed matching analysis.
    
    This endpoint:
    1. Extracts text from the uploaded resume
    2. Analyzes the content using NLP
    3. Compares against the job description
    4. Returns a comprehensive analysis
    """
    try:
        # Extract text from resume
        resume_text = await extract_text_from_file(resume_file)
        
        # Process with ML models
        match_score = ml_models.calculate_similarity(job_description, resume_text)
        
        # Extract skills from resume and job description
        resume_skills = ml_models.extract_skills(resume_text)
        job_skills = ml_models.extract_skills(job_description)
        
        # Calculate skill matches
        matching_skills = list(set(resume_skills) & set(job_skills))
        missing_skills = list(set(job_skills) - set(resume_skills))
        
        # Generate strengths and weaknesses
        strengths = matching_skills[:3] if matching_skills else ["Strong educational background"]
        weaknesses = [f"Could benefit from more experience with {skill}" for skill in missing_skills[:2]]
        
        # Generate interview questions
        questions = ml_models.generate_questions(job_description, resume_text, num_questions=5)
        
        # Generate personalized pitch
        pitch = (
            f"We're impressed with your background in {', '.join(strengths[:2])}. "
            f"Your experience aligns well with this position. "
            "We'd love to discuss how your skills can contribute to our team."
        )
        
        # Calculate skill match percentages
        skills_match = {skill: 100.0 if skill in matching_skills 
                       else 0.0 for skill in job_skills}
        
        # Generate job fit summary
        job_fit = (
            f"The candidate shows a {match_score:.1f}% match with the job requirements. "
            f"They have strong experience in {', '.join(strengths[:2])} but could benefit from "
            f"additional experience in {', '.join(missing_skills[:2]) if missing_skills else 'various areas'}."
        )
        
        # Identify potential red flags
        red_flags = []
        if len(missing_skills) > len(job_skills) * 0.7:  # More than 70% skills missing
            red_flags.append("Significant number of required skills are missing")
        if "bachelor" not in resume_text.lower() and "master" not in resume_text.lower():
            red_flags.append("Formal education not clearly specified")
            
        # Calculate experience match (simplified)
        experience_match = min(100, len(matching_skills) / max(1, len(job_skills)) * 100)
        
        # Identify skill gaps
        skill_gaps = {
            skill: "Consider additional training or certification" 
            for skill in missing_skills
        }
        
        return {
            "match_score": round(match_score, 2),
            "skills_match": skills_match,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_skills": missing_skills,
            "recommended_questions": questions,
            "suggested_pitch": pitch,
            "job_fit": job_fit,
            "red_flags": red_flags,
            "experience_match": round(experience_match, 2),
            "skill_gaps": skill_gaps
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_ai_enhanced_proposal(
    job_title: str,
    candidate_name: str,
    company_name: str,
    key_qualifications: List[str],
    job_description: str,
    candidate_background: str
) -> str:
    """Generate a more personalized proposal using NLP techniques."""
    # In a production environment, you might use an LLM here
    # This is a simplified version that uses templates and basic NLP
    
    # Extract key aspects from job description
    doc = nlp(job_description[:10000])  # Limit to first 10k chars for performance
    key_aspects = [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) > 1]
    
    # Generate personalized introduction
    intro_phrases = [
        f"We were particularly impressed by your experience in {key_qualifications[0]} and {key_qualifications[1]}.",
        f"Your background in {key_qualifications[0]} makes you a strong candidate for this role.",
        f"Your expertise in {', '.join(key_qualifications[:2])} aligns perfectly with our requirements.",
    ]
    
    # Generate value proposition
    value_props = [
        f"Opportunity to work with cutting-edge {key_aspects[0] if key_aspects else 'technologies'}",
        "Competitive compensation and benefits package",
        "Flexible work arrangements and professional development opportunities"
    ]
    
    # Generate call-to-action
    ctas = [
        "We'd love to schedule a call to discuss this opportunity in more detail.",
        "Please let us know your availability for a brief conversation about this role.",
        "We're excited about the possibility of you joining our team and would love to chat further."
    ]
    
    # Compose the proposal
    proposal = f"""Subject: Exciting Opportunity - {job_title} at {company_name}

Dear {candidate_name},

I hope this message finds you well. I'm reaching out from {company_name} regarding the {job_title} position. {intro}

About the Role:
{job_summary}

Why You're a Great Fit:
• {qualifications}

What We Offer:
• {benefits}

{cta}

Looking forward to your response.

Best regards,
[Your Name]
{company_name} Talent Acquisition
""".format(
        candidate_name=candidate_name,
        company_name=company_name,
        job_title=job_title,
        intro=np.random.choice(intro_phrases),
        job_summary=job_description[:200] + "..." if len(job_description) > 200 else job_description,
        qualifications='\n• '.join(key_qualifications[:3]),
        benefits='\n• '.join(value_props),
        cta=np.random.choice(ctas)
    )
    
    return proposal

@router.post("/generate-proposal", tags=["Recruitment Buddy"])
async def generate_proposal(
    job_title: str = Form(...),
    candidate_name: str = Form(...),
    company_name: str = Form(...),
    key_qualifications: List[str] = Form(...),
    job_description: str = Form(...),
    candidate_background: str = Form(""),
    token: str = Depends(JWTBearer())
):
    """
    Generate a personalized recruitment proposal for a candidate using AI.
    
    This endpoint generates a professional and personalized proposal that can be sent to candidates,
    incorporating details from the job description and candidate's background.
    """
    try:
        # Generate AI-enhanced proposal
        proposal = await generate_ai_enhanced_proposal(
            job_title=job_title,
            candidate_name=candidate_name,
            company_name=company_name,
            key_qualifications=key_qualifications,
            job_description=job_description,
            candidate_background=candidate_background
        )
        
        return JSONResponse(content={"proposal": proposal})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_technical_questions(skill: str, level: str) -> List[str]:
    """Generate technical questions based on skill and experience level."""
    base_questions = {
        'junior': [
            f"Can you explain what {skill} is and how you've used it?",
            f"What are the basic concepts of {skill} that you're familiar with?",
            f"Can you describe a simple project where you used {skill}?"
        ],
        'mid-level': [
            f"How would you optimize a {skill} implementation for better performance?",
            f"Can you explain a challenge you faced with {skill} and how you solved it?",
            f"How do you ensure code quality when working with {skill}?"
        ],
        'senior': [
            f"How would you design a scalable architecture using {skill}?",
            f"What are the limitations of {skill} and how have you worked around them?",
            f"How would you mentor a junior developer learning {skill}?"
        ]
    }
    
    level = level.lower()
    if level not in base_questions:
        level = 'mid-level'
        
    return base_questions[level]

@router.post("/interview-questions", tags=["Recruitment Buddy"])
async def generate_interview_questions(
    job_title: str = Form(...),
    experience_level: str = Form("mid-level"),
    technical_skills: List[str] = Form(default_factory=list),
    job_description: Optional[str] = Form(None),
    resume_text: Optional[str] = Form(None),
    token: str = Depends(JWTBearer())
):
    """
    Generate a comprehensive set of interview questions using ML and NLP.
    
    This endpoint generates:
    - Technical questions based on required skills
    - Behavioral questions based on experience level
    - Role-specific questions from job description
    - Personalized questions based on candidate's background
    """
    try:
        questions = []
        
        # 1. Add role-specific questions
        role_questions = [
            f"Can you walk us through your experience with {job_title} positions?",
            f"What interests you most about this {job_title} role?",
            f"How does your experience align with the responsibilities of a {job_title}?"
        ]
        questions.extend(role_questions)
        
        # 2. Add technical questions for each skill
        for skill in technical_skills[:5]:  # Limit to top 5 skills
            skill_questions = generate_technical_questions(skill, experience_level)
            questions.extend(skill_questions)
        
        # 3. Add behavioral questions based on experience level
        behavioral_questions = {
            'junior': [
                "Tell me about a time you learned a new technology quickly.",
                "Describe a challenging problem you solved during your studies or internships.",
                "How do you handle feedback on your code?"
            ],
            'mid-level': [
                "Describe a complex project you worked on and your role in it.",
                "How do you handle disagreements with team members about technical decisions?",
                "Can you tell us about a time you had to refactor or improve existing code?"
            ],
            'senior': [
                "How do you approach making architectural decisions?",
                "Describe your experience mentoring junior developers.",
                "How do you balance technical debt with delivering new features?"
            ]
        }
        
        level = experience_level.lower()
        if level not in behavioral_questions:
            level = 'mid-level'
        questions.extend(behavioral_questions[level])
        
        # 4. Add questions based on job description (if provided)
        if job_description:
            # Extract key terms using NLP
            doc = nlp(job_description[:10000])  # Limit to first 10k chars
            key_terms = [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) <= 3]
            
            for term in key_terms[:3]:  # Use top 3 key terms
                questions.append(f"How does your experience relate to {term}?")
        
        # 5. Add personalized questions based on resume (if provided)
        if resume_text:
            # Extract potential talking points
            resume_doc = nlp(resume_text[:5000])  # First 5k chars to avoid too much processing
            
            # Look for projects, technologies, and achievements
            projects = [ent.text for ent in resume_doc.ents if ent.label_ in ['ORG', 'PRODUCT', 'TECH']]
            
            for project in projects[:2]:  # Ask about up to 2 projects
                questions.append(f"Can you tell me more about your work on {project}?")
        
        # Shuffle questions for variety
        np.random.shuffle(questions)
        
        # Limit to 15 questions max
        questions = questions[:15]
        
        # Categorize questions
        categorized_questions = {
            "technical": [q for q in questions if any(skill.lower() in q.lower() for skill in technical_skills)],
            "behavioral": [q for q in questions if q not in [*questions[:3], *[q for q in questions if any(skill.lower() in q.lower() for skill in technical_skills)]]],
            "role_specific": role_questions
        }
        
        return JSONResponse(content={
            "questions": questions,
            "categorized_questions": categorized_questions,
            "total_questions": len(questions)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-resume", response_model=ResumeData, tags=["Recruitment Buddy"])
async def parse_resume(
    resume_file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    token: str = Depends(JWTBearer())
):
    """
    Parse a resume and extract structured information.
    
    This endpoint extracts:
    - Contact information
    - Skills
    - Work experience
    - Education
    - Certifications
    """
    try:
        # Extract text from resume
        resume_text = await extract_text_from_file(resume_file)
        
        # Extract skills
        skills = ml_models.extract_skills(resume_text)
        
        # Simple pattern matching for experience and education
        # In a production environment, you would use more sophisticated NLP
        experience = []
        education = []
        
        # Look for common section headers
        lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
        
        # Simple state machine to parse sections
        current_section = None
        for line in lines:
            line_lower = line.lower()
            
            # Check for section headers
            if any(header in line_lower for header in ["experience", "work history", "employment"]):
                current_section = "experience"
                continue
            elif any(header in line_lower for header in ["education", "academic"]):
                current_section = "education"
                continue
            elif any(header in line_lower for header in ["skills", "technical skills"]):
                current_section = "skills"
                continue
                
            # Parse content based on current section
            if current_section == "experience" and len(line) > 10:  # Simple heuristic
                # Try to extract company and duration
                parts = re.split(r'\s+-\s+', line, maxsplit=1)
                if len(parts) == 2:
                    experience.append({
                        "company": parts[0].strip(),
                        "details": parts[1].strip()
                    })
            elif current_section == "education" and len(line) > 5:  # Simple heuristic
                education.append({
                    "institution": line.strip()
                })
        
        return ResumeData(
            text=resume_text,
            skills=skills,
            experience=experience,
            education=education
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-job-description", response_model=JobAnalysis, tags=["Recruitment Buddy"])
async def analyze_job_description(
    job_description: str = Form(..., description="Job description text"),
    token: str = Depends(JWTBearer())
):
    """
    Analyze a job description and extract key information.
    
    This endpoint extracts:
    - Required skills
    - Experience level
    - Key responsibilities
    - Technical terms
    """
    try:
        # Extract skills
        skills = ml_models.extract_skills(job_description)
        
        # Determine experience level
        experience_level = "mid-level"
        text_lower = job_description.lower()
        if any(term in text_lower for term in ["senior", "lead", "principal", "5+ years", "5+ years"]):
            experience_level = "senior"
        elif any(term in text_lower for term in ["junior", "entry-level", "0-2 years", "1-3 years"]):
            experience_level = "junior"
        
        # Extract key responsibilities (simple approach)
        doc = nlp(job_description[:10000])  # Limit to first 10k chars
        sentences = [sent.text for sent in doc.sents]
        responsibilities = [sent for sent in sentences[:5] if len(sent.split()) > 5]  # Simple heuristic
        
        # Extract technical terms
        technical_terms = [chunk.text for chunk in doc.noun_chunks 
                          if any(char.isupper() or char.isdigit() or char in '-_/' 
                                for char in chunk.text)]
        
        return JobAnalysis(
            skills=skills,
            experience_level=experience_level,
            key_responsibilities=responsibilities[:5],  # Return top 5
            technical_terms=list(set(technical_terms))[:20]  # Return top 20 unique terms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/match-skills", response_model=SkillsMatchResult, tags=["Recruitment Buddy"])
async def match_skills(
    request: SkillsMatchRequest,
    token: str = Depends(JWTBearer())
):
    """
    Match a candidate's skills against required skills for a position.
    
    This endpoint calculates:
    - Overall match score
    - List of matching skills
    - List of missing skills
    - Match percentage
    """
    try:
        required_skills = set(skill.lower() for skill in request.required_skills)
        candidate_skills = set(skill.lower() for skill in request.candidate_skills)
        
        matching_skills = list(required_skills & candidate_skills)
        missing_skills = list(required_skills - candidate_skills)
        
        match_percentage = (len(matching_skills) / max(1, len(required_skills))) * 100
        
        return SkillsMatchResult(
            match_score=round(match_percentage, 2),
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            match_percentage=round(match_percentage, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))