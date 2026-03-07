/* API URL */

const API="https://innovatex-backend-production.up.railway.app"


/* AUTO GREETING */

setTimeout(()=>{
bot("Hi 👋 I am your InnovateX Internship AI Assistant. Ask me anything about internships.")
},800)



/* BOT MESSAGE */

function bot(text){

let chat=document.getElementById("chat")

let div=document.createElement("div")

div.className="bot"

div.innerText=text

chat.appendChild(div)

chat.scrollTop=chat.scrollHeight

}



/* USER MESSAGE */

function user(text){

let chat=document.getElementById("chat")

let div=document.createElement("div")

div.className="user"

div.innerText=text

chat.appendChild(div)

chat.scrollTop=chat.scrollHeight

}



/* SEND MESSAGE */

async function send(){

let msg=document.getElementById("msg").value.trim()

if(msg==="") return

user(msg)

document.getElementById("msg").value=""

let typing=document.createElement("div")

typing.className="bot"

typing.innerText="AI is typing..."

typing.id="typing"

document.getElementById("chat").appendChild(typing)

try{

let response=await fetch(API+"/ai-chat",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
question:msg
})
})

let data=await response.json()

let typingEl=document.getElementById("typing")
if(typingEl) typingEl.remove()

if(data.reply){
bot(data.reply)
}
else if(data.answer){
bot(data.answer)
}
else{
bot("AI response unavailable")
}

}catch(error){

let typingEl=document.getElementById("typing")
if(typingEl) typingEl.remove()

bot("⚠️ AI server error")

}

}



/* ENTER KEY SEND */

document.getElementById("msg").addEventListener("keypress",function(e){

if(e.key==="Enter"){
send()
}

})



/* QUICK BUTTONS */

function sayHi(){

user("Hi")

sendAI("Hi")

}



function internship(){

user("I want internship")

bot("Please upload your resume so I can analyze your skills.")

createUploadButton()

}



/* CREATE RESUME UPLOAD BUTTON */

function createUploadButton(){

let btn=document.createElement("button")

btn.innerText="Upload Resume"

btn.className="upload"

btn.onclick=uploadResume

document.getElementById("chat").appendChild(btn)

}



/* UPLOAD RESUME */

async function uploadResume(){

let input=document.createElement("input")

input.type="file"

input.accept=".pdf"

input.onchange=async function(){

let file=input.files[0]

let formData=new FormData()

formData.append("resume",file)

bot("Uploading resume...")

try{

let res=await fetch(API+"/upload-resume",{
method:"POST",
body:formData
})

let data=await res.json()

bot("Resume uploaded successfully ✅")

detectSkills(data.resume_text || "")

}catch(e){

bot("⚠️ Resume upload failed")

}

}

input.click()

}



/* SKILL DETECTION */

function detectSkills(text){

let skills=[]

let t=text.toLowerCase()

if(t.includes("python")) skills.push("Python")
if(t.includes("java")) skills.push("Java")
if(t.includes("machine learning")) skills.push("Machine Learning")
if(t.includes("sql")) skills.push("SQL")
if(t.includes("html")) skills.push("HTML")
if(t.includes("css")) skills.push("CSS")

if(skills.length===0){

bot("No major skills detected")

}else{

bot("Detected Skills: "+skills.join(", "))

recommendInternships(skills)

}

}



/* INTERNSHIP RECOMMENDATION */

async function recommendInternships(skills){

bot("Finding internships based on your skills...")

try{

let res=await fetch(API+"/live-internships")

let data=await res.json()

if(!data || data.length===0){
bot("No internships found")
return
}

data.slice(0,3).forEach(job=>{

bot(
"Company: "+job.company+
"\nRole: "+job.title+
"\nLocation: "+job.location
)

})

}catch(e){

bot("⚠️ Internship API error")

}

}



/* INTERVIEW SIMULATOR */

async function startInterview(){

bot("Starting interview preparation...")

try{

let res=await fetch(API+"/mcq")

let data=await res.json()

bot("Sample Interview Question:")

bot(data.question)

}catch(e){

bot("⚠️ Interview API error")

}

}



/* QUICK AI CALL */

async function sendAI(message){

let typing=document.createElement("div")

typing.className="bot"

typing.innerText="AI is typing..."

typing.id="typing"

document.getElementById("chat").appendChild(typing)

try{

let response=await fetch(API+"/ai-chat",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
question:message
})
})

let data=await response.json()

let typingEl=document.getElementById("typing")
if(typingEl) typingEl.remove()

bot(data.reply || data.answer || "AI response unavailable")

}catch(e){

let typingEl=document.getElementById("typing")
if(typingEl) typingEl.remove()

bot("⚠️ AI server error")

}

}



/* LOGOUT */

function logout(){

localStorage.removeItem("loggedUser")

window.location="login.html"

}