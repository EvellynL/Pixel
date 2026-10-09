// Pixel - firmware do ESP32
// Lê um sensor de toque capacitivo (VCC, GND, SIG), conta os toques de uma
// sequência e publica a emoção correspondente no tópico MQTT "emocao":
//   - exatamente 3 toques -> "love"
//   - mais de 10 toques   -> "furious"

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

#include "config.h"

// ---------- Hardware ----------
const uint8_t PINO_TOQUE = 4;  // SIG do sensor capacitivo

// ---------- Regras de toque ----------
const unsigned long DEBOUNCE_MS = 50;         // ignora ruído no sinal
const unsigned long FIM_SEQUENCIA_MS = 1500;  // pausa que encerra uma sequência de toques
const int TOQUES_LOVE = 3;
const int TOQUES_FURIOUS = 10;  // acima deste valor envia "furious"

// ---------- MQTT ----------
const char *TOPICO_EMOCAO = "emocao";
const unsigned long RECONEXAO_MS = 3000;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

bool estadoLido = LOW;
bool estadoEstavel = LOW;
unsigned long ultimaMudanca = 0;
unsigned long ultimoToque = 0;
unsigned long ultimaTentativaMqtt = 0;
int contadorToques = 0;
bool furiousEnviado = false;

void conectarWiFi() {
  Serial.printf("Conectando ao Wi-Fi \"%s\"", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nWi-Fi conectado. IP: %s\n", WiFi.localIP().toString().c_str());
}

// Tenta reconectar ao broker sem travar a leitura do sensor por muito tempo.
void garantirMqtt() {
  if (mqtt.connected() || WiFi.status() != WL_CONNECTED) return;
  unsigned long agora = millis();
  if (agora - ultimaTentativaMqtt < RECONEXAO_MS) return;
  ultimaTentativaMqtt = agora;

  String clientId = "pixel-esp32-" + WiFi.macAddress();
  Serial.printf("Conectando ao broker MQTT %s:%d... ", MQTT_BROKER, MQTT_PORTA);
  if (mqtt.connect(clientId.c_str())) {
    Serial.println("ok");
  } else {
    Serial.printf("falhou (estado %d)\n", mqtt.state());
  }
}

void publicarEmocao(const char *emocao) {
  if (mqtt.publish(TOPICO_EMOCAO, emocao)) {
    Serial.printf("Publicado em \"%s\": %s\n", TOPICO_EMOCAO, emocao);
  } else {
    Serial.printf("Falha ao publicar \"%s\" (MQTT desconectado?)\n", emocao);
  }
}

void lerSensor() {
  unsigned long agora = millis();
  bool leitura = digitalRead(PINO_TOQUE);

  if (leitura != estadoLido) {
    estadoLido = leitura;
    ultimaMudanca = agora;
  }

  // Sinal estável por DEBOUNCE_MS: aceita a mudança
  if (agora - ultimaMudanca >= DEBOUNCE_MS && estadoEstavel != estadoLido) {
    estadoEstavel = estadoLido;
    if (estadoEstavel == HIGH) {  // início de um toque
      contadorToques++;
      ultimoToque = agora;
      Serial.printf("Toque %d\n", contadorToques);

      // Responde na hora, sem esperar o fim da sequência
      if (contadorToques > TOQUES_FURIOUS && !furiousEnviado) {
        publicarEmocao("furious");
        furiousEnviado = true;
      }
    }
  }

  // Fim da sequência: ficou sem tocar por FIM_SEQUENCIA_MS
  if (contadorToques > 0 && estadoEstavel == LOW && agora - ultimoToque >= FIM_SEQUENCIA_MS) {
    Serial.printf("Sequência encerrada com %d toque(s)\n", contadorToques);
    if (contadorToques == TOQUES_LOVE) {
      publicarEmocao("love");
    }
    contadorToques = 0;
    furiousEnviado = false;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PINO_TOQUE, INPUT);

  conectarWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORTA);
}

void loop() {
  garantirMqtt();
  mqtt.loop();
  lerSensor();
}
