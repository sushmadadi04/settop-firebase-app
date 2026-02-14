from flask import Flask, render_template, request, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "settop_secret"

# FIREBASE CONNECT
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase key from environment variable
firebase_key = os.environ.get("FIREBASE_KEY")
firebase_dict = json.loads(firebase_key)

cred = credentials.Certificate(firebase_dict)
firebase_admin.initialize_app(cred)

db = firestore.client()
users_ref = db.collection("users")

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"]=="Naidu" and request.form["password"]=="041345":
            return redirect(url_for("dashboard"))
        flash("Invalid Login")
    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    today = datetime.today().strftime("%d-%m-%Y")
    users = users_ref.stream()
    dues=[]
    for u in users:
        d=u.to_dict()
        if d["due_date"]<=today:
            dues.append(d)
    return render_template("dashboard.html",dues=dues)

# CREATE USER
@app.route("/create",methods=["GET","POST"])
def create_user():
    if request.method=="POST":
        users_ref.add({
            "name":request.form["name"],
            "box_no":request.form["box_no"],
            "mobile":request.form["mobile"],
            "amount":request.form["amount"],
            "due_date":request.form["due_date"]
        })
        return redirect(url_for("dashboard"))
    return render_template("create_user.html")

# USER DETAILS
# USER DETAILS + SEARCH + DEFAULTERS
@app.route("/users")
def users():

    name = request.args.get("name")
    box = request.args.get("box")
    days = request.args.get("days")

    data = []
    for doc in users_ref.stream():
        u = doc.to_dict()
        u["id"] = doc.id
        data.append(u)

    # 🔍 SEARCH BY NAME
    if name:
        data = [u for u in data if name.lower() in u["name"].lower()]

    # 🔍 SEARCH BY BOX NUMBER
    if box:
        data = [u for u in data if box.lower() in u["box_no"].lower()]

    # 📌 DEFAULTER FILTER
    if days:
        today = datetime.today()
        days = int(days)

        filtered = []
        for u in data:
            due_date = datetime.strptime(u["due_date"], "%d-%m-%Y")
            overdue_days = (today - due_date).days

            if overdue_days >= days:
                filtered.append(u)

        data = filtered

    return render_template("user_details.html", users=data)

# DELETE USER
@app.route("/delete/<id>")
def delete(id):
    users_ref.document(id).delete()
    return redirect(url_for("users"))

# MARK PAID
@app.route("/paid/<id>")
def paid(id):
    new_due=(datetime.today()+timedelta(days=30)).strftime("%d-%m-%Y")
    users_ref.document(id).update({"due_date":new_due})
    return redirect(url_for("users"))

# EDIT USER
@app.route("/edit/<id>",methods=["GET","POST"])
def edit(id):
    doc=users_ref.document(id)
    user=doc.get().to_dict()
    if request.method=="POST":
        doc.update({
            "name":request.form["name"],
            "box_no":request.form["box_no"],
            "mobile":request.form["mobile"],
            "amount":request.form["amount"],
            "due_date":request.form["due_date"]
        })
        return redirect(url_for("users"))
    return render_template("edit_user.html",user=user,id=id)

if __name__ == "__main__":
    app.run()
# redeploy trigger