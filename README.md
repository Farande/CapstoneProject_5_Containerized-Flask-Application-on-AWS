# Containerized Flask Application on AWS – Company Complaint System

## 1. Project Title and Objective

**Project Title:** Containerized Flask Application on AWS (Company Complaint System)

**Objective:**
This project is a Flask web application that lets employees submit and track complaints, and lets administrators review them through a dashboard. The application is packaged as a **Docker container** and deployed on AWS. All data (users, complaints and departments) is stored in **Amazon DynamoDB**, and application logs are sent to **Amazon CloudWatch**.

The project demonstrates containerization, serverless NoSQL data modelling, IAM-based access, network security with security groups, and monitoring on AWS.

### Features

- Employee registration and login, with department selection (39 common large-company departments are seeded)
- Employee dashboard and complaint history
- Complaint submission and tracking
- Administrator dashboard with counts and reports
- DynamoDB backend (the application no longer uses RDS/MySQL)
- Docker + Gunicorn deployment

---

## 2. AWS Services Used

| Service | Purpose |
|---|---|
| **Amazon DynamoDB** | Stores the `Users`, `Complaints` and `Departments` tables (on-demand billing) |
| **Amazon ECS** | Runs the containerized Flask application (`complaint-cluster` and its task) |
| **Amazon ECR** | Stores the Docker image *(if used, confirm in your account)* |
| **AWS IAM** | Task/execution role granting read/write access to the DynamoDB tables and the complaints index |
| **Amazon VPC Security Groups** | Controls inbound access to the application |
| **Amazon CloudWatch Logs** | Collects application logs for monitoring and troubleshooting |

**Other technologies:** Python, Flask, Gunicorn, Docker, Boto3

---

## 3. Architecture / Workflow

### Architecture

```
            Employee / Administrator
                      |
                      | HTTP request
                      v
             Security Group (inbound rules)
                      |
                      v
        ECS Cluster: complaint-cluster
        +-----------------------------+
        |  Task: Docker container     |
        |  Flask app + Gunicorn       |
        +--------------+--------------+
                       |                    |
                       | Boto3 (IAM role)   | Application logs
                       v                    v
              Amazon DynamoDB         Amazon CloudWatch Logs
        +----------------------+
        | Users                |
        | Complaints           |
        |   └ user_id-index    |
        | Departments          |
        +----------------------+
```

### Application Workflow

1. A user opens the home page and chooses **Employee Portal** or **Admin**.
2. An employee registers (choosing a department) and logs in.
3. The employee submits a complaint, which is saved to the `Complaints` table.
4. The employee dashboard and complaint history read complaints through the `user_id-index`.
5. An administrator logs in and views counts and reports across all complaints.
6. Every request and error is written to CloudWatch Logs.

### DynamoDB Data Model

| Table | Partition key | Notes |
|---|---|---|
| `Users` | `email` | Employee and administrator accounts |
| `Complaints` | `complaint_id` | Global secondary index `user_id-index`, ordered by `created_at` |
| `Departments` | `id` | Seeded with 39 common large-company functions (original IDs 1–7 preserved) |

All tables use **on-demand billing**.

### Repository Structure

```
CapstoneProject_5_Containerized-Flask-Application-on-AWS/
│
├── Screenshot/            # Project screenshots
├── Scripts/               # Helper scripts
├── static/                # CSS, JavaScript, images
├── templates/             # HTML templates
├── app.py                 # Flask application
├── setup_dynamodb.py      # Creates tables and seeds departments
├── Dockerfile             # Container image definition
├── .dockerignore
├── .env.example           # Example configuration
├── requirements.txt
└── README.md
```

---

## 4. Implementation Steps

1. **Build the Flask application** with registration, login, complaint submission, employee dashboard, complaint history and admin dashboard.
2. **Design the DynamoDB tables** (`Users`, `Complaints`, `Departments`) and a `user_id-index` GSI so employees can list their own complaints ordered by date.
3. **Write `setup_dynamodb.py`** to create the tables, seed the departments and optionally create the first administrator.
4. **Remove the RDS/MySQL dependency** and move all data access to Boto3 and DynamoDB.
5. **Containerize the app** with a Dockerfile that runs the application with Gunicorn.
6. **Create the IAM role** that gives the application read/write access to the three tables and the complaints index. The role used for initial setup also needs permission to create and describe tables.
7. **Push the image** to a container registry and create an **ECS cluster** (`complaint-cluster`) with a task running the container.
8. **Configure the security group** to allow inbound traffic only on the application port.
9. **Enable CloudWatch Logs** for the container to monitor the application.
10. **Test** registration, complaint submission, dashboards and logs end to end.

---

## 5. Screenshots

### Home Page (Employee Portal and Admin)
![Home page with Employee portal and Admin](Screenshot/home%20page%20with%20Employee%20portal%20and%20Admin.png)

### Employee Dashboard
![Employee Dashboard](Screenshot/Employee%20Dashboard.png)

### Complaint History Table
![Complaint history table](Screenshot/Complaint%20history%20table%20.png)

### Admin Dashboard
![Admin Dashboard](Screenshot/Admin%20Dashboard.png)

### ECS Cluster with the Running Task
![complaint-cluster with the task](Screenshot/complaint-cluster%20with%20the%20task.png)

### Security Group Configuration
![Security Group Configuration](Screenshot/Security%20Group%20Configuration.png)

### CloudWatch Application Logs
![CloudWatch Application Logs](Screenshot/CloudWatch%20Application%20Logs.png)

---

## 6. How to Run or Deploy the Project

### Prerequisites

- Python 3.12 (or another currently supported Python 3.10+ release)
- An AWS account and credentials configured through the standard AWS credential chain
- Docker (for container builds)

### Run Locally

1. Clone the repository and install the dependencies:
   ```bash
   git clone https://github.com/Farande/CapstoneProject_5_Containerized-Flask-Application-on-AWS.git
   cd CapstoneProject_5_Containerized-Flask-Application-on-AWS
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set a unique `FLASK_SECRET_KEY`. The table names and AWS region can also be changed there.
3. Configure AWS credentials. For AWS deployments, prefer an **IAM role** instead of putting access keys in `.env`.
4. Create the tables and seed the departments:
   ```powershell
   python setup_dynamodb.py
   ```
5. Optionally create the first administrator:
   ```powershell
   python setup_dynamodb.py --admin-email admin@example.com --admin-password "choose-a-strong-password"
   ```
6. Start the application:
   ```bash
   python app.py
   ```

Re-run `python setup_dynamodb.py` at any time to add or refresh the seeded department choices in the registration form.

### Run with Docker

```bash
docker build -t complaint-system .
docker run -p 5000:5000 --env-file .env complaint-system
```

Adjust the port to match the one used in your Dockerfile and Gunicorn command.

### Deploy on AWS (ECS)

1. Build the image and push it to your container registry (for example Amazon ECR).
2. Create the DynamoDB tables by running `setup_dynamodb.py` once with credentials allowed to create and describe tables.
3. Create an IAM task role with read/write access to the `Users`, `Complaints` and `Departments` tables and the `user_id-index`.
4. Create an ECS cluster (`complaint-cluster`), a task definition that uses the image, and run the task or service.
5. Set the task's environment variables (`FLASK_SECRET_KEY`, table names, AWS region).
6. Attach a security group that allows inbound traffic on the application port.
7. Turn on CloudWatch logging in the task definition.
8. Open the task's public address and confirm the home page loads.

### Security Notes

- **Never commit `.env`**. Keep only `.env.example` in the repository, and add `.env`, `__pycache__/` and `*.pem` to `.gitignore`.
- Use an IAM role instead of access keys wherever possible.
- Open only the required port in the security group.
- Use a strong, unique `FLASK_SECRET_KEY` and a strong administrator password.

---

## 7. Key Learnings

- **Containerization:** Packaging a Flask app with Docker and Gunicorn makes the deployment portable and repeatable.
- **DynamoDB data modelling:** Designing tables around access patterns, such as a global secondary index (`user_id-index`) ordered by `created_at` for per-employee complaint history.
- **Migrating from SQL to NoSQL:** Replacing RDS/MySQL with DynamoDB removed the need to manage a database server, and on-demand billing removed capacity planning.
- **IAM roles over access keys:** Giving the application a role with only the table and index permissions it needs is safer than storing credentials in `.env`.
- **Network security:** Security groups act as the first line of defense by restricting which traffic can reach the container.
- **Observability:** CloudWatch Logs make it possible to troubleshoot a running container without logging into it.
- **Scaling considerations:** Admin counts and reports use table scans, which is fine for a demo but should be replaced with purpose-built aggregates or indexes for a large production dataset.
- **Configuration management:** Keeping secrets and environment-specific settings out of the code and out of version control.

---

