# Ethics Quiz Telegram Bot

A Telegram bot designed to help students prepare for the exam "Ethical, Legal, Social and Economic Aspects of Computer Science" through a Q&A system.
A Telegram bot that sends ethics questions periodically and helps users learn about ethical aspects in computer science and technology.

## Features

- 🤖 Sends periodic ethics questions (every 15 minutes between 9:00 and 18:00)
- 📊 Tracks daily statistics for each user
- 🎯 Multiple choice questions with instant feedback
- 🧠 AI-powered explanations for answers (when enabled)
- 📈 Daily statistics summary at 21:00

## Quick Start

You can immediately start using the hosted version of this bot:
- Search for `@aspetti_etici_bot` on Telegram
- Start the bot with `/start` command

## Self Hosting

### Prerequisites

- Python 3.8+
- Telegram Bot Token
- Google Gemini API Key (optional, for AI explanations)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dalmasluca/ethics-quiz-bot.git
cd ethics-quiz-bot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your credentials:
```
TELEGRAM_TOKEN=your_telegram_bot_token
AI_API=your_gemini_api_key  # Optional: for AI-powered explanations
```

4. Run the bot:
```bash
python ethics-quiz-bot/bot.py
```

## Available Commands

- `/start` - Start the bot and receive automatic questions
- `/statistiche` - View your daily statistics and success rate
- `/stop_domande` - Disable automatic questions
- `/start_domande` - Enable automatic questions
- `/domanda` - Get a random ethics question

## AI Explanations Feature

When you include a Google Gemini API key in your `.env` file, the bot will provide detailed explanations for both correct and incorrect answers using AI. This helps users better understand the reasoning behind each answer.

To enable this feature:
1. Get an API key from Google Gemini
2. Add it to your `.env` file as `AI_API=your_key_here`

If no API key is provided, the bot will still function normally but without AI explanations.

## Commands

The bot offers 5 main commands:

### `/start`
- Initiates the bot
- Registers the user in the system
- Enables automatic questions every 15 minutes
- Sends a welcome message with basic instructions

### `/domanda`
- Sends an immediate random ethics question
- Can be used anytime, even if automatic questions are disabled
- Includes multiple choice answers (A, B, C, D)
- Provides instant feedback and AI explanation (if enabled)

### `/statistiche`
- Shows your daily performance statistics
- Displays total questions answered today
- Shows number of correct answers
- Calculates your success rate percentage

### `/stop_domande`
- Disables automatic questions
- Stops the 15-minute interval messages
- You can still request questions manually using `/domanda`
- Useful when you need a break or during busy times

### `/start_domande`
- Re-enables automatic questions
- Resumes the 15-minute interval messages
- Questions will be sent between 9:00 and 18:00
- Perfect for when you're ready to continue learning

Note: At 21:00 each day, all users receive their daily statistics automatically, showing their performance summary for the day.

## Hosted Version

For convenience, you can use the hosted version of this bot at `@aspetti_etici_bot`. This version is maintained and already configured with all features, including AI explanations.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.## Note

## Note

This is an unofficial study tool. All questions and content are based on the course material but should be used as a supplement to official course resources.
