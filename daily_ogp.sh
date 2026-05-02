#!/bin/bash
# Resumen diario OGP - ghost
# Busca noticias de OGP/presupuesto/gobierno en fuentes de PR
# y las envía por Telegram.
# Ejecutar de lunes a viernes en la mañana.

BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
CHAT_ID="$TELEGRAM_CHAT_ID"
LOG="/tmp/ogp_daily.log"
DATE=$(date '+%Y-%m-%d %H:%M')

if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "ERROR: TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID deben estar definidos"
    exit 1
fi

send_telegram() {
    local msg="$1"
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=${msg}" \
        -d "parse_mode=Markdown" > /dev/null 2>&1
}

# --- Scraping El Vocero ---
VOCERO=$(curl -sL "https://www.elvocero.com/" 2>/dev/null | \
    sed -n 's/.*<h3[^>]*><a[^>]*href="\([^"]*\)"[^>]*>\([^<]*\)<.*/* [\2](\1)/p' | head -6)

# --- Scraping Primera Hora (sección gobierno) ---
PH=$(curl -sL "https://www.primerahora.com/noticias/gobierno/" 2>/dev/null | \
    sed -n 's/.*<h[23][^>]*><a[^>]*href="\([^"]*\)"[^>]*>\([^<]*\)<.*/* [\2](\1)/p' | head -5)

# --- Scraping El Nuevo Día (sección gobierno) ---
END=$(curl -sL "https://www.elnuevodia.com/noticias/gobierno/" 2>/dev/null | \
    sed -n 's/.*<h[23][^>]*><a[^>]*href="\([^"]*\)"[^>]*>\([^<]*\)<.*/* [\2](\1)/p' | head -5)

# Construir mensaje
MSG="🌅 *Resumen OGP · ${DATE}*

*El Vocero:*
${VOCERO:-  _No se pudieron obtener titulares_}

*Primera Hora / Gobierno:*
${PH:-  _No se pudieron obtener titulares_}

*El Nuevo Día / Gobierno:*
${END:-  _No se pudieron obtener titulares_}

---
_Generado por ghost · hermes_"

send_telegram "$MSG"
echo "[$DATE] Resumen OGP enviado por Telegram" >> "$LOG"
echo "OK"
