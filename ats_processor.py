import re

# Comprehensive list of tech terms, languages, frameworks, and methodologies
COMMON_TECH_KEYWORDS = [
    # Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'golang', 'rust', 'kotlin', 'swift', 'scala', 'r', 'html', 'css', 'sql',
    # Frameworks & Libraries
    'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring boot', 'laravel', 'asp.net', 'jquery', 'bootstrap', 'tailwind', 'next.js', 'nuxt',
    # Databases & Caching
    'mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'cassandra', 'elasticsearch', 'oracle', 'dynamodb', 'firebase', 'mariadb',
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'ansible', 'terraform', 'git', 'github', 'gitlab', 'ci/cd', 'nginx', 'apache',
    # Concepts & Methodologies
    'dsa', 'data structures', 'algorithms', 'system design', 'rest api', 'graphql', 'websockets', 'agile', 'scrum', 'oop', 'microservices',
    # AI/ML & Data Science
    'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'data science', 'analytics',
    # General Soft Skills & Management
    'communication', 'leadership', 'teamwork', 'problem solving', 'project management', 'collaboration', 'testing', 'unit testing', 'debugging'
]

# Basic English Stopwords
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
    'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
    'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
    'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up',
    'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
    'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn',
    'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn'
}

def clean_and_tokenize(text):
    """
    Cleans text by lowering, removing symbols, and splitting into individual words (tokens).
    Also filters out common English stopwords.
    """
    if not text:
        return []
    # Lowercase
    text = text.lower()
    # Normalize phrases like "rest api" or "data structures" to single hyphenated words
    text = text.replace("rest api", "rest-api")
    text = text.replace("data structures", "data-structures")
    text = text.replace("system design", "system-design")
    text = text.replace("spring boot", "spring-boot")
    text = text.replace("machine learning", "machine-learning")
    text = text.replace("deep learning", "deep-learning")
    text = text.replace("data science", "data-science")
    text = text.replace("unit testing", "unit-testing")
    text = text.replace("problem solving", "problem-solving")
    text = text.replace("project management", "project-management")
    
    # Remove symbols and punctuation
    text = re.sub(r'[^\w\s\-\.]', ' ', text)
    
    # Tokenize
    tokens = text.split()
    
    # Remove stopwords
    filtered_tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    
    return filtered_tokens

def extract_keywords(tokens):
    """
    Identifies common industry tech keywords present in a tokenized text.
    """
    found_keywords = set()
    for token in tokens:
        # Match base token
        if token in COMMON_TECH_KEYWORDS:
            found_keywords.add(token)
            
        # Match normalized hyphenated values
        normalized_token = token.replace('-', ' ')
        if normalized_token in COMMON_TECH_KEYWORDS:
            found_keywords.add(normalized_token)
            
    return found_keywords

def analyze_ats_score(resume_text, job_desc_text):
    """
    Computes ATS score (0 to 100), extracts matched/missing keywords,
    and returns recommendations to optimize the resume.
    """
    if not resume_text or not job_desc_text:
        return {
            'score': 0,
            'matched': [],
            'missing': [],
            'recommendations': ['Please enter both resume text and job description to analyze.']
        }
        
    # Clean and tokenize
    resume_tokens = clean_and_tokenize(resume_text)
    job_tokens = clean_and_tokenize(job_desc_text)
    
    # Set representation
    resume_set = set(resume_tokens)
    job_set = set(job_tokens)
    
    # Extract tech keywords
    resume_tech = extract_keywords(resume_tokens)
    job_tech = extract_keywords(job_tokens)
    
    # 1. Tech Keyword Overlap Score (Weight: 70%)
    if len(job_tech) > 0:
        tech_overlap = len(resume_tech.intersection(job_tech))
        tech_score = (tech_overlap / len(job_tech)) * 100
    else:
        tech_score = 50.0  # Fallback if no specific keywords are detected
        
    # 2. General Token Cosine/Jaccard Similarity Score (Weight: 30%)
    intersection_tokens = resume_set.intersection(job_set)
    union_tokens = resume_set.union(job_set)
    
    if len(union_tokens) > 0:
        jaccard_score = (len(intersection_tokens) / len(union_tokens)) * 100
    else:
        jaccard_score = 0.0
        
    # Combined score (weighted)
    final_score = int((tech_score * 0.7) + (jaccard_score * 0.3))
    # Cap score boundaries
    final_score = min(100, max(5, final_score))
    
    # Extrapolate missing and matched
    matched_keywords = sorted(list(job_tech.intersection(resume_tech)))
    missing_keywords = sorted(list(job_tech.difference(resume_tech)))
    
    # Generate tailored recommendations
    recommendations = []
    
    # Overall score evaluation
    if final_score >= 80:
        recommendations.append("Excellent alignment! Your resume is highly optimized for this role. You are ready to apply.")
    elif final_score >= 50:
        recommendations.append("Good start, but your resume has notable keyword gaps compared to the job description.")
    else:
        recommendations.append("Low match score. Your resume lacks critical keywords requested by the recruiter.")
        
    # Keyword recommendations
    if missing_keywords:
        rec_words = ", ".join([f"'{w}'" for w in missing_keywords[:5]])
        recommendations.append(f"Consider integrating missing keywords like {rec_words} in your Skills or Experience section if you possess these skills.")
    
    # Section presence check
    lower_resume = resume_text.lower()
    if 'education' not in lower_resume:
        recommendations.append("Action Required: Include a dedicated 'Education' section detailing your degree and graduation details.")
    if 'project' not in lower_resume:
        recommendations.append("Action Required: Add a 'Projects' section highlighting building apps using relevant tech stacks.")
    if 'experience' not in lower_resume and 'internship' not in lower_resume:
        recommendations.append("Tip: Add an 'Experience' or 'Internships' section to display practical work (even virtual internships count!).")
        
    return {
        'score': final_score,
        'matched': matched_keywords,
        'missing': missing_keywords,
        'recommendations': recommendations
    }
