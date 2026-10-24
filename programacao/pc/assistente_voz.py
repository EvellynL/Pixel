"""Assistente de voz do Pixel (roda no PC).

Aperte Enter para começar a falar e Enter de novo para terminar. A fala é
transcrita no próprio PC (faster-whisper), enviada ao Gemini, e a resposta é
falada em voz alta (Piper).

Uso:
    python assistente_voz.py                     # microfone e saída padrão
    python assistente_voz.py --listar-dispositivos
    python assistente_voz.py --mic 3 --saida 5   # escolhe o fone pelo número
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from google import genai
from google.genai import errors, types
from piper import PiperVoice
from piper.download_voices import download_voice

# ---------- Configuração ----------
# Apelido do Google que sempre aponta para o modelo Flash mais recente
# (rápido e disponível no plano gratuito)
MODELO_GEMINI = "gemini-flash-latest"

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


def carregar_whisper():
    """Usa a GPU NVIDIA se ela funcionar; senão, usa o processador.

    O teste é feito já na carga porque, sem as bibliotecas CUDA (cuBLAS/cuDNN),
    o erro só aparece na primeira transcrição."""
    try:
        whisper = WhisperModel(WHISPER_MODELO, device="auto", compute_type="int8")
        teste = np.zeros(WHISPER_TAXA, dtype=np.float32)  # 1 s de silêncio
        list(whisper.transcribe(teste, language="pt")[0])
        return whisper
    except RuntimeError as e:
        print(f"⚠️  GPU indisponível ({e}). Usando o processador.")
        return WhisperModel(WHISPER_MODELO, device="cpu", compute_type="int8")


def transcrever(whisper, audio):
    # vad_filter remove os trechos de silêncio antes de transcrever
    segmentos, _ = whisper.transcribe(audio, language="pt", vad_filter=True)
    return " ".join(s.text.strip() for s in segmentos).strip()


def perguntar(chat, texto):
    """Envia a fala ao Gemini e devolve o texto da resposta (ou None se falhar).
    O objeto `chat` guarda o histórico da conversa sozinho."""
    try:
        resp = chat.send_message(texto)
    except errors.ClientError as e:
        if e.code == 429:
            print("❌ Limite do plano gratuito atingido. Espere um pouco e tente de novo.")
        elif e.code in (400, 401, 403):
            print(f"❌ Erro da API ({e.code}). Confira a chave em GEMINI_API_KEY. Detalhe: {e.message}")
        else:
            print(f"❌ Erro da API ({e.code}): {e.message}")
        return None
    except errors.ServerError as e:
        print(f"❌ O servidor do Gemini falhou ({e.code}). Tente de novo.")
        return None
    except Exception as e:  # sem internet, tempo esgotado etc.
        print(f"❌ Não consegui falar com o Gemini ({type(e).__name__}). Verifique a internet.")
        return None

    if not resp.text:  # resposta bloqueada pelos filtros de segurança
        return "Desculpe, não consigo responder isso."
    return resp.text.strip()


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

    # Confere a chave antes de carregar os modelos, que demoram
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        print(
            "❌ Chave do Gemini não encontrada na variável GEMINI_API_KEY.\n"
            "   Para usar só neste terminal (PowerShell):  $env:GEMINI_API_KEY = \"sua-chave\"\n"
            "   Para salvar de vez:  setx GEMINI_API_KEY \"sua-chave\"  e depois feche e abra\n"
            "   o VS Code (ou o terminal) de novo."
        )
        sys.exit(1)

    print("Carregando modelos (pode demorar na primeira vez)...")
    whisper = carregar_whisper()
    voz = carregar_voz()
    client = genai.Client()  # lê a chave da variável GEMINI_API_KEY
    chat = client.chats.create(
        model=MODELO_GEMINI,
        config=types.GenerateContentConfig(system_instruction=SYSTEM),
    )

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

        resposta = perguntar(chat, texto)
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
