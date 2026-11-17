[Español](README.md) | [English](README.en.md) | **Português**

# Clipper Live

Uma skill grátis pro Claude Code que **assiste lives AO VIVO** e vai separando cortes verticais enquanto o
streamer joga. Feita pro lançamento do GTA 6, mas funciona com qualquer live.

Você manda o link da live (Twitch, Kick ou YouTube), deixa o computador ligado, e a cada 30 minutos recebe:

- cortes verticais (1080×1920): câmera do streamer em cima, jogo embaixo
- título de gancho e legenda palavra por palavra
- um `.txt` com a legenda do post, as hashtags e o crédito da live

Você aprova ou recusa cada corte. O aprovado vai pra uma pasta; o recusado é apagado.

O sistema vem em **espanhol** e também funciona em **inglês** e **português**.

📖 **[Guia passo a passo](docs/GUIA.pt.md)**: instalação, uso, aprovação dos cortes e solução de problemas.

## Como funciona

```
 live ──► Streamlink grava em pedaços de 5 min ──► Whisper escreve a fala + mede gritos
   └────► leitor de chat (Twitch / YouTube / Kick) ──► marca onde a galera agitou
                              │
          a cada 30 min: bloco de texto com [ALTO +12dB] [CHAT 3x] [RISADA/HYPE]
                              │
                Claude lê, dá nota e escolhe os momentos
                              │
     corte montado (câmera + jogo + título + legenda) ──► fila de aprovação
                              │
     limpeza: apaga a gravação que já virou corte, respeitando os GB que você reservou
```

- **Gravação ao vivo com o [Streamlink](https://github.com/streamlink/streamlink)**: pula os anúncios da Twitch,
  reconecta se a live cair e espera a live começar (até 8 h).
- **Escuta no seu computador** (faster-whisper). Usa a placa de vídeo NVIDIA se tiver.
- **Chat ao vivo**: Twitch (sem conta), YouTube e Kick. Se uma plataforma bloquear o chat, segue com a fala e o
  volume.
- **Atualização automática e segura**: Streamlink, yt-dlp, Whisper e ffmpeg se atualizam sozinhos a cada 12 h. Se
  uma versão nova quebrar algo, ele volta pra anterior.
- Também corta vídeos que já acabaram (VOD): é só mandar o link.

## Instalação

Precisa do **Claude Code**: o app em https://claude.com/download, na aba **Code**. Também roda de graça com o
Ollama, mas as escolhas ficam piores.

Cole no Claude Code:

> instala o clipper live em português: https://github.com/nexcorsair-create/Clipper-Live

Ou rode direto (serve também pra atualizar):

- **Windows (PowerShell):** `$env:CLIPPER_LANG="pt"; irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex`
- **Mac/Linux:** `curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | CLIPPER_LANG=pt bash`

Ele confere o Python, instala o Streamlink, o yt-dlp, o ffmpeg e o Whisper, testa tudo e avisa quando estiver
pronto. Depois o Claude pergunta **em qual pasta guardar** e **quantos GB reservar**. Recomendo 50 GB: uma hora
de live em 720p ocupa uns 2 GB até ser analisada.

### Trocar o idioma

Diga ao Claude "muda o idioma pra português", ou rode `clip.py configurar --lingua pt` (`es`, `en`, `pt`).

## Usando

- "vigia essa live: https://twitch.tv/fulano"
- "acha as maiores lives de GTA 6 agora"
- "aprova o 3 e o 5" / "recusa o 4"
- "como tá a live?" / "para de vigiar"

Os cortes ficam em `SUA-PASTA/cortes/pendientes` e, depois de aprovados, em `SUA-PASTA/cortes/aprobados`.

**Dica:** quando o Claude pedir permissão pra rodar o `clip.py`, escolha "sempre permitir". Assim ele trabalha
sozinho a live inteira.

## Precisa ter

- Windows, Mac ou Linux
- Python 3.10 ou mais novo (o instalador resolve no Windows)
- uns 3 GB pro programa e os modelos, mais os GB reservados pras gravações
- internet estável (grava a live enquanto você assiste)

## Limites

- Live só pra membros ou com trava de idade não grava (precisa de login).
- O sistema decide pela fala, pelo volume e pelo chat; ele não "vê" a imagem. Um momento só visual entra se o chat
  explodir.
- O corte sai de 30 a 40 min depois do momento (é o ciclo de análise). Dá pra mudar: "analisa a cada 20 min".
- Ele não posta sozinho: você posta os aprovados.

## Respeite os streamers

Corte só quem libera cortes e mantenha o crédito que vem no `.txt` de cada corte.

## Créditos

Ideia do fluxo (escutar a live, a IA dar nota por blocos, câmera em cima e jogo embaixo) inspirada no
[skill-clips](https://github.com/davixavier-coder/skill-clips) de Davi Xavier. Gravação ao vivo pelo
[Streamlink](https://github.com/streamlink/streamlink); downloads pelo [yt-dlp](https://github.com/yt-dlp/yt-dlp);
escuta pelo [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
