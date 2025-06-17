# Medo - Medical Assistant Chatbot

## Description

Medo is a Flask-based web application designed to act as a helpful medical assistant. It provides a chat interface for users to ask medical questions and includes functionality to parse uploaded text-based prescriptions and automatically add medication reminders to the user's Google Calendar. The application leverages Large Language Models (LLMs) via Ollama for natural language understanding and response generation, integrates with Google Translate for multilingual support, and uses the Google Calendar API for scheduling.

## Features

*   **User Authentication:** Secure user registration and login system.
*   **Chat Interface:** Real-time chat with the Medo assistant.
*   **LLM-Powered Responses:** Utilizes Ollama (Llama 3.2) to answer medical queries.
*   **Web Search Integration:** Uses Firecrawl API to fetch relevant, up-to-date information from the web when necessary to answer queries accurately.
*   **Prescription Parsing:** Upload `.txt` prescription files for automatic parsing using an LLM.
*   **Google Calendar Integration:** Automatically creates medication reminder events in the user's primary Google Calendar based on parsed prescription timings (supports specific times, keywords like "morning", "lunch", "night", and instructions like "before/after food").
*   **Multilingual Support:** Translates user input to English for processing and translates responses back to the user's preferred language (supports English, Hindi, Spanish, French via Google Translate API).
*   **Language Settings:** Users can change their preferred language via a settings page.

## Technology Stack

*   **Backend:** Python, Flask
*   **LLM:** Ollama (running Llama 3.2)
*   **Web Search:** Firecrawl API
*   **Translation:** Google Cloud Translate API (v2)
*   **Calendar:** Google Calendar API (v3)
*   **Authentication:** Google OAuth 2.0 (for Calendar), Custom password hashing
*   **Data Storage:** Excel (`users.xlsx`) for user data
*   **Frontend:** HTML, CSS, JavaScript (templates rendered by Flask)

## Setup and Installation

### Prerequisites

1.  **Python:** Ensure Python 3.x is installed.
2.  **Ollama:** Install and run Ollama locally. Make sure the model specified in `app.py` (e.g., `llama3.2:latest`) is pulled (`ollama pull llama3.2:latest`).
3.  **Google Cloud Account:**
    *   Enable Google Translate API and Google Calendar API.
    *   Create a **Service Account** for the Translate API and download its key as `translate.json`.
    *   Create an **OAuth 2.0 Client ID** for the Calendar API and download it as `tempCredentials.json`.
4.  **Firecrawl API Key:** Obtain an API key from [Firecrawl](https://firecrawl.dev/).

### Installation Steps

1.  **Clone/Download the Repository**

2.  **Install Required Python Packages:**
    ```bash
    pip install flask ollama pandas openpyxl requests python-dotenv google-cloud-translate google-api-python-client google-auth-httplib2 google-auth-oauthlib werkzeug torch
    ```

3.  **Configure the Environment:**
    *   Place your Google Translate service account key as `translate.json` in the project root.
    *   Place your Google Calendar OAuth credentials as `tempCredentials.json` in the project root.
    *   Create a `.env` file in the project root and add your Firecrawl API key.

4.  **Set Up User Data:**
    *   Create an Excel file named `users.xlsx` with columns for `email`, `username`, `password_hash`, and `language`.

5.  **Authorize Google Calendar:**
    *   Run `python create_event.py` once to authorize access to your Google Calendar.
    *   Follow the browser prompts to authenticate and grant permissions.

6.  **Run the Application:**
    ```bash
    python app.py
    ```
    The application will be available at `http://127.0.0.1:5000`

## Usage

### User Registration and Login

1. Access the login page at the root URL (`/`).
2. Click on the registration link to create a new account.
3. Provide email, username, and a secure password (at least 8 characters, including an uppercase letter and a digit).
4. Log in with your credentials.

### Chat Interface

1. After login, you'll be directed to the chat interface.
2. Type medical questions in the chat input.
3. Receive responses from Medo, which may include real-time web search results for up-to-date information.

### Prescription Upload

1. In the chat interface, use the prescription upload feature.
2. Select a `.txt` file containing prescription details.
3. The system will parse the prescription using the LLM, extract medication details, and create calendar events for each medication.
4. View confirmation messages and any errors.

### Language Settings

1. Navigate to the settings page.
2. Select your preferred language from the dropdown.
3. Save the changes to update your language preference.

## Advanced Features

### Smart Medicine Timing Recognition

The system is designed to intelligently interpret timing instructions in prescriptions:

* **Specific Times:** Recognizes formats like "9:00 AM", "14:30", "8pm".
* **Meal-based Keywords:** Maps "breakfast" to 8:00 AM, "lunch" to 12:00 PM, "dinner" to 6:00 PM, etc.
* **Special Instructions:** Extracts and includes instructions like "before food", "after meals", etc.

### Enhanced Calendar Events

Calendar events include:
* Medication name and dosage as the event title
* Complete medication details in the event description
* Specific timing based on parsed instructions
* Popup reminder 10 minutes before the scheduled time

## Troubleshooting

* **Google Calendar Authentication:** If events aren't being created, run `python create_event.py` manually to re-authenticate.
* **LLM Issues:** Ensure Ollama is running with the correct model loaded.
* **Translation Errors:** Verify that `translate.json` has valid credentials and the API is enabled.
* **File Access:** Check permissions if encountering file not found errors.

## Security Notes

* User passwords are hashed before storage.
* Google OAuth flow follows security best practices.
* Always keep your credential files (`translate.json`, `tempCredentials.json`, `token.json`) secure.
* Change the Flask secret key from 'your_secret_key_here' in production.

## Future Improvements

* Replace Excel-based user storage with a proper database.
* Add advanced error handling and retry mechanisms.
* Implement more sophisticated user interfaces.
* Add support for additional languages and medical terminology.
