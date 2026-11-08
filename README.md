# 📦 Air Cargo Tracking Telegram Bot

An asynchronous Telegram bot built with **Python**, **Aiogram 3**, and **Playwright** that scrapes air cargo tracking updates from portals (like Pathfinder) in real-time, parses shipment milestones into structured tables, and provides automatic background polling every 4 hours until the shipment is successfully delivered (`DLV`).

## 🚀 Features

- **Headless Browser Scraping:** Bypasses heavy SPA rendering challenges using Playwright.
- **Structured Timeline:** Extracts origin, destination, weight, flight details, and status milestones into a clean Markdown table.
- **Background Auto-Tracking:** Automatically polls active shipments every 4 hours and sends notifications on status updates.
- **Smart Termination:** Automatically stops background monitoring once the cargo reaches the `DLV` (Delivered) status.

---

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/advlogpro/air-cargo-tracking-bot.git](https://github.com/advlogpro/air-cargo-tracking-bot.git)
   cd air-cargo-tracking-bot

2. **Create and activate a virtual environment:**

python3 -m venv venv
source venv/bin/activate

3. **Install dependencies:**

pip install -r requirements.txt
playwright install chromium

4. **Configure your Bot Token:**

Open bot_tracker.py and replace "YOUR_TELEGRAM_BOT_TOKEN" with your actual Telegram bot token from @BotFather.

5. **Run the bot:**

python bot_tracker.py

📄 License
This project is open-source and available under the MIT License.
