#ifndef WATER_SENSOR_NODE_H
#define WATER_SENSOR_NODE_H

#include <stdint.h>
#include <stdbool.h>

#define WHO_MIN_PH        6.5f
#define WHO_MAX_PH        8.5f
#define WHO_MAX_TURBIDITY 5.0f /* NTU */
#define MAX_PHYSICAL_LPS  15.0f /* Liters per second max limit */

typedef struct {
    char sensor_id[16];
    float liters_flowed;
    float cumulative_liters;
    float ph_level;
    float turbidity_ntu;
    uint32_t sequence_number;
    uint32_t timestamp_epoch;
    uint16_t packet_crc16;
} WaterTelemetryPacket;

uint16_t compute_crc16_ccitt(const uint8_t* data, size_t length);
bool validate_who_drinking_standard(float ph, float turbidity);
bool verify_sensor_packet_integrity(const WaterTelemetryPacket* packet);

#endif /* WATER_SENSOR_NODE_H */
