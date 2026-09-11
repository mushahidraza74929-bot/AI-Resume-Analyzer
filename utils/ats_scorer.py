import re


# ==========================================
# COMMON WORDS TO IGNORE
# ==========================================

STOP_WORDS = {

    "the",
    "and",
    "with",
    "for",
    "from",
    "this",
    "that",
    "have",
    "has",
    "will",
    "are",
    "you",
    "your",
    "our",
    "they",
    "their",
    "them",
    "into",
    "about",
    "after",
    "before",
    "using",
    "used",
    "should",
    "would",
    "could",
    "must",
    "can",
    "able",
    "looking",
    "seeking",
    "work",
    "working",
    "experience",
    "developer",
    "candidate",
    "role",
    "position",
    "team",
    "company",
    "job",
    "years",
    "year"

}


# ==========================================
# EXTRACT IMPORTANT KEYWORDS
# ==========================================

def extract_keywords(text):

    text = text.lower()

    words = re.findall(
        r"[a-zA-Z][a-zA-Z0-9+#.-]*",
        text
    )

    keywords = []

    for word in words:

        word = word.strip(
            ".,!?()[]{}:;"
        )

        if len(word) < 3:
            continue

        if word in STOP_WORDS:
            continue

        if word not in keywords:

            keywords.append(word)

    return keywords


# ==========================================
# ATS SCORE
# ==========================================

def calculate_ats_score(
    resume_text,
    job_description,
    matched_skills,
    resume_skills
):

    resume_lower = resume_text.lower()


    # ==========================================
    # REQUIRED JOB SKILLS
    # ==========================================
    
    # Import skill detector from matcher
    from utils.matcher import find_skills_in_text

    required_skills = find_skills_in_text(
        job_description
    )


    # ==========================================
    # SKILLS SCORE - 50 POINTS
    # ==========================================

    if len(required_skills) > 0:

        skill_percentage = (
            len(matched_skills)
            /
            len(required_skills)
        ) * 100

    else:

        skill_percentage = 0


    skill_score = skill_percentage * 0.50


    # ==========================================
    # KEYWORD SCORE - 20 POINTS
    # ==========================================

    job_keywords = extract_keywords(
        job_description
    )


    matched_keywords = []


    for keyword in job_keywords:

        if keyword in resume_lower:

            matched_keywords.append(
                keyword
            )


    if len(job_keywords) > 0:

        keyword_percentage = (
            len(matched_keywords)
            /
            len(job_keywords)
        ) * 100

    else:

        keyword_percentage = 0


    keyword_score = keyword_percentage * 0.20


    # ==========================================
    # EDUCATION SCORE - 15 POINTS
    # ==========================================

    education_keywords = [

        "bachelor",
        "master",
        "b.tech",
        "m.tech",
        "bca",
        "mca",
        "degree",
        "computer science",
        "engineering",
        "information technology"

    ]


    education_found = False


    for keyword in education_keywords:

        if keyword in resume_lower:

            education_found = True

            break


    if education_found:

        education_score = 15

    else:

        education_score = 0


    # ==========================================
    # EXPERIENCE SCORE - 15 POINTS
    # ==========================================

    experience_keywords = [

        "experience",
        "developer",
        "intern",
        "internship",
        "worked",
        "company",
        "project",
        "employment"

    ]


    experience_found = False


    for keyword in experience_keywords:

        if keyword in resume_lower:

            experience_found = True

            break


    if experience_found:

        experience_score = 15

    else:

        experience_score = 0


    # ==========================================
    # FINAL ATS SCORE
    # ==========================================

    ats_score = (

        skill_score
        +
        keyword_score
        +
        education_score
        +
        experience_score

    )


    # Keep score between 0 and 100

    ats_score = min(
        max(ats_score, 0),
        100
    )


    # ==========================================
    # RETURN RESULT
    # ==========================================

    return {

        "ats_score": round(
            ats_score,
            2
        ),

        "skill_score": round(
            skill_score,
            2
        ),

        "keyword_score": round(
            keyword_score,
            2
        ),

        "education_score":
            education_score,

        "experience_score":
            experience_score,

        "job_keywords":
            job_keywords,

        "matched_keywords":
            matched_keywords,

        "required_skills":
            required_skills

    }