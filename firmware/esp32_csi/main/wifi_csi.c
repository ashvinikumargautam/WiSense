#include "wifi_csi.h"
#include <string.h>
#include <esp_wifi.h>
#include <esp_log.h>
#include <esp_timer.h>
static const char *TAG = "wifi_csi";
static csi_callback_t s_cb = NULL;
static void *s_ctx = NULL;
static uint32_t s_seq = 0;
#ifdef CONFIG_ESP32_WIFI_ENABLE_WIFI_TX_STATS
static void csi_rx_cb(void *ctx, wifi_csi_info_t *info) {
    if (!s_cb || !info) return;
    csi_data_t d = {0};
    d.timestamp = esp_timer_get_time() / 1000;
    d.sequence = ++s_seq;
    d.rssi = info->rx_ctrl.rssi;
    d.channel = info->rx_ctrl.channel;
    int n = info->len; if (n > CSI_MAX_SUBCARRIERS) n = CSI_MAX_SUBCARRIERS;
    int8_t *raw = (int8_t *)info->buf;
    for (int i = 0; i < n && (i*2+1) < info->len; i++) {
        d.csi[i][0] = (float)raw[i*2] / 127.0f;
        d.csi[i][1] = (float)raw[i*2+1] / 127.0f;
    }
    d.n_subcarriers = n;
    s_cb(&d, s_ctx);
}
#endif
void wifi_csi_init(csi_callback_t cb, void *ctx) {
    s_cb = cb; s_ctx = ctx; s_seq = 0;
#ifdef CONFIG_ESP32_WIFI_ENABLE_WIFI_TX_STATS
    wifi_csi_config_t cfg = {.enable=1,.acquire_csi_legacy=1,.acquire_csi_ht20=1,.acquire_csi_ht40=0,.acquire_csi_vht=0};
    esp_wifi_set_csi_config(&cfg);
    esp_wifi_register_csi_cb(csi_rx_cb);
    ESP_LOGI(TAG, "CSI initialized");
#else
    ESP_LOGW(TAG, "CSI not enabled in menuconfig");
#endif
}
void wifi_csi_deinit(void) {
#ifdef CONFIG_ESP32_WIFI_ENABLE_WIFI_TX_STATS
    esp_wifi_unregister_csi_cb();
#endif
    s_cb = NULL; s_ctx = NULL;
}
