# Eliza Watch — сповіщення про «Щось не так з Елайзою»

Агент кожні 5 хвилин перевіряє starylev.com.ua і пише в Telegram, щойно там
з'являється сторінка книги або згадка про передпродаж. Після першої знахідки
вимикається сам.

## 1. Telegram-бот (3 хв)
1. У Telegram відкрити @BotFather → `/newbot` → скопіювати **токен**.
2. Написати своєму новому боту будь-що.
3. Відкрити в браузері `https://api.telegram.org/bot<ТОКЕН>/getUpdates` →
   знайти `"chat":{"id":123456789` — це **chat id**.

## 2. Запуск на GitHub (працює без вашого ноутбука)
1. github.com → New repository (Private) → завантажити файли з цієї папки
   (разом із `.github/workflows/eliza-watch.yml`).
2. Settings → Secrets and variables → Actions → New repository secret:
   `TG_TOKEN` і `TG_CHAT_ID`.
3. Вкладка Actions → «Eliza watch» → **Run workflow** — перевірити, що працює.

## Альтернатива: на своєму комп'ютері (кожні 60 с, швидше)
```
export TG_TOKEN=...  TG_CHAT_ID=...
python monitor.py --test       # тестове повідомлення
python monitor.py --loop 60
```

## Перевірка, що агент «бачить» сайт
Тимчасово запустіть із ширшим словом:
`WATCH_URLS="https://starylev.com.ua/search?q=Павлюк" python monitor.py`
Якщо сайт показує пошук іншою адресою — відкрийте пошук на сайті ВСЛ,
скопіюйте URL і вставте в `DEFAULT_URLS` у monitor.py.
