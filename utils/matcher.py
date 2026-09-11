import re


# ==========================================
# SKILL LIST
# ==========================================

ALL_SKILLS = [

    "JavaScript",
    "Java",
    "Python",
    "C++",
    "C",
    "HTML",
    "CSS",
    "SQL",
    "MySQL",
    "MongoDB",
    "Django",
    "Flask",
    "Spring Boot",
    "React",
    "Node.js",
    "Express",
    "Git",
    "GitHub",
    "AWS",
    "Docker"

]


# ==========================================
# FIND SKILLS IN TEXT
# ==========================================

def find_skills_in_text(text):

    found_skills = []

    text_lower = text.lower()


    for skill in ALL_SKILLS:

        skill_lower = skill.lower()


        # ------------------------------------------
        # Special handling for skills with symbols
        # ------------------------------------------

        if skill_lower in ["c++", "c"]:

            pattern = r"(?<![a-z0-9])" + re.escape(skill_lower) + r"(?![a-z0-9])"

        else:

            pattern = r"(?<![a-z0-9])" + re.escape(skill_lower) + r"(?![a-z0-9])"


        if re.search(pattern, text_lower):

            found_skills.append(skill)


    return found_skills


# ==========================================
# RESUME ↔ JOB MATCHING
# ==========================================

def match_resume_with_job(
    resume_skills,
    job_description
):

    # ------------------------------------------
    # Find skills required by job
    # ------------------------------------------

    required_skills = find_skills_in_text(
        job_description
    )


    # ------------------------------------------
    # Find matched skills
    # ------------------------------------------

    matched_skills = []

    for skill in required_skills:

        for resume_skill in resume_skills:

            if skill.lower() == resume_skill.lower():

                matched_skills.append(skill)

                break


    # ------------------------------------------
    # Find missing skills
    # ------------------------------------------

    missing_skills = []

    for skill in required_skills:

        if skill not in matched_skills:

            missing_skills.append(skill)


    # ------------------------------------------
    # Calculate match score
    # ------------------------------------------

    if len(required_skills) > 0:

        match_score = (
            len(matched_skills)
            /
            len(required_skills)
        ) * 100

    else:

        match_score = 0


    # ------------------------------------------
    # Return result
    # ------------------------------------------

    return {

        "required_skills": required_skills,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "match_score": round(
            match_score,
            2
        )

    }