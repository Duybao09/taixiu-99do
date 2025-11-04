import threading
import time
from flask import Flask, jsonify
from predictor import fetch_data, check_for_new_session, get_latest_prediction

app = Flask(__name__)

def background_loop():
    """Luồng nền tự động fetch dữ liệu và dự đoán"""
    while True:
        try:
            data = fetch_data()
            check_for_new_session(data)
        except Exception as e:
            print(f"⚠️ Lỗi vòng lặp nền: {e}")
        time.sleep(10)

@app.route("/api/du-doan", methods=["GET"])
def api_du_doan():
    """Endpoint chính trả về kết quả và dự đoán mới nhất"""
    latest = get_latest_prediction()
    if not latest:
        return jsonify({"message": "Chưa có dữ liệu dự đoán."}), 200
    return jsonify(latest)

if __name__ == "__main__":
    # Khởi động luồng nền tự động cập nhật
    threading.Thread(target=background_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)