// Configuração de rede do Pixel.
// Copie este arquivo para "config.h" (na mesma pasta) e preencha os dados.
// O "config.h" está no .gitignore para que a senha do Wi-Fi não vá para o GitHub.
#pragma once

#define WIFI_SSID   "nome-da-sua-rede"
#define WIFI_SENHA  "senha-da-sua-rede"

// IP do Raspberry Pi, onde roda o broker Mosquitto
#define MQTT_BROKER "192.168.0.100"
#define MQTT_PORTA  1883
