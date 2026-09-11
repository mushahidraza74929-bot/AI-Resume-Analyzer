import re


def extract_email(text):

    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

    match = re.search(email_pattern, text)

    if match:
        return match.group()

    return "Not found"


def extract_phone(text):

    phone_pattern = r'(\+91[\s-]?)?[6-9]\d{9}'

    match = re.search(phone_pattern, text)

    if match:
        return match.group()

    return "Not found"


def extract_name(text):

    lines = text.strip().split("\n")

    for line in lines[:5]:

        line = line.strip()

        if line and len(line.split()) <= 4:

            if not any(char.isdigit() for char in line):

                if "@" not in line:

                    return line

    return "Not found"


def extract_skills(text):

    skills_list = [
        "Java",
        "Python",
        "C",
        "C++",
        "JavaScript",
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

    found_skills = []

    text_lower = text.lower()

    for skill in skills_list:

        if skill.lower() in text_lower:

            found_skills.append(skill)

    return found_skills


def extract_section(text, section_names):

    lines = text.splitlines()

    section_text = []

    inside_section = False

    for line in lines:

        clean_line = line.strip()

        # Check whether this line is a section heading
        if any(
            section_name.lower() in clean_line.lower()
            for section_name in section_names
        ):

            inside_section = True

            continue

        # Stop when another major section starts
        if inside_section:

            major_sections = [
                "professional summary",
                "technical skills",
                "education",
                "experience",
                "work experience",
                "projects",
                "certifications",
                "achievements"
            ]

            if (
                clean_line.lower() in major_sections
                and not any(
                    section_name.lower() in clean_line.lower()
                    for section_name in section_names
                )
            ):

                break

            if clean_line:

                section_text.append(clean_line)

    if section_text:

        return "\n".join(section_text)

    return "Not found"


def extract_education(text):

    education_keywords = [
        "education",
        "academic",
        "qualification"
    ]

    return extract_section(
        text,
        education_keywords
    )


def extract_experience(text):

    experience_keywords = [
        "experience",
        "work experience",
        "professional experience"
    ]

    return extract_section(
        text,
        experience_keywords
    )


def extract_projects(text):

    project_keywords = [
        "projects",
        "project",
        "personal projects"
    ]

    return extract_section(
        text,
        project_keywords
    )


def extract_resume_information(text):

    information = {

        "name": extract_name(text),

        "email": extract_email(text),

        "phone": extract_phone(text),

        "skills": extract_skills(text),

        "education": extract_education(text),

        "experience": extract_experience(text),

        "projects": extract_projects(text)

    }

    return information