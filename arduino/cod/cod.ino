#include <EEPROM.h>

const int LM35_PIN = A0;
const int LED_PIN = 8;
const int WATER_PIN = A1;

const int WATER_THRESHOLD = 200;

// EEPROM pentru 10 mesaje
const int MSG_COUNT = 10;
const int MSG_SIZE = 50;
const int MSG_START = 0;
const int MSG_INDEX_ADDR = 600;
// EEPROM pentru 10 evenimente de inundatie
const int EVENT_COUNT = 10;
const int EVENT_SIZE = 40;
const int EVENT_START = 700;
const int EVENT_INDEX_ADDR = 950;
void setup() {
  Serial.begin(9600);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  delay(1000);

  analogRead(LM35_PIN);
  analogRead(WATER_PIN);
  delay(100);

  Serial.println("SYSTEM:READY");
}
void salveazaEveniment(String eveniment) {
  int index = EEPROM.read(EVENT_INDEX_ADDR);

  if (index < 0 || index >= EVENT_COUNT) {
    index = 0;
  }

  int adresa = EVENT_START + index * EVENT_SIZE;

  for (int i = 0; i < EVENT_SIZE; i++) {
    EEPROM.update(adresa + i, 0);
  }

  for (int i = 0; i < eveniment.length() && i < EVENT_SIZE - 1; i++) {
    EEPROM.update(adresa + i, eveniment[i]);
  }

  index = (index + 1) % EVENT_COUNT;
  EEPROM.update(EVENT_INDEX_ADDR, index);
}
void afiseazaEvenimente() {
  Serial.println("EVENTS_START");

  for (int slot = 0; slot < EVENT_COUNT; slot++) {
    int adresa = EVENT_START + slot * EVENT_SIZE;
    String eveniment = "";

    for (int i = 0; i < EVENT_SIZE; i++) {
      char c = EEPROM.read(adresa + i);

      if (c == 0) {
        break;
      }

      eveniment += c;
    }

    Serial.print(slot);
    Serial.print(":");

    if (eveniment.length() > 0) {
      Serial.println(eveniment);
    } else {
      Serial.println("-");
    }
  }

  Serial.println("EVENTS_END");
}

float citesteTemperatura() {
  long suma = 0;

  for (int i = 0; i < 10; i++) {
    suma += analogRead(LM35_PIN);
    delay(10);
  }

  float valoareMedie = suma / 10.0;
  float tensiune = valoareMedie * (5.0 / 1023.0);
  float temperaturaC = tensiune * 100.0;

  return temperaturaC;
}
void stergeEveniment(int slot) {
  if (slot < 0 || slot >= EVENT_COUNT) {
    Serial.println("EVENT:INVALID");
    return;
  }

  int adresa = EVENT_START + slot * EVENT_SIZE;

  for (int i = 0; i < EVENT_SIZE; i++) {
    EEPROM.update(adresa + i, 0);
  }

  Serial.print("EVENT:DELETED:");
  Serial.println(slot);
}

int citesteApa() {
  long suma = 0;

  for (int i = 0; i < 10; i++) {
    suma += analogRead(WATER_PIN);
    delay(10);
  }

  int valoareMedie = suma / 10;
  return valoareMedie;
}

void salveazaMesaj(String mesaj) {
  int index = EEPROM.read(MSG_INDEX_ADDR);

  if (index < 0 || index >= MSG_COUNT) {
    index = 0;
  }

  int adresa = MSG_START + index * MSG_SIZE;

  // stergem slotul vechi
  for (int i = 0; i < MSG_SIZE; i++) {
    EEPROM.update(adresa + i, 0);
  }

  // salvam mesajul nou
  for (int i = 0; i < mesaj.length() && i < MSG_SIZE - 1; i++) {
    EEPROM.update(adresa + i, mesaj[i]);
  }

  index = (index + 1) % MSG_COUNT;
  EEPROM.update(MSG_INDEX_ADDR, index);
}

void afiseazaMesaje() {
  Serial.println("MESSAGES_START");

  for (int slot = 0; slot < MSG_COUNT; slot++) {
    int adresa = MSG_START + slot * MSG_SIZE;
    String mesaj = "";

    for (int i = 0; i < MSG_SIZE; i++) {
      char c = EEPROM.read(adresa + i);

      if (c == 0) {
        break;
      }

      mesaj += c;
    }

    Serial.print(slot);
    Serial.print(":");

    if (mesaj.length() > 0) {
      Serial.println(mesaj);
    } else {
      Serial.println("-");
    }
  }

  Serial.println("MESSAGES_END");
}


void loop() {
  if (Serial.available()) {
    String comanda = Serial.readStringUntil('\n');
    comanda.trim();

    // LED ON
    if (comanda == "A") {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("LED:ON");
    }

    // LED OFF
    else if (comanda == "S") {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED:OFF");
    }

    // TEMPERATURA
    else if (comanda == "T") {
      float temperatura = citesteTemperatura();

      Serial.print("TEMP:");
      Serial.println(temperatura);
    }

    // APA / INUNDATIE
    else if (comanda == "W") {
      int valoareApa = citesteApa();

      Serial.print("WATER:");
      Serial.print(valoareApa);
      Serial.print(";");

      if (valoareApa >= WATER_THRESHOLD) {
        Serial.println("FLOOD");
      } else {
        Serial.println("OK");
      }
    }

    // MESAJ DIN WEB / SERIAL
    else if (comanda.startsWith("M:")) {
      String mesaj = comanda.substring(2);

      salveazaMesaj(mesaj);

      Serial.print("MSG:SAVED:");
      Serial.println(mesaj);
    }

    // AFISARE MESAJE
    else if (comanda == "P") {
      afiseazaMesaje();
    }

    // SALVARE EVENIMENT INUNDATIE
    else if (comanda == "F") {
      int valoareApa = citesteApa();

      if (valoareApa >= WATER_THRESHOLD) {
        String eveniment = "Inundatie val=" + String(valoareApa);
        salveazaEveniment(eveniment);

        Serial.print("EVENT:SAVED:");
        Serial.println(eveniment);
      } else {
        Serial.print("EVENT:NO_FLOOD:");
        Serial.println(valoareApa);
      }
    }

    // AFISARE EVENIMENTE
    else if (comanda == "E") {
      afiseazaEvenimente();
    }

    // STERGERE EVENIMENT
    else if (comanda.startsWith("D:")) {
      int slot = comanda.substring(2).toInt();
      stergeEveniment(slot);
    }

    else {
      Serial.print("UNKNOWN_COMMAND:");
      Serial.println(comanda);
    }
  }
}
