from flask import Flask
from questions import questions
import random

app = Flask(__name__)

@app.route("/")
def home():

    q = random.choice(questions)

    html = f"""
    <html>
    <head>
        <title>Matematika Quiz</title>
    </head>

    <body style="font-family:Arial;padding:40px;">

        <h1>{q['subject']}</h1>

        <h2>{q['question']}</h2>

        <ol type="A">
    """

    for option in q["options"]:
        html += f"<li>{option}</li>"

    html += """
        </ol>

    </body>
    </html>
    """

    return html

if __name__ == "__main__":
    app.run()
