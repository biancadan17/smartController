from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)

state = {
    "temperature": "-",
    "water_value": "-",
    "water_status": "-",
    "led_status": "OFF",
    "last_response": "Nu exista raspuns inca.",
    "messages": [],
    "events": [],
    "pending_command": ""
}


@app.route("/")
def index():
    return render_template("index.html", state=state)


@app.route("/led/on")
def led_on():
    state["pending_command"] = "A"
    state["led_status"] = "ON"
    state["last_response"] = "Comanda LED ON trimisa catre gateway"
    return redirect("/")


@app.route("/led/off")
def led_off():
    state["pending_command"] = "S"
    state["led_status"] = "OFF"
    state["last_response"] = "Comanda LED OFF trimisa catre gateway"
    return redirect("/")


@app.route("/temperature")
def temperature():
    state["pending_command"] = "T"
    state["last_response"] = "Cerere temperatura trimisa catre gateway"
    return redirect("/")


@app.route("/water")
def water():
    state["pending_command"] = "W"
    state["last_response"] = "Cerere senzor apa trimisa catre gateway"
    return redirect("/")


@app.route("/message", methods=["POST"])
def message():
    msg = request.form.get("message", "").strip()

    if msg:
        state["pending_command"] = "M:" + msg
        state["messages"].append(msg)

        if len(state["messages"]) > 10:
            state["messages"].pop(0)

        state["last_response"] = "Mesaj trimis catre gateway: " + msg

    return redirect("/")


@app.route("/flood/save")
def flood_save():
    state["pending_command"] = "F"
    state["last_response"] = "Cerere salvare eveniment inundatie trimisa catre gateway"
    return redirect("/")


@app.route("/events/load")
def events_load():
    state["pending_command"] = "E"
    state["last_response"] = "Cerere incarcare evenimente trimisa catre gateway"
    return redirect("/")


@app.route("/event/delete/<int:slot>")
def event_delete(slot):
    state["pending_command"] = "D:" + str(slot)
    state["last_response"] = "Cerere stergere eveniment slot " + str(slot)
    return redirect("/")


# Gateway-ul intreaba Azure daca exista comanda noua
@app.route("/api/get-command")
def api_get_command():
    command = state["pending_command"]
    state["pending_command"] = ""

    return jsonify({
        "command": command
    })


# Gateway-ul trimite inapoi datele primite de la Arduino
@app.route("/api/update", methods=["POST"])
def api_update():
    data = request.json

    if not data:
        return jsonify({"status": "no data"})

    if "temperature" in data:
        state["temperature"] = data["temperature"]

    if "water_value" in data:
        state["water_value"] = data["water_value"]

    if "water_status" in data:
        state["water_status"] = data["water_status"]

    if "led_status" in data:
        state["led_status"] = data["led_status"]

    if "last_response" in data:
        state["last_response"] = data["last_response"]

    if "events" in data:
        state["events"] = data["events"]

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
    