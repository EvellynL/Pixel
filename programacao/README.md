# 💻 Programação

Código-fonte do Pixel.

## Estrutura

```
programacao/
├── raspberry/   # Código do Raspberry Pi 4 (display, expressões, MQTT e IA)
└── esp32/       # Firmware do ESP32 (sensores capacitivos, giroscópio e MQTT)
```

- **[`raspberry/`](raspberry/)**: controle do display MHS, renderização das expressões, cliente MQTT, gerenciador de emoções e módulos de inteligência artificial (linguagem natural).
- **[`esp32/`](esp32/)**: leitura dos sensores de toque capacitivo e do giroscópio, conversão dos dados em emoções e publicação via MQTT.
