# 🍓 Raspberry Pi 4

Código que roda no Raspberry Pi 4, o cérebro principal do Pixel.

## `eyes.py`: olhos animados

Desenha os olhos no display MHS (480×320) e assina o tópico MQTT **`emocao`** no Mosquitto do próprio Raspberry.

- O display mostra a emoção **`normal`** o tempo todo.
- Quando o ESP32 publica **`love`** ou **`angry`**, os olhos mudam para essa emoção por **5 segundos** (`MOOD_DURATION`) e depois voltam ao normal. Se a mesma emoção chegar de novo nesse período, o tempo recomeça.
- **Tocar na tela 3 vezes ou mais em até 2 segundos** (`TOUCHES_NEEDED` e `TOUCH_WINDOW`) mostra **`furious`** pelo mesmo tempo. O toque é lido direto do controlador ADS7846 do display MHS (biblioteca `evdev`) e também pelo pygame. Um toque que chega pelos dois caminhos conta só uma vez.
- Qualquer outra mensagem é ignorada. As outras emoções (`tired`, `happy`, `wide`) continuam definidas em `MOODS`, mas não são usadas por enquanto.

As configurações ficam no topo do arquivo: `MQTT_HOST`, `MQTT_PORT`, `MQTT_TOPIC`, `MQTT_MOODS`, `TOUCH_MOOD`, `MOOD_DURATION`, `TOUCHES_NEEDED`, `TOUCH_WINDOW` e `TOUCH_DEBOUNCE`.

### Dependências

```bash
sudo apt install -y python3-pygame python3-paho-mqtt python3-evdev
```

Para ler o touch sem `sudo`, o usuário precisa estar no grupo `input` (no Raspberry Pi OS o usuário padrão já está): `sudo usermod -aG input $USER`.

### Executando

```bash
python3 eyes.py
```

Aperte **Esc** para sair. Para testar sem o ESP32, publique uma emoção de outro terminal:

```bash
mosquitto_pub -h localhost -t emocao -m love
mosquitto_pub -h localhost -t emocao -m angry
```

## Próximos passos

- Gerenciador de estados emocionais mais completo;
- Módulos de inteligência artificial (linguagem natural).
