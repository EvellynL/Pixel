"""Olhos animados estilo OLED para display 480x320 (Raspberry Pi).

Mostra a emocao "normal" o tempo todo. Quando o ESP32 publica "love" ou
"furious" no topico MQTT "emocao", troca para essa emocao por alguns
segundos e depois volta ao normal.
"""
import math
import queue
import random
import time

import paho.mqtt.client as mqtt
import pygame

W, H = 480, 320
FPS = 30

# MQTT (o broker Mosquitto roda no proprio Raspberry Pi)
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "emocao"

MOOD_DEFAULT = "normal"
MQTT_MOODS = ("love", "furious")  # emocoes aceitas vindas do ESP32
MOOD_DURATION = 8.0  # segundos mostrando a emocao recebida antes de voltar ao normal

BG_DEFAULT = (0, 0, 0)
FG_DEFAULT = (0, 220, 255)  # cor padrao dos olhos (ciano)
BLUSH_COLOR = (255, 90, 140)  # cor das bochechas (misturada com o fundo)

# Velocidades de transicao (maior = mais rapido). Valores baixos = suave,
# bom para o display SPI com poucos quadros por segundo.
SPEED_SHAPE = 5.0  # formato / posicao dos olhos
SPEED_COLOR = 2.5  # cor dos olhos, fundo, bochechas, balanco, pulsar
SLOW_KEYS = ("blush", "shake", "pulse")

BLINK_CLOSE = 12.0
BLINK_OPEN = 8.0
SHAKE_FREQ = 1.8  # balancos por segundo (super-irritado)
PULSE_FREQ = 0.9  # batidas por segundo (apaixonado)

# Valores padrao de cada humor (todos com o tamanho do olho neutro).
BASE = dict(
    w=130, h=150, r=30,
    tired=0.0, angry=0.0, happy=0.0,
    shake=0.0, blush=0.0, pulse=0.0,
)

# Cada humor so precisa listar o que muda em relacao ao BASE.
#   color = cor dos olhos, bg = cor do fundo, heart = olhos de coracao,
#   look = olha para os lados sozinho
MOODS = {
    "normal": dict(),
    "tired": dict(tired=0.45),
    "angry": dict(angry=0.42, color=(255, 30, 30)),
    "happy": dict(happy=0.55, r=40),
    "wide": dict(w=125, h=165, r=40),
    "furious": dict(  # super-irritado
        angry=0.5, shake=8.0, color=(210, 10, 10), bg=(200, 100, 0), look=False
    ),
    "love": dict(  # apaixonado
        heart=True, blush=1.0, pulse=1.0,
        color=(220, 20, 60), bg=(255, 160, 195), look=False,
    ),
}


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def heart_points(cx, cy, scale_x, scale_y, n=48):
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * scale_x, cy + (y - 2.5) * scale_y))
    return pts


class Eyes:
    def __init__(self):
        self.cur = dict(BASE, gap=50, x=0.0, y=0.0)
        self.tgt = dict(self.cur)
        self.color = list(FG_DEFAULT)
        self.color_tgt = list(FG_DEFAULT)
        self.bg = list(BG_DEFAULT)
        self.bg_tgt = list(BG_DEFAULT)
        self.name = "normal"
        self.heart = False
        self.pending_heart = None
        self.look = True
        self.blink = 0.0  # 0 = aberto, 1 = fechado
        self.blink_dir = 0
        self.closed_until = 0.0
        now = time.time()
        self.next_blink = now + 3
        self.next_look = now + 2

    def set_mood(self, name):
        spec = MOODS[name]
        self.name = name
        for key, default in BASE.items():
            self.tgt[key] = spec.get(key, default)
        self.color_tgt = list(spec.get("color", FG_DEFAULT))
        self.bg_tgt = list(spec.get("bg", BG_DEFAULT))
        self.look = spec.get("look", True)

        # Trocar entre olho normal e coracao: fecha os olhos, troca o
        # formato com eles fechados e reabre (evita uma troca brusca).
        want_heart = spec.get("heart", False)
        if want_heart != self.heart:
            self.pending_heart = want_heart
            self.blink_dir = 1
        else:
            self.pending_heart = None

    def update(self, dt):
        ks = min(1.0, dt * SPEED_SHAPE)
        kc = min(1.0, dt * SPEED_COLOR)
        for key in self.cur:
            self.cur[key] = lerp(self.cur[key], self.tgt[key], kc if key in SLOW_KEYS else ks)
        for i in range(3):
            self.color[i] = lerp(self.color[i], self.color_tgt[i], kc)
            self.bg[i] = lerp(self.bg[i], self.bg_tgt[i], kc)

        now = time.time()

        # piscar
        if self.blink_dir == 0 and now > self.next_blink:
            self.blink_dir = 1
        if self.blink_dir == 1:
            self.blink += dt * BLINK_CLOSE
            if self.blink >= 1:
                self.blink, self.blink_dir = 1.0, -1
                if self.pending_heart is not None:
                    self.heart = self.pending_heart
                    self.pending_heart = None
                    self.closed_until = now + 0.25
        elif self.blink_dir == -1 and now >= self.closed_until:
            self.blink -= dt * BLINK_OPEN
            if self.blink <= 0:
                self.blink, self.blink_dir = 0.0, 0
                self.next_blink = now + random.uniform(2, 6)

        # olhar para os lados
        if self.look:
            if now > self.next_look:
                self.tgt["x"] = random.choice([-50, -25, 0, 0, 25, 50])
                self.tgt["y"] = random.choice([-20, 0, 0, 15])
                self.next_look = now + random.uniform(1.5, 4)
        else:
            self.tgt["x"] = 0.0
            self.tgt["y"] = 0.0

    def draw(self, surf):
        c = self.cur
        bg = tuple(int(v) for v in self.bg)
        fg = tuple(int(v) for v in self.color)
        surf.fill(bg)

        now = time.time()
        w = c["w"]
        h = max(6.0, c["h"] * (1 - 0.92 * self.blink))
        cy = H / 2 + c["y"]
        shake = math.sin(now * 2 * math.pi * SHAKE_FREQ) * c["shake"]
        left = W / 2 - (2 * w + c["gap"]) / 2 + c["x"] + shake

        for i in (0, 1):
            x = left + i * (w + c["gap"])

            # bochechas (apaixonado)
            if c["blush"] > 0.02:
                side = -1 if i == 0 else 1
                cheek = mix(bg, BLUSH_COLOR, 0.7 * min(1.0, c["blush"]))
                ccx = x + w / 2 + side * 24
                pygame.draw.ellipse(surf, cheek, (ccx - 38, cy + 54 - 15, 76, 30))

            if self.heart:
                beat = 1 + 0.07 * c["pulse"] * math.sin(now * 2 * math.pi * PULSE_FREQ)
                s = (w / 32) * beat
                v = min(1.0, h / c["h"])
                pygame.draw.polygon(surf, fg, heart_points(x + w / 2, cy, s, s * v))
                continue

            rect = pygame.Rect(int(x), int(cy - h / 2), int(w), int(h))
            pygame.draw.rect(surf, fg, rect, border_radius=int(min(c["r"], h / 2)))

            # palpebras (tired = canto externo baixo, angry = canto interno baixo)
            outer = h * c["tired"]
            inner = h * c["angry"]
            if outer > 1 or inner > 1:
                d_left, d_right = (outer, inner) if i == 0 else (inner, outer)
                pygame.draw.polygon(
                    surf,
                    bg,
                    [
                        (rect.left - 1, rect.top - 1),
                        (rect.right + 1, rect.top - 1),
                        (rect.right + 1, rect.top + d_right),
                        (rect.left - 1, rect.top + d_left),
                    ],
                )

            # feliz: "morde" a parte de baixo com uma elipse da cor do fundo
            if c["happy"] > 0.02:
                cut = h * c["happy"]
                pygame.draw.ellipse(surf, bg, (rect.left - 6, rect.bottom - cut, rect.w + 12, h))


def start_mqtt(inbox):
    """Assina o topico de emocoes. As mensagens recebidas vao para a fila
    `inbox`, lida pelo loop principal (o paho roda em outra thread)."""
    try:  # paho-mqtt 2.x
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:  # paho-mqtt 1.x
        client = mqtt.Client()

    def on_connect(client, userdata, *args):
        print(f"MQTT conectado a {MQTT_HOST}:{MQTT_PORT}, assinando '{MQTT_TOPIC}'")
        client.subscribe(MQTT_TOPIC)  # (re)assina a cada conexao

    def on_message(client, userdata, msg):
        inbox.put(msg.payload.decode("utf-8", errors="ignore").strip().lower())

    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=10)
    # connect_async + loop_start: nao trava a animacao se o broker cair
    client.connect_async(MQTT_HOST, MQTT_PORT)
    client.loop_start()
    return client


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    eyes = Eyes()
    eyes.set_mood(MOOD_DEFAULT)

    inbox = queue.Queue()
    client = start_mqtt(inbox)
    back_to_default = None  # momento de voltar ao normal

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000, 0.1)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False

        while not inbox.empty():
            mood = inbox.get()
            if mood in MQTT_MOODS:
                print(f"Emocao recebida: {mood}")
                if mood != eyes.name:
                    eyes.set_mood(mood)
                back_to_default = time.time() + MOOD_DURATION  # renova o tempo
            else:
                print(f"Emocao ignorada: {mood!r}")

        if back_to_default is not None and time.time() > back_to_default:
            eyes.set_mood(MOOD_DEFAULT)
            back_to_default = None

        eyes.update(dt)
        eyes.draw(screen)
        pygame.display.flip()

    client.loop_stop()
    client.disconnect()
    pygame.quit()


if __name__ == "__main__":
    main()
