# ESP32 CSI Firmware

Collects Wi-Fi CSI and sends to WiSense backend.

Prerequisites: ESP-IDF v5.0+, ESP32-S2 or ESP32-C3

Configuration: Edit main/main.c for WIFI_SSID, WIFI_PASSWORD, BACKEND_URL, DEVICE_ID, DEVICE_TOKEN

Build: idf.py set-target esp32s2 && idf.py build && idf.py flash monitor

Data Format: JSON with timestamp, sequence, rssi, channel, csi array
