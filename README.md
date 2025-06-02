# DULMS Notifications Bot

A web application that scrapes the Delta University Learning Management System (DULMS) for assignments and quizzes, and sends notifications about upcoming deadlines.

## Features

- Web interface for easy interaction
- Automated login to DULMS with CAPTCHA solving
- Extracts assignments and quizzes information
- Identifies upcoming deadlines
- Discord notifications for approaching deadlines
- Real-time log streaming
- API endpoints for programmatic access

## Project Structure

```
DULMS-Notifications-BOT/
├── app/                      # Application package
│   ├── api/                  # API endpoints
│   │   ├── endpoints/        # API route handlers
│   │   └── api.py            # API router
│   ├── config/               # Configuration settings
│   ├── core/                 # Core application logic
│   ├── models/               # Data models and schemas
│   ├── services/             # Business logic services
│   └── utils/                # Utility functions
├── frontend/                 # Frontend assets
│   ├── static/               # Static files (CSS, JS)
│   └── index.html            # Main HTML page
├── logs/                     # Log files
├── tests/                    # Unit and integration tests
├── .env                      # Environment variables
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/DULMS-Notifications-BOT.git
   cd DULMS-Notifications-BOT
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Download Microsoft Edge WebDriver:
   - Go to [Microsoft Edge WebDriver Downloads](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
   - Download the version matching your Edge browser
   - Place the `msedgedriver.exe` in the project root directory

5. Create a `.env` file with your configuration:
   ```
   LOG_LEVEL=INFO
   HEADLESS_MODE=True
   DRIVER_PATH=msedgedriver.exe
   ```

## Usage

1. Start the application:
   ```
   python main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

3. Enter your DULMS credentials and an anti-captcha.com API key

4. Optionally, add a Discord webhook URL to receive notifications

## API Endpoints

### Start a Scraper Task
`POST /api/v1/scraper/scrape`

Request body:
```json
{
  "username": "your-dulms-username",
  "password": "your-dulms-password",
  "captcha_api_key": "your-anti-captcha-api-key",
  "discord_webhook": "optional-discord-webhook-url"
}
```

Response:
```json
{
  "task_id": "unique-task-id",
  "status": "started"
}
```

### Get Task Status and Results
`GET /api/v1/scraper/status/{task_id}`

Response:
```json
{
  "task_id": "unique-task-id",
  "status": "completed",
  "assignments": [...],
  "quizzes": [...]
}
```

### Stream Task Logs
`GET /api/v1/scraper/logs/{task_id}`

Response: Server-Sent Events (SSE) stream

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.