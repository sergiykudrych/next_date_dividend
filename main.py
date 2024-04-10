import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message
import requests
from bs4 import BeautifulSoup
router = Router()
TOKEN = '7017404386:AAFgfOsMdlVmVq2KpIdnGcsaxird94SYsKE'
dp = Dispatcher()
headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
bot = Bot(TOKEN)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Привіт👋\nBідправ мені тікер акцій і я надішлю коли планована наступна дата виплати девідендів")


def get_date_next_devident(text):
    response = requests.get(f'https://a2-finance.com/ru/issuers/{text}/dividends', headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    div_tag = soup.find('div', attrs={'data-type': 'prev_next_dividends'})

    if div_tag is None:
        message = "Не знайшли такий тікет"
        return message

    block_tab_panels = div_tag.find("div", class_="tab-content").find_all("div", class_="tab-pane")
    list_data = []

    for item in block_tab_panels:
        ticker = item.find("span", class_="ticker-badge-diff m-r-xs")

        if ticker is not None:
            ticker_text = ticker.get_text(strip=True)
            ticker = ticker_text.split(":")[1] if ":" in ticker_text else None
            ticker = ticker + " "
        else:
            ticker = ''
        
        list_tr = item.find("table", class_="table-prev-next-dividends").find("tbody").find_all("tr")
        
        for tr in list_tr:
            tds = tr.find_all('td')
            info = ''
            dev = ''

            for td in tds:
                if td.text.strip() == "Эксдивидендная дата":
                    last_td = tds[-1].get_text(strip=True)
                    info = f"{ticker}{last_td}"

            for td in tds:
                if td.text.strip() == "Дивиденд":
                    data = tds[-1].get_text(strip=True)
                    dev = f'Виплата на 1 акцію {data}'
        
            list_data.append(f'{info}{dev}')

    return list_data

def seach_stocks(text):
    url = f"https://a2-finance.com/ru/qs?query={text}"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.json()
        if len(html_content['suggestions']) == 0:
            message = "Не знайшли такий токен"
            return message
        list_stocks = []
        # Вивести значення категорії та URL для кожного елементу
        for suggestion in html_content['suggestions']:
            url = suggestion['data']['url']
            if "/ru/issuers/" in url:
                value = ' '.join(suggestion['value'].split(';'))
                obj = {"name": value, "url": "https://a2-finance.com" + url}
                list_stocks.append(obj)
        
        return list_stocks
    else:
        message = "Не знайшли такий токен"
        return message


# @dp.inline_handler()
# async def inline_handler(query: types.InlineQuery):
#     text = query.query or 'echo'
#     items = seach_stocks(text.lower())
#     if isinstance(items, list):
#         articles = [InlineQueryResultArticle(
#             id=hashlib.md5(f'{item["name"]}{index}'.encode()).hexdigest(),
#             title=f'{item["name"]}',
#             input_message_content=InputTextMessageContent(
#                 message_text=f'{item["name"]}'),
#         ) for index, item in enumerate(items)]
#         await query.answer(articles, cache_time=60, is_personal=True)
#     else:
#         articles = [InlineQueryResultArticle(
#             id=1,
#             title=f'Не знайшли такий тікет',
#             input_message_content=InputTextMessageContent(
#                 message_text=f'Не знайшли такий тікет'),
#         ) ]
#         await query.answer(articles, cache_time=60, is_personal=True)


@dp.message()
async def text_handler(message: types.Message) -> None:
    # Отримуємо текст повідомлення
    # Відправляємо повідомлення з смайликом загрузки 🔄
    chat_id = message.chat.id
    send_message = await message.answer("Збираємо інформацію... 🔄")
    text = message.text.split(' ')[0]
    data_info = seach_stocks(text)
    message_id = send_message.message_id
    
    if isinstance(data_info, list):
        target = data_info[0]['url'].split('/')[-1]
        next_date = get_date_next_devident(target.lower())
        print(next_date)
        # Видаляємо пусті рядки
        cleaned_data = [item for item in next_date if item]

        # Формуємо повідомлення
        message_send = ""
        for i in range(0, len(cleaned_data), 2):  # Змінено крок на 2, так як нам потрібно обробляти два рядки одночасно
            # Перевіряємо, чи є достатньо елементів у списку перед використанням індексації
            if i + 1 < len(cleaned_data):
                message_send += f"\n{cleaned_data[i+1]}\n{cleaned_data[i]}\n\n"
            else:
                break  # Зупиняємо цикл, якщо індекс вийшов за межі довжини списку

        await message.answer(f'Наступна прогнозована виплата\n' + message_send)
        # Видаляємо відправлене повідомлення про завантаження
        if send_message:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)


    else:
        # Отримуємо ідентифікатор відправленого повідомлення
        message_id = send_message.message_id
        
        await message.answer( data_info)
        # Видаляємо відправлене повідомлення про завантаження
        if send_message:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)



async def main() -> None:
    bot = Bot(TOKEN)
    # And the run events dispatching
    await dp.start_polling(bot)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())