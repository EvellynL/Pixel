"""Assistente de voz do Pixel (roda no PC).

Aperte Enter para começar a falar e Enter de novo para terminar. A fala é
transcrita no próprio PC (faster-whisper), enviada ao Claude, e a resposta é
falada em voz alta (Piper).

Uso:
    python assistente_voz.py                     # microfone e saída padrão
    python assistente_voz.py --listar-dispositivos
    python assistente_voz.py --mic 3 --saida 5   # escolhe o fone pelo número
"""
import argparse
import sys
from pathlib import Path

import anthropic
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from piper import PiperVoice
from piper.download_voices import download_voice

# ---------- Configuração ----------
MODELO_CLAUDE = "claude-opus-5-5"
ESFORCO = "low"  # "low" deixa a resposta mais rápida, bom para conversa

WHISPER_MODELO = "small"  # tiny, base, small, medium... (maior = entende melhor, mais lento)
WHISPER_TAXA = 16000  # o Whisper trabalha com áudio a 16 kHz

VOZ_PIPER = "pt_BR-faber-medium"
PASTA_MODELOS = Path(__file__).parent / "modelos"

SYSTEM = (
    "Você é o Pixel, um pequeno robô assistente de mesa, simpático e curioso. "
    "Suas respostas serão faladas em voz alta: responda sempre em português do Brasil, "
    "em no máximo 2 ou 3 frases curtas, sem listas, emojis, markdown ou símbolos que "
    "não possam ser lidos em voz alta."
)


def carregar_voz():
    """Carrega a voz do Piper, baixando-a na primeira execução."""
    PASTA_MODELOS.mkdir(exist_ok=True)
    caminho = PASTA_MODELOS / f"{VOZ_PIPER}.onnx"
    if not caminho.exists():
        print(f"Baixando a voz {VOZ_PIPER} (só na primeira vez)...")
        download_voice(VOZ_PIPER, PASTA_MODELOS)
    return PiperVoice.load(caminho)


def gravar(mic):
    """Grava do microfone até o usuário apertar Enter. Retorna áudio a 16 kHz."""
    taxa = int(sd.query_devices(mic, "input")["default_samplerate"])
    blocos = []

    def callback(indata, frames, tempo, status):
        blocos.append(indata[:, 0].copy())

    # Grava na taxa nativa do microfone: muitos fones não aceitam 16 kHz direto
    with sd.InputStream(device=mic, channels=1, samplerate=taxa, dtype="float32", callback=callback):
        input("🎙️  Gravando... aperte Enter para terminar.")

    if not blocos:
        return np.zeros(0, dtype=np.float32)
    audio = np.concatenate(blocos)
    return reamostrar(audio, taxa, WHISPER_TAXA)


def reamostrar(audio, taxa_origem, taxa_destino):
    if taxa_origem == taxa_destino or len(audio) == 0:
        return audio
    duracao = len(audio) / taxa_origem
    n_destino = int(duracao * taxa_destino)
    x_origem = np.linspace(0, duracao, num=len(audio), endpoint=False)
    x_destino = np.linspace(0, duracao, num=n_destino, endpoint=False)
    return np.interp(x_destino, x_origem, audio).astype(np.float32)


def transcrever(whisper, audio):
    # vad_filter remove os trechos de silêncio antes de transcrever
    segmentos, _ = whisper.transcribe(audio, language="pt", vad_filter=True)
    return " ".join(s.text.strip() for s in segmentos).strip()


def perguntar(client, historico, texto):
    """Envia a fala ao Claude e devolve o texto da resposta (ou None se falhar)."""
    historico.append({"role": "user", "content": texto})
    try:
        resp = client.beta.messages.create(
            model=MODELO_CLAUDE,
            max_tokens=4096,
            system=SYSTEM,
            messages=historico,
            output_config={"effort": ESFORCO},
            # Se o modelo recusar o pedido, outro modelo tenta responder
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        historico.pop()
        print("❌ Chave da API inválida ou ausente. Configure a variável ANTHROPIC_API_KEY.")
        return None
    except anthropic.RateLimitError:
        historico.pop()
        print("❌ Limite de uso da API atingido. Tente de novo em alguns segundos.")
        return None
    except anthropic.APIStatusError as e:
        historico.pop()
        print(f"❌ Erro da API ({e.status_code}): {e.message}")
        return None
    except anthropic.APIConnectionError:
        historico.pop()
        print("❌ Sem conexão com a API. Verifique a internet.")
        return None

    if resp.stop_reason == "refusal":
        historico.pop()
        return "Desculpe, não posso ajudar com isso."

    # Guarda a resposta completa no histórico para o Pixel lembrar da conversa
    historico.append({"role": "assistant", "content": resp.content})
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def falar(voz, texto, saida):
    pedacos = list(voz.synthesize(texto))
    if not pedacos:
        return
    audio = np.concatenate([p.audio_float_array for p in pedacos])
    sd.play(audio, pedacos[0].sample_rate, device=saida)
    sd.wait()


def main():
    parser = argparse.ArgumentParser(description="Assistente de voz do Pixel")
    parser.add_argument("--listar-dispositivos", action="store_true",
                        help="mostra os microfones e saídas de áudio e sai")
    parser.add_argument("--mic", type=int, help="número do microfone (veja --listar-dispositivos)")
    parser.add_argument("--saida", type=int, help="número da saída de áudio (veja --listar-dispositivos)")
    args = parser.parse_args()

    if args.listar_dispositivos:
        print(sd.query_devices())
        return

    print("Carregando modelos (pode demorar na primeira vez)...")
    whisper = WhisperModel(WHISPER_MODELO, device="auto", compute_type="int8")
    voz = carregar_voz()
    client = anthropic.Anthropic()  # lê a chave da variável ANTHROPIC_API_KEY
    historico = []

    print("\n🤖 Pixel pronto! Aperte Enter para falar, ou digite 'sair' e Enter para encerrar.\n")
    while True:
        if input("> ").strip().lower() in ("sair", "q"):
            break

        audio = gravar(args.mic)
        if len(audio) < WHISPER_TAXA * 0.3:  # menos de 0,3 s: nada para ouvir
            print("(não ouvi nada)")
            continue

        texto = transcrever(whisper, audio)
        if not texto:
            print("(não entendi, tente de novo)")
            continue
        print(f"🧑 Você: {texto}")

        resposta = perguntar(client, historico, texto)
        if not resposta:
            continue
        print(f"🤖 Pixel: {resposta}\n")
        falar(voz, resposta, args.saida)

    print("Até logo!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
