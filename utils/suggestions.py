# ==========================================
# RESUME IMPROVEMENT SUGGESTIONS
# ==========================================

def generate_suggestions(
    resume_text,
    job_description,
    matched_skills,
    missing_skills
):

    suggestions = []


    # ==========================================
    # MISSING SKILLS
    # ==========================================

    if missing_skills:

        for skill in missing_skills:

            suggestions.append(
                "Consider adding "
                + skill
                + " if you have relevant experience."
            )


    # ==========================================
    # JOB DESCRIPTION CHECK
    # ==========================================

    if not job_description.strip():

        suggestions.append(
            "Add a job description to get "
            "better job-specific recommendations."
        )


    # ==========================================
    # RESUME LENGTH CHECK
    # ==========================================

    word_count = len(
        resume_text.split()
    )


    if word_count < 200:

        suggestions.append(
            "Your resume appears short. "
            "Consider adding relevant projects, "
            "skills, and experience."
        )


    # ==========================================
    # EXPERIENCE CHECK
    # ==========================================

    experience_words = [

        "experience",
        "internship",
        "intern",
        "worked",
        "employment"

    ]


    has_experience = False


    for word in experience_words:

        if word in resume_text.lower():

            has_experience = True

            break


    if not has_experience:

        suggestions.append(
            "Add your work experience or "
            "internship experience if available."
        )


    # ==========================================
    # PROJECT CHECK
    # ==========================================

    if "project" not in resume_text.lower():

        suggestions.append(
            "Add relevant projects to demonstrate "
            "your practical skills."
        )


    # ==========================================
    # SKILLS CHECK
    # ==========================================

    if not matched_skills:

        suggestions.append(
            "Add relevant technical skills "
            "that match the target job."
        )


    # ==========================================
    # KEYWORD SUGGESTION
    # ==========================================

    if job_description.strip():

        suggestions.append(
            "Use important keywords from the "
            "job description naturally in your resume."
        )


    # ==========================================
    # ACHIEVEMENT SUGGESTION
    # ==========================================

    suggestions.append(
        "Use measurable achievements where possible, "
        "such as percentages, numbers, or results."
    )


    # ==========================================
    # RETURN SUGGESTIONS
    # ==========================================

    return suggestions