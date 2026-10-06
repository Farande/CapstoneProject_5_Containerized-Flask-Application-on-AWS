import argparse
import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

from departments import DEPARTMENT_NAMES

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-south-1")
USERS = os.getenv("USERS_TABLE", "Users")
COMPLAINTS = os.getenv("COMPLAINTS_TABLE", "Complaints")
DEPARTMENTS = os.getenv("DEPARTMENTS_TABLE", "Departments")

dynamodb = boto3.resource("dynamodb", region_name=REGION)


def create_table(**kwargs):
    name = kwargs["TableName"]
    try:
        table = dynamodb.create_table(BillingMode="PAY_PER_REQUEST", **kwargs)
        print(f"Creating table {name}")
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") != "ResourceInUseException":
            raise
        table = dynamodb.Table(name)
        print(f"Table {name} already exists")

    table.wait_until_exists()


def seed_departments():
    table = dynamodb.Table(DEPARTMENTS)
    with table.batch_writer() as batch:
        for index, name in enumerate(DEPARTMENT_NAMES, start=1):
            batch.put_item(Item={"id": str(index), "department_name": name})
    print(f"Seeded {len(DEPARTMENT_NAMES)} departments")


def create_admin(email, password):
    try:
        dynamodb.Table(USERS).put_item(
            Item={
                "email": email.strip().lower(),
                "employee_id": "ADMIN001",
                "name": "Administrator",
                "password": generate_password_hash(password),
                "department_id": "7",
                "role": "admin",
            },
            ConditionExpression="attribute_not_exists(email)",
        )
    except ClientError as error:
        if (
            error.response.get("Error", {}).get("Code")
            == "ConditionalCheckFailedException"
        ):
            raise ValueError(
                f"User {email} already exists; admin was not overwritten"
            ) from error
        raise
    print(f"Admin user created: {email}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--admin-email")
    parser.add_argument("--admin-password")
    args = parser.parse_args()

    if bool(args.admin_email) != bool(args.admin_password):
        parser.error("--admin-email and --admin-password must be provided together")

    create_table(
        TableName=USERS,
        KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
    )

    create_table(
        TableName=COMPLAINTS,
        KeySchema=[{"AttributeName": "complaint_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "complaint_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user_id-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )

    create_table(
        TableName=DEPARTMENTS,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
    )

    seed_departments()
    if args.admin_email and args.admin_password:
        create_admin(args.admin_email, args.admin_password)


if __name__ == "__main__":
    main()
