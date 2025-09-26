from datetime import date
import json
import utils


with open("cache.json") as f:
    config = json.load(f)
    creds = utils.TelegramCredentials(config.get("id", ""), config.get("hash", ""))

channel_name = "rozetked"
keywords = ["искусственный", "интеллект", "обучение"]

start_date = date(2024, 8, 23)  # Дата, с которой начинаем поиск

if __name__ == "__main__":
    print(utils.search_posts_with_links(creds, channel_name, keywords, start_date))
