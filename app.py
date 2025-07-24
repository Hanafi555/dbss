from flask import Flask, render_template, request
import joblib
from groq import Groq
import requests
import joblib
import sqlite3
import datetime

import os

app = Flask(__name__)

# ------------------- Load Models Once at Startup -------------------
# These files must be in the same folder as app.py!
#os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# for cloud ..........

@app.route("/",methods=["GET","POST"])
def igindex():
    return render_template("index.html")

@app.route("/main",methods=["GET","POST"])
def main():
    q = request.form.get("q")
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("user.db")
    conn.execute("INSERT INTO user (name,timestamp) VALUES(?,?)", (q, t ))
    conn.commit()
    conn.close()
    return render_template("main.html")

@app.route("/user_log", methods=["POST", "GET"])
def user_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute('''select * from user''')
    r=""
    for row in c:
      print(row)
      r = r + str(row)
    c.close()
    conn.close()
    return render_template("user_log.html", r=r )

@app.route("/delete_log", methods=["GET", "POST"])
def delete_log():
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user')
    conn.commit()
    conn.close()
    return render_template("delete_log.html", message="User log deleted successfully.")

@app.route("/llama",methods=["GET","POST"])
def llama():
    return render_template("llama.html")

# your real route
@app.route("/llama_reply", methods=["GET", "POST"])
def llama_reply():
    q = request.form.get("q")
    try:
        client = Groq()
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": q}]
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        print(f"[LLAMA ERROR]: {str(e)}")
        answer = f"Error: {str(e)}"
    return render_template("llama_reply.html", r=answer)

@app.route("/deepseek",methods=["GET","POST"])
def deepseek():
    return render_template("deepseek.html")


@app.route("/deepseek_reply",methods=["GET","POST"])
def deepseek_reply():
    q = request.form.get("q")

    # load model
    client = Groq()
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {
                "role": "user",
                "content": q
            }
        ]
    )
    # print(completion.choices[0].message.content)

    return(render_template("deepseek_reply.html", r=completion.choices[0].message.content))

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
                # Load vectorizer and model
                cv = joblib.load("cv_encoder.pkl")
                model = joblib.load("lr_model.pkl")
                # Transform input and predict
                q_vec = cv.transform([q])
                result = model.predict(q_vec)[0]
            except Exception as e:
                result = f"Error: {str(e)}"
        return render_template("check_spam_reply.html", r=result, q=q)
    else:
        return render_template("check_spam_reply.html", r="", q="")
    
# ------------------------------------------
@app.route('/sepia_hf', methods=['GET', 'POST'])
def sepia_hf():
    return render_template("sepia_hf.html")


if __name__ == "__main__":
    app.run()
