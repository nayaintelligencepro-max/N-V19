#!/usr/bin/env python3
"""NAYA — Setup Telegram (2 min). Usage: python3 tools/setup_telegram.py"""
import os, sys, time
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

def get_updates(token):
    try:
        import requests
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
        return r.json().get("result", []) if r.status_code == 200 else []
    except Exception as e:
        print(f"Erreur: {e}"); return []

def test_send(token, chat_id):
    try:
        import requests
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id":chat_id, "text":"✅ <b>NAYA V19</b> — Bot configuré!", "parse_mode":"HTML"}, timeout=10)
        return r.status_code == 200
    except: return False

def save_config(token, chat_id):
    env_local = ROOT / ".env"
    lines = [l for l in (env_local.read_text().splitlines() if env_local.exists() else [])
             if not l.startswith(("TELEGRAM_BOT_TOKEN=","TELEGRAM_CHAT_ID="))]
    lines += [f"TELEGRAM_BOT_TOKEN={token}", f"TELEGRAM_CHAT_ID={chat_id}"]
    env_local.write_text("\n".join(lines) + "\n")

def main():
    print("\n" + "="*50 + "\n  NAYA V19 — Config Telegram\n" + "="*50 + "\n")
    print("1. Telegram → @BotFather → /newbot → copie le token\n")
    token = input("📋 BOT TOKEN: ").strip()
    if len(token) < 20: print("❌ Token invalide"); return
    print("\n2. Envoie un message à ton bot, puis Entrée")
    input("   [Entrée]...")
    updates = get_updates(token)
    if not updates:
        chat_id = input("⚠️ Chat ID manuellement: ").strip()
    else:
        chats = {}
        for u in updates:
            msg = u.get("message", {})
            cid = str(msg.get("chat", {}).get("id", ""))
            name = msg.get("chat", {}).get("first_name", "?")
            if cid: chats[cid] = name
        chat_id = list(chats.keys())[0]
        print(f"✅ Chat ID: {chat_id} ({list(chats.values())[0]})")
    if test_send(token, chat_id): print("✅ Message test envoyé!")
    else: print("⚠️ Test échoué")
    save_config(token, chat_id)
    print(f"\n✅ Telegram configuré! Token: {token[:8]}... Chat: {chat_id}\n")

if __name__ == "__main__": main()
