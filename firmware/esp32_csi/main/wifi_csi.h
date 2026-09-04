#ifndef WIFI_CSI_H
#define WIFI_CSI_H
#include <stdint.h>
#define CSI_MAX_SUBCARRIERS 64
typedef struct {
    int64_t timestamp;
    uint32_t sequence;
    float rssi;
    uint8_t channel;
    float csi[CSI_MAX_SUBCARRIERS][2];
    int n_subcarriers;
} csi_data_t;
typedef void (*csi_callback_t)(const csi_data_t *data, void *ctx);
void wifi_csi_init(csi_callback_t callback, void *ctx);
void wifi_csi_deinit(void);
#endif
