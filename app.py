from flask import Flask, request, render_template_string
from questions import questions
import random

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Matematika Quiz</title>

<style>

body{
background:#0f172a;
font-family:Arial;
color:white;
display:flex;
justify-content:center;
padding:40px;
}

.card{
background:#1e293b;
padding:30px;
border-radius:20px;
width:700px;
box-shadow:0 0 20px rgba(0,0,0,.3);
}

h1{
color:#22c55e;
}

button{
background:#22c55e;
color:white;
border:none;
padding:12px 20px;
border-radius:10px;
cursor:pointer;
margin-top:20px;
width:100%;
}

.option{
margin:12px 0;
padding:10px;
background:#334155;
border-radius:10px;
}

.timer{
font-size:20px;
color:#4ade80;
margin-bottom:20px;
}

</style>
</head>

<body>

<div class="card">

<h1>Matematika Quiz</h1>

<div class="timer">
⏱ Vaqt: <span id="time">20:00</span>
</div>

<h3>{{subject}}</h3>

<h2>{{question}}</h2>

<form method="POST">

{% for op in options %}
<div class="option">

<input type="radio"
name="answer"
value="{{op}}">

{{op}}

</div>
{% endfor %}

<button type="submit">
Keyingi Savol
</button>

</form>

</div>

<script>

let time=1200;

setInterval(()=>{

let m=Math.floor(time/60);
let s=time%60;

document.getElementById("time").innerText=
String(m).padStart(2,'0')
+":"
+String(s).padStart(2,'0');

if(time>0){
time--;
}

},1000);

</script>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():

    q = random.choice(questions)

    return render_template_string(
        HTML,
        subject=q["subject"],
        question=q["question"],
        options=q["options"]
    )

if __name__ == "__main__":
    app.run()
