# Company Complaint Management System

A web-based **Company Complaint Management System** that allows employees to register, log in, submit complaints, and track their complaint status. Administrators can manage complaints, update their status, add responses, and view department-wise complaint analytics.

The application is developed using **Flask** and containerized using **Docker**. It is deployed on **Amazon ECS Fargate**, with **Amazon DynamoDB** used as the database.

---

##  Features

### Employee Features

* Employee registration
* Employee login
* Select department
* Submit a complaint
* View submitted complaints
* Check complaint status
* View admin response
* Track complaint resolution

### Admin Features

* Admin login
* View all employee complaints
* View complaint details
* Update complaint status
* Add response to complaints
* Resolve complaints
* View department-wise complaint analytics

---

## Technologies Used

| Technology                          | Purpose                   |
| ----------------------------------- | ------------------------- |
| Python                              | Backend programming       |
| Flask                               | Web application framework |
| HTML/CSS                            | Frontend                  |
| JavaScript                          | Client-side functionality |
| Docker                              | Containerization          |
| Amazon ECR                          | Docker image storage      |
| Amazon ECS Fargate                  | Application deployment    |
| Amazon DynamoDB                     | Database                  |
| AWS Systems Manager Parameter Store | Secure configuration      |
| AWS IAM                             | Access control            |
| Amazon CloudWatch                   | Application logs          |
| Gunicorn                            | Production web server     |

---

## Architecture

                 Employee / Admin
                        |
                        v
              +-------------------+
              |   Flask Web App   |
              +-------------------+
                        |
                        v
              +-------------------+
              |  Docker Container |
              +-------------------+
                        |
                        v
              +-------------------+
              |    Amazon ECR     |
              +-------------------+
                        |
                        v
              +-------------------+
              |  Amazon ECS       |
              |     Fargate       |
              +-------------------+
                  /      |       \
                 /       |        \
                v        v         v
        DynamoDB     Parameter   CloudWatch
                     Store         Logs

---

## Project Structure

company-complaint-system/
├─ app.py
├─ setup_dynamodb.py
├─ departments.py
├─ requirements.txt
├─ Dockerfile
├─ README.md
├─ .env
├─ static/
│  ├─ css/
│  │  └─ style.css
│  └─ js/
│     ├─ app.js
│     └─ analytics.js
├─ templates/
│  ├─ base.html
│  ├─ index.html
│  ├─ login.html
│  ├─ register.html
│  ├─ employee_dashboard.html
│  ├─ complaint_form.html
│  ├─ complaint_history.html
│  ├─ complaint_details.html
│  ├─ admin_dashboard.html
│  ├─ all_complaints.html
│  └─ analytics.html
├─ data/
│  └─ (app data / local storage related files if added later)
└─ venv/
   └─ Python virtual environment


---

## DynamoDB Tables

The application uses three DynamoDB tables.

### 1. Users

Stores employee and administrator account information.

**Partition Key:**


email


Example:


admin@company.com
employee@company.com


---

### 2. Complaints

Stores employee complaints and their current status.

**Partition Key:**


complaint_id


A Global Secondary Index is also used:


user_id-index


This allows complaints to be retrieved for a particular employee.



### 3. Departments

Stores the departments available in the company.

Example departments:


IT
Finance
HR
Sales
Marketing
Operations
Administration


---

##  Environment Variables

Create a `.env` file for local development.


AWS_REGION=ap-south-1

USERS_TABLE=Users
COMPLAINTS_TABLE=Complaints
DEPARTMENTS_TABLE=Departments

FLASK_SECRET_KEY=your-secret-key

> Do not upload the `.env` file to GitHub.

---

## Installation

### 1. Clone the Repository


git clone https://github.com/Farande/company-complaint-system.git


Go inside the project:


cd company-complaint-system


---

### 2. Create a Virtual Environment

On Windows:


python -m venv venv


Activate it:


venv\Scripts\activate


---

### 3. Install Dependencies


pip install -r requirements.txt


---

## Configure AWS CLI

Make sure AWS CLI is installed and configured.


aws configure


Enter:


AWS Access Key ID
AWS Secret Access Key
Default region: ap-south-1
Output format: json


Check the configuration:


aws sts get-caller-identity


---

##  Create DynamoDB Tables

Run the DynamoDB setup script:


python setup_dynamodb.py --admin-email admin@company.com --admin-password "Admin@123"


This creates the required DynamoDB tables and administrator account.

---

## Run the Application Locally

Start the Flask application:


python app.py


The application should be available at:


http://localhost:5000


---

##  Docker Setup

### Build the Docker Image


docker build -t complaint-system .


Check the image:


docker images


---

### Run the Docker Container

docker run --rm -p 5000:5000 `
  --env-file .env `
  -v "$env:USERPROFILE\.aws:/root/.aws:ro" `
  complaint-system


Open:


http://localhost:5000


---

# AWS Deployment

The application is deployed using:


Docker
   ↓
Amazon ECR
   ↓
Amazon ECS Fargate


---

## 1. Create Amazon ECR Repository


aws ecr create-repository `
  --repository-name complaint-system `
  --region ap-south-1


---

## 2. Get AWS Account ID


aws sts get-caller-identity


Copy the `Account` value.

Example:


123456789012


---

## 3. Login to Amazon ECR


aws ecr get-login-password `
  --region ap-south-1 |
docker login `
  --username AWS `
  --password-stdin `
 423370095540.dkr.ecr.ap-south-1.amazonaws.com


---

## 4. Tag the Docker Image


docker tag complaint-system:latest `
  423370095540.dkr.ecr.ap-south-1.amazonaws.com/complaint-system:latest


---

## 5. Push the Image to ECR


docker push `
  423370095540.dkr.ecr.ap-south-1.amazonaws.com/complaint-system:latest


After this, the Docker image will be available in Amazon ECR.

---

#  AWS Systems Manager Parameter Store

The Flask secret key is stored securely using AWS Systems Manager Parameter Store.

Generate a random secret:


python -c "import secrets; print(secrets.token_hex(32))"


Create the parameter:

aws ssm put-parameter `
  --name /complaint/FLASK_SECRET_KEY `
  --type SecureString `
  --value "YOUR_RANDOM_SECRET" `
  --region ap-south-1


The application retrieves the secret through the ECS task configuration.

---

#  IAM Roles

The ECS application uses IAM roles instead of storing AWS access keys inside the Docker image.

Two main roles are required:

### ECS Task Execution Role

Used by ECS to:

* Pull the Docker image from ECR
* Send container logs to CloudWatch

### Complaint Task Role

Used by the Flask application to access:

* DynamoDB
* Systems Manager Parameter Store
* KMS for encrypted parameters

The required permissions are provided in:

IAM-task-role-policy.json


---

#  ECS Fargate Deployment

Create an ECS cluster:


complaint-cluster


Use:


Launch Type: Fargate


Create a task definition:


complaint-task


Recommended task resources:


CPU:    0.25 vCPU
Memory: 0.5 GB


Container name:


complaint-container


Container port:

5000

Docker image:

423370095540.dkr.ecr.ap-south-1.amazonaws.com/complaint-system:latest


---

##  ECS Environment Variables

Configure these environment variables in the ECS task definition:


AWS_REGION=ap-south-1
USERS_TABLE=Users
COMPLAINTS_TABLE=Complaints
DEPARTMENTS_TABLE=Departments


Add the Flask secret as an ECS secret:


FLASK_SECRET_KEY


Source:


AWS Systems Manager Parameter Store


Parameter:


/complaint/FLASK_SECRET_KEY


---

#CloudWatch Logs

Create/use the log group:

/ecs/complaint-system


Container logs are sent to Amazon CloudWatch.

This helps to check:

* Flask errors
* Container startup problems
* Application requests
* AWS/DynamoDB errors

---

# Security Group

Create a security group such as:


Complaint-ECS-SG


For a simple learning deployment, allow:


Type: Custom TCP
Port: 5000
Source: 0.0.0.0/0


> For a production application, the security configuration should be restricted and the application should normally be placed behind a load balancer with HTTPS.

---

# ECS Service

Create an ECS service:


Service name: complaint-service
Desired tasks: 1
Launch type: Fargate


Configure:


Public subnet: Yes
Public IP: ON
Security Group: Complaint-ECS-SG


Once the task is running, copy the public IP address.

Open:


http://PUBLIC_IP:5000


---

# Application Flow

## Employee Flow


Register
   ↓
Login
   ↓
Employee Dashboard
   ↓
Select Department
   ↓
Submit Complaint
   ↓
Complaint stored in DynamoDB
   ↓
View Complaint Status
   ↓
Admin Response
   ↓
Complaint Resolved


---

## Admin Flow


Admin Login
     ↓
Admin Dashboard
     ↓
View All Complaints
     ↓
Open Complaint
     ↓
Update Status
     ↓
Add Response
     ↓
Resolve Complaint
     ↓
View Analytics


---

#  Analytics

The administrator can view department-wise complaint statistics.

Example:

| Department     | Total | Resolved | Pending |
| -------------- | ----: | -------: | ------: |
| IT             |    10 |        8 |       2 |
| Finance        |     8 |        6 |       2 |
| HR             |     5 |        4 |       1 |
| Sales          |     7 |        3 |       4 |
| Marketing      |     4 |        3 |       1 |
| Operations     |     6 |        5 |       1 |
| Administration |     2 |        2 |       0 |

The analytics page is available only to administrators.

Example route:


/admin/analytics


---

# Testing

### Employee Testing

1. Open the application.
2. Register a new employee.
3. Login with the employee account.
4. Select a department.
5. Submit a complaint.
6. Check the complaint in the dashboard.
7. Verify the complaint is stored in DynamoDB.

### Admin Testing

1. Login using the administrator account.
2. Open the admin dashboard.
3. View employee complaints.
4. Open a complaint.
5. Change the complaint status.
6. Add an admin response.
7. Resolve the complaint.
8. Open the analytics page.
9. Verify department-wise statistics.

---

#  Troubleshooting

### Docker is not running

Make sure Docker Desktop is running.

Check:


docker version


---

### Check ECS Task Status

Use the AWS Console:


AWS Console
→ ECS
→ Clusters
→ complaint-cluster
→ Services
→ complaint-service
→ Tasks


Check whether the task is:


RUNNING


---

### Check Application Logs

Go to:


CloudWatch
→ Log groups
→ /ecs/complaint-system


Open the latest log stream.

---

### Check DynamoDB Tables

Go to:


AWS Console
→ DynamoDB
→ Tables


Check:


Users
Complaints
Departments


---

# Security Notes

* Do not upload `.env` files to GitHub.
* Do not put AWS access keys inside the Dockerfile.
* Do not hard-code passwords in the application.
* Use IAM roles for ECS permissions.
* Store sensitive configuration in Parameter Store.
* Use HTTPS and restricted security groups for production deployments.

---

#  Future Improvements

The project can be extended with:

* Application Load Balancer
* HTTPS/SSL
* Custom domain
* Email notifications
* Complaint priority
* File/image attachments
* Advanced analytics
* Search and filtering
* Pagination
* Admin activity logs
* Automated CI/CD deployment


