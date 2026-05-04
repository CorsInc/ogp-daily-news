#!/usr/bin/env python3
"""
ogp-daily-news: Envía resumen de noticias de gobierno de Puerto Rico por Telegram.
Lee fuentes: El Nuevo Día (h2/h3), El Vocero (texto plano).
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
import html
import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            enc = "utf-8"
            if "charset=" in content_type:
                enc = content_type.split("charset=")[-1].split(";")[0].strip()
            return raw.decode(enc, errors="replace")
    except Exception:
        return ""


def extract_clean_text(html_text: str) -> str:
    if BeautifulSoup:
        soup = BeautifulSoup(html_text, 'lxml')
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg', 'nav', 'footer', 'header']):
            tag.decompose()
        return soup.get_text(separator='\n')
    else:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '\n', text)
        return text


SKIP_PHRASES = [
    'javascript', 'stylesheet', 'cookie', 'publicidad', 'suscríbete',
    'menú', 'resultados para', 'cargar más', 'recibir', 'no, gracias',
    'recibe nuestro boletín', 'te invitamos', 'dark mode', 'secciones',
    'últimas noticias', 'recibe notificaciones', 'todos los derechos',
    'microsoft edge', 'google chrome', 'firefox', 'safari',
    'facebook', 'twitter', 'instagram', 'youtube',
    'brandstudio', 'suplementos', 'horóscopo', 'edición impresa',
    'shoppers', 'clasificados', 'edictos', 'ofertas',
    'cargar más noticias', 'nuestro sitio no es visible',
    'sun and clouds', 'a few clouds', 'high ', 'low ',
    'como padre', 'secuestrados por el cuatrienio',
    'recibe nuestro boletín diario', 'las noticias explicadas',
    'browserdetect', 'if(!array',
    'dos fabricantes de la mifepristona',
    'shakira ofreció un concierto',
    'una fuerza oculta está elevando',
    'tortuga más vieja',
    'relación cercana y afectiva',
]


def is_headline_candidate(line: str) -> bool:
    line = line.strip()
    if len(line) < 30 or len(line) > 300:
        return False
    if not line[0].isupper() and line[0] not in '¿¡"\'«':
        return False
    if line[-1] not in '.?!…"\'»a-zA-Z0-9':
        return False
    ll = line.lower()
    for skip in SKIP_PHRASES:
        if skip in ll:
            return False
    if line.isupper() and len(line) > 40:
        return False
    symbols = sum(1 for c in line if c in '{}[]|\\/*<>')
    if symbols > 3:
        return False
    return True


def fetch_headlines_end() -> list:
    html_text = fetch_html("https://www.elnuevodia.com/noticias/gobierno/")
    if not html_text:
        return ["(no se pudo obtener el sitio)"]

    headlines = []

    if BeautifulSoup:
        soup = BeautifulSoup(html_text, 'lxml')
        for tag in soup.find_all(['h2', 'h3']):
            subhead = tag.find('span', class_='standard-teaser-subheadline')
            if subhead:
                subhead_text = subhead.get_text(strip=True)
                subhead.extract()
                title_text = tag.get_text(strip=True)
                full_text = title_text + ". " + subhead_text
            else:
                full_text = tag.get_text(strip=True)

            if is_headline_candidate(full_text):
                headlines.append(full_text)
    else:
        for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', html_text, re.DOTALL):
            inner = m.group(1)
            sh_m = re.search(
                r'<span[^>]*class="[^"]*standard-teaser-subheadline[^"]*"[^>]*>(.*?)</span>',
                inner, re.DOTALL
            )
            if sh_m:
                title = re.sub(r'<[^>]+>', '', inner[:sh_m.start()]).strip()
                sub = re.sub(r'<[^>]+>', '', sh_m.group(1)).strip()
                full_text = title + ". " + sub
            else:
                full_text = re.sub(r'<[^>]+>', '', inner).strip()
                full_text = re.sub(r'\s+', ' ', full_text)

            if is_headline_candidate(full_text):
                headlines.append(full_text)

    seen = set()
    unique = []
    for h in headlines:
        key = h[:80].lower()
        if key not in seen:
            seen.add(key)
            unique.append(h)

    return unique[:6] if unique else ["(no se encontraron titulares)"]


def fetch_headlines_vocero() -> list:
    html_text = fetch_html("https://www.elvocero.com/")
    if not html_text:
        return ["(no se pudo obtener el sitio)"]

    text = extract_clean_text(html_text)
    headlines = extract_headlines_from_text(text)

    filtered = [h for h in headlines if len(h.split()) >= 5]
    return filtered[:6] if filtered else ["(no se encontraron titulares)"]


def extract_headlines_from_text(text: str) -> list:
    headlines = []
    seen = set()

    for line in text.split('\n'):
        line = line.strip()
        line = re.sub(r'\s+', ' ', line)
        if not is_headline_candidate(line):
            continue
        key = line[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        headlines.append(html.unescape(line))

    return headlines[:6]


def escape_md(text: str) -> str:
    """Escapa caracteres especiales de MarkdownV2 de Telegram.
    
    Los 19 caracteres que Telegram requiere escapar con \\:
    _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special_chars = set('_*[]()~`>#+-=|{}.!')
    result = []
    for c in text:
        if c in special_chars:
            result.append('\\' + c)
        else:
            result.append(c)
    return ''.join(result)


def build_summary() -> str:
    today = datetime.now().strftime("%A, %d de %B de %Y")
    lines = []

    lines.append("📰 *Resumen de Noticias*")
    lines.append(f"_{today}_")
    lines.append("")

    lines.append("▸ *El Nuevo Dia*")
    headlines = fetch_headlines_end()
    for h in headlines[:5]:
        lines.append(f"  • {escape_md(h.strip())}")
    lines.append("")

    lines.append("▸ *El Vocero*")
    headlines = fetch_headlines_vocero()
    for h in headlines[:5]:
        lines.append(f"  • {escape_md(h.strip())}")
    lines.append("")

    now = datetime.now()
    lines.append(f"🕐 Generado: {escape_md(now.strftime('%Y-%m-%d %H:%M'))} AST")
    lines.append("Fuentes: END, El Vocero")

    return "\n".join(lines)


def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID", file=sys.stderr)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }).encode()

    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("✅ Mensaje enviado a Telegram")
                return True
            else:
                print(f"❌ Telegram error: {result}", file=sys.stderr)
                return False
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ HTTP {e.code}: {body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False


def main():
    summary = build_summary()
    print(summary)
    print("\n" + "=" * 50)
    if send_telegram(summary):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
