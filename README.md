# Medo - AI Medical Assistant

Medo is an intelligent medical assistant powered by AI that provides medical information, supports multiple languages, and includes speech-to-text and text-to-speech capabilities.

## Features

- 🩺 AI-powered medical question answering
- 🗣️ Speech-to-text input in multiple languages
- 🔊 Text-to-speech responses
- 🌍 Multi-language support (English, Hindi, Spanish, French, Telugu, Korean)
- 📋 Prescription parsing and calendar integration
- 🔍 Web search integration for up-to-date medical information

## Screenshots

### Chat Interface
![Chat Page](./images/chat_page.jpg)
*Interactive chat interface showing how to communicate with Medo - ask questions via text or voice input, get AI responses with audio playback, and upload prescriptions for calendar integration*

### Language Support
![Language Support](./images/language_supports.jpg)
*Multi-language support - Choose from English, Hindi, Spanish, French, Telugu, and Korean for both voice input and text responses*

## Demo

<!-- For GIFs or videos -->
![Medo Demo](./images/demo.gif)
*Live demo of voice interaction*

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/medo-medical-assistant.git
cd medo-medical-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Cloud credentials (see Configuration section)

4. Run the application:
```bash
python app.py
```

## Configuration

Create the following credential files:
- `speech-credentials.json` - Google Cloud Speech API credentials
- `translate.json` - Google Cloud Translate API credentials
- `token.json` - Google Calendar API token
- `.env` - Environment variables

## Tech Stack

- **Backend**: Flask, Python
- **AI/ML**: Ollama (Llama 3.2), Google Cloud APIs
- **Frontend**: HTML, CSS, JavaScript
- **Database**: Excel (users.xlsx)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
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
* Implement more sophisticated user interfaces.
* Add support for additional languages and medical terminology.
