from flask import Flask, render_template, request, redirect, session, make_response, send_from_directory
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

load_dotenv()

from utils.db import get_db_connection
from utils.pdf_parser import extract_text_from_pdf
from utils.docx_parser import extract_text_from_docx
from utils.resume_parser import extract_resume_information
from utils.matcher import match_resume_with_job
from utils.ats_scorer import calculate_ats_score
from utils.suggestions import generate_suggestions
from utils.quality_scorer import calculate_quality_score


# ==========================================
# FLASK APPLICATION
# ==========================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


# ==========================================
# CSRF SECURITY
# ==========================================

csrf = CSRFProtect(app)


# ==========================================
# SESSION SECURITY
# ==========================================

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = False


# ==========================================
# UPLOAD CONFIGURATION
# ==========================================

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx"
}

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==========================================
# CHECK ALLOWED FILE
# ==========================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# REGISTER
# ==========================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get("name")

        email = request.form.get("email")

        password = request.form.get("password")

        if not name or not email or not password:

            return """
                <h2>Registration Failed ❌</h2>
                <p>Please fill all fields.</p>
                <a href="/register">Try Again</a>
            """

        hashed_password = generate_password_hash(
            password
        )

        connection = get_db_connection()

        cursor = connection.cursor()

        try:

            query = """
                INSERT INTO users
                (name, email, password)
                VALUES (%s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    name,
                    email,
                    hashed_password
                )
            )

            connection.commit()

            return render_template(
    "registration_success.html"
)

        except Exception as e:

            return f"""
                <h2>Registration Failed ❌</h2>
                <p>{e}</p>
                <a href="/register">Try Again</a>
            """

        finally:

            cursor.close()

            connection.close()


    return render_template(
        "register.html"
    )


# ==========================================
# LOGIN
# ==========================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get("email")

        password = request.form.get("password")

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        try:

            query = """
                SELECT *
                FROM users
                WHERE email = %s
            """

            cursor.execute(
                query,
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password"],
                password
            ):

                session["user_id"] = user["id"]

                session["user_name"] = user["name"]

                session["user_email"] = user["email"]

                return redirect(
                    "/dashboard"
                )

            return """
                <h2>Login Failed ❌</h2>
                <p>Invalid email or password. Please try again.</p>
                <a href="/login">Try Again</a>
            """

        finally:

            cursor.close()

            connection.close()


    return render_template(
        "login.html"
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    response = redirect("/login")

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# ==========================================
# PROFILE
# ==========================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        if request.method == "POST":

            profile_pic = request.files.get(
                "profile_pic"
            )

            if profile_pic and profile_pic.filename != "":

                original_filename = secure_filename(
                    profile_pic.filename
                )

                extension = os.path.splitext(
                    original_filename
                )[1].lower()

                allowed_images = {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                }

                if extension not in allowed_images:

                    return """
                        <h2>Invalid Image Type ❌</h2>
                        <p>Only JPG, JPEG, PNG and WEBP are allowed.</p>
                        <a href="/profile">Try Again</a>
                    """

                unique_filename = (
                    "profile_"
                    + str(session["user_id"])
                    + "_"
                    + os.urandom(12).hex()
                    + extension
                )

                profile_folder = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    "profiles"
                )

                os.makedirs(
                    profile_folder,
                    exist_ok=True
                )

                filepath = os.path.join(
                    profile_folder,
                    unique_filename
                )

                profile_pic.save(filepath)

                cursor.execute(
                    """
                    SELECT profile_pic
                    FROM users
                    WHERE id = %s
                    """,
                    (session["user_id"],)
                )

                old_user = cursor.fetchone()

                old_picture = None

                if old_user:

                    old_picture = old_user.get(
                        "profile_pic"
                    )

                cursor.execute(
                    """
                    UPDATE users
                    SET profile_pic = %s
                    WHERE id = %s
                    """,
                    (
                        unique_filename,
                        session["user_id"]
                    )
                )

                connection.commit()

                if old_picture:

                    old_filepath = os.path.join(
                        profile_folder,
                        old_picture
                    )

                    if os.path.exists(old_filepath):

                        os.remove(old_filepath)

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                profile_pic
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if not user:

            session.clear()

            return redirect("/login")

        return render_template(
            "profile.html",
            user=user
        )

    finally:

        cursor.close()

        connection.close()


# ==========================================
# PROFILE PICTURE
# ==========================================

@app.route("/profile-picture/<filename>")
def profile_picture(filename):

    if "user_id" not in session:

        return redirect("/login")

    profile_folder = os.path.join(
        app.config["UPLOAD_FOLDER"],
        "profiles"
    )

    return send_from_directory(
        profile_folder,
        filename
    )


# ==========================================
# CHANGE PASSWORD
# ==========================================

@app.route(
    "/change-password",
    methods=["GET", "POST"]
)
def change_password():

    if "user_id" not in session:

        return redirect("/login")

    if request.method == "GET":

        return render_template(
            "change_password.html"
        )

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    if not current_password or not new_password or not confirm_password:

        return """
            <h2>All Fields Are Required ❌</h2>

            <p>
                Please fill in all password fields.
            </p>

            <a href="/change-password">
                Try Again
            </a>
        """

    if new_password != confirm_password:

        return """
            <h2>Passwords Do Not Match ❌</h2>

            <p>
                New password and confirm password must match.
            </p>

            <a href="/change-password">
                Try Again
            </a>
        """

    if len(new_password) < 6:

        return """
            <h2>Password Too Short ❌</h2>

            <p>
                Password must contain at least 6 characters.
            </p>

            <a href="/change-password">
                Try Again
            </a>
        """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if not user:

            session.clear()

            return redirect("/login")

        if not check_password_hash(
            user["password"],
            current_password
        ):

            return """
                <h2>Current Password Is Incorrect ❌</h2>

                <p>
                    Please enter your current password correctly.
                </p>

                <a href="/change-password">
                    Try Again
                </a>
            """

        hashed_password = generate_password_hash(
            new_password
        )

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE id = %s
            """,
            (
                hashed_password,
                session["user_id"]
            )
        )

        connection.commit()

        return render_template(
    "password_changed.html"
)

    except Exception as e:

        print(
            "Change Password Error:",
            e
        )

        if connection:
            connection.rollback()

        return """
            <h2>Password Change Failed ❌</h2>

            <p>
                Something went wrong while changing your password.
                Please try again.
            </p>

            <a href="/change-password">
                Try Again
            </a>
        """

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM resumes
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        total_resumes = cursor.fetchone()["total"]


        cursor.execute(
            """
            SELECT AVG(ats_score) AS average_ats
            FROM resumes
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        average_ats = cursor.fetchone()["average_ats"]

        if average_ats is None:

            average_ats = 0

        else:

            average_ats = round(
                float(average_ats),
                2
            )


        cursor.execute(
            """
            SELECT AVG(match_score) AS average_match
            FROM resumes
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        average_match = cursor.fetchone()["average_match"]

        if average_match is None:

            average_match = 0

        else:

            average_match = round(
                float(average_match),
                2
            )


        cursor.execute(
            """
            SELECT MAX(ats_score) AS best_ats
            FROM resumes
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        best_ats = cursor.fetchone()["best_ats"]

        if best_ats is None:

            best_ats = 0

        else:

            best_ats = round(
                float(best_ats),
                2
            )


        cursor.execute(
            """
            SELECT
                id,
                filename,
                ats_score,
                match_score,
                created_at
            FROM resumes
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (session["user_id"],)
        )

        recent_resumes = cursor.fetchall()


        return render_template(
            "dashboard.html",
            total_resumes=total_resumes,
            average_ats=average_ats,
            average_match=average_match,
            best_ats=best_ats,
            recent_resumes=recent_resumes
        )

    finally:

        cursor.close()

        connection.close()


# ==========================================
# HISTORY
# ==========================================

@app.route("/history")
def history():

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                id,
                filename,
                ats_score,
                match_score,
                created_at
            FROM resumes
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )

        resumes = cursor.fetchall()

        return render_template(
            "history.html",
            resumes=resumes
        )

    finally:

        cursor.close()

        connection.close()


# ==========================================
# EDIT RESUME
# ==========================================

@app.route(
    "/edit/<int:resume_id>",
    methods=["GET", "POST"]
)
def edit_resume(resume_id):

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT *
            FROM resumes
            WHERE id = %s
            AND user_id = %s
            """,
            (
                resume_id,
                session["user_id"]
            )
        )

        resume = cursor.fetchone()

        if not resume:

            return """
                <h2>Resume Not Found ❌</h2>
                <p>This resume could not be found.</p>
                <a href="/history">Back to History</a>
            """

        if request.method == "GET":

            return render_template(
                "edit_resume.html",
                resume=resume
            )

        job_description = request.form.get(
            "job_description",
            ""
        )

        if not job_description.strip():

            return """
                <h2>Job Description Required ❌</h2>
                <a href="/history">Back to History</a>
            """

        skills_text = resume.get(
            "skills",
            ""
        )

        if skills_text:

            skills = [
                skill.strip()
                for skill in skills_text.split(",")
                if skill.strip()
            ]

        else:

            skills = []

        matching_result = match_resume_with_job(
            skills,
            job_description
        )

        required_skills = matching_result.get(
            "required_skills",
            []
        )

        matched_skills = matching_result.get(
            "matched_skills",
            []
        )

        missing_skills = matching_result.get(
            "missing_skills",
            []
        )

        match_score = matching_result.get(
            "match_score",
            0
        )

        resume_text = " ".join(
            [
                str(resume.get("name", "")),
                str(resume.get("email", "")),
                str(resume.get("phone", "")),
                str(resume.get("skills", "")),
                str(resume.get("education", "")),
                str(resume.get("experience", "")),
                str(resume.get("projects", ""))
            ]
        )

        quality_score = calculate_quality_score(
            resume_text
        )

        quality_score = calculate_quality_score(
            resume_text
        )

        ats_result = calculate_ats_score(
            resume_text,
            job_description,
            matched_skills,
            skills
        )

        ats_score = ats_result.get(
            "ats_score",
            0
        )

        skill_score = ats_result.get(
            "skill_score",
            0
        )

        keyword_score = ats_result.get(
            "keyword_score",
            0
        )

        education_score = ats_result.get(
            "education_score",
            0
        )

        experience_score = ats_result.get(
            "experience_score",
            0
        )

        matched_keywords = ats_result.get(
            "matched_keywords",
            []
        )

        suggestions = generate_suggestions(
            resume_text,
            job_description,
            matched_skills,
            missing_skills
        )

        cursor.execute(
            """
            UPDATE resumes
            SET
                job_description = %s,
                match_score = %s,
                ats_score = %s
            WHERE id = %s
            AND user_id = %s
            """,
            (
                job_description,
                match_score,
                ats_score,
                resume_id,
                session["user_id"]
            )
        )

        connection.commit()

        return render_template(
            "result.html",
            resume_id=resume_id,
            filename=resume.get("filename", "Resume"),
            ats_score=ats_score,
            match_score=match_score,
            quality_score=quality_score,
            skill_score=skill_score,
            keyword_score=keyword_score,
            education_score=education_score,
            experience_score=experience_score,
            required_skills=required_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_keywords=matched_keywords,
            name=resume.get("name", "Not found"),
            email=resume.get("email", "Not found"),
            phone=resume.get("phone", "Not found"),
            education=resume.get("education", "Not found"),
            experience=resume.get("experience", "Not found"),
            projects=resume.get("projects", "Not found"),
            suggestions=suggestions
        )

    finally:

        cursor.close()

        connection.close()


# ==========================================
# VIEW OLD REPORT
# ==========================================

@app.route("/report/<int:resume_id>")
def report(resume_id):

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT *
            FROM resumes
            WHERE id = %s
            AND user_id = %s
            """,
            (
                resume_id,
                session["user_id"]
            )
        )

        resume = cursor.fetchone()

        if not resume:

            return """
                <h2>Resume Report Not Found ❌</h2>

                <a href="/history">
                    Back to History
                </a>
            """

        skills_text = resume.get(
            "skills",
            ""
        )

        if skills_text:

            skills = [
                skill.strip()
                for skill in skills_text.split(",")
                if skill.strip()
            ]

        else:

            skills = []

        job_description = resume.get(
            "job_description",
            ""
        )

        matching_result = match_resume_with_job(
            skills,
            job_description
        )

        required_skills = matching_result.get(
            "required_skills",
            []
        )

        matched_skills = matching_result.get(
            "matched_skills",
            []
        )

        missing_skills = matching_result.get(
            "missing_skills",
            []
        )

        match_score = matching_result.get(
            "match_score",
            resume.get(
                "match_score",
                0
            )
        )

        resume_text = " ".join(
            [
                str(resume.get("name", "")),
                str(resume.get("email", "")),
                str(resume.get("phone", "")),
                str(resume.get("skills", "")),
                str(resume.get("education", "")),
                str(resume.get("experience", "")),
                str(resume.get("projects", ""))
            ]
        )

        ats_result = calculate_ats_score(
            resume_text,
            job_description,
            matched_skills,
            skills
        )

        ats_score = resume.get(
            "ats_score",
            ats_result.get(
                "ats_score",
                0
            )
        )

        skill_score = ats_result.get(
            "skill_score",
            0
        )

        keyword_score = ats_result.get(
            "keyword_score",
            0
        )

        education_score = ats_result.get(
            "education_score",
            0
        )

        experience_score = ats_result.get(
            "experience_score",
            0
        )

        matched_keywords = ats_result.get(
            "matched_keywords",
            []
        )

        suggestions = generate_suggestions(
            resume_text,
            job_description,
            matched_skills,
            missing_skills
        )

        return render_template(
            "result.html",

            resume_id=resume_id,

            filename=resume.get(
                "filename",
                "Resume"
            ),

            ats_score=ats_score,

            match_score=match_score,

            skill_score=skill_score,

            keyword_score=keyword_score,

            education_score=education_score,

            experience_score=experience_score,

            required_skills=required_skills,

            matched_skills=matched_skills,

            missing_skills=missing_skills,

            matched_keywords=matched_keywords,

            name=resume.get(
                "name",
                "Not found"
            ),

            email=resume.get(
                "email",
                "Not found"
            ),

            phone=resume.get(
                "phone",
                "Not found"
            ),

            education=resume.get(
                "education",
                "Not found"
            ),

            experience=resume.get(
                "experience",
                "Not found"
            ),

            projects=resume.get(
                "projects",
                "Not found"
            ),

            suggestions=suggestions
        )

    finally:

        cursor.close()

        connection.close()


# ==========================================
# DOWNLOAD ANALYSIS REPORT
# ==========================================

@app.route("/download/<int:resume_id>")
def download_report(resume_id):

    if "user_id" not in session:

        return redirect("/login")

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM resumes
            WHERE id = %s
            AND user_id = %s
            """,
            (
                resume_id,
                session["user_id"]
            )
        )

        resume = cursor.fetchone()

        if not resume:

            return """
                <h2>Resume Report Not Found ❌</h2>

                <a href="/history">
                    Back to History
                </a>
            """

        report_text = f"""
AI RESUME ANALYZER - ANALYSIS REPORT
====================================

Resume: {resume.get("filename", "Resume")}
Name: {resume.get("name", "Not found")}
Email: {resume.get("email", "Not found")}
Phone: {resume.get("phone", "Not found")}

ATS Score: {resume.get("ats_score", 0)}/100
Job Match: {resume.get("match_score", 0)}%

Skills:
{resume.get("skills", "Not found")}

Education:
{resume.get("education", "Not found")}

Experience:
{resume.get("experience", "Not found")}

Projects:
{resume.get("projects", "Not found")}

Job Description:
{resume.get("job_description", "Not found")}

====================================
Generated by AI Resume Analyzer
"""

        response = make_response(
            report_text
        )

        response.headers[
            "Content-Type"
        ] = "text/plain; charset=utf-8"

        response.headers[
            "Content-Disposition"
        ] = (
            "attachment; "
            "filename=resume_analysis_report.txt"
        )

        return response

    except Exception as e:

        print(
            "Download Report Error:",
            e
        )

        return """
            <h2>Download Failed ❌</h2>

            <p>
                Something went wrong while generating
                the report.
            </p>

            <a href="/history">
                Back to History
            </a>
        """

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ==========================================
# DELETE RESUME
# ==========================================

@app.route(
    "/delete/<int:resume_id>",
    methods=["POST"]
)
def delete_resume(resume_id):

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT filename
            FROM resumes
            WHERE id = %s
            AND user_id = %s
            """,
            (
                resume_id,
                session["user_id"]
            )
        )

        resume = cursor.fetchone()

        if not resume:

            return """
                <h2>Resume Not Found ❌</h2>

                <a href="/history">
                    Back to History
                </a>
            """

        filename = resume["filename"]

        try:

            cursor.execute(
                """
                DELETE FROM resumes
                WHERE id = %s
                AND user_id = %s
                """,
                (
                    resume_id,
                    session["user_id"]
                )
            )

            connection.commit()

        except Exception as e:

            print(
                "Resume Delete Error:",
                e
            )

            connection.rollback()

            return """
                <h2>Delete Failed ❌</h2>

                <p>
                    Something went wrong while deleting the resume.
                    Please try again.
                </p>

                <a href="/history">
                    Back to History
                </a>
            """

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        if os.path.exists(filepath):

            os.remove(filepath)

        return redirect(
            "/history"
        )

    finally:

        cursor.close()

        connection.close()


# ==========================================
# UPLOAD AND ANALYZE
# ==========================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    if "user_id" not in session:

        return redirect("/login")

    if request.method == "GET":

        return render_template(
            "upload.html"
        )

    resume = request.files.get(
        "resume"
    )

    job_description = request.form.get(
        "job_description",
        ""
    )

    if not resume:

        return """
            <h2>No Resume Uploaded ❌</h2>
            <a href="/upload">Try Again</a>
        """

    if resume.filename == "":

        return """
            <h2>Please Select a Resume ❌</h2>
            <a href="/upload">Try Again</a>
        """

    if not allowed_file(
        resume.filename
    ):

        return """
            <h2>Invalid File Type ❌</h2>

            <p>
                Only PDF and DOCX files are allowed.
            </p>

            <a href="/upload">
                Try Again
            </a>
        """

    # ==========================================
    # SECURE UNIQUE FILENAME
    # ==========================================

    original_filename = secure_filename(
        resume.filename
    )

    if original_filename == "":

        return """
            <h2>Invalid Filename ❌</h2>
            <a href="/upload">Try Again</a>
        """

    user_id = session["user_id"]

    file_extension = os.path.splitext(
        original_filename
    )[1].lower()

    unique_name = (
        str(user_id)
        + "_"
        + os.urandom(16).hex()
        + file_extension
    )

    filename = unique_name

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    resume.save(filepath) 
    if not os.path.exists(filepath):

     return """
        <h2>File Upload Failed ❌</h2>
        <p>The resume could not be saved.</p>
        <a href="/upload">Try Again</a>
    """

    # ==========================================
    # EXTRACT RESUME TEXT
    # ==========================================

    file_extension = os.path.splitext(
        filename
    )[1].lower()

    if file_extension == ".pdf":

        resume_text = extract_text_from_pdf(
            filepath
        )

    elif file_extension == ".docx":

        resume_text = extract_text_from_docx(
            filepath
        )

    else:

        if os.path.exists(filepath):

            os.remove(filepath)

        return """
            <h2>Unsupported File Type ❌</h2>

            <p>
                Only PDF and DOCX files are supported.
            </p>

            <a href="/upload">
                Try Again
            </a>
        """

    if not resume_text or not resume_text.strip():

        if os.path.exists(filepath):

            os.remove(filepath)

        return """
            <h2>Could Not Read Resume ❌</h2>

            <p>
                No readable text was found.
            </p>

            <a href="/upload">
                Try Another Resume
            </a>
        """

    # ==========================================
    # RESUME INFORMATION
    # ==========================================

    resume_information = extract_resume_information(
        resume_text
    )

    name = resume_information.get(
        "name",
        "Not found"
    )

    email = resume_information.get(
        "email",
        "Not found"
    )

    phone = resume_information.get(
        "phone",
        "Not found"
    )

    skills = resume_information.get(
        "skills",
        []
    )

    education = resume_information.get(
        "education",
        "Not found"
    )

    experience = resume_information.get(
        "experience",
        "Not found"
    )

    projects = resume_information.get(
        "projects",
        "Not found"
    )

    # ==========================================
    # RESUME QUALITY SCORE
    # ==========================================

    quality_score = calculate_quality_score(
        resume_text
    )

    # ==========================================
    # JOB MATCHING
    # ==========================================

    matching_result = match_resume_with_job(
        skills,
        job_description
    )

    required_skills = matching_result.get(
        "required_skills",
        []
    )

    matched_skills = matching_result.get(
        "matched_skills",
        []
    )

    missing_skills = matching_result.get(
        "missing_skills",
        []
    )

    match_score = matching_result.get(
        "match_score",
        0
    )

    # ==========================================
    # ATS SCORE
    # ==========================================

    ats_result = calculate_ats_score(
        resume_text,
        job_description,
        matched_skills,
        skills
    )

    ats_score = ats_result.get(
        "ats_score",
        0
    )

    skill_score = ats_result.get(
        "skill_score",
        0
    )

    keyword_score = ats_result.get(
        "keyword_score",
        0
    )

    education_score = ats_result.get(
        "education_score",
        0
    )

    experience_score = ats_result.get(
        "experience_score",
        0
    )

    matched_keywords = ats_result.get(
        "matched_keywords",
        []
    )

    # ==========================================
    # SUGGESTIONS
    # ==========================================

    suggestions = generate_suggestions(
        resume_text,
        job_description,
        matched_skills,
        missing_skills
    )

    # ==========================================
    # SAVE TO DATABASE
    # ==========================================

    connection = get_db_connection()

    cursor = connection.cursor()

    try:

        query = """
            INSERT INTO resumes
            (
                user_id,
                filename,
                name,
                email,
                phone,
                skills,
                education,
                experience,
                projects,
                job_description,
                match_score,
                ats_score
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        values = (
            user_id,
            filename,
            name,
            email,
            phone,
            ", ".join(skills),
            education,
            experience,
            projects,
            job_description,
            match_score,
            ats_score
        )

        cursor.execute(
            query,
            values
        )

        resume_id = cursor.lastrowid

        connection.commit()

    except Exception as e:

        print(
            "Resume Database Error:",
            e
        )

        connection.rollback()

        return """
            <h2>Upload Failed ❌</h2>

            <p>
                Something went wrong while saving your resume.
                Please try again.
            </p>

            <a href="/upload">
                Try Again
            </a>
        """

    finally:

        cursor.close()

        connection.close()

    # ==========================================
    # SHOW RESULT
    # ==========================================

    return render_template(
        "result.html",

        resume_id=resume_id,

        filename=filename,

        ats_score=ats_score,

        match_score=match_score,

        skill_score=skill_score,

        keyword_score=keyword_score,

        education_score=education_score,

        experience_score=experience_score,

        required_skills=required_skills,

        matched_skills=matched_skills,

        missing_skills=missing_skills,

        matched_keywords=matched_keywords,

        name=name,

        email=email,

        phone=phone,

        education=education,

        experience=experience,

        projects=projects,

        suggestions=suggestions
    )


# ==========================================
# FILE TOO LARGE
# ==========================================

@app.errorhandler(413)
def file_too_large(error):

    return """
        <h2>File Too Large ❌</h2>

        <p>
            Maximum resume size is 5 MB.
        </p>

        <a href="/upload">
            Try Again
        </a>
    """, 413
# ==========================================
# 404 ERROR HANDLER
# ==========================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404
# ==========================================
# 500 ERROR HANDLER
# ==========================================

@app.errorhandler(500)
def internal_server_error(error):

    return render_template(
        "500.html"
    ), 500


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )