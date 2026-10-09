# 📡 ESP32

Firmware do ESP32, responsável pela parte sensorial do Pixel. É um projeto **PlatformIO**: abra esta pasta (`programacao/esp32`) no VS Code com a extensão PlatformIO.

## O que ele faz

Lê um sensor de toque capacitivo (ex.: TTP223), conta os toques de uma sequência e publica a emoção no tópico MQTT **`emocao`**, que o Raspberry Pi assina:

| Toques na sequência | Mensagem publicada | Quando é enviada |
|---|---|---|
| Exatamente 3 | `love` | Ao fim da sequência |
| Mais de 10 | `furious` | No 11º toque, na hora |
| Outros valores | — | Nada é enviado |

Uma sequência termina quando o sensor fica **1,5 s** sem ser tocado. A mensagem é texto puro (ex.: `love`), sem JSON.

Os valores ficam no topo de [`src/main.cpp`](src/main.cpp) e podem ser ajustados: `PINO_TOQUE`, `TOQUES_LOVE`, `TOQUES_FURIOUS`, `FIM_SEQUENCIA_MS` e `DEBOUNCE_MS`.

## Ligação

| Sensor | ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SIG | GPIO 4 |

> ⚠️ Alimente o sensor com **3,3 V**, não 5 V: o ESP32 trabalha com 3,3 V e o pino SIG repete a tensão de alimentação.

## Configuração

1. Copie `include/config.example.h` para `include/config.h`.
2. Preencha o nome e a senha do Wi-Fi e o **IP do Raspberry Pi** (veja com `hostname -I` no Raspberry).

O `config.h` está no `.gitignore`, então a senha do Wi-Fi não vai para o GitHub.

## Preparando o Mosquitto no Raspberry Pi

A partir da versão 2, o Mosquitto só aceita conexões do próprio Raspberry. Para o ESP32 conseguir se conectar pela rede, crie o arquivo `/etc/mosquitto/conf.d/pixel.conf`:

```
listener 1883
allow_anonymous true
```

E reinicie o serviço:

```bash
sudo systemctl restart mosquitto
```

> `allow_anonymous true` serve para a rede de casa durante o desenvolvimento. Mais tarde dá para adicionar usuário e senha.

## Gravando e testando

1. Na barra do PlatformIO, clique em **Upload** (→) e depois em **Monitor** (🔌). O monitor serial roda a 115200 baud.
2. No Raspberry Pi, acompanhe o tópico:

   ```bash
   mosquitto_sub -h localhost -t emocao -v
   ```

3. Toque 3 vezes no sensor e espere 1,5 s: deve aparecer `emocao love`. Toque mais de 10 vezes seguidas: deve aparecer `emocao furious`.

## Próximos passos

- Fazer o `eyes.py` assinar o tópico `emocao` e trocar a expressão;
- Ler o giroscópio.
