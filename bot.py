import os
import requests
import time
from datetime import datetime, timedelta
from supabase import create_client

# 1. Lấy Keys từ môi trường GitHub Actions
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Định nghĩa Data Structure chứa các chặng bay cần theo dõi
ROUTES_TO_TRACK = [
    # ---- Các chặng nội địa ----
    {"origin": "SGN", "destination": "HAN"}, # TP.HCM - Hà Nội
    {"origin": "HAN", "destination": "DAD"}, # Hà Nội - Đà Nẵng
    
    # ---- Các chặng quốc tế ----
    {"origin": "HAN", "destination": "NNG"}, # Hà Nội - Nam Ninh (Trung Quốc)
    {"origin": "SGN", "destination": "BKK"}, # TP.HCM - Bangkok (Thái Lan)
    {"origin": "HAN", "destination": "ICN"}  # Hà Nội - Seoul (Hàn Quốc)
]

def run_bot():
    # 3. Tính toán ngày bay tự động (Ví dụ: Cào giá vé của đúng 30 ngày tính từ hôm nay)
    future_date = datetime.now() + timedelta(days=30)
    target_date_str = future_date.strftime("%Y-%m-%d")
    
    print(f"Bắt đầu cào dữ liệu giá vé cho ngày khởi hành: {target_date_str}\n")
    
    url = "https://flights-sky.p.rapidapi.com/flights/search-roundtrip?fromEntityId=PARI"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": "flights-sky.p.rapidapi.com"}
    
    # 4. Vòng lặp xử lý từng chặng bay
    for route in ROUTES_TO_TRACK:
        origin = route["origin"]
        destination = route["destination"]
        
        print(f"🔄 Đang cào chặng {origin} ➡️ {destination}...")
        
        querystring = {
            "originId": origin, 
            "destinationId": destination, 
            "fromDate": target_date_str, 
            "currency": "VND"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            
            if response.status_code == 200:
                data = response.json()
                if 'flights' in data and len(data['flights']) > 0:
                    cheapest_price = data['flights'][0]['price']
                    
                    payload = {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": target_date_str,
                        "total_price_vnd": cheapest_price
                    }
                    
                    # Insert vào Database
                    supabase.table('price_history').insert(payload).execute()
                    print(f"✅ Đã lưu: {cheapest_price} VND")
                else:
                    print(f"⚠️ Không có chuyến bay nào được tìm thấy.")
            else:
                print(f"❌ Lỗi API HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Lỗi hệ thống khi xử lý chặng này: {e}")
            
        # 5. BẮT BUỘC: Delay để tránh bị khóa API (Rate Limiting)
        # Các API miễn phí thường cấm gọi quá nhanh (ví dụ: không quá 1 request/giây)
        time.sleep(3) 

    print("\n🎉 Hoàn tất toàn bộ chiến dịch cào dữ liệu hôm nay!")

if __name__ == "__main__":
    run_bot()
