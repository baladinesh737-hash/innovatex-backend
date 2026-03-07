from flask import Flask, request, jsonify
import requests
from models import db, User
import json
import pandas as pd
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from groq import Groq
import os

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "InnovateX Backend Live", 200

# ---------------- ENV ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------- DATABASE ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///innovatex.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------- FILE UPLOAD ----------------
UPLOAD_FOLDER = "/tmp"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- ENV KEYS ----------------
OLLAMA_URL = os.environ.get("OLLAMA_URL")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")


# ---------------- SKILLS LIST ----------------
SKILLS = [
    "python","java","c++","javascript",
    "flask","django","react","node",
    "sql","mongodb","machine learning",
    "data analysis","aws","docker",
    "html","css","git"
]


# ---------------- LEARNING RESOURCES ----------------
LEARNING_RESOURCES = {
    "python": ["https://www.youtube.com/watch?v=rfscVS0vtbw"],
    "java": ["https://www.youtube.com/watch?v=grEKMHGYyns"],
    "c++": ["https://www.youtube.com/watch?v=vLnPwxZdW4Y"],
    "javascript": ["https://www.youtube.com/watch?v=W6NZfCO5SIk"],
    "flask": ["https://www.youtube.com/watch?v=Z1RJmh_OqeA"],
    "django": ["https://www.youtube.com/watch?v=F5mRW0jo-U4"],
    "react": ["https://www.youtube.com/watch?v=bMknfKXIFA8"],
    "node": ["https://www.youtube.com/watch?v=TlB_eWDSMt4"],
    "sql": ["https://www.youtube.com/watch?v=HXV3zeQKqGY"],
    "mongodb": ["https://www.youtube.com/watch?v=ofme2o29ngU"],
    "machine learning": ["https://www.youtube.com/watch?v=GwIo3gDZCVQ"],
    "data analysis": ["https://www.youtube.com/watch?v=r-uOLxNrNk8"],
    "aws": ["https://www.youtube.com/watch?v=ulprqHHWlng"],
    "docker": ["https://www.youtube.com/watch?v=fqMOX6JJhGo"],
    "html": ["https://www.youtube.com/watch?v=pQN-pnXPaVg"],
    "css": ["https://www.youtube.com/watch?v=1Rs2ND1ryYc"],
    "git": ["https://www.youtube.com/watch?v=RGOj5yH7evk"]
}

# ---------------- CAREER PATHS ----------------
CAREER_PATHS = {
    "AI Engineer":["python","machine learning"],
    "Backend Developer":["python","flask","sql"],
    "Frontend Developer":["react","javascript","html","css"],
    "Data Analyst":["python","data analysis","sql"]
}


# ---------------- SKILL EXTRACTION ----------------
def extract_skills(resume_text):

    # convert text to lowercase
    resume_text = resume_text.lower()

    # separators to clean text
    separators = ["-", ",", "|", "/", "\n", "·", "."]

    for sep in separators:
        resume_text = resume_text.replace(sep, " ")

    # detected skills list
    found_skills = []

    for skill in SKILLS:
        if skill in resume_text:
            found_skills.append(skill)

    return found_skills


# ---------------- INTERNSHIP MATCH ----------------
def recommend_internships(user_skills, internships):

    results = []

    for job in internships:

        job_skills = job.get("skills", [])
        score = 0
        missing_skills = []
        learning_links = []   # create learning links list

        # check matching skills
        for skill in job_skills:
            if skill in user_skills:
                score += 1
            else:
                missing_skills.append(skill)

        total = len(job_skills) if len(job_skills) > 0 else 1
        match_percentage = int((score / total) * 100)

        # add learning resources for missing skills
        for skill in missing_skills:
            if skill in LEARNING_RESOURCES:
                learning_links.extend(LEARNING_RESOURCES[skill])

        predicted_career = "General Software Intern"

        # predict career path
        for career, skills in CAREER_PATHS.items():
            if all(skill in user_skills for skill in skills[:2]):
                predicted_career = career
                break

        job["match_percentage"] = match_percentage
        job["missing_skills"] = missing_skills
        job["learning_resources"] = learning_links
        job["recommended_career"] = predicted_career

        results.append(job)

    results.sort(key=lambda x: x["match_percentage"], reverse=True)

    return results

# ---------------- HEALTH CHECK ----------------
@app.route("/health")
def health_check():
    return "OK", 200


# ---------------- AI CHAT ----------------
@app.route("/ai-chat", methods=["POST"])
def ai_chat():

    data = request.json
    question = data.get("question")

    try:

        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role":"system","content":"You are InnovateX AI assistant helping students with internships."},
                {"role":"user","content":question}
            ]
        )

        answer = completion.choices[0].message.content

        return jsonify({"answer":answer})

    except Exception as e:

        print(e)

        return jsonify({"answer":"AI service error"})
        
# ---------------- SAVE USER ----------------
@app.route("/save-user", methods=["POST"])
def save_user():

    data = request.get_json()

    user = User(
        name=data.get("name"),
        email=data.get("email"),
        college=data.get("college"),
        degree=data.get("degree")
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message":"User saved successfully"})


# ---------------- VERIFY COLLEGE ----------------
@app.route("/verify-college", methods=["POST"])
def verify_college():

    try:

        file_path = os.path.join(BASE_DIR,"colleges.xlsx")

        if not os.path.exists(file_path):
            return jsonify({"status":"not available"})

        df = pd.read_excel(file_path)
        colleges = df.iloc[:,0].str.lower().tolist()

        data = request.get_json()
        college = data.get("college","").lower()

        if college in colleges:
            return jsonify({"status":"verified"})
        else:
            return jsonify({"status":"not verified"})

    except Exception as e:
        print("COLLEGE ERROR:",e)
        return jsonify({"status":"error"})


# ---------------- UPLOAD RESUME ----------------
@app.route("/upload-resume", methods=["POST"])
def upload_resume():

    if "resume" not in request.files:
        return jsonify({"error":"No file uploaded"}),400

    file = request.files["resume"]
    filename = secure_filename(file.filename)

    path = os.path.join(app.config["UPLOAD_FOLDER"],filename)
    file.save(path)

    return jsonify({"file_path":path})


# ---------------- EXTRACT RESUME TEXT ----------------
@app.route("/extract-resume-text", methods=["POST"])
def extract_resume_text():

    data = request.get_json()
    file_path = data.get("file_path")

    if not file_path or not os.path.exists(file_path):
        return jsonify({"error":"File not found"}),404

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content

    return jsonify({
        "status":"success",
        "resume_text":text
    })


# ---------------- EXTRACT SKILLS ----------------
@app.route("/extract-skills", methods=["POST"])
def skills():

    data = request.get_json()
    resume_text = data.get("resume_text","")

    detected_skills = extract_skills(resume_text)

    return jsonify({
        "skills":detected_skills
    })


# ---------------- RECOMMEND INTERNSHIPS ----------------
@app.route("/recommend-internships", methods=["POST"])
def recommend():

    data = request.get_json()
    user_skills = data.get("skills", [])

    file_path = os.path.join(BASE_DIR,"data","internships.json")

    with open(file_path,"r") as f:
        internships = json.load(f)

    results = recommend_internships(user_skills, internships)

    return jsonify(results)


# ---------------- RESUME SCORE ----------------
@app.route("/resume-score", methods=["POST"])
def resume_score():

    data = request.get_json()
    resume_text = data.get("resume_text","")

    skills = extract_skills(resume_text)

    score = min(len(skills)*10,100)

    strengths = []
    improvements = []

    if "project" in resume_text.lower():
        strengths.append("Has project experience")
    else:
        improvements.append("Add project experience")

    return jsonify({
        "resume_score":score,
        "skills_found":skills,
        "strengths":strengths,
        "improvements":improvements
    })

# ---------------- AI RESUME FEEDBACK ----------------
@app.route("/ai-resume-feedback", methods=["POST"])
def ai_resume_feedback():

    try:

        data = request.get_json()
        resume_text = data.get("resume_text","")

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role":"system",
                    "content":"You are an expert HR recruiter. Analyze resumes and give feedback."
                },
                {
                    "role":"user",
                    "content":f"Analyze this resume and give strengths, weaknesses and improvement tips:\n{resume_text}"
                }
            ]
        )

        reply = completion.choices[0].message.content

        return jsonify({"feedback":reply})

    except Exception as e:
        return jsonify({"error":str(e)})

# ---------------- SKILL GAP ----------------
@app.route("/skill-gap", methods=["POST"])
def skill_gap():

    data = request.get_json()

    # normalize user skills
    user_skills = [skill.lower().strip() for skill in data.get("skills", [])]

    role = data.get("role", "").lower().strip()

    role_skills = {
        "ai intern": ["python","machine learning","deep learning","tensorflow"],
        "backend developer": ["python","flask","sql","docker"],
        "frontend developer": ["javascript","react","html","css"],
        "data analyst": ["python","sql","data analysis","excel"]
    }

    required_skills = role_skills.get(role, [])

    missing_skills = []

    for skill in required_skills:
        if skill.lower() not in user_skills:
            missing_skills.append(skill)

    return jsonify({
        "role": role,
        "your_skills": user_skills,
        "required_skills": required_skills,
        "missing_skills": missing_skills
    })
    
# ---------------- INTERVIEW SIMULATOR ----------------
@app.route("/interview-sim", methods=["POST"])
def interview_sim():

    data = request.get_json()

    role = data.get("role","").lower()
    skills = data.get("skills",[])

    interview_bank = {
        "ai intern":[
            "Explain machine learning basics",
            "What is overfitting?",
            "Explain difference between supervised and unsupervised learning",
            "Describe a ML project you built"
        ],

        "backend developer":[
            "Explain REST API",
            "What is Flask?",
            "Explain database indexing",
            "Describe a backend project you built"
        ],

        "frontend developer":[
            "What is React?",
            "Explain Virtual DOM",
            "Difference between CSS Flexbox and Grid",
            "Describe a frontend project"
        ],

        "data analyst":[
            "Explain data cleaning process",
            "Difference between mean and median",
            "Explain a data analysis project",
            "How do you visualize data?"
        ]
    }

    questions = interview_bank.get(role,[
        "Explain your strongest project",
        "What technologies do you know?",
        "Why should we hire you?"
    ])

    tips = []

    if "python" not in skills:
        tips.append("Learn Python basics")

    if "project" not in skills:
        tips.append("Prepare to explain your projects clearly")

    tips.append("Practice explaining concepts clearly")
    tips.append("Prepare real project examples")

    return jsonify({
        "role":role,
        "questions":questions,
        "preparation_tips":tips
    })

# ---------------- AI INTERVIEW FEEDBACK ----------------
@app.route("/evaluate-answer", methods=["POST"])
def evaluate_answer():

    try:

        data = request.get_json()
        question = data.get("question","")
        answer = data.get("answer","")

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role":"system",
                    "content":"You are a technical interviewer evaluating answers."
                },
                {
                    "role":"user",
                    "content":f"Question: {question}\nCandidate Answer: {answer}\nGive score out of 10 and improvement tips."
                }
            ]
        )

        reply = completion.choices[0].message.content

        return jsonify({"evaluation":reply})

    except Exception as e:
        return jsonify({"error":str(e)})

    # ---------------- CAREER ROADMAP ----------------
@app.route("/career-roadmap", methods=["POST"])
def career_roadmap():

    data = request.get_json()

    goal = data.get("goal", "").lower()
    skills = data.get("skills", [])

    roadmap_bank = {

        "ai engineer":[
            "Learn Python programming",
            "Study Machine Learning fundamentals",
            "Build 2 Machine Learning projects",
            "Learn Deep Learning",
            "Participate in AI competitions or internships"
        ],

        "backend developer":[
            "Learn Python or Node.js",
            "Master Flask / Django framework",
            "Learn SQL and database design",
            "Build REST APIs",
            "Deploy backend projects to cloud"
        ],

        "frontend developer":[
            "Learn HTML, CSS and JavaScript",
            "Learn React framework",
            "Build responsive UI projects",
            "Learn API integration",
            "Deploy portfolio website"
        ],

        "data analyst":[
            "Learn Python and Pandas",
            "Learn Data Cleaning techniques",
            "Learn Data Visualization (Matplotlib / PowerBI)",
            "Work with SQL databases",
            "Build real data analysis projects"
        ]
    }

    roadmap = roadmap_bank.get(goal, [
        "Learn programming fundamentals",
        "Build projects",
        "Improve problem solving",
        "Create GitHub portfolio",
        "Apply for internships"
    ])

    return jsonify({
        "goal": goal,
        "current_skills": skills,
        "roadmap": roadmap
    })

    # ---------------- AI CAREER PREDICT ----------------
@app.route("/predict-career", methods=["POST"])
def predict_career():
    try:

        data = request.get_json()
        skills = data.get("skills", [])

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role":"system",
                    "content":"You are a career advisor AI."
                },
                {
                    "role":"user",
                    "content":f"Based on these skills {skills}, suggest best tech career path."
                }
            ]
        )

        reply = completion.choices[0].message.content

        return jsonify({"career_prediction":reply})

    except Exception as e:
        return jsonify({"error":str(e)})
        
    # ---------------- LIVE INTERNSHIPS ----------------
@app.route("/live-internships")
def live_internships():

    if not RAPIDAPI_KEY:
        return jsonify({"error":"API key missing"}),500

    role = request.args.get("role","software engineer internship")

    url = "https://jsearch27.p.rapidapi.com/search"

    querystring = {
        "query":role,
        "page":"1",
        "num_pages":"1",
        "date_posted":"3days",
        "location":"India"
    }

    headers = {
        "X-RapidAPI-Key":RAPIDAPI_KEY,
        "X-RapidAPI-Host":"jsearch27.p.rapidapi.com"
    }

    response = requests.get(url,headers=headers,params=querystring)

    data = response.json()

    results = []

    for job in data.get("data",[]):

        results.append({
            "company":job.get("employer_name"),
            "role":job.get("job_title"),
            "location":job.get("job_city"),
            "apply_link":job.get("job_apply_link"),
            "logo":job.get("employer_logo")
        })

    return jsonify(results)

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)