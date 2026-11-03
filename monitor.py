#!/usr/bin/env python3
"""
Eliza Watch — стежить за сайтом Видавництва Старого Лева і пише в Telegram,
щойно там з'являється «Щось не так з Елайзою» (Ілларіон Павлюк).

Запуск:
  python monitor.py            # одна перевірка (для GitHub Actions)
  python monitor.py --loop 60  # перевіряти кожні 60 с (на своєму комп'ютері)
  python monitor.py --test     # надіслати тестове повідомлення в Telegram
"""
import os, re, sys, time, json, urllib.request, urllib.parse
from html import unescape

# Сторінки, які перевіряємо. Якщо знайдете на сайті ВСЛ точну сторінку пошуку
# чи автора — додайте її сюди або в змінну оточення WATCH_URLS (через кому).
DEFAULT_URLS = [
    "https://starylev.com.ua/",
    "https://starylev.com.ua/search?q=" + urllib.parse.quote("Елайза"),
    "https://starylev.com.ua/search?q=" + urllib.parse.quote("Павлюк"),
]
URLS = [u.strip() for u in os.getenv("WATCH_URLS", "").split(",") if u.strip()] or DEFAULT_URLS

# Ознаки в адресі посилання (slug товару) і в тексті сторінки
SLUG_RE = re.compile(r"(elay|elaiz|elajz|eliza|elayza)", re.I)
TEXT_RE = re.compile(r"елайз", re.I)
PREORDER_RE = re.compile(r"передпродаж|передзамовлен|попередній продаж", re.I)

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
STATE_FILE = os.getenv("STATE_FILE", "seen.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "uk,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")


def telegram(text):
    if not (TG_TOKEN and TG_CHAT_ID):
        print("[!] TG_TOKEN / TG_CHAT_ID не задані — повідомлення лише в консоль:\n" + text)
        return
    data = urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": text,
                                   "disable_web_page_preview": "false"}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data, timeout=20)


def check_once():
    """Повертає список знахідок: [(url_сторінки, [посилання_на_товар], є_передпродаж)]"""
    hits = []
    for url in URLS:
        try:
            html = fetch(url)
        except Exception as e:
            print(f"[warn] {url}: {e}")
            continue
        links = set()
        for href in re.findall(r'href=["\']([^"\']+)["\']', html):
            if SLUG_RE.search(urllib.parse.unquote(href)):
                links.add(urllib.parse.urljoin(url, unescape(href)))
        text_hit = bool(TEXT_RE.search(html))
        if links or text_hit:
            hits.append((url, sorted(links), bool(PREORDER_RE.search(html))))
    return hits


def load_seen():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=1)


def run(seen):
    hits = check_once()
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if not hits:
        print(f"{stamp} — поки нічого")
        return False
    new_links = {l for _, links, _ in hits for l in links} - seen
    new_pages = {p for p, links, _ in hits if not links} - seen
    if not (new_links or new_pages):
        print(f"{stamp} — знахідки вже надіслані раніше")
        return True
    lines = ["🔔 «Щось не так з Елайзою» з'явилась на сайті Старого Лева!"]
    if any(pre for _, _, pre in hits):
        lines.append("На сторінці є слова «передпродаж/передзамовлення» — схоже, відкрили!")
    for l in sorted(new_links):
        lines.append("📖 " + l)
    for p in sorted(new_pages):
        lines.append("🔎 згадка на сторінці: " + p)
    lines.append("\nДалі: оформити передзамовлення / написати в оптовий відділ ВСЛ, "
                 "відкрити передзамовлення на soloveyko.es.")
    telegram("\n".join(lines))
    print("\n".join(lines))
    save_seen(seen | new_links | new_pages)
    return True


def main():
    if "--test" in sys.argv:
        telegram("✅ Eliza Watch підключено. Я напишу, щойно книга з'явиться на starylev.com.ua")
        return
    seen = load_seen()
    if "--loop" in sys.argv:
        i = sys.argv.index("--loop")
        delay = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 60
        while True:
            run(seen)
            seen = load_seen()
            time.sleep(delay)
    found = run(seen)
    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"found={'true' if found else 'false'}\n")


if __name__ == "__main__":
    main()
