from flask import Flask, render_template, redirect, request
import serial
import time


app = Flask(__name__)

# =========================
# CONFIGURARE SERIAL ARDUINO
# =========================

# Schimbă COM3 cu portul tău real: COM3, COM4, COM5 etc.
PORT = "COM3"
BAUD = 9600

arduino = serial.Serial(PORT, BAUD, timeout=2)
time.sleep(2)



last_response = "Nu exista raspuns inca."
temperature = "-"
water_value = "-"
water_status = "-"
led_status = "OFF"

messages = []
events = []


# =========================
# FUNCȚII SERIAL
# =========================

def trimite_comanda(comanda):
    arduino.reset_input_buffer()
    arduino.write((comanda + "\n").encode())

    raspuns = arduino.readline().decode(errors="ignore").strip()
    return raspuns


def citeste_lista_evenimente():
    global last_response

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

    last_response = "Evenimente incarcate din EEPROM"
    return lista




# =========================
# RUTE FLASK
# =========================

@app.route("/")
def index():
    return render_template(
        "index.html",
        last_response=last_response,
        temperature=temperature,
        water_value=water_value,
        water_status=water_status,
        led_status=led_status,
        messages=messages,
        events=events
    )


@app.route("/led/on")
def led_on():
    global last_response, led_status

    last_response = trimite_comanda("A")
    led_status = "ON"

    return redirect("/")


@app.route("/led/off")
def led_off():
    global last_response, led_status

    last_response = trimite_comanda("S")
    led_status = "OFF"

    return redirect("/")


@app.route("/temperature")
def get_temperature():
    global last_response, temperature

    last_response = trimite_comanda("T")

    if last_response.startswith("TEMP:"):
        temperature = last_response.replace("TEMP:", "")

    return redirect("/")


@app.route("/water")
def get_water():
    global last_response, water_value, water_status

    last_response = trimite_comanda("W")

    if last_response.startswith("WATER:"):
        data = last_response.replace("WATER:", "")
        parts = data.split(";")

        if len(parts) == 2:
            water_value = parts[0]
            water_status = parts[1]

    return redirect("/")


@app.route("/message", methods=["POST"])
def send_message():
    global last_response, messages

    mesaj = request.form.get("message", "")

    if mesaj.strip() != "":
        last_response = trimite_comanda("M:" + mesaj)

        messages.append(mesaj)

        if len(messages) > 10:
            messages.pop(0)

    return redirect("/")


@app.route("/flood/save")
def save_flood_event():
    global last_response, events

    last_response = trimite_comanda("F")

    if last_response.startswith("EVENT:SAVED:"):
        eveniment = last_response.replace("EVENT:SAVED:", "")

        # Simulare notificare email
        last_response = (
            last_response
            + " | EMAIL:SIMULAT - notificare generata pentru: "
            + eveniment
        )

    events = citeste_lista_evenimente()

    return redirect("/")


@app.route("/events/load")
def load_events():
    global events

    events = citeste_lista_evenimente()

    return redirect("/")


@app.route("/event/delete/<int:slot>")
def delete_event(slot):
    global last_response, events

    last_response = trimite_comanda("D:" + str(slot))

    # După ștergere, reîncărcăm lista de evenimente
    events = citeste_lista_evenimente()

    return redirect("/")
@app.route("/email/test")
def test_email():
    global last_response

    try:
        trimite_email_inundatie("TEST EMAIL - Proiect Sincretic")
        last_response = "EMAIL TEST:TRIMIS"
    except Exception as e:
        last_response = "EMAIL TEST:EROARE: " + str(e)

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)