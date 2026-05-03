#!/usr/bin/env python3
"""
ogp-daily-news: Envía resumen de noticias OGP/gobierno por Telegram.
Lee fuentes de noticias PR, genera resumen y lo envía.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
import html
import re

# ── Config ──────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# Fuentes de noticias de PR (gobierno/OGP)
SOURCES = [
    ("El Nuevo Día - Gobierno", "https://www.elnuevodia.com/noticias/gobierno/"),
    ("Primera Hora - Gobierno", "https://www.primerahora.com/noticias/gobierno/"),
    ("El Vocero",              "https://www.elvocero.com/"),
]

USER_AGENT = "ogp-daily-news/1.0"


def fetch_text(url: str) -> str:
    """Descarga el HTML de una URL y devuelve texto limpio básico."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"[Error al obtener {url}: {e}]"

    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:3000]


def build_summary() -> str:
    """Construye el resumen del día."""
    today = datetime.now().strftime("%A, %d de %B de %Y")
    lines = [f"📰 *Resumen de Noticias — {today}*\n"]

    for name, url in SOURCES:
        lines.append(f"▸ *{name}*")
        text = fetch_text(url)

        # Extraer titulares
        headlines = re.findall(
            r'(?:aria-label="|title="|alt=")?([A-Z][^.]{30,200}[.?!])',
            text
        )
        if not headlines:
            headlines = [text[:200]] if len(text) > 50 else ["(sin contenido)"]
        for h in headlines[:3]:
            lines.append(f"  • {html.unescape(h.strip())}")
        lines.append("")

    lines.append(f"\n🕐 Generado: {datetime.now().strftime('%Y-%m-%d %H:%M AST')}")
    lines.append("_Fuentes: END, Primera Hora, El Vocero_")
    return "\n".join(lines)


def send_telegram(text: str) -> bool:
    """Envía mensaje por Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID", file=sys.stderr)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
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
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}", file=sys.stderr)
        return False


def main():
    summary = build_summary()
    print(summary)
    print("\n" + "="*50)
    if send_telegram(summary):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
