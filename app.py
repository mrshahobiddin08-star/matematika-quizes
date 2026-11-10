from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Matematika Quizlar</h1>

    <h2>Mavzular:</h2>

    <ul>
        <li>Matritsalar</li>
        <li>Determinantlar</li>
        <li>Chiziqli tenglamalar</li>
        <li>Kompleks sonlar</li>
        <li>Vektorlar</li>
        <li>Funksiyalar</li>
    </ul>

    <p>120 ta savol bazasi tayyorlanmoqda.</p>
    """
    
if __name__ == "__main__":
    app.run()
