# 🖥️ PC: assistente de voz do Pixel

Programa em Python que roda no **PC**. Você fala no microfone do fone, a inteligência artificial entende e responde com voz. O processamento da fala fica no PC porque o Raspberry Pi tem hardware limitado.

> Por enquanto é só a conversa por voz. A integração com o Raspberry (expressões sincronizadas, status de conexão), o pomodoro e os lembretes vêm depois.

## Como funciona

```
🎤 fone → faster-whisper (fala → texto, no PC) → Gemini (resposta) → Piper (texto → fala, no PC) → 🔊 fone
```

| Etapa | Biblioteca | Onde roda |
|---|---|---|
| Fala → texto | [faster-whisper](https://github.com/SYSTRAN/faster-whisper), modelo `small` | No PC, sem internet |
| Resposta | [Gemini](https://ai.google.dev) (`gemini-flash-latest`) | Na nuvem (precisa de internet e de uma chave **gratuita**) |
| Texto → fala | [Piper](https://github.com/OHF-Voice/piper1-gpl), voz `pt_BR-faber-medium` | No PC, sem internet |

O Pixel lembra do que foi dito enquanto o programa estiver aberto.

## Instalação

Precisa do **Python 3.10 ou mais novo**. Dentro desta pasta (`programacao/pc`):

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

> No Linux, instale também o PortAudio: `sudo apt install libportaudio2`. No Windows e no macOS ele já vem com o `sounddevice`.

### Chave gratuita do Gemini

1. Entre em [aistudio.google.com/apikey](https://aistudio.google.com/apikey) com a sua conta Google.
2. Clique em **Create API key** e copie a chave. Não precisa cadastrar cartão.
3. Salve a chave na variável de ambiente `GEMINI_API_KEY`:

```bash
# Windows (PowerShell) - depois feche e abra o terminal de novo
setx GEMINI_API_KEY "sua-chave-aqui"
# Linux / macOS
export GEMINI_API_KEY="sua-chave-aqui"
```

> **Usando o terminal do VS Code?** Depois do `setx`, feche e abra o **VS Code inteiro**, não só o terminal. Para conferir, rode `echo $env:GEMINI_API_KEY`: a chave deve aparecer. Para testar na hora, sem reiniciar, use `$env:GEMINI_API_KEY = "sua-chave-aqui"`, que vale só para aquele terminal.

> O plano gratuito tem um limite de pedidos por minuto e por dia. Para uma conversa com o Pixel ele costuma sobrar; se passar, o programa avisa e é só esperar um pouco. No plano gratuito, o Google pode usar as conversas para melhorar os produtos dele, então evite falar informações pessoais sensíveis.

## Usando

```bash
python assistente_voz.py
```

1. Aperte **Enter** para começar a falar.
2. Fale e aperte **Enter** de novo para terminar.
3. O Pixel mostra o que entendeu, escreve a resposta e fala.

Digite `sair` e Enter para encerrar.

Na **primeira execução**, o programa baixa o modelo do Whisper (~500 MB) e a voz do Piper (~60 MB). Depois disso, essas duas etapas funcionam sem internet. A voz fica na pasta `modelos/`, que não vai para o Git.

### Usando o microfone e o som do fone

Se o programa não pegar o fone sozinho, veja o número de cada dispositivo:

```bash
python assistente_voz.py --listar-dispositivos
```

E escolha o microfone (`--mic`) e a saída de som (`--saida`) pelo número:

```bash
python assistente_voz.py --mic 1 --saida 4
```

## Ajustes

No topo de `assistente_voz.py`:

| Configuração | O que muda |
|---|---|
| `WHISPER_MODELO` | `base` é mais rápido; `medium` entende melhor, mas é mais lento |
| `VOZ_PIPER` | Outra voz em português, ex.: `pt_BR-cadu-medium` |
| `SYSTEM` | A personalidade do Pixel e como ele responde |
| `MODELO_GEMINI` | O modelo do Gemini. `gemini-flash-latest` sempre aponta para o Flash mais recente |
| `MODELO_RESERVA` | Modelo usado quando o principal continua fora do ar (ex.: erro 503, servidor sobrecarregado). A conversa continua com o mesmo histórico |

## Placa de vídeo NVIDIA (opcional)

Se o PC tiver uma GPU NVIDIA, o programa tenta usá-la para transcrever mais rápido. Para isso funcionar, a GPU precisa das bibliotecas **cuBLAS e cuDNN 9 para CUDA 12**. Sem elas, aparece o aviso `GPU indisponível (... cublas64_12.dll ...)` e o programa usa o processador sozinho. Ele continua funcionando, só um pouco mais devagar.

Para ativar a GPU no Windows, siga a seção de GPU do [README do faster-whisper](https://github.com/SYSTRAN/faster-whisper#gpu): basta baixar as DLLs indicadas lá e colocá-las numa pasta que esteja no `PATH`.
