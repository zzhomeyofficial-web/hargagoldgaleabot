from flask import Flask, request
import requests
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

# Muat file .env
load_dotenv()

app = Flask(__name__)

# Ambil variabel dari .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLOUD_NAME = os.getenv("CLOUD_NAME")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

@app.route("/", methods=["GET"])
def home():
    return "🤖 Galea Gold Bot Aktif", 200

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" in data and "photo" in data["message"]:
        caption = data["message"].get("caption", "").lower()
        photos = data["message"]["photo"]
        file_id = photos[-1]["file_id"]

        # Ambil file dari Telegram
        file_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        # Tentukan nama file berdasar caption
        if "antam" in caption:
            public_id = "antam"
        elif "ubs" in caption:
            public_id = "ubs"
        elif "eoa" in caption:
            public_id = "eoa"
        else:
            public_id = "harga_emas"

        # Upload ke Cloudinary (overwrite gambar lama)
        result = cloudinary.uploader.upload(
            file_url,
            public_id=public_id,
            overwrite=True,
            invalidate=True
        )

        # Kirim balasan ke Telegram
        chat_id = data["message"]["chat"]["id"]
        preview_url = result["secure_url"]
        text = f"✅ Gambar *{public_id.upper()}* berhasil diperbarui!\n\n📎 {preview_url}"
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                     params={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
