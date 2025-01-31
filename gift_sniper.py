import html
import time
import traceback
from datetime import datetime

import requests
import sentry_sdk
import humanize

# ------------- SETTINGS START -------------
# how much max to buy
HOW_MUCH = 1000
# telegram ID of user to whom send gifts
OWNER_ID = 270954850
TIMEOUT_BUY_IN_SECONDS = 1.2  # min 1.01 (maybe)
# token for bot, obtained from @botfather
TELEGRAM_BOT_TOKEN = "7803866275:AAEtVrdjQxOhBdgxSfTkE_fOD1llHsdBYWs"
# optional param for debug reporting
SENTRY_API_KEY = ""
# if True will ignore checks and will buy the most expensive gifts for specified [how_much]
DO_FORCE_BUY = False
# if the most expensive collection has more than this then ignore it
MAX_COLLECTION_TOTAL_COUNT = 6_000
# ------------- SETTINGS END -------------


if SENTRY_API_KEY:
    sentry_sdk.init(
        dsn=SENTRY_API_KEY,
        environment="tg_gifts_scanner",
        traces_sample_rate=1.0,
    )


class WatchForNewGifts:
    def __init__(self):
        # cache available gifts
        self.cached_limited_gifts_ids = {_["id"] for _ in self.get_available_limited_gifts()}
        self.gift_id_to_buy = None
        self.could_gift_be_upgraded = False

    def check_for_new_limited_gifts(self) -> bool:
        print(f"-> Scanning new gifts ({datetime.now()})")
        new_limited_gift_ids = {_["id"] for _ in self.get_available_limited_gifts()}
        # if we have new gifts in 'new_limited_gift_ids' that were not present in 'cached_limited_gifts_ids'
        if new_limited_gift_ids - self.cached_limited_gifts_ids:
            print("-> Detected new gifts")
            self.send_notification("NEW GIFTS AVAILABLE")
            return True
        return False

    def get_available_limited_gifts(self) -> list:
        response = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getAvailableGifts"
        )
        response.raise_for_status()
        # double check that everything is in order
        assert response.json()["ok"] == True, "Error in telegram API (get_available_limited_gifts)"
        gifts = response.json()["result"]["gifts"]
        # filter out only limited gifts
        limited_gifts = [_ for _ in gifts if "total_count" in _]
        return limited_gifts

    def send_notification(self, notify_text: str) -> None:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": OWNER_ID,
                "text": html.escape(notify_text),
                "parse_mode": "HTML",
                "disable_notification": False,
                "disable_web_page_preview": True,
            },
        )
        return None

    def search_most_expensive_gift_to_buy(self) -> str:
        limited_gifts = self.get_available_limited_gifts()
        # find the most expensive limited gift to buy
        gift_to_buy = max(limited_gifts, key=lambda x: x["star_count"])
        print("-> Detected the most expensive limited gift:")
        print(f"id: {gift_to_buy['id']}")
        print(f"emoji: {gift_to_buy['sticker']['emoji']}")
        print(f"star_count: {gift_to_buy['star_count']} ⭐")
        print(
            f"remaining: {humanize.intcomma(gift_to_buy['remaining_count'])} / {humanize.intcomma(gift_to_buy['total_count'])}\n"
        )
        # filters
        if gift_to_buy["total_count"] > MAX_COLLECTION_TOTAL_COUNT:
            print(f"-> NOT BUYING as 'total_count' > MAX_COLLECTION_TOTAL_COUNT")
            return

        self.gift_id_to_buy = gift_to_buy["id"]

        if "upgrade_star_count" in gift_to_buy:
            self.could_gift_be_upgraded = False
        return gift_to_buy["id"]

    def bulk_buy_gifts(self) -> None:
        for i in range(HOW_MUCH):
            time.sleep(TIMEOUT_BUY_IN_SECONDS)
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendGift",
                data={
                    "user_id": int(OWNER_ID),
                    "gift_id": str(self.gift_id_to_buy),
                    **({"pay_for_upgrade": True} if self.could_gift_be_upgraded else {}),
                },
            )
            response.raise_for_status()
            # double check that everything is in order
            assert response.json()["ok"] == True, "Error in telegram API (bulk_buy_gifts)"
            print(f"progress: {i + 1} / {HOW_MUCH}")
        return None

    def run(self) -> None:
        try:
            while True:
                print("\n-> Sleeping for 4s")
                time.sleep(4)

                new_limited_gifts_available = self.check_for_new_limited_gifts()

                if new_limited_gifts_available or DO_FORCE_BUY:
                    # search for the most expensive shit to buy (aka the most rarest)
                    self.search_most_expensive_gift_to_buy()
                    if self.gift_id_to_buy:
                        # launch bulk buy
                        self.bulk_buy_gifts()
                        # exit program
                        break

        except KeyboardInterrupt:
            pass
        except Exception as e:
            traceback.print_exc()
            if SENTRY_API_KEY:
                sentry_sdk.capture_exception(e)
            self.send_notification(f"🏴‍☠️ error: {traceback.format_exc()[:666]}... 🏴‍☠️")


if __name__ == "__main__":
    bot = WatchForNewGifts()
    bot.run()