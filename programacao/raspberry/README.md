# 🍓 Raspberry Pi 4

Código que roda no Raspberry Pi 4, o cérebro principal do Pixel.

## `eyes.py`: olhos animados

Desenha os olhos no display MHS (480×320) e assina o tópico MQTT **`emocao`** no Mosquitto do próprio Raspberry.

- O display mostra a emoção **`normal`** o tempo todo.
- Quando o ESP32 publica **`love`** ou **`furious`**, os olhos mudam para essa emoção por **8 segundos** e depois voltam ao normal. Se a mesma emoção chegar de novo nesse período, o tempo recomeça.
- Qualquer outra mensagem é ignorada. As outras emoções (`tired`, `angry`, `happy`, `wide`) continuam definidas em `MOODS`, mas não são usadas por enquanto.

As configurações ficam no topo do arquivo: `MQTT_HOST`, `MQTT_PORT`, `MQTT_TOPIC`, `MQTT_MOODS` e `MOOD_DURATION`.

### Dependências

```bash
sudo apt install -y python3-pygame python3-paho-mqtt
```

### Executando

```bash
python3 eyes.py
```

Aperte **Esc** para sair. Para testar sem o ESP32, publique uma emoção de outro terminal:

```bash
mosquitto_pub -h localhost -t emocao -m love
mosquitto_pub -h localhost -t emocao -m furious
```

## Próximos passos

- Gerenciador de estados emocionais mais completo;
- Módulos de inteligência artificial (linguagem natural).
