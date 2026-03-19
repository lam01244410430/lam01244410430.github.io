import os
import requests
import time
from datetime import datetime, timedelta
from supabase import create_client

# Nạp biến môi trường
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_dynamic_routes():
    """Lấy danh sách chặng bay do người dùng yêu cầu từ Database"""
    try:
        response = supabase.table('tracked_routes').select('origin, destination').execute()
        return response.data
    except Exception as e:
        print(f"❌ Lỗi khi đọc Database: {e}")
        return []

def run_upgraded_bot():
    print(f"🚀 KHỞI ĐỘNG HỆ THỐNG SĂN VÉ (DYNAMIC) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Lấy danh sách chặng bay động
    routes_to_track = get_dynamic_routes()
    
    if not routes_to_track:
        print("⚠️ Không có chặng bay nào trong danh sách yêu cầu. Dừng hệ thống.")
        return

    print(f"📋 Tìm thấy {len(routes_to_track)} chặng bay do người dùng yêu cầu.")

    dep_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    ret_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")

    url = "https://flights-sky.p.rapidapi.com/flights/search-roundtrip"
    headers = {
        "x-rapidapi-host": "flights-sky.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY 
    }

    # Vòng lặp duyệt qua danh sách lấy từ Database
    for route in routes_to_track:
        origin = route["origin"]
        dest = route["destination"]
        print(f"\n🔄 Đang xử lý chặng: {origin} ➡️ {dest}")

        querystring = {"origin": origin, "destination": dest, "date": dep_date, "returnDate": ret_date, "adults": "1", "currency": "VND"}

        try:
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code == 200:
                data = response.json()
                # Tạm dùng cấu trúc phổ biến, bạn cần điều chỉnh nếu API trả về khác
                if 'data' in data and 'itineraries' in data['data'] and len(data['data']['itineraries']) > 0:
                    cheapest_price = data['data']['itineraries'][0]['price']['raw']
                    
                    payload = {"origin": origin, "destination": dest, "departure_date": dep_date, "total_price_vnd": cheapest_price}
                    supabase.table('price_history').insert(payload).execute()
                    print(f"✅ Đã lưu giá: {cheapest_price:,.0f} VND")
                else:
                    print("⚠️ Không tìm thấy giá vé trong JSON trả về.")
            else:
                print(f"❌ API Lỗi: {response.status_code}")
        except Exception as e:
            print(f"❌ Lỗi xử lý chặng {origin}-{dest}: {e}")

        time.sleep(3) # Tránh bị block API

if __name__ == "__main__":
    run_upgraded_bot()
