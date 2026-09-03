---
title: Cockpit Container Server Management Dashboard
emoji: 🎛️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Container Server Management Dashboard powered by Cockpit and Python app.py
---

# 🎛️ Cockpit Container Management Dashboard

Trang quản lý máy chủ chạy bên trong Docker Container, được tích hợp với mã nguồn [Cockpit](https://github.com/cockpit-project/cockpit.git) và điều phối thông qua Python `app.py`.

Trang quản lý này được tối ưu hóa cho **Hugging Face Spaces (Docker SDK)** và môi trường **Docker Container độc lập**, cho phép bạn giám sát và quản lý tài nguyên môi trường Docker (CPU, RAM, Tiến trình, Hệ thống file, Terminal web) một cách an toàn và nhẹ nhàng.

---

## 🌟 Tính năng nổi bật

- 📊 **Giám sát Tài nguyên Container:** Theo dõi mức sử dụng CPU, RAM, Disk, Network theo thời gian thực inside Container.
- 💻 **Web Terminal tích hợp:** Truy cập Shell môi trường Linux trong Docker trực tiếp từ trình duyệt.
- ⚙️ **Quản lý Tiến trình (Process Manager):** Xem danh sách tiến trình, kiểm tra tài nguyên và điều khiển các service inside Container.
- 🔒 **An toàn & Độc lập:** Dashboard chỉ quản lý môi trường bên trong Docker Container (Isolated), không can thiệp trực tiếp vào Host OS.
- 🚀 **Tương thích Hugging Face Spaces:** Cấu hình sẵn cổng `7860` và YAML Metadata tương thích hoàn toàn với Hugging Face Spaces Docker SDK.

---

## 🏗️ Kiến trúc Project

```
Hermes-Gateway/
├── app.py              # Orchestrator chính: clone/tích hợp Cockpit source, cấu hình & khởi chạy service
├── Dockerfile          # Môi trường Debian Slim siêu nhẹ (~180MB) hỗ trợ Cockpit & Python 3
├── requirements.txt    # Thư viện Python phụ trợ (psutil, flask, requests, ...)
├── cockpit.conf        # Cấu hình Web Service cho Cockpit
└── README.md           # Tài liệu hướng dẫn & HF Spaces metadata
```

---

## 🔑 Tài khoản đăng nhập mặc định

Khi container khởi chạy, tài khoản quản trị mặc định inside container là:

- **Username:** `admin`
- **Password:** `admin123` *(Có thể tùy chỉnh qua biến môi trường `ADMIN_PASSWORD`)*

---

## 🚀 Hướng dẫn chạy bằng Docker

### 1. Build Docker Image

```bash
docker build -t hermes-cockpit-gateway .
```

### 2. Chạy Container

```bash
docker run -d \
  -p 7860:7860 \
  --name cockpit-dashboard \
  -e ADMIN_PASSWORD="your_secure_password" \
  hermes-cockpit-gateway
```

### 3. Truy cập Dashboard

Mở trình duyệt và truy cập: [http://localhost:7860](http://localhost:7860)

---

## 🤗 Triển khai lên Hugging Face Spaces

1. Tạo một Space mới trên **Hugging Face**.
2. Chọn **Space SDK: Docker**.
3. Push toàn bộ mã nguồn repo này lên Hugging Face Space của bạn.
4. Hugging Face Spaces sẽ tự động build và expose cổng `7860`.

---

## 📄 Giấy phép

Dự án phát triển dựa trên mã nguồn mở [Cockpit](https://github.com/cockpit-project/cockpit.git) theo giấy phép **LGPL-2.1 / MIT**.
