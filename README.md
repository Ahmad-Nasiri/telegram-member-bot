
***

```markdown
# 🤖 Telegram Member Bot

A Telegram bot for increasing members of groups and channels using source groups.

## ✨ Features

- ✅ Increase members for Telegram groups and channels
- ✅ Save contacts from source groups (two methods: auto-join and file upload)
- ✅ Full admin panel with inline buttons
- ✅ Manage source groups (add/remove/list)
- ✅ Get token and settings at runtime (no file editing required)
- ✅ Real-time progress display
- ✅ Daily order limit per user
- ✅ Supports Termux (Android)

## 📋 Prerequisites

- Python 3.11 or higher
- Telegram account (for API_ID and API_HASH)
- Bot token from [@BotFather](https://t.me/BotFather)

## 🚀 Installation Methods

### Method 1: Git Clone (Fastest)

```bash
git clone https://github.com/Ahmad-Nasiri/telegram-member-bot.git
cd telegram-member-bot
pip install -r requirements.txt
python bot.py
```

### Method 2: Copy Code (Without Git)

1. Create the following files in a new folder:
   - `bot.py`
   - `database.py`
   - `member_adder.py`
   - `requirements.txt`

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the bot:
```bash
python bot.py
```

### Method 3: Termux (Android)

```bash
pkg update && pkg upgrade -y
pkg install python git -y
git clone https://github.com/Ahmad-Nasiri/telegram-member-bot.git
cd telegram-member-bot
pip install -r requirements.txt
python bot.py
```

## 🔧 Initial Setup

After running, the bot will ask for:

1. **Bot Token**: Get from [@BotFather](https://t.me/BotFather)
2. **Phone Number**: With country code (e.g., `+98912xxxxxxx`)
3. **API_ID**: From [my.telegram.org](https://my.telegram.org/apps)
4. **API_HASH**: From [my.telegram.org](https://my.telegram.org/apps)
5. **Owner ID**: Optional (press Enter for auto-detect)

## 📱 Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Start the bot and show rules |
| `/admin` | Admin panel (owner only) |
| `/add_source -1001234567890` | Add source group by chat_id |
| `/remove_source -1001234567890` | Remove source group |
| `/list_sources` | List all source groups |
| `/save_contacts` | Save contacts from source groups |
| `/stats` | Show bot statistics (owner only) |

## 📂 File Structure

```
telegram-member-bot/
├── bot.py              # Main bot file
├── database.py         # Database management
├── member_adder.py     # Member adding logic
├── requirements.txt    # Dependencies
├── README.md           # This file
└── LICENSE             # License
```

## ⚙️ Configuration

Settings are stored in `config.py` which is automatically created after first run.

## 🛡️ Security

- Bot token is stored in `config.py`
- Account info is stored in the same file
- It is recommended to add `config.py` to `.gitignore`

## 📝 Rules

1. This bot is developed by [Ahmad-Nasiri](https://github.com/Ahmad-Nasiri)
2. The developer is not responsible for how users use this bot
3. Using this bot for spam or violating Telegram's terms is prohibited

## 🤝 Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License.

## 👨‍💻 Developer

- **Ahmad-Nasiri** - [GitHub](https://github.com/Ahmad-Nasiri)

---

⭐ Star this repo if you find it useful!
```
