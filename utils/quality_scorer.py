def calculate_quality_score(resume_text):

    score = 0
    resume_lower = resume_text.lower()

    # Contact information
    if "@" in resume_text:
        score += 15

    if any(char.isdigit() for char in resume_text):
        score += 10

    # Skills
    skill_words = [
        "java",
        "python",
        "sql",
        "javascript",
        "html",
        "css",
        "mysql",
        "spring boot"
    ]

    skill_count = 0

    for skill in skill_words:

        if skill in resume_lower:
            skill_count += 1

    if skill_count >= 5:
        score += 20
    elif skill_count >= 3:
        score += 15
    elif skill_count >= 1:
        score += 10

    # Education
    education_words = [
        "education",
        "bachelor",
        "master",
        "b.tech",
        "bca",
        "mca",
        "degree"
    ]

    if any(word in resume_lower for word in education_words):
        score += 15

    # Experience
    experience_words = [
        "experience",
        "internship",
        "intern",
        "developer",
        "worked"
    ]

    if any(word in resume_lower for word in experience_words):
        score += 15

    # Projects
    if "project" in resume_lower:
        score += 10

    # Resume length
    word_count = len(resume_text.split())

    if 200 <= word_count <= 800:
        score += 15
    elif 100 <= word_count < 200:
        score += 10
    elif word_count > 800:
        score += 5

    return min(score, 100)