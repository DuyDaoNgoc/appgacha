# 🎮 Gacha Simulator - HSR Style

Ứng dụng Gacha System kiểu Honkai: Star Rail với Admin Panel quản lý character.

## 🚀 Cách chạy

### Chạy Backend

```bash
cd d:\appNguyenHoangDang
python app.py
```

Backend sẽ chạy trên: `http://172.16.0.18:5000`

### Truy cập từ trình duyệt PC

- **Trang chủ:** http://172.16.0.18:5000/
- **Gacha App:** http://172.16.0.18:5000/gacha
- **Admin Panel:** http://172.16.0.18:5000/admin

### Truy cập từ Android App

App sẽ load từ webview, tự động kết nối đến server.

---

## 📋 Admin Panel - Quản lý Character

Truy cập: **http://172.16.0.18:5000/admin**

### Tính năng:

✅ **Thêm Character mới**

- Nhập tên character
- Chọn rarity (3-Star, 4-Star, 5-Star)
- Nhập Emoji
- Upload ảnh character
- Lưu vào database

✅ **Quản lý danh sách**

- Xem tất cả character
- Thống kê số lượng (3-Star, 4-Star, 5-Star)
- Xóa character không cần thiết
- Hiển thị ảnh preview

### Dữ liệu lưu ở đâu?

Characters được lưu tại: **`data/characters.json`**

```json
[
  {
    "id": "abc12345",
    "name": "Seele",
    "emoji": "💎",
    "rarity": "5",
    "image": "data:image/png;base64,...",
    "created_at": "2026-03-31T..."
  }
]
```

---

## 🎯 Gacha App - Roll Character

Truy cập: **http://172.16.0.18:5000/gacha**

### Chức năng:

- **Gacha 1 lần** - Roll 1 character
- **Gacha 10 lần** - Roll 10 characters (có guarantee)
- **Card Flip Animation** - Animation lật card khi roll
- **Rarity Color** - Hiển thị màu theo rarity
- **History** - Lưu lịch sử roll

### Rarity Distribution (Tỷ lệ)

- **5-Star:** 3%
- **4-Star:** 12%
- **3-Star:** 85%

---

## 🔧 API Endpoints

### Character Management

```
GET /api/characters
- Lấy danh sách tất cả characters

POST /api/characters
- Thêm character mới
- Body: { name, emoji, rarity, image }

DELETE /api/characters/<id>
- Xóa character theo ID
```

### Gacha System

```
POST /api/gacha
- Roll gacha
- Body: { count: 1 or 10 }
- Returns: Array of results

GET /api/health
- Health check
```

---

## 📸 Thêm Character - Ví dụ

1. Vào **Admin Panel** → http://172.16.0.18:5000/admin
2. Nhập: **Seele**
3. Chọn Rarity: **5-Star**
4. Nhập Emoji: **💎**
5. Upload ảnh
6. Click **Thêm Character**
7. Character sẽ xuất hiện trong danh sách

---

## 🐛 Troubleshooting

### "Offline" status trong app

→ Kiểm tra Server IP trong Settings (Cấu hình)
→ Phải là: **172.16.0.18:5000**

### Ảnh không hiển thị

→ Ảnh được lưu dạng Base64 trong JSON
→ Tối đa ~50 characters (do giới hạn ảnh Base64)

### Backend không chạy

```bash
# Kiểm tra port 5000 có bị chiếm không
netstat -ano | findstr :5000

# Kill process (nếu cần)
taskkill /PID <PID> /F
```

---

## 📊 Cấu trúc Folder

```
appNguyenHoangDang/
├── app.py                    ← Backend Flask
├── project/
│   └── www/
│       ├── index.html        ← Gacha App
│       ├── admin.html        ← Admin Panel
│       ├── home.html         ← Trang chủ
│       ├── script.js         ← Frontend logic
│       └── style.css         ← Styles
├── data/
│   └── characters.json       ← Character database
└── android/                  ← Android app
```

---

## 🎨 Customization

### Thay đổi tỷ lệ Gacha

Edit trong `app.py`:

```python
if rand < 0.03:  # 3% - 5-star
    rarity_filter = '5'
elif rand < 0.15:  # 12% - 4-star
    rarity_filter = '4'
else:  # 85% - 3-star
    rarity_filter = '3'
```

### Thay đổi màu rarity

Edit trong `admin.html` CSS:

```css
.rarity-5 {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  //... your color
}
```

---

**🎉 Chúc bạn sử dụng vui vẻ!**
