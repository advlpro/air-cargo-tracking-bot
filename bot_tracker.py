import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from playwright.async_api import async_playwright

# Replace with your actual Telegram Bot Token
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)

# Dictionary to keep active background trackers: {tracking_number: chat_id}
active_trackers = {}


async def fetch_tracking_data(tracking_number: str):
    url = f"https://pathfinder.digitalfactory.aero/{tracking_number}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            page_text = await page.inner_text("body")
            return page_text
        except Exception as e:
            print(f"Error fetching {tracking_number}: {e}")
            return None
        finally:
            await browser.close()


def parse_shipment_report(raw_text: str, tracking_number: str) -> tuple[str, bool]:
    """Parses raw Pathfinder text into a structured timeline table"""
    if not raw_text or "Application error" in raw_text:
        return "❌ Error loading tracking data from server.", False

    origin = "JFK" if "JFK" in raw_text else "?"
    dest = "HAM" if "HAM" in raw_text else "?"

    # Extract status milestones using regex
    events_raw = re.findall(r'(RCS|DEP|RCF|NFD|DLV)\s+(\d{2}[A-Z]{3}\s*\|\s*\d{2}:\d{2}\*?)\s+([^\n]+)', raw_text)

    formatted_lines = [
        f"📦 **Status AWB `{tracking_number}`**\n",
        f"✈️ **Route:** `{origin} ➔ {dest}`\n",
        f"📋 **Timeline:**\n"
        f"`Status | Details | Local Time`\n"
        f"----------------------------------------"
    ]

    is_delivered = False
    for status, time_str, details in events_raw:
        clean_details = details.strip()
        clean_time = time_str.replace("*", "").strip()

        formatted_lines.append(f"• **{status}** | {clean_details} | 🕒 `{clean_time}`")

        if status == "DLV" or "Delivered" in raw_text:
            is_delivered = True

    if not events_raw:
        formatted_lines.append(raw_text[:600])

    return "\n".join(formatted_lines), is_delivered


# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Air Cargo Tracking Bot**\n\n"
        "Send your AWB number to check status and start auto-tracking:\n"
        "`/status 881-26641451` or just send the tracking number.",
        parse_mode="Markdown"
    )


@dp.message(Command("status"))
@dp.message(F.text)
async def handle_tracking_request(message: types.Message):
    text = message.text.strip()

    if text.startswith("/status"):
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            tracking_number = parts[1].strip()
        else:
            await message.answer("⚠️ Please provide an AWB number, e.g., `/status 881-26641451`", parse_mode="Markdown")
            return
    else:
        tracking_number = text

    chat_id = message.chat.id
    waiting_msg = await message.answer(f"🔍 Launching browser & fetching AWB `{tracking_number}`...",
                                       parse_mode="Markdown")

    raw_text = await fetch_tracking_data(tracking_number)
    report, delivered = parse_shipment_report(raw_text, tracking_number)

    await bot.edit_message_text(
        text=report,
        chat_id=chat_id,
        message_id=waiting_msg.message_id,
        parse_mode="Markdown"
    )

    if not delivered:
        if tracking_number not in active_trackers:
            active_trackers[tracking_number] = chat_id
            asyncio.create_task(background_tracker(tracking_number, chat_id))
    else:
        await message.answer(
            f"✅ Shipment `{tracking_number}` is already delivered (`DLV`). Auto-tracking not required.",
            parse_mode="Markdown")


async def background_tracker(tracking_number: str, chat_id: int):
    """Background loop checking status every 4 hours"""
    print(f"Started background tracker for {tracking_number}")

    while tracking_number in active_trackers:
        await asyncio.sleep(4 * 3600)  # Check every 4 hours

        print(f"Background check for {tracking_number}...")
        raw_text = await fetch_tracking_data(tracking_number)
        report, delivered = parse_shipment_report(raw_text, tracking_number)

        await bot.send_message(
            chat_id=chat_id,
            text=f"🔄 **Shipment Status Update!**\n\n{report}",
            parse_mode="Markdown"
        )

        if delivered:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🏁 Shipment `{tracking_number}` reached **DLV / Delivered** status. Monitoring completed and stopped.",
                parse_mode="Markdown"
            )
            active_trackers.pop(tracking_number, None)
            break


async def main():
    print("Air Cargo Tracking Bot started successfully...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")