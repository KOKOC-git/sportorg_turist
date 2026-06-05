import sys
import time
import serial

port = sys.argv[1] if len(sys.argv) > 1 else "COM1"
baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 9600

print(f"Opening {port} at {baudrate}...")
ser = serial.Serial(port, baudrate=baudrate, timeout=0.05)

ser.dtr = True
ser.rts = True

last_lines = None

print("Monitoring bytes and modem lines. Press Ctrl+C to stop.")
print("Trigger the photo finish now.")

try:
    while True:
        lines = {
            "CTS": ser.cts,
            "DSR": ser.dsr,
            "CD": ser.cd,
            "RI": ser.ri,
        }

        if lines != last_lines:
            print("LINES:", lines)
            last_lines = lines

        data = ser.read(1024)
        if data:
            print("DATA:", data, "HEX:", data.hex(" "))

        time.sleep(0.05)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    ser.close()