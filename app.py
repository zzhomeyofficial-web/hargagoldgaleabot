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
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

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

    # 🔹 Sekarang dukung photo dan document
    if "message" in data and ("photo" in data["message"] or "document" in data["message"]):
        try:
            # Ambil caption, bersihkan & ubah huruf kecil
            caption = data["message"].get("caption", "").strip().lower()
            chat_id = data["message"]["chat"]["id"]
            logging.info(f"📩 Caption diterima: '{caption}'")

            # Ambil file_id tergantung jenis kiriman
            if "photo" in data["message"]:
                file_id = data["message"]["photo"][-1]["file_id"]
                logging.info("📷 Jenis file: photo")
            elif "document" in data["message"]:
                file_id = data["message"]["document"]["file_id"]
                logging.info("📄 Jenis file: document")
            else:
                logging.warning("⚠️ Tidak ditemukan file_id (bukan foto/file).")
                return "OK", 200

            # 🔗 Ambil file dari Telegram
            file_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

            # 🏷️ Tentukan nama file berdasarkan caption
            if "antam" in caption:
                public_id = "antam"
            elif "silver" in caption:
                public_id = "silver"
            elif "eoa" in caption:
                public_id = "eoa"
            else:
                public_id = "harga_emas"

            logging.info(f"📦 Upload ke Cloudinary sebagai: {public_id}")

            # ☁️ Upload ke Cloudinary (overwrite gambar lama)
            result = cloudinary.uploader.upload(
                file_url,
                public_id=public_id,
                overwrite=True,
                invalidate=True
            )

            preview_url = result["secure_url"]

            # 💬 Gunakan mode Markdown aman (URL diapit tanda < > supaya tidak error)
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
            logging.info(f"✅ Upload berhasil untuk {public_id}")

        except Exception as e:
            logging.error(f"❌ Error: {e}")
            chat_id = data["message"]["chat"]["id"]
            error_text = f"⚠️ Terjadi kesalahan saat memperbarui gambar: {e}"
            requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                params={"chat_id": chat_id, "text": error_text}
            )

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

