# Company Complaint System

The Flask application stores users, complaints, and departments in Amazon
DynamoDB. It no longer connects to or requires the previous RDS/MySQL database.

## Configure and run

1. Use Python 3.12 (or another currently supported Python 3.10+ release) and
   install the dependencies with `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and set a unique `FLASK_SECRET_KEY`. The table
   names and AWS region can also be changed there.
3. Configure AWS credentials through the standard AWS credential chain. For
   AWS deployments, prefer an IAM role instead of putting access keys in `.env`.
4. Create the tables and seed the departments:

   ```powershell
   python setup_dynamodb.py
   ```

5. Optionally create the first administrator:

   ```powershell
   python setup_dynamodb.py --admin-email admin@example.com --admin-password "choose-a-strong-password"
   ```

6. Run locally with `python app.py`, or use the included Dockerfile/Gunicorn
   command for deployment.

The setup script creates `Users` (email partition key), `Complaints`
(complaint_id partition key and a `user_id-index` GSI ordered by `created_at`),
and `Departments` (id partition key), using on-demand billing. The application
role needs read/write access to these tables and the complaints index. The role
used for initial setup also needs permission to create and describe tables.
The department seed includes 39 common large-company functions. The original
department IDs 1–7 are preserved; rerun `python setup_dynamodb.py` to add or
refresh the seeded department choices in the registration form.

The employee dashboard and complaint history use the `user_id-index`.
Administrator counts and reports scan the complaints table; for a large
production dataset, replace those scans with purpose-built aggregates/indexes.
