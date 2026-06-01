import serial
import time
import requests


AZURE_URL = "https://smartcontroller-bianca-bdccbvagb4f6fnhj.francecentral-01.azurewebsites.net"


PORT = "COM3"
BAUD = 9600

arduino = serial.Serial(PORT, BAUD, timeout=2)
time.sleep(2)


def trimite_la_arduino(command):
    arduino.reset_input_buffer()
    arduino.write((command + "\n").encode())

    response = arduino.readline().decode(errors="ignore").strip()
    return response


def citeste_evenimente_din_arduino():
    arduino.reset_input_buffer()
    arduino.write(("E\n").encode())

    lista = []
    started = False

    while True:
        line = arduino.readline().decode(errors="ignore").strip()

        if line == "":
            break

        if line == "EVENTS_START":
            started = True
            continue

        if line == "EVENTS_END":
            break

        if started:
            if ":" in line:
                parts = line.split(":", 1)
                slot = parts[0]
                text = parts[1]

                if text != "-":
                    lista.append({
                        "slot": slot,
                        "text": text
                    })

    return lista


def trimite_update_la_azure(payload):
    try:
        requests.post(AZURE_URL + "/api/update", json=payload, timeout=5)
    except Exception as e:
        print("Eroare la update catre Azure:", e)


while True:
    try:
        response = requests.get(AZURE_URL + "/api/get-command", timeout=5)
        data = response.json()

        command = data.get("command", "")

        if command:
            print("Comanda primita din Azure:", command)

            arduino_response = trimite_la_arduino(command)
            print("Raspuns Arduino:", arduino_response)

            payload = {
                "last_response": arduino_response
            }

            if arduino_response.startswith("LED:ON"):
                payload["led_status"] = "ON"

            elif arduino_response.startswith("LED:OFF"):
                payload["led_status"] = "OFF"

            elif arduino_response.startswith("TEMP:"):
                payload["temperature"] = arduino_response.replace("TEMP:", "")

            elif arduino_response.startswith("WATER:"):
                content = arduino_response.replace("WATER:", "")
                parts = content.split(";")

                if len(parts) == 2:
                    payload["water_value"] = parts[0]
                    payload["water_status"] = parts[1]

            elif arduino_response.startswith("MSG:SAVED:"):
                payload["last_response"] = arduino_response

            elif arduino_response.startswith("EVENT:SAVED:"):
                payload["last_response"] = (
                    arduino_response
                    + " | EMAIL:SIMULAT - notificare generata"
                )

                events = citeste_evenimente_din_arduino()
                payload["events"] = events

            elif arduino_response.startswith("EVENT:NO_FLOOD:"):
                payload["last_response"] = arduino_response

            elif arduino_response.startswith("EVENT:DELETED:"):
                events = citeste_evenimente_din_arduino()
                payload["events"] = events

            elif arduino_response.startswith("EVENTS_START"):
                events = citeste_evenimente_din_arduino()
                payload["events"] = events

            
            if command == "E":
                events = citeste_evenimente_din_arduino()
                payload["events"] = events
                payload["last_response"] = "Evenimente incarcate din EEPROM"

            trimite_update_la_azure(payload)

    except Exception as e:
        print("Eroare gateway:", e)

    time.sleep(1)