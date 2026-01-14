# Sakai Announcement Bot 📢

Automatically fetches announcements from Sakai LMS and sends them via Telegram.

## Features

- ✅ **Automatic Login**: Handles Sakai authentication automatically
- ✅ **Notification Fetching**: Extracts announcements from notification panel
- ✅ **Content Extraction**: Retrieves full announcement content
- ✅ **Telegram Notifications**: Sends new announcements via Telegram
- ✅ **Duplicate Prevention**: Saves announcements to prevent sending the same one twice
- ✅ **GitHub Actions**: Runs on schedule without local machine needed
- ✅ **Robust Error Handling**: Detailed logging for troubleshooting
- ✅ **Type Hints**: Modern Python code with type annotations

## How It Works

The bot automatically:
1. Logs into your Sakai account
2. Checks the notification panel for new announcements
3. **Only sends truly NEW announcements** (keeps history to avoid duplicates)
4. Extracts full content from announcement detail pages
5. Sends formatted messages via Telegram
6. Runs on schedule without needing your computer on

## Important: Announcement Deduplication

The bot **only sends announcements once**. It maintains a record of all sent announcements in `duyurular.json` (stored on your local machine during testing, or in GitHub Actions environment during automated runs).

- New announcements = announcements not previously sent ✅ **Will send**
- Old announcements = announcements already sent previously ❌ **Will skip**

This prevents spam and ensures you only get notified about truly new content.

## Architecture

```
debis_bot/
├── sakai_bot.py                 # Main bot application
├── duyurular.json               # Saved announcements (Git-ignored)
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
├── .gitignore                   # Git exclusions
├── README.md                    # Turkish documentation
├── README_EN.md                 # English documentation (this file)
└── .github/workflows/
    └── sakai_check.yml          # GitHub Actions automation
```

## Installation

### 1. Fork and Clone Repository

1. Click the **Fork** button in the top-right corner of this page.
2. Clone your forked repository:

```bash
git clone https://github.com/YOUR_USERNAME/debis_bot.git
cd debis_bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Telegram bot token from @BotFather | `6123456789:ABCDEfG...` |
| `TELEGRAM_CHAT_ID` | Your Telegram user ID | `987654321` |
| `SAKAI_USERNAME` | Sakai LMS username | `student_id` |
| `SAKAI_PASSWORD` | Sakai LMS password | `password` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SAKAI_URL` | `https://online.deu.edu.tr/portal` | Sakai portal URL |
| `HEADLESS` | `1` | Run in headless mode (0=UI, 1=headless) |

### Getting Telegram Credentials

1. **Telegram Bot Token**:
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command
   - Copy the API token

2. **Telegram Chat ID**:
   - Use `/my_id` command with [@userinfobot](https://t.me/userinfobot)
   - Or open this URL: `https://api.telegram.org/bot<TOKEN>/getUpdates`

## Local Testing

```bash
python sakai_bot.py
```

This will:
- Run once and exit
- Create/update `duyurular.json` locally
- Send any new announcements to Telegram

## GitHub Actions Setup

### 1. Create Repository Secrets
Go to **Settings → Secrets and variables → Actions** and add:

- `TELEGRAM_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram user ID
- `SAKAI_USERNAME`: Sakai username
- `SAKAI_PASSWORD`: Sakai password

### 2. Automation Schedule

The workflow runs on **every 30 minutes** (GitHub Actions minimum interval).

> **Note:** GitHub Actions has a minimum 30-minute scheduling interval. For more frequent checks, consider alternative services like Render, Vercel Cron, or AWS Lambda.

To modify the schedule, edit `.github/workflows/sakai_check.yml`:

```yaml
on:
  schedule:
    - cron: '*/30 * * * *'  # Change 30 to your desired minutes
```

Example cron schedules:
- `'0 8 * * *'` = Daily at 08:00 UTC
- `'0 */6 * * *'` = Every 6 hours
- `'*/30 * * * *'` = Every 30 minutes

### 3. Manual Trigger
Run anytime from GitHub **Actions** tab:
1. Select "Sakai Announcement Bot"
2. Click "Run workflow"

## How The Bot Works

### Initialization Phase
- Validates all required environment variables
- Sets up logging system

### WebDriver Setup
- Initializes Chrome browser (downloads driver automatically)
- Falls back to Firefox if Chrome unavailable
- Runs in headless mode (no UI) for GitHub Actions

### Login Phase
- Navigates to Sakai portal
- Fills username and password
- Waits for authentication to complete

### Fetch Announcements
- Opens the notification panel (bell icon)
- Attempts multiple detection strategies:
  - Looks for bullhorn notification counter
  - Scans with 7 different XPath selectors
  - Filters by icon, link href, or announcement keywords
  - Skips generic menu items (calendar, resources, settings, etc.)

### Extract Content
- Opens each announcement detail page
- Extracts full announcement content
- Cleans up formatting

### Deduplication
- Compares against previously saved announcements
- Only selects truly NEW ones
- Saves announcement list to `duyurular.json`

### Telegram Notification
- Sends new announcements via Telegram API
- Formats message with title and content
- Logs success/failure

## Logging

Bot outputs detailed logs including:
- Authentication status
- Announcement detection process
- Item acceptance/rejection reasons
- Telegram notification delivery
- Errors with full stack traces

All logs are printed to stdout for GitHub Actions review.

## Security Notes

- ⚠️ **Never commit `.env` file** - it contains credentials
- ✅ Use GitHub Secrets for sensitive data
- ✅ Credentials only exist in GitHub Actions environment
- ✅ `.gitignore` protects local `.env` and `duyurular.json`
- ✅ No credentials are logged or printed

## Troubleshooting

### No Announcements Detected
- Verify Sakai credentials are correct
- Check notification panel manually in Sakai
- Review GitHub Actions logs for debug output
- Bot attempts multiple detection strategies, all logs show why items were accepted/rejected

### Telegram Messages Not Arriving
- Verify `TELEGRAM_TOKEN` is correct
- Start chat with your bot: @YourBotName
- Check `TELEGRAM_CHAT_ID` matches your user ID (not bot ID)
- Ensure Telegram API is accessible from GitHub servers

### Login Fails
- Verify username/password are correct
- Check if Sakai requires additional authentication
- Check if your account is active
- Review GitHub Actions logs for Sakai login errors

### WebDriver Issues
Bot automatically handles:
- Chrome driver download via webdriver-manager
- Firefox fallback if Chrome unavailable
- Headless and UI modes
- Multiple browser initialization attempts

## Performance

- **Timeout**: Page load (10s), Element wait (15s)
- **Rate Limiting**: 1 second between Telegram messages
- **Max Announcements**: 20 per run
- **Execution Time**: ~30-60 seconds per run
- **Frequency**: Every 30 minutes (adjustable)

## Updating the Bot

To get latest improvements:

```bash
cd debis_bot
git pull origin main
pip install -r requirements.txt --upgrade
```

## License

MIT

## Support

For issues, create a GitHub Issue with:
- Error message and logs
- `.env` configuration (without credentials!)
- Sakai portal URL
- Screenshot if possible
