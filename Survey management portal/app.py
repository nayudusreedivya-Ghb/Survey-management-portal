from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect("survey.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    # Survey table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    # Questions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER NOT NULL,
            question TEXT NOT NULL
        )
    """)

    # Responses table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    # Create default survey if database is empty
    count = conn.execute(
        "SELECT COUNT(*) FROM surveys"
    ).fetchone()[0]

    if count == 0:

        cursor = conn.execute(
            """
            INSERT INTO surveys (title, description)
            VALUES (?, ?)
            """,
            (
                "Student Feedback Survey",
                "Please share your feedback about the college and learning experience."
            )
        )

        survey_id = cursor.lastrowid

        questions = [
            "How satisfied are you with the teaching?",
            "How satisfied are you with the college infrastructure?",
            "How would you rate the learning environment?",
            "Are you satisfied with the laboratory facilities?",
            "Would you recommend this college to others?"
        ]

        for question in questions:
            conn.execute(
                """
                INSERT INTO questions (survey_id, question)
                VALUES (?, ?)
                """,
                (survey_id, question)
            )

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def index():

    conn = get_db()

    surveys = conn.execute(
        "SELECT * FROM surveys"
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        surveys=surveys
    )


# ---------------- SURVEY ----------------

@app.route("/survey/<int:survey_id>", methods=["GET", "POST"])
def survey(survey_id):

    conn = get_db()

    survey_data = conn.execute(
        "SELECT * FROM surveys WHERE id = ?",
        (survey_id,)
    ).fetchone()

    questions = conn.execute(
        "SELECT * FROM questions WHERE survey_id = ?",
        (survey_id,)
    ).fetchall()

    conn.close()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]

        conn = get_db()

        for question in questions:

            answer = request.form.get(
                f"question_{question['id']}"
            )

            if answer:

                conn.execute(
                    """
                    INSERT INTO responses
                    (survey_id, name, email, question_id, answer)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        survey_id,
                        name,
                        email,
                        question["id"],
                        answer
                    )
                )

        conn.commit()
        conn.close()

        return redirect(url_for("thankyou"))

    return render_template(
        "survey.html",
        survey=survey_data,
        questions=questions
    )


# ---------------- THANK YOU ----------------

@app.route("/thankyou")
def thankyou():

    return render_template("thankyou.html")


# ---------------- ADMIN ----------------

@app.route("/admin")
def admin():

    conn = get_db()

    responses = conn.execute("""
        SELECT
            responses.id,
            responses.name,
            responses.email,
            surveys.title,
            questions.question,
            responses.answer
        FROM responses
        JOIN surveys
        ON responses.survey_id = surveys.id
        JOIN questions
        ON responses.question_id = questions.id
        ORDER BY responses.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        responses=responses
    )


# ---------------- RUN ----------------

if __name__ == "__main__":

    init_db()

    app.run(debug=True)