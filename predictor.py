import requests
import time
from collections import defaultdict, Counter

# === API nguồn dữ liệu 99do ===
API_URL = "https://rickapi.store/tx/api/GetListSoiCau"
API_TOKEN = "Bearer i6SGNKiSQS8jVTwmZZdqwL8BBCQZWQFMqgb9J3gBG7uwdZiTlsGd2rxCjfcfYf7rqt/mtHcJUhD438z3ryi5QYaPzMoSsOP/zJQ8K8kbY7H/JD4dIYtSoCFJjTVl69f8PjndW1TzKWib6mieSmW4AQlyUMkvyC+Zsq2BzY4duAI="

headers = {
    "Authorization": API_TOKEN,
    "Origin": "https://99do.club",
    "Referer": "https://99do.club/",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

last_session_id = None
history = []
latest_prediction = {}

def result_to_tx(total):
    return "T" if total >= 11 else "X"

def extract_dice_from_data(data):
    return [(d["Dice1"], d["Dice2"], d["Dice3"]) for d in reversed(data)]

def predict_next(history, max_window=7):
    n = len(history)
    if n < 3:
        count = Counter(history)
        pred = max(count, key=count.get)
        confidence = count[pred] / len(history) if len(history) else 0
        return pred, confidence, "Thống kê gần nhất (dữ liệu ít)"

    weighted_votes = defaultdict(float)
    prediction_reason = ""

    for window in range(min(max_window, n-1), 1, -1):
        pattern = "".join(history[-window:])
        counter = Counter()
        positions = []

        for i in range(n - window):
            if "".join(history[i:i+window]) == pattern:
                next_pos = i + window
                if next_pos < n:
                    counter[history[next_pos]] += 1
                    positions.append(next_pos)

        if counter:
            weighted_counter = defaultdict(float)
            for outcome in counter:
                weighted_sum = 0.0
                for pos in positions:
                    if pos < n and history[pos] == outcome:
                        weight = 1 / (n - pos)
                        weighted_sum += weight
                weighted_counter[outcome] = weighted_sum

            pred = max(weighted_counter, key=weighted_counter.get)
            confidence = weighted_counter[pred] / sum(weighted_counter.values())
            prediction_reason = f"Mẫu lặp '{pattern}' với trọng số"
            return pred, confidence, prediction_reason

    if n >= 5 and len(set(history[-5:])) == 1:
        return history[-1], 0.9, "Cầu bệt mạnh (5 phiên giống nhau)"

    if n >= 6:
        last6 = history[-6:]
        if all(last6[i] != last6[i+1] for i in range(5)):
            next_tx = "T" if last6[-1] == "X" else "X"
            return next_tx, 0.8, "Cầu xen kẽ mở rộng (6 phiên gần nhất)"

    for cycle_len in range(2, 4):
        if n >= cycle_len * 2:
            cycle = history[-cycle_len:]
            repeated = True
            for i in range(1, n // cycle_len):
                if history[-(i+1)*cycle_len : -i*cycle_len] != cycle:
                    repeated = False
                    break
            if repeated:
                next_idx = n % cycle_len
                pred = cycle[next_idx]
                return pred, 0.85, f"Phát hiện chu kỳ lặp lại (chu kỳ {cycle_len})"

    recent = history[-8:]
    count = Counter(recent)
    if abs(count["T"] - count["X"]) >= 5:
        pred = "T" if count["T"] > count["X"] else "X"
        confidence = count[pred] / 8
        return pred, confidence, "Xu hướng nghiêng rõ rệt (8 phiên gần nhất)"

    count_all = Counter(history)
    pred = max(count_all, key=count_all.get)
    confidence = count_all[pred] / n
    return pred, confidence, "Fallback: Thống kê tổng thể"

def fetch_data():
    try:
        # ✅ Bỏ kiểm tra SSL để tránh lỗi CERTIFICATE_VERIFY_FAILED
        response = requests.get(API_URL, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Lỗi khi gọi API: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Lỗi kết nối: {e}")
        return None

def check_for_new_session(data):
    global last_session_id, history, latest_prediction

    if data and isinstance(data, list) and len(data) > 0:
        latest_session = data[0]
        current_session_id = latest_session["GameSessionID"]

        if current_session_id != last_session_id:
            dice_list = extract_dice_from_data(data)
            totals = [sum(d) for d in dice_list]
            history = [result_to_tx(t) for t in totals]

            prediction, confidence, reason = predict_next(history)
            latest_prediction = {
                "phien": latest_session["GameSessionID"],
                "ket_qua": result_to_tx(latest_session["DiceSum"]),
                "du_doan": prediction,
                "do_tin_cay": f"{confidence*100:.1f}%",
                "co_so": reason
            }

            print(f"🎲 Phiên {latest_session['GameSessionID']} | Tổng {latest_session['DiceSum']} → {result_to_tx(latest_session['DiceSum'])}")
            print(f"🤖 Dự đoán: {prediction} ({confidence*100:.1f}%) | {reason}\n")

            last_session_id = current_session_id
    else:
        print("⚠️ Không nhận được dữ liệu hợp lệ.")

def get_latest_prediction():
    return latest_prediction
