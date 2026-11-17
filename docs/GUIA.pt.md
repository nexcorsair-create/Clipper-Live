[Español](GUIA.md) | [English](GUIDE.en.md) | **Português**

# Clipper Live — Guia passo a passo

Este guia explica, sem termos técnicos, como instalar o Clipper Live e usar ele pra tirar cortes de lives enquanto
elas acontecem. Não precisa saber programar: você conversa com o Claude e ele cuida do resto.

---

## 1. O que o Clipper Live faz

O Clipper Live assiste uma live da Twitch, da Kick ou do YouTube **enquanto ela está ao vivo** e, a cada 30 minutos,
te entrega os melhores momentos já cortados em vídeo vertical, prontos pro TikTok, Reels ou Shorts.

Cada corte vem com:

- a **câmera do streamer em cima** e o **jogo embaixo** (formato 1080×1920)
- um **título de gancho** escrito no vídeo
- **legenda palavra por palavra**
- um arquivo `.txt` com a **legenda do post**, as **hashtags** e o **crédito** da live

Você só **aprova** ou **recusa** cada corte. O aprovado fica guardado; o recusado é apagado.

### Como ele decide o que é um bom momento

1. **Grava** a live em pedaços de 5 minutos.
2. **Escuta** tudo que o streamer fala e transforma em texto, no seu próprio computador.
3. **Mede os gritos**: marca quando o streamer falou muito mais alto que o normal.
4. **Lê o chat**: marca quando a galera começou a escrever muito mais rápido (ou mandar "KKKK", "CLIPA"…).
5. A cada 30 minutos, **o Claude lê tudo isso**, dá uma nota de 0 a 100 pra cada momento e escolhe os melhores.
6. O sistema **monta os cortes** e coloca na fila pra você aprovar.

---

## 2. O que você precisa

| Precisa | Detalhe |
|---|---|
| Computador | Windows, Mac ou Linux. Com 16 GB de RAM roda tranquilo; com placa NVIDIA, melhor ainda. |
| Claude Code | O app do Claude (https://claude.com/download), aba **Code**. Plano Pro ou maior. |
| Espaço em disco | Uns **3 GB** pro programa + o espaço que você reservar pras gravações (recomendado **50 GB**). |
| Internet | Estável. O sistema grava a live enquanto você assiste. |
| Python | 3.10 ou mais novo. No Windows o instalador coloca sozinho. No Mac, o guia diz o que fazer. |

> **E de graça?** Também roda com o Ollama (IA local, sem pagar), mas as escolhas de momentos ficam piores e
> precisa de um computador forte (16 GB de RAM ou mais).

---

## 3. Instalação (uma vez só)

### Passo 1 — Abra o Claude Code

Abra o app do Claude, entre na aba **Code** e escolha uma pasta qualquer pra trabalhar (por exemplo, uma pasta
nova chamada `cortes`).

### Passo 2 — Peça a instalação

Escreva no chat:

> instala o clipper live em português: https://github.com/nexcorsair-create/Clipper-Live

O Claude roda o instalador. Leva de 5 a 15 minutos na primeira vez, porque ele baixa:

- **Streamlink** (grava a live)
- **yt-dlp** (baixa vídeos e o chat do YouTube)
- **ffmpeg** (monta os vídeos)
- **Whisper** (transforma a fala em texto)
- o detector de rosto (acha a câmera do streamer)

No final aparece **TUDO INSTALADO**.

> **Se faltar o Python:** no Windows o instalador instala sozinho e pede pra fechar e abrir o app do Claude; depois
> peça a instalação de novo. No Mac abre o site do Python: clique em **Download Python**, instale e peça a
> instalação de novo.

> **Instalação manual** (se preferir não pedir pro Claude), no PowerShell do Windows:
> `$env:CLIPPER_LANG="pt"; irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex`
> No Mac/Linux, no Terminal:
> `curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | CLIPPER_LANG=pt bash`

### Passo 3 — Escolha a pasta e o espaço

O Claude vai fazer duas perguntas:

1. **Em qual pasta guardo as gravações e os cortes?**
   O normal é `C:\Users\SEU-USUARIO\clipper-live` (Windows) ou `~/clipper-live` (Mac). Se tiver um HD externo
   com espaço, melhor ainda.
2. **Quantos GB posso usar?**
   Cada hora de live em 720p ocupa uns 2 GB enquanto não é analisada. A limpeza apaga sozinha o que já virou
   corte. **Recomendado: 50 GB** (mínimo 15).

Pronto: já dá pra vigiar lives.

### Passo 4 — Permissões (importante)

Na primeira vez que o Claude rodar o programa, o app vai perguntar se você permite. Escolha **"sempre permitir"**
pro `clip.py`. Assim o Claude trabalha sozinho por horas sem pedir confirmação toda hora.

---

## 4. Vigiando uma live

### Passo 1 — Mande o link

Escreva no Claude:

> vigia essa live: https://www.twitch.tv/NOME-DO-CANAL

Funcionam links da **Twitch** (`twitch.tv/canal`), da **Kick** (`kick.com/canal`) e do **YouTube** (o link da
live ou `youtube.com/@canal/live`).

Não sabe quem vigiar? Peça:

> acha as maiores lives de GTA 6 agora

O Claude mostra uma lista com quantas pessoas estão assistindo cada uma, e você escolhe.

### Passo 2 — Deixe o computador ligado

Daqui pra frente é tudo automático:

- Se a live **ainda não começou**, o sistema espera (até 8 horas).
- Se a live **cair**, ele reconecta sozinho.
- Depois de **20 minutos sem sinal**, ele considera que a live acabou.
- O gravador continua rodando mesmo se você fechar a janela do terminal.

**Não desligue o computador nem deixe ele suspender** enquanto vigia.

### Passo 3 — Receba e aprove os cortes

A cada 30 minutos de live, o Claude mostra os cortes novos, por exemplo:

```
#3  nota 88  [01:12:03–01:12:41]  ELE NÃO ACREDITOU NO TAMANHO DO MAPA
     grita ao ver o mapa inteiro; o chat explodiu; fecha sozinho
     C:\Users\...\clipper-live\cortes\pendientes\003_canal.mp4
```

Abra o vídeo, assista e responda:

> aprova o 3 e o 5

> recusa o 4

- **Aprovado** → vai pra `cortes/aprobados/`.
- **Recusado** → é apagado na hora.
- Se você não responder, o corte fica esperando em `cortes/pendientes/` e o Claude continua trabalhando.

### Passo 4 — Poste

Na pasta `cortes/aprobados/NOME-DA-LIVE/` cada corte tem o `.mp4` e o `.txt`. Copie o texto do `.txt` como
legenda do post: ele já traz as hashtags e o crédito pro streamer.

### Passo 5 — Termine

Quando a live acaba, o Claude faz um resumo (quantos cortes saíram, quantos você aprovou e onde estão). Se quiser
parar antes:

> para de vigiar

---

## 5. Frases úteis

| Você quer… | Escreva |
|---|---|
| Ver como está tudo | "como tá a live?" |
| Ver os cortes esperando aprovação | "quais cortes estão pendentes?" |
| Vigiar várias lives ao mesmo tempo | "vigia essas lives: LINK1 LINK2" |
| Análise mais frequente | "analisa a cada 20 minutos" |
| Ser mais exigente | "só cortes com nota 80 ou mais" |
| Mais cortes por bloco | "até 5 cortes por bloco" |
| Vídeo com mais qualidade | "grava em 1080p" (ocupa mais espaço) |
| Trocar o idioma | "muda o idioma pra espanhol" / "…pra inglês" |
| Forçar a atualização | "atualiza o clipper" |
| Cortar um vídeo que já acabou | "corta esse vídeo: LINK" |

---

## 6. Onde fica cada coisa

```
clipper-live/                       ← a pasta que você escolheu
├── cortes/
│   ├── pendientes/                 ← cortes esperando sua aprovação
│   └── aprobados/
│       └── canal-2026-11-19/       ← cortes aprovados de cada live (.mp4 + .txt)
└── lives/
    └── canal-2026-11-19/           ← gravação, texto, chat e blocos (se limpa sozinha)
```

O programa em si fica instalado em `~/.clipper-live` (não precisa mexer).

---

## 7. Espaço em disco e limpeza

O Clipper Live respeita os GB que você reservou:

- A gravação que **já foi analisada e cortada** é apagada uma hora depois.
- Se o uso passar de **85%** do reservado, ele apaga mais cedo.
- Se passar de **95%**, apaga até gravação ainda não analisada e avisa (sinal de que precisa reservar mais espaço).
- Os cortes **recusados** são apagados na hora.
- Os cortes **aprovados nunca são apagados sozinhos**: depois de postar, tire eles da pasta.

---

## 8. Atualizações

Você não precisa fazer nada. Toda vez que começa a vigiar uma live, se passou mais de 12 horas desde a última
vez, o sistema atualiza o Streamlink, o yt-dlp, o Whisper e o ffmpeg. Depois **testa se tudo funciona**; se uma
versão nova quebrou alguma coisa, ele volta sozinho pra anterior.

Ele nunca atualiza enquanto uma live está sendo gravada.

Pra atualizar o próprio Clipper Live (quando sair versão nova no GitHub), peça:

> atualiza a skill do clipper live

---

## 9. Problemas comuns

| Você vê… | O que significa | O que fazer |
|---|---|---|
| "trancada por idade" ou "só pra membros" | O site pede login pra ver essa live. | Escolha outra live. |
| "(sem chat)" no status | A plataforma bloqueou a leitura do chat. | Nada: os cortes continuam saindo pela fala e pelo volume. |
| "O VIGIA CAIU" | Algo falhou ao começar (link errado, site fora do ar…). | Confira o link. Se estiver certo, peça "atualiza o clipper" e vigie de novo. |
| "ESPAÇO: apaguei gravação ainda não analisada" | Reservou pouco espaço ou o Claude está atrasado. | Reserve mais GB: "usa 80 GB". |
| A live está no ar mas não grava | Pode ser uma mudança na plataforma. | Peça "atualiza o clipper" e vigie de novo. |
| Um corte saiu ruim | A IA escolheu um momento ruim. | "recusa o N". |

---

## 10. Limites (o que ele não faz)

- Não grava lives **só pra membros** ou com **trava de idade**.
- Decide pela **fala, pelo volume e pelo chat**; não "vê" a imagem. Um momento só visual entra se o chat explodir.
- O corte sai **de 30 a 40 minutos** depois do momento (é o ciclo de análise).
- **Não posta** nas redes: você posta os aprovados.

---

## 11. Respeite os streamers

Corte só streamers que permitem cortes (muitos têm canal oficial de cortes ou liberam). Mantenha sempre o crédito
que vem no `.txt` de cada corte.
