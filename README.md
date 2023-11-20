# Blog
This application works as a blogging platform where administrators can perform actions such as creating, updating and deleting blog posts. Non-administrator users have the ability to view, like and comment on posts, but these features have not yet been implemented.
# Prerequisites:
  * Python 3.10 or higher

# Installation:

  In the project's root directory, install a virtual environment:

    python -m venv venv

  Activate the virtual environment:

    venv\Scripts\activate

  Install the application's dependencies:

    pip install -r requirements.txt

  Initialize the Database:

    flask db init

  Migrate to the database:

    flask db migrate
    flask db upgrade

  Run the App:

    flask run

# First Step
  Create an admin user 
  
      python create_admin_user.py
# API Documentation
## List Articles
- Endpoint:
GET /
- Description:
Get a list of articles.

- Parameters:
  page (optional): Page number for pagination (default is 1).
- Response:
  Success (200 OK): List of articles in JSON format.
    ``` json
    {
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "content": "Article Content",
      "images": ["image1.jpg", "image2.jpg"],
      "created_at": "dd-mm-yyyy hh:mm"
    },
    // ... other articles ...
    ]
    }

    ```
## Create Article
- Endpoint:
POST /create
- Description:
Create a new article.

- Parameters:
  Headers: Authentication headers (User must be logged in and have admin privileges).
  Body: Form data with article details.
  
- Response:
  Success (302 Found or 200 Ok): Redirect to the list of articles.
  Error (403 Forbidden): If the user doesn't have admin privileges.

## Update Article
- Endpoint:
POST or PUT /update/<article_id>
- Description:
Update an existing article.

- Parameters:
  Headers: Authentication headers (User must be logged in and have admin privileges).
  Body: Form data or JSON payload with updated article details.
  
- Response:
  Success (302 Found or 200 OK): Redirect to the list of articles or JSON response.
  Error (403 Forbidden or 404 Not Found): If the user doesn't have admin privileges or the article is not found.

## Delete Article
- Endpoint:
DELETE /delete/<article_id>
- Description:
Delete an article.

- Parameters:
  Headers: Authentication headers (User must be logged in and have admin privileges).
  
- Response:
  Success (200 OK): JSON response with a success message.
  Error (403 Forbidden or 404 Not Found): If the user doesn't have admin privileges or the article is not found.
  
