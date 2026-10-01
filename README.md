# Flappy Brasileirão ⚽

Um "Flappy Bird" com os times do Campeonato Brasileiro, feito em Python com [pygame](https://www.pygame.org/).

Escolha seu time entre os 14 clubes disponíveis e voe entre as traves dos rivais, marcando pontos a cada time que você supera!

## Times disponíveis

Flamengo, Palmeiras, Corinthians, São Paulo, Santos, Grêmio, Internacional, Atlético-MG, Cruzeiro, Fluminense, Botafogo, Vasco, Bahia e Fortaleza — cada um com as cores e listras do seu escudo.

## Como jogar

| Tela  | Controles |
|-------|-----------|
| Menu  | `←`/`→` (ou `A`/`D`) escolhe o time · `ENTER`/`ESPAÇO` começa |
| Jogo  | `ESPAÇO`, `↑` ou clique para voar · `P` pausa · `ESC` volta ao menu |

A cada 10 rivais superados o jogo grita **GOOOOL!** e fica mais rápido. Seu recorde é salvo por time em `recordes.json`.

## Requisitos

- Python 3.8+ (recomendado: **3.12**, já que o pygame ainda não publica wheels para o 3.14)
- [pygame](https://www.pygame.org/)

## Instalação e execução

```bash
pip install pygame
python flappy_brasileirao.py
```

Se seu `python` padrão apontar para uma versão sem suporte do pygame, use o lançador específico, por exemplo:

```bash
py -3.12 -m pip install pygame
py -3.12 flappy_brasileirao.py
```

## Estrutura

- `flappy_brasileirao.py` — todo o jogo (menu, física, colisão, desenho)
- `recordes.json` — recordes salvos automaticamente por time (gerado ao jogar)
