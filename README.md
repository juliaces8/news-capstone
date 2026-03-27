# News Portal Platform
### Software Engineering Capstone Project - Article Subscription API

This project is a Django-based news platform connecting Readers,
Journalists, and Publishers. It uses **MariaDB 11.4** for production-grade
data management and features a RESTful API to deliver content based on
user subscriptions and role-based permissions.

---

## 🚀 Key Features

* **Role-Based Access:** Distinct permissions for Readers, Journalists,
  and Editors using custom role logic.
* **MariaDB Integration:** Professional database backend running on
  Port 3307 for high-performance content delivery.
* **Editor Sandboxing:** Editors are strictly limited to approving or
  editing content belonging to their specific assigned Publisher.
* **Subscription Logic:** Readers follow both individual Journalists
  and entire Publishing houses to build a personalized feed.
* **Personalized API Feed:** A dedicated REST endpoint filters articles
  based on the user's active subscriptions and approval status.

---

## 🛠️ Installation & Local Setup

### 1. Database Configuration
Ensure MariaDB is running on **Port 3307**. Create the database:

```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

2. Initialize Environment

git clone [https://github.com/juliaces8/news-capstone.git]
(https://github.com/juliaces8/news-capstone.git)
cd news-capstone
python -m venv .venv
# Windows:
.\.venv\Scripts\activate

3. Install Dependencies

pip install django djangorestframework mysqlclient

4. Migrations & Admin Setup

python manage.py migrate
python manage.py createsuperuser

🔑 Permissions & Security Logic

Access to the Editor Dashboard and content modification is protected
using UserPassesTestMixin. The system validates the relationship between
the user and the content:

Editors: Must have the 'editor' role AND their publisher_id must
match the article's publisher_id.

Journalists: Can only edit or delete their own authored content.

Admins: Have global override permissions for all content.

📡 REST API Documentation
Get My Subscriptions
Returns a personalized list of approved articles from followed journalists
and publishers.

Endpoint: /api/articles/subscribed/

Method: GET

Authentication: Basic Auth (Required)

Response Format: JSON

Example Success Response (200 OK):

[
    {
        "id": 10,
        "title": "Article Title",
        "author_name": "journalist_pro",
        "publisher_name": "ABCD Post",
        "created_at": "2026-03-26T14:30:00Z"
    }
]

🖥️ Running the Application

python manage.py runserver

Access the application at: http://127.0.0.1:8000/