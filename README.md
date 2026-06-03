# React + Vite Fullstack Social Platform

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.
Currently, two official plugins are available:
* `@vitejs/plugin-react` uses Oxc
* `@vitejs/plugin-react-swc` uses SWC

*Note: The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see the official documentation.*

## Features

* **User Authentication:** Secure Login and Signup workflows using bcrypt.
* **Social Feed & Posts:** A dynamic home feed, post creation capabilities, and individual post views.
* **User Profiles & Avatars:** User directory, individual profile pages, and personalized visual avatars.
* **Search:** Integrated search functionality to find users or content.
* **Navigation:** Responsive top bar navigation and an informational About page.

---

## Flask Backend

This project includes a Flask backend in the `backend/` folder that exposes the following endpoints:

* `POST /api/signup` - Register a new user
* `POST /api/login` - Authenticate a user
* `GET /api/users?limit=&start=&search=` - Fetch paginated users with optional search
* `GET /api/users/<user_id>` - Fetch a specific user profile
* `GET /api/posts?limit=&start=&userId=` - Fetch paginated posts (all, or by a specific user)
* `POST /api/posts` - Create a new post
* `GET /api/feed` - Fetch all posts for the main home feed

### Backend Setup

Ensure your local MySQL server is running.

1. Navigate to the backend directory and activate the virtual environment:

```bash
# Windows
cd backend
venv\Scripts\activate

# macOS/Linux
cd backend
source venv/bin/activate
Install the backend dependencies:

Bash
# Install required Python packages
pip install -r requirements.txt
Configure environment variables:
Create a new file named .env in the backend/ directory and add your local database credentials in the following format:

קטע קוד
# Add these variables to your newly created .env file
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_local_password
DB_NAME=hw_2
(Optional) Seed the database with initial mock data:

Bash
# Run database seed script
python seed.py
Start the backend server:

Bash
# Start Flask application
python app.py
The backend API will run on http://localhost:5000.

Frontend
The React frontend is located in the root folder. To run it, open a new terminal window (keep the backend running) and execute:

Bash
# Install Node dependencies
npm install

# Start the development server
npm run dev