#include "water_sensor_node.h"

uint16_t compute_crc16_ccitt(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (int j = 0; j < 8; ++j) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

bool validate_who_drinking_standard(float ph, float turbidity) {
    if (ph < WHO_MIN_PH || ph > WHO_MAX_PH) {
        return false;
    }
    if (turbidity > WHO_MAX_TURBIDITY || turbidity < 0.0f) {
        return false;
    }
    return true;
}

bool verify_sensor_packet_integrity(const WaterTelemetryPacket* packet) {
    if (!packet) return false;
    if (packet->liters_flowed < 0.0f || packet->liters_flowed > (MAX_PHYSICAL_LPS * 60.0f)) {
        return false; /* Flow surge anomaly */
    }
    return validate_who_drinking_standard(packet->ph_level, packet->turbidity_ntu);
}
