# Book Spot - Run Instructions 🚀

This guide provides step-by-step instructions to set up and run the Book Spot application from a fresh git clone.

## 📋 Prerequisites

Ensure you have the following installed on your system:
*   **Git**: For cloning the repository.
*   **Python 3.8+**: The application backend language.
*   **AWS CLI** (Optional but recommended for AWS setup): For configuring credentials.

---

## 🛠️ Initial Setup (Common)

These steps are required for both Local and AWS versions.

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd capstone_bookstore
    ```

2.  **Create a Virtual Environment**
    It is recommended to use a virtual environment to manage dependencies.
    ```bash
    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🏠 Option 1: Run Locally (SQLite)

This version uses a local SQLite database file (`instance/bookstore.db`). Ideal for development and testing without AWS dependencies.

1.  **Initialize the Database**
    This script creates the database schema and seeds it with initial book data.
    ```bash
    python init_db.py
    ```
    *(Optional)* You can also run `python init_users.py` if available to seed default users.

2.  **Run the Application**
    ```bash
    python app.py
    ```

3.  **Access the App**
    Open your browser and navigate to: `http://127.0.0.1:5000`

---

## ☁️ Option 2: Run with AWS (DynamoDB)

This version uses AWS DynamoDB as the backend database.

### 1. AWS Configuration

You need valid AWS credentials with permissions for DynamoDB and SNS.

*   **If you have AWS CLI installed:**
    Run `aws configure` and enter your keys, region, and output format.
*   **Manually:**
    Create a `.env` file in the root directory (copy `.env.example` if it exists) or manually add:
    ```ini
    AWS_DEFAULT_REGION=us-east-1
    SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:MyTopic  # Optional, for notifications
    MAIL_USERNAME=your_gmail_username
    MAIL_PASSWORD=your_gmail_password
    ```

### 2. Database Setup via Migration

Since the project uses a migration script to populate DynamoDB from SQLite, follow these steps:

1.  **Ensure Local SQLite Data Exists**
    Run the local init script first to generate the source data:
    ```bash
    python init_db.py
    ```

2.  **Create DynamoDB Tables**
    This script creates the required tables (`Books`, `Users`, `Orders`, etc.) in your AWS account.
    ```bash
    python create_dynamodb_tables.py
    ```

3.  **Migrate Data to DynamoDB**
    This script reads from the local `bookstore.db` and pushes data to DynamoDB.
    ```bash
    python batch_migrate.py
    ```

### 3. Run the AWS Application

```bash
python app_aws.py
```

### 4. Access the App

Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 🐞 Troubleshooting

*   **Database Errors (Local):** If you see "no such table" errors, ensure you ran `python init_db.py`.
*   **AWS Permission Errors:** Ensure your IAM user has `AmazonDynamoDBFullAccess` and `AmazonSNSFullAccess` (or restrictive policies as needed).
*   **Missing Environment Variables:** Ensure the `.env` file is properly loaded. You may need to create it if it doesn't exist.
