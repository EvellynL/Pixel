# 🤖 Pixel — Robô Assistente de Mesa

> Um pequeno robô de mesa expressivo, que reage ao toque e ao movimento e conversa em linguagem natural com a ajuda de inteligência artificial.

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![Plataforma](https://img.shields.io/badge/plataforma-Raspberry%20Pi%204%20%7C%20ESP32-blue)
![Protocolo](https://img.shields.io/badge/comunica%C3%A7%C3%A3o-MQTT-660066)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

---

## 📑 Sumário

- [Sobre o projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura do sistema](#-arquitetura-do-sistema)
- [Hardware](#-hardware)
- [Comunicação via MQTT](#-comunicação-via-mqtt)
- [Sistema de emoções](#-sistema-de-emoções)
- [Inteligência artificial](#-inteligência-artificial)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Primeiros passos](#-primeiros-passos)
- [Roadmap](#-roadmap)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 💡 Sobre o projeto

O **Pixel** é um robô assistente de mesa pensado para ser um companheiro interativo: ele mostra expressões faciais em um display, percebe quando é tocado ou movimentado e responde com emoções correspondentes. A proposta é evoluir para um assistente capaz de **entender e responder em linguagem natural**, usando modelos de inteligência artificial.

O sistema é dividido em dois "cérebros":

| Módulo | Responsabilidade |
|---|---|
| **Raspberry Pi 4** | Cérebro principal: controla o display, renderiza as expressões, roda o broker/cliente MQTT e os módulos de IA. |
| **ESP32** | Sistema sensorial: lê os sensores de toque capacitivo e o giroscópio, interpreta os dados e publica a emoção correspondente via MQTT. |

---

## ✨ Funcionalidades

- 😊 **Expressões faciais animadas** exibidas em um display MHS controlado pelo Raspberry Pi 4.
- 👆 **Percepção de toque** por sensores capacitivos (ex.: carinho na cabeça, toque rápido, toque prolongado).
- 🔄 **Percepção de movimento** com giroscópio (ex.: ser levantado, inclinado, sacudido ou virado).
- 📡 **Comunicação sem fio** entre ESP32 e Raspberry Pi via protocolo **MQTT** sobre Wi-Fi.
- 🧠 **Inteligência artificial** com foco em processamento e treinamento com **linguagem natural** *(planejado)*.
- 🗣️ **Interação por voz** *(planejado)*.

---

## 🏗️ Arquitetura do sistema

```
┌──────────────────────────────┐                    ┌──────────────────────────────────┐
│            ESP32             │                    │          Raspberry Pi 4          │
│                              │                    │                                  │
│  ┌────────────────────────┐  │                    │  ┌────────────────────────────┐  │
│  │ Sensores capacitivos   │──┤                    │  │ Broker MQTT (Mosquitto)    │  │
│  └────────────────────────┘  │                    │  └─────────────┬──────────────┘  │
│  ┌────────────────────────┐  │   MQTT (Wi-Fi)     │                │                 │
│  │ Giroscópio / IMU       │──┤ ─────────────────▶ │  ┌─────────────▼──────────────┐  │
│  └────────────────────────┘  │  emocao            │  │ Gerenciador de emoções     │  │
│  ┌────────────────────────┐  │  pixel/sensores/…  │  └─────────────┬──────────────┘  │
│  │ Lógica sensor → emoção │  │                    │                │                 │
│  └────────────────────────┘  │                    │  ┌─────────────▼──────────────┐  │
└──────────────────────────────┘                    │  │ Renderização de expressões │──┼──▶ Display MHS
                                                    │  └────────────────────────────┘  │
                                                    │  ┌────────────────────────────┐  │
                                                    │  │ Módulo de IA (linguagem    │  │
                                                    │  │ natural) — planejado       │  │
                                                    │  └────────────────────────────┘  │
                                                    └──────────────────────────────────┘
```

**Fluxo de funcionamento:**

1. O **ESP32** lê continuamente os sensores capacitivos e o giroscópio.
2. Os dados brutos são filtrados e interpretados para identificar um evento (ex.: "carinho", "sacudida").
3. O evento é convertido em uma **emoção** (ex.: `feliz`, `tonto`) e publicado em um tópico MQTT.
4. O **Raspberry Pi 4** recebe a mensagem, atualiza o estado emocional do robô e exibe a expressão correspondente no **display MHS**.
5. *(Futuro)* O módulo de IA combina o estado emocional com as interações em linguagem natural para gerar respostas mais ricas.

---

## 🔧 Hardware

### Componentes principais

| Componente | Função | Observações |
|---|---|---|
| Raspberry Pi 4 | Processamento principal, display, MQTT e IA | Recomendado 4 GB de RAM ou mais para os módulos de IA |
| Display MHS | Exibição das expressões faciais | Display LCD da linha MHS (SPI) conectado ao GPIO do Raspberry Pi |
| ESP32 | Leitura de sensores e envio das emoções | Wi-Fi integrado e pinos de toque capacitivo nativos |
| Sensores de toque capacitivo | Detecção de toque | Podem ser os pinos *touch* nativos do ESP32 ou módulos dedicados (ex.: TTP223, MPR121) |
| Giroscópio / IMU | Detecção de movimento e orientação | Ex.: MPU6050 (I²C) |
| Fonte de alimentação | Alimentação do sistema | 5 V / 3 A (USB-C) para o Raspberry Pi 4 |

> ⚠️ A lista de componentes ainda pode mudar conforme o projeto evolui. Modelos específicos de sensores e o tamanho do display serão definidos e documentados na pasta [`eletronica/`](eletronica/).

### Estrutura mecânica

A estrutura mecânica do Pixel **ainda está sendo definida**. Os estudos, esboços e arquivos de modelagem 3D ficarão na pasta [`mecanica/`](mecanica/). Pontos a considerar:

- Carcaça compacta, adequada para ficar sobre uma mesa;
- Encaixe frontal para o display (o "rosto" do robô);
- Posicionamento dos sensores capacitivos em áreas de toque naturais (ex.: topo da cabeça, laterais);
- Fixação firme do giroscópio para leituras confiáveis;
- Ventilação para o Raspberry Pi 4;
- Acesso fácil a portas USB, alimentação e cartão microSD.

---

## 📡 Comunicação via MQTT

A comunicação entre o ESP32 e o Raspberry Pi 4 é feita pelo protocolo **MQTT**, leve e ideal para IoT. A sugestão é rodar o broker **Mosquitto** no próprio Raspberry Pi.

### Tópicos propostos

| Tópico | Publicador | Assinante | Descrição |
|---|---|---|---|
| `emocao` | ESP32 | Raspberry Pi | Emoção calculada a partir dos sensores (texto puro, ex.: `love`) |
| `pixel/sensores/toque` | ESP32 | Raspberry Pi | Eventos de toque (para depuração e IA) |
| `pixel/sensores/giroscopio` | ESP32 | Raspberry Pi | Leituras ou eventos de movimento |
| `pixel/status` | ESP32 / RPi | Ambos | Estado de conexão (*online*/*offline*) |

### Mensagens do tópico `emocao`

O ESP32 publica o nome da emoção como texto puro. Já implementado em [`programacao/esp32/`](programacao/esp32/):

| Estímulo | Mensagem |
|---|---|
| 3 toques no sensor capacitivo | `love` |
| Mais de 10 toques seguidos | `angry` |

> Os nomes dos tópicos e o formato das mensagens são uma proposta inicial e podem ser ajustados durante o desenvolvimento.

---

## 😄 Sistema de emoções

Mapeamento inicial entre os estímulos captados pelo ESP32 e as emoções exibidas:

| Estímulo | Sensor | Emoção |
|---|---|---|
| Carinho / toque prolongado | Capacitivo | 😊 `feliz` |
| Toque rápido | Capacitivo | 😮 `surpreso` |
| Toques repetidos e insistentes | Capacitivo | 😠 `irritado` |
| Ser levantado | Giroscópio | 🤩 `animado` |
| Ser sacudido | Giroscópio | 😵 `tonto` |
| Ser virado / inclinado demais | Giroscópio | 😨 `assustado` |
| Sem interação por muito tempo | — | 😴 `sonolento` |
| Estado padrão | — | 🙂 `neutro` |

---

## 🧠 Inteligência artificial

Um dos objetivos centrais do Pixel é incorporar **inteligência artificial**, principalmente voltada a **linguagem natural**. Possíveis frentes de trabalho:

- **Conversação em linguagem natural:** entender comandos e perguntas do usuário e responder de forma coerente com a "personalidade" do robô.
- **Treinamento / ajuste fino com linguagem natural:** ensinar novos comportamentos e respostas ao Pixel por meio de exemplos em texto.
- **Reconhecimento de fala (STT) e síntese de voz (TTS):** permitir interação por voz.
- **Emoções contextuais:** usar a IA para escolher expressões a partir do conteúdo da conversa, combinando com os dados dos sensores.
- **Execução local e/ou em nuvem:** avaliar modelos leves que rodem no Raspberry Pi 4 e APIs em nuvem para tarefas mais pesadas.

> As tecnologias e modelos de IA ainda serão escolhidos. As decisões e experimentos serão documentados em [`programacao/`](programacao/).

---

## 📂 Estrutura do repositório

```
Pixel/
├── programacao/
│   ├── raspberry/ # Código do Raspberry Pi 4 (expressões, MQTT, IA)
│   └── esp32/     # Firmware do ESP32 (sensores e MQTT)
├── eletronica/    # Esquemáticos, pinagens, lista de componentes e diagramas de ligação
├── mecanica/      # Modelos 3D, desenhos técnicos e estudos da estrutura do robô
├── LICENSE
└── README.md
```

---

## 🚀 Primeiros passos

> Esta seção será completada à medida que o código for sendo desenvolvido.

### Pré-requisitos

- Raspberry Pi 4 com **Raspberry Pi OS** instalado;
- Driver do display MHS configurado no Raspberry Pi;
- **Python 3** no Raspberry Pi;
- **Arduino IDE** ou **PlatformIO** para programar o ESP32;
- Broker MQTT (ex.: **Mosquitto**).

### Instalando o broker MQTT no Raspberry Pi

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```

### Testando a comunicação

Em um terminal, assine o tópico de emoções:

```bash
mosquitto_sub -h localhost -t "emocao"
```

Em outro, publique uma mensagem de teste:

```bash
mosquitto_pub -h localhost -t "emocao" -m "love"
```

---

## 🗺️ Roadmap

- [x] Criação do repositório e estrutura inicial
- [ ] Definição final dos componentes eletrônicos
- [ ] Configuração do display MHS no Raspberry Pi 4
- [ ] Desenho e animação das expressões faciais
- [ ] Firmware do ESP32 para leitura dos sensores capacitivos
- [ ] Leitura e interpretação dos dados do giroscópio
- [ ] Comunicação ESP32 ↔ Raspberry Pi via MQTT
- [ ] Gerenciador de emoções no Raspberry Pi
- [ ] Definição e modelagem da estrutura mecânica
- [ ] Integração de IA com linguagem natural
- [ ] Interação por voz
- [ ] Montagem e testes do protótipo completo

---

## 🤝 Contribuindo

Sugestões e contribuições são bem-vindas! Para contribuir:

1. Faça um *fork* do projeto;
2. Crie uma *branch* para sua alteração (`git checkout -b minha-feature`);
3. Faça *commit* das mudanças (`git commit -m "Adiciona minha feature"`);
4. Envie para o seu *fork* (`git push origin minha-feature`);
5. Abra um *Pull Request*.

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">Feito com 💙 por <strong>Evellyn Lindoso</strong></p>
