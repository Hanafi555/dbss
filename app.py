from flask import Flask, render_template, request
import joblib
from groq import Groq
import requests

import os

app = Flask(__name__)

# ------------------- Load Models Once at Startup -------------------
# These files must be in the same folder as app.py!
#cv = joblib.load("cv_encoder.pkl")
#model = joblib.load("model.pkl")
#os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# for cloud ..........

@app.route("/",methods=["GET","POST"])
def igindex():
    return render_template("index.html")

@app.route("/main",methods=["GET","POST"])
def main():
    q = request.form.get("q")
    # db
    return render_template("main.html")

@app.route("/llama",methods=["GET","POST"])
def llama():
    return render_template("llama.html")



# your real route
@app.route("/llama_reply", methods=["GET", "POST"])
def llama_reply():
    q = request.form.get("q")
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": q}]
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        print(f"[LLAMA ERROR]: {str(e)}")
        answer = f"Error: {str(e)}"
    return render_template("llama_reply.html", r=answer)

# your debug route (temporary)
@app.route("/groq_test")
def groq_test():
    try:
        r = requests.get("https://api.groq.com", timeout=5)
        return f"Groq API status: {r.status_code}"
    except Exception as e:
        return f"Groq API error: {str(e)}"



@app.route("/deepseek",methods=["GET","POST"])
def deepseek():
    return render_template("deepseek.html")

@app.route("/deepseek_reply",methods=["GET","POST"])
def deepseek_reply():
    q = request.form.get("q")
    try:
        client = Groq()
        completion = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[{"role": "user", "content": q}]
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"Error: {str(e)}"
    return render_template("deepseek_reply.html", r=answer)

@app.route("/dbs",methods=["GET","POST"])
def dbs():
    return render_template("dbs.html")

@app.route("/check_spam", methods=["GET", "POST"])
def check_spam():
    return render_template("check_spam.html")

@app.route("/prediction",methods=["GET","POST"])
def prediction():
    q = float(request.form.get("q"))
    # load model
    dbs_model = joblib.load("dbs.jl")
    pred = dbs_model.predict([[q]])
    return render_template("prediction.html", r=pred)

@app.route("/telegram",methods=["GET","POST"])
def telegram():
    domain_url = request.url_root
    delete_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    set_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={domain_url}/webhook"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    if webhook_response.status_code == 200:
        status = "The telegram bot is running. Please check with the telegram bot. @The_Prediction_bot"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    return render_template("telegram.html", status=status)

@app.route("/stop_telegram",methods=["GET","POST"])
def stop_telegram():
    domain_url = 'https://dbss-1-sd96.onrender.com'
    delete_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    webhook_response = requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    if webhook_response.status_code == 200:
        status = "The telegram bot is stopped. "
    else:
        status = "Failed to stop the telegram bot. Please check the logs."
    return render_template("telegram.html", status=status)

@app.route("/webhook",methods=["GET","POST"])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        query = update["message"]["text"]

        client = Groq()
        completion_ds = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": query}]
        )
        response_message = completion_ds.choices[0].message.content

        send_message_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(send_message_url, json={
            "chat_id": chat_id,
            "text": response_message
        })
    return('ok', 200)

# ----------- CHECK SPAM FEATURE -----------
@app.route("/check_spam_reply", methods=["GET", "POST"])
def check_spam_reply():
    if request.method == "POST":
        q = request.form.get("q", "")
        if not q:
            result = "No input provided."
        else:
            try:
                q_vec = cv.transform([q])
                result = model.predict(q_vec)[0]
            except Exception as e:
                result = f"Error: {str(e)}"
        return render_template("check_spam_reply.html", r=result, q=q)
    else:
        return render_template("check_spam_reply.html", r="", q="")
# ------------------------------------------

if __name__ == "__main__":
    app.run()
