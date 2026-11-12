#!/usr/bin/env python3
"""
AQUALEDGER: CRYPTOGRAPHICALLY VERIFIED CLEAN WATER FLOW & ESCROW PROTOCOL
========================================================================
Author: Usman Bamidele (100L Mathematics Student, FUNAAB)
Track: Social Good, Humanitarian Infrastructure & Zero-Corruption Escrow
Mission: Eliminating NGO embezzlement through Merkle-verified IoT water telemetry.
"""

import sys
import time
import json
import hmac
import hashlib
import struct
from typing import Dict, Any, List, Tuple, Optional

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Protocol Invariants
MIN_PH_THRESHOLD = 6.5
MAX_PH_THRESHOLD = 8.5
MAX_TURBIDITY_NTU = 5.0          # WHO clean drinking water standard (< 5 NTU)
MAX_FLOW_RATE_LPS = 15.0         # Physical flow limit (Liters per second)
PAYOUT_PER_1000_LITERS_USD = 2.50 # $2.50 released per 1,000 liters verified

class WaterSensorAttestor:
    """Simulates cryptographic hardware secure enclave on solar water well telemetry unit."""

    def __init__(self, sensor_id: str, secret_key: str = "AQUA_SECURE_ENCLAVE_2026"):
        self.sensor_id = sensor_id
        self.secret_key = secret_key.encode('utf-8')
        self.cumulative_liters: float = 0.0

    def generate_telemetry_packet(self, liters_flowed: float, ph: float, turbidity: float, seq_num: int) -> Dict[str, Any]:
        """Constructs and signs an immutable water quality and volume measurement packet."""
        timestamp = int(time.time())
        self.cumulative_liters += liters_flowed

        payload_str = f"{self.sensor_id}:{liters_flowed:.2f}:{self.cumulative_liters:.2f}:{ph:.2f}:{turbidity:.2f}:{seq_num}:{timestamp}"
        signature = hmac.new(self.secret_key, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()

        packet = {
            "sensor_id": self.sensor_id,
            "liters_flowed": round(liters_flowed, 2),
            "cumulative_liters": round(self.cumulative_liters, 2),
            "ph": round(ph, 2),
            "turbidity": round(turbidity, 2),
            "seq_num": seq_num,
            "timestamp": timestamp,
            "signature": signature
        }
        return packet

class MerkleTelemetryTree:
    """Builds cryptographic Merkle proof tree for batch verification of water measurements."""

    @staticmethod
    def hash_leaf(packet: Dict[str, Any]) -> str:
        serialized = json.dumps(packet, sort_keys=True).encode('utf-8')
        return hashlib.sha256(serialized).hexdigest()

    @classmethod
    def compute_merkle_root(cls, packets: List[Dict[str, Any]]) -> str:
        if not packets:
            return hashlib.sha256(b"EMPTY_TREE").hexdigest()
        
        current_level = [cls.hash_leaf(p) for p in packets]
        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])
            next_level = []
            for i in range(0, len(current_level), 2):
                combined = (current_level[i] + current_level[i+1]).encode('utf-8')
                next_level.append(hashlib.sha256(combined).hexdigest())
            current_level = next_level
        return current_level[0]

class CleanWaterEscrowSentry:
    """Enforces non-custodial milestone funding release based on verified WHO water standards."""

    def __init__(self, initial_escrow_deposit_usd: float, secret_key: str = "AQUA_SECURE_ENCLAVE_2026"):
        self.escrow_vault_usd: float = initial_escrow_deposit_usd
        self.released_funds_usd: float = 0.0
        self.total_verified_clean_liters: float = 0.0
        self.last_seq_nums: Dict[str, int] = {}
        self.secret_key = secret_key.encode('utf-8')
        self.verified_ledger: List[Dict[str, Any]] = []

    def verify_and_settle_packet(self, packet: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Validates 4 core invariants:
        1. Cryptographic HMAC authenticity.
        2. Sequence monotonicity (Anti-replay).
        3. Physical flow rate sanity bounds.
        4. WHO chemical water quality compliance (pH 6.5-8.5, Turbidity < 5 NTU).
        """
        sensor_id = packet["sensor_id"]
        liters = packet["liters_flowed"]
        cum_liters = packet["cumulative_liters"]
        ph = packet["ph"]
        turbidity = packet["turbidity"]
        seq_num = packet["seq_num"]
        timestamp = packet["timestamp"]
        sig = packet["signature"]

        # Invariant 1: Cryptographic Authentication
        payload_str = f"{sensor_id}:{liters:.2f}:{cum_liters:.2f}:{ph:.2f}:{turbidity:.2f}:{seq_num}:{timestamp}"
        expected_sig = hmac.new(self.secret_key, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return False, 0.0, "ERR_CRYPTOGRAPHIC_SIGNATURE_INVALID"

        # Invariant 2: Sequence Monotonicity (Anti-Replay)
        last_seq = self.last_seq_nums.get(sensor_id, 0)
        if seq_num <= last_seq:
            return False, 0.0, f"ERR_REPLAY_ATTACK_DETECTED: LastSeq={last_seq}, RecvSeq={seq_num}"

        # Invariant 3: Physical Flow Rate Bounds
        if liters <= 0 or liters > (MAX_FLOW_RATE_LPS * 60): # 1 minute batch max
            return False, 0.0, f"ERR_FLOW_RATE_ANOMALY: {liters}L exceeds physical bounds"

        # Invariant 4: WHO Clean Water Quality Standard Check
        if ph < MIN_PH_THRESHOLD or ph > MAX_PH_THRESHOLD:
            return False, 0.0, f"ERR_CONTAMINATED_PH: {ph} outside safe WHO limits [6.5 - 8.5]"

        if turbidity > MAX_TURBIDITY_NTU:
            return False, 0.0, f"ERR_HIGH_TURBIDITY: {turbidity} NTU exceeds safe WHO limit (5.0 NTU)"

        # All invariants passed -> Calculate and execute milestone escrow release
        payout = (liters / 1000.0) * PAYOUT_PER_1000_LITERS_USD
        if payout > self.escrow_vault_usd:
            payout = self.escrow_vault_usd # Cap at available escrow

        self.escrow_vault_usd -= payout
        self.released_funds_usd += payout
        self.total_verified_clean_liters += liters
        self.last_seq_nums[sensor_id] = seq_num

        audit_entry = {
            "tx_hash": hashlib.sha256(f"{sensor_id}:{seq_num}:{payout}".encode()).hexdigest()[:16],
            "sensor": sensor_id,
            "liters_verified": liters,
            "payout_usd": round(payout, 4),
            "vault_remaining": round(self.escrow_vault_usd, 4),
            "timestamp": timestamp
        }
        self.verified_ledger.append(audit_entry)
        return True, round(payout, 4), "SUCCESS_FUNDS_DISBURSED"
