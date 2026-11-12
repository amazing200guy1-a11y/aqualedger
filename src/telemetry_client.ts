/**
 * AQUALEDGER IOT TELEMETRY & ESCROW CLIENT
 */

export interface TelemetryReading {
  sensorId: string;
  litersFlowed: number;
  cumulativeLiters: number;
  ph: number;
  turbidityNtu: number;
  seqNum: number;
  timestamp: number;
  signature: string;
}

export class AquaLedgerClient {
  public static readonly MIN_PH = 6.5;
  public static readonly MAX_PH = 8.5;
  public static readonly MAX_TURBIDITY = 5.0;

  public static isPotable(reading: TelemetryReading): boolean {
    return reading.ph >= this.MIN_PH &&
           reading.ph <= this.MAX_PH &&
           reading.turbidityNtu <= this.MAX_TURBIDITY;
  }

  public static computeEscrowReleaseUSD(liters: number): number {
    return (liters / 1000.0) * 2.50;
  }
}
