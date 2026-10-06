import os
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from departments import DEPARTMENT_NAMES
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
USERS_TABLE = os.getenv("USERS_TABLE", "Users")
COMPLAINTS_TABLE = os.getenv("COMPLAINTS_TABLE", "Complaints")
DEPARTMENTS_TABLE = os.getenv("DEPARTMENTS_TABLE", "Departments")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
users_table = dynamodb.Table(USERS_TABLE)
complaints_table = dynamodb.Table(COMPLAINTS_TABLE)
departments_table = dynamodb.Table(DEPARTMENTS_TABLE)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "development-secret-key")


def get_all_items(operation, **kwargs):
    items = []
    response = operation(**kwargs)
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        response = operation(**kwargs)
        items.extend(response.get("Items", []))

    return items


def get_departments():
    departments = get_all_items(departments_table.scan)
    existing_ids = {department["id"] for department in departments}
    missing_departments = [
        {"id": str(index), "department_name": name}
        for index, name in enumerate(DEPARTMENT_NAMES, start=1)
        if str(index) not in existing_ids
    ]

    if missing_departments:
        with departments_table.batch_writer() as batch:
            for department in missing_departments:
                batch.put_item(Item=department)
        departments.extend(missing_departments)

    return sorted(departments, key=lambda department: department["department_name"])


def get_department_names():
    return {
        department["id"]: department["department_name"]
        for department in get_all_items(departments_table.scan)
    }


def get_complaints_for_user(user_id):
    complaints = get_all_items(
        complaints_table.query,
        IndexName="user_id-index",
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
    )
    department_names = get_department_names()
    for complaint in complaints:
        complaint["department_name"] = department_names.get(
            complaint["department_id"], ""
        )
    return complaints


def get_all_complaints():
    complaints = get_all_items(complaints_table.scan)
    users_by_email = {
        user["email"]: user for user in get_all_items(users_table.scan)
    }
    department_names = get_department_names()

    for complaint in complaints:
        user = users_by_email.get(complaint["user_id"], {})
        complaint["employee_id"] = user.get("employee_id", "")
        complaint["employee_name"] = user.get("name", "")
        complaint["email"] = user.get("email", "")
        complaint["department_name"] = department_names.get(
            complaint["department_id"], ""
        )

    return sorted(complaints, key=lambda complaint: complaint["created_at"], reverse=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    departments = get_departments()

    if request.method == "POST":
        employee_id = request.form.get("employee_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department_id = request.form.get("department_id", "").strip()

        if not all((employee_id, name, email, password, department_id)):
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if not departments_table.get_item(Key={"id": department_id}).get("Item"):
            flash("Please select a valid department.", "danger")
            return redirect(url_for("register"))

        duplicate_employee = any(
            user.get("employee_id") == employee_id
            for user in get_all_items(users_table.scan)
        )
        if duplicate_employee:
            flash("Employee ID or email may already exist.", "danger")
            return redirect(url_for("register"))

        user = {
            "email": email,
            "employee_id": employee_id,
            "name": name,
            "password": generate_password_hash(password),
            "department_id": department_id,
            "role": "employee",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            users_table.put_item(
                Item=user,
                ConditionExpression="attribute_not_exists(email)",
            )
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                flash("Employee ID or email may already exist.", "danger")
                return redirect(url_for("register"))
            raise

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", departments=departments)


@app.route("/login", methods=["GET", "POST"])
def login():
    portal_role = request.values.get("portal", "").strip().lower()
    if portal_role not in {"", "employee", "admin"}:
        portal_role = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = users_table.get_item(Key={"email": email}).get("Item")

        if user and check_password_hash(user["password"], password):
            if portal_role and user["role"] != portal_role:
                flash(
                    "This account does not have access to the selected portal.",
                    "danger",
                )
                return render_template("login.html", portal_role=portal_role)

            session["user_id"] = user["email"]
            session["employee_id"] = user["employee_id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["department_id"] = user["department_id"]

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("employee_dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html", portal_role=portal_role)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/employee/dashboard")
def employee_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "employee":
        return redirect(url_for("admin_dashboard"))

    complaints = get_complaints_for_user(session["user_id"])
    return render_template(
        "employee_dashboard.html",
        total=len(complaints),
        pending=sum(complaint["status"] == "Pending" for complaint in complaints),
        resolved=sum(complaint["status"] == "Resolved" for complaint in complaints),
    )


@app.route("/complaint/new", methods=["GET", "POST"])
def new_complaint():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "employee":
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        complaint_type = request.form.get("complaint_type", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "")
        if not complaint_type or not description or priority not in {
            "Low",
            "Medium",
            "High",
            "Critical",
        }:
            flash("Please complete all complaint fields with valid values.", "danger")
            return redirect(url_for("new_complaint"))

        complaint_id = "CMP-" + uuid.uuid4().hex[:8].upper()
        now = datetime.now(timezone.utc).isoformat()
        complaints_table.put_item(
            Item={
                "complaint_id": complaint_id,
                "user_id": session["user_id"],
                "employee_id": session["employee_id"],
                "department_id": session["department_id"],
                "complaint_type": complaint_type,
                "description": description,
                "priority": priority,
                "status": "Pending",
                "resolution": "",
                "created_at": now,
                "updated_at": now,
                "resolved_at": "",
            },
            ConditionExpression="attribute_not_exists(complaint_id)",
        )
        flash(f"Complaint {complaint_id} registered successfully.", "success")
        return redirect(url_for("complaint_history"))

    return render_template("complaint_form.html")


@app.route("/complaints")
def complaint_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "employee":
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "complaint_history.html",
        complaints=get_complaints_for_user(session["user_id"]),
    )


@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("employee_dashboard"))

    complaints = get_all_items(complaints_table.scan)
    return render_template(
        "admin_dashboard.html",
        total=len(complaints),
        pending=sum(complaint["status"] == "Pending" for complaint in complaints),
        in_progress=sum(
            complaint["status"] == "In Progress" for complaint in complaints
        ),
        resolved=sum(complaint["status"] == "Resolved" for complaint in complaints),
    )


@app.route("/admin/complaints")
def all_complaints():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("employee_dashboard"))

    return render_template("all_complaints.html", complaints=get_all_complaints())


@app.route("/admin/complaint/<string:complaint_id>", methods=["GET", "POST"])
def complaint_details(complaint_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("employee_dashboard"))

    if request.method == "POST":
        status = request.form.get("status", "")
        if status not in {"Pending", "In Progress", "Resolved", "Rejected"}:
            flash("Please select a valid complaint status.", "danger")
            return redirect(url_for("complaint_details", complaint_id=complaint_id))

        resolution = request.form.get("resolution", "").strip()
        now = datetime.now(timezone.utc).isoformat()
        complaints_table.update_item(
            Key={"complaint_id": complaint_id},
            UpdateExpression=(
                "SET #status = :status, resolution = :resolution, "
                "resolved_at = :resolved_at, updated_at = :updated_at"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": status,
                ":resolution": resolution,
                ":resolved_at": now if status == "Resolved" else "",
                ":updated_at": now,
            },
            ConditionExpression="attribute_exists(complaint_id)",
        )
        flash("Complaint updated successfully.", "success")
        return redirect(url_for("complaint_details", complaint_id=complaint_id))

    complaint = complaints_table.get_item(
        Key={"complaint_id": complaint_id}
    ).get("Item")
    if not complaint:
        return "Complaint not found", 404

    user = users_table.get_item(Key={"email": complaint["user_id"]}).get("Item", {})
    department = departments_table.get_item(
        Key={"id": complaint["department_id"]}
    ).get("Item", {})
    complaint["employee_id"] = user.get("employee_id", "")
    complaint["employee_name"] = user.get("name", "")
    complaint["email"] = user.get("email", "")
    complaint["department_name"] = department.get("department_name", "")
    return render_template("complaint_details.html", complaint=complaint)


@app.route("/admin/analytics")
def analytics():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("employee_dashboard"))

    complaints = get_all_items(complaints_table.scan)
    department_data = []
    for department in get_departments():
        department_complaints = [
            complaint
            for complaint in complaints
            if complaint["department_id"] == department["id"]
        ]
        department_data.append(
            {
                "department_name": department["department_name"],
                "total_complaints": len(department_complaints),
                "resolved_complaints": sum(
                    complaint["status"] == "Resolved"
                    for complaint in department_complaints
                ),
                "pending_complaints": sum(
                    complaint["status"] == "Pending"
                    for complaint in department_complaints
                ),
                "in_progress_complaints": sum(
                    complaint["status"] == "In Progress"
                    for complaint in department_complaints
                ),
            }
        )

    return render_template("analytics.html", department_data=department_data)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )
