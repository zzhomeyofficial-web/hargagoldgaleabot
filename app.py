from flask import Flask, request
import requests
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
import logging

# 🔧 Muat file .env
load_dotenv()

app = Flask(__name__)

# ⚙️ Konfigurasi logging (biar terlihat di Render logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# 🔑 Ambil variabel dari .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLOUD_NAME = os.getenv("CLOUD_NAME")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# ☁️ Konfigurasi Cloudinary
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

    # Proses hanya pesan dengan photo atau document
    if "message" in data and ("photo" in data["message"] or "document" in data["message"]):
        try:
            caption = data["message"].get("caption", "").strip().lower()
            chat_id = data["message"]["chat"]["id"]
            logging.info(f"📩 Caption diterima: '{caption}'")

            # Ambil file_id sesuai jenis file
            if "photo" in data["message"]:
                file_id = data["message"]["photo"][-1]["file_id"]
                logging.info("📷 Jenis file: photo")
            elif "document" in data["message"]:
                file_id = data["message"]["document"]["file_id"]
                logging.info("📄 Jenis file: document")
            else:
                logging.warning("⚠️ Tidak ada file_id ditemukan.")
                return "OK", 200

            # 🏷️ Tentukan nama file berdasarkan caption
            if "antam" in caption:
                public_id = "antam"
            elif "silver" in caption:
                public_id = "silver"
            elif "eoa" in caption:
                public_id = "eoa"
            elif "king" in caption or "halim" in caption or "king halim" in caption:
                public_id = "king_halim"
            elif "ubs" in caption:
                public_id = "ubs"
            else:
                public_id = "harga_emas"


            logging.info(f"📦 Upload ke Cloudinary sebagai: {public_id}")

            # Upload ke Cloudinary
            result = cloudinary.uploader.upload(
                file_url,
                public_id=public_id,
                overwrite=True,
                invalidate=True
            )

            preview_url = result["secure_url"]
            logging.info(f"✅ Upload berhasil: {preview_url}")

            # 💬 Kirim balasan ke Telegram (Markdown aman)
            text = f"✅ Harga *{public_id.upper()}* telah diperbarui!\n\n📎 <{preview_url}>"

            response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                params={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False
                }
            )

            logging.info(f"📤 Respon Telegram: {response.text}")
            logging.info(f"✅ Upload & balasan sukses untuk {public_id}")

        except Exception as e:
            logging.error(f"❌ Error: {e}")
            try:
                chat_id = data["message"]["chat"]["id"]
                error_text = f"⚠️ Terjadi kesalahan saat memperbarui gambar: {e}"
                requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={"chat_id": chat_id, "text": error_text}
                )
            except Exception as inner_e:
                logging.error(f"💥 Gagal kirim pesan error: {inner_e}")

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

