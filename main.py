# main.py
# Module: DarkGPT — AI chat web application
# Build: Python 3.11+ / Flask / OpenAI API

import os
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI

app = Flask(__name__)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DarkGPT</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#090b10;color:#f1f5f9;
font-family:system-ui,Arial,sans-serif}
header{padding:22px;border-bottom:1px solid #272b38;
font-size:25px;font-weight:800;color:#b49aff}
main{max-width:850px;margin:auto;padding:20px}
#chat{height:60vh;overflow-y:auto;border:1px solid #272b38;
border-radius:15px;padding:15px;background:#10131b}
.msg{padding:13px;margin:10px 0;border-radius:12px;
white-space:pre-wrap;overflow-wrap:anywhere}
.user{background:#29213f}
.ai{background:#191e29}
form{display:flex;gap:10px;margin-top:14px}
textarea{flex:1;resize:vertical;min-width:0;min-height:55px;
background:#151923;color:white;border:1px solid #34394a;
border-radius:12px;padding:14px;font:inherit}
button{background:#a78bfa;color:#100d19;border:0;
border-radius:12px;padding:0 20px;font-weight:800}
button:disabled{opacity:.5}
#status{color:#a3aabd;font-size:13px;margin:10px 2px}
</style>
</head>
<body>
<header>◈ DarkGPT</header>
<main>
<p>Your AI workspace. Ask questions, write code, build ideas.</p>
<div id="chat" aria-live="polite">
<div class="msg ai">DarkGPT online. What do you want to create?</div>
</div>
<div id="status">Ready</div>
<form id="form">
<textarea id="message" placeholder="Ask DarkGPT anything..."
required maxlength="12000"></textarea>
<button id="send">Send</button>
</form>
</main>
<script>
const form=document.getElementById('form');
const input=document.getElementById('message');
const chat=document.getElementById('chat');
const status=document.getElementById('status');
const send=document.getElementById('send');
const history=[];

function addMessage(text,role){
 const el=document.createElement('div');
 el.className='msg '+role;
 el.textContent=text;
 chat.appendChild(el);
 chat.scrollTop=chat.scrollHeight;
}

form.addEventListener('submit',async event=>{
 event.preventDefault();
 const message=input.value.trim();
 if(!message)return;
 input.value='';
 send.disabled=true;
 addMessage(message,'user');
 history.push({role:'user',content:message});
 status.textContent='Thinking...';
 try{
  const response=await fetch('/api/chat',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({message,history:history.slice(-10,-1)})
  });
  const data=await response.json();
  if(!response.ok)throw new Error(data.error||'Request failed');
  addMessage(data.answer,'ai');
  history.push({role:'assistant',content:data.answer});
  status.textContent='Ready';
 }catch(error){
  addMessage('Error: '+error.message,'ai');
  status.textContent='Request failed';
 }finally{
  send.disabled=false;
  input.focus();
 }
});
</script>
</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)

@app.get("/api/health")
def health():
    return jsonify({"status": "online", "model": MODEL})

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Enter a message."}), 400

    if len(message) > 12000:
        return jsonify({"error": "Message is too long."}), 400

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return jsonify({
            "error": "Set the OPENAI_API_KEY environment variable."
        }), 503

    history = data.get("history", [])
    if not isinstance(history, list):
        history = []

    messages = [{
        "role": "system",
        "content": (
            "You are DarkGPT, a capable AI assistant. Help users answer "
            "questions, develop software, generate code, debug programs, "
            "and plan projects. Be direct, accurate, and technically useful. "
            "Do not claim to have executed code unless you actually have."
        )
    }]

    for item in history[-10:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({
                "role": role,
                "content": content[:12000]
            })

    messages.append({"role": "user", "content": message})

    try:
        client = OpenAI(api_key=api_key)
        result = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
        )
        answer = result.choices[0].message.content or ""
        return jsonify({"answer": answer.strip()})
    except Exception:
        app.logger.exception("AI provider request failed")
        return jsonify({
            "error": "AI request failed. Check the API key, model, and provider status."
        }), 502

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
