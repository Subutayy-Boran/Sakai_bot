# Sakai Announcement Bot 📢

Automatically fetches announcements from Sakai LMS and sends them via Telegram.

## Features

- ✅ **Automatic Login**: Handles Sakai authentication automatically
- ✅ **Notification Fetching**: Extracts announcements from notification panel
- ✅ **Content Extraction**: Retrieves full announcement content
- ✅ **Telegram Notifications**: Sends new announcements via Telegram
- ✅ **Persistent Storage**: Saves announcements to prevent duplicates
- ✅ **GitHub Actions**: Runs on schedule without local machine needed
- ✅ **Robust Error Handling**: Detailed logging for troubleshooting
- ✅ **Type Hints**: Modern Python code with type annotations

## Architecture

```
debis_bot/
├── sakai_bot_final.py              # Main bot application
├── duyurular.json                  # Saved announcements (local only)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .gitignore                      # Git exclusions
├── README.md                       # This file
└── .github/workflows/
    └── sakai_check.yml            # GitHub Actions workflow
```

## Installation

### 1. Clone Repository
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
python sakai_bot_final.py
```

## GitHub Actions Setup

### 1. Create Repository Secrets
Go to **Settings → Secrets and variables → Actions** and add:

- `TELEGRAM_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram user ID
- `SAKAI_USERNAME`: Sakai username
- `SAKAI_PASSWORD`: Sakai password

### 2. Automation Schedule
- **Default**: Every 30 minutes
- **Modify**: Edit `.github/workflows/sakai_check.yml`

Example cron schedules:
- `'0 8 * * *'` = Daily at 08:00 UTC
- `'0 */6 * * *'` = Every 6 hours
- `'*/15 * * * *'` = Every 15 minutes

### 3. Manual Trigger
Run anytime from GitHub **Actions** tab:
1. Select "Sakai Announcement Bot"
2. Click "Run workflow"

## How It Works

1. **Initialization**: Validates required configuration
2. **WebDriver Setup**: Initializes Chrome or Firefox browser
3. **Login**: Authenticates with Sakai credentials
4. **Fetch**: Retrieves announcements from notification panel or page search
5. **Content**: Extracts full announcement content from detail pages
6. **Compare**: Identifies new announcements vs saved ones
7. **Notify**: Sends new announcements via Telegram
8. **Save**: Persists announcements to prevent duplicates

## Logging

Bot outputs detailed logs including:
- Authentication status
- Announcement fetch progress
- Telegram notification delivery
- Errors with full stack traces

All logs are printed to stdout for GitHub Actions review.

## Security Notes

- ⚠️ **Never commit `.env` file** - it contains credentials
- ✅ Use GitHub Secrets for sensitive data
- ✅ Credentials only exist in GitHub Actions environment
- ✅ `.gitignore` protects local `.env` and `duyurular.json`

## Troubleshooting

### No Announcements Found
- Check if you're logged into Sakai
- Verify credentials in `.env`
- Check Sakai portal structure (may have changed)

### Telegram Messages Not Arriving
- Verify `TELEGRAM_TOKEN` is correct
- Start chat with your bot: @YourBotName
- Check `TELEGRAM_CHAT_ID` matches your ID
- Ensure Telegram API is accessible

### Login Fails
- Verify username/password are correct
- Check if Sakai requires additional authentication
- Check if your account is active

### WebDriver Issues
Bot automatically handles:
- Chrome driver download via webdriver-manager
- Firefox fallback if Chrome unavailable
- Headless and UI modes

## Performance

- **Timeout**: Page load (10s), Element wait (15s)
- **Rate Limiting**: 1 second between Telegram messages
- **Max Announcements**: 20 per run
- **Execution Time**: ~30-60 seconds

## License

MIT

## Support

For issues, create a GitHub Issue with:
- Error message and logs
- `.env` configuration (without credentials)
- Sakai portal URL
- Screenshot if possible
