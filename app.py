import os
import requests as req
from flask import Flask, request, render_template_string,send_file
@app.route("/Aondofa.jpeg")
def photo():
    return send_file("Aondofa.jpeg", mimetype="image/jpeg")
app = Flask(__name__)

VERIFY_TOKEN = "techbeat123"
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("PHONE_ID", "")

# Demo voters - replace with real INEC data later
voters = {
    "aondofa terna|12-05-1990|makurdi": {"name": "Aondofa Terna Doose", "status": "READY", "location": "Makurdi LGA Office, Room 2"},
    "aondofa terna|01-01-1995|makurdi": {"name": "Aondofa Terna James", "status": "READY", "location": "Makurdi LGA Office, Room 1"},
    "mary ochanya|10-10-1992|otukpo": {"name": "Mary Ochanya", "status": "READY", "location": "Otukpo LGA Office"},
    "seun ade|05-05-1988|gboko": {"name": "Seun Ade", "status": "NOT READY", "location": ""},
}

user_state = {}

def get_reply(num, text):
    low = text.strip().lower()

    # Step 2: User is confirming YES / NO
    if num in user_state:
        voter = user_state[num]
        if low.startswith("yes"):
            del user_state[num]
            if voter["status"] == "READY":
                return f"GOOD NEWS, {voter['name']}. Your PVC is READY. Collect at: {voter['location']}"
            else:
                return f"Hello {voter['name']}, your PVC is NOT READY yet. Please check again later."
        if low.startswith("no"):
            del user_state[num]
            return "Okay, cancelled. Send your details again like: Aondofa Terna, 12-05-1990, Makurdi"
        # If they typed something else while waiting, treat as new search
        del user_state[num]

    # Step 1: Expect Name, DOB, LGA
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 3:
        return "Welcome to Techbeat! Send your details like this:\nAondofa Terna, 12-05-1990, Makurdi"

    name, dob, lga = parts[0].lower(), parts[1].strip(), parts[2].lower()
    key = f"{name}|{dob}|{lga}"

    if key in voters:
        voter = voters[key]
        user_state[num] = voter
       return f"I found: {voter['name']}, {dob}, {lga.title()}. Is this you? Reply YES or NO\n\n📸 Your photo: https://techbeat-demo.onrender.com/Aondofa.jpeg"
    
    # Check if same name exists with different DOB (duplicate name case)
    matches = [v for k, v in voters.items() if k.startswith(name + "|") and k.endswith("|" + lga)]
    if matches:
        return f"I found {len(matches)} people named {parts[0]} in {lga.title()}. Please send your full details with Date of Birth like: {parts[0]}, 12-05-1990, {lga.title()}"

    return "Name not found. Check spelling, DOB format DD-MM-YYYY, and LGA. Or your PVC may not be registered. Send again like: Aondofa Terna, 12-05-1990, Makurdi"

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Arial;background:#ece5dd;margin:0}.top{background:#075e54;color:white;padding:15px;font-weight:bold}.box{padding:15px}.msg{background:white;padding:10px;border-radius:8px;margin:10px 0;max-width:80%}.me{background:#dcf8c6;margin-left:auto}input{width:75%;padding:12px;border-radius:20px;border:1px solid #ccc}button{background:#25d366;border:none;padding:12px 18px;border-radius:20px;color:white;font-weight:bold}</style></head>
<body><div class="top">Techbeat - PVC Checker</div><div class="box" id="chat"><div class="msg">Welcome! Send: Name, DD-MM-YYYY, LGA<br>Example: Aondofa Terna, 12-05-1990, Makurdi</div></div>
<div style="position:fixed;bottom:0;width:100%;background:white;padding:10px;display:flex"><input id="t" placeholder="Type here..."><button onclick="send()">Send</button></div>
<script>async function send(){let v=document.getElementById('t').value;if(!v)return;document.getElementById('chat').innerHTML+=`<div class="msg me">${v}</div>`;document.getElementById('t').value='';let r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:v})});let j=await r.json();document.getElementById('chat').innerHTML+=`<div class="msg">${j.reply}</div>`;window.scrollTo(0,document.body.scrollHeight)}</script></body></html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    return {"reply": get_reply("web-test", data.get("msg",""))}

@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Wrong token"
    try:
        data = request.json
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            msg = entry["messages"][0]
            sender = msg["from"]
            text = msg["text"]["body"]
            reply = get_reply(sender, text)
            req.post(f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
                json={"messaging_product":"whatsapp","to":sender,"text":{"body":reply}})
    except Exception as e:
        print("Webhook error:", e)
    return "OK"

if __name__=="__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
