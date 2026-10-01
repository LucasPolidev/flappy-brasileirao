"""
Flappy Brasileirão
------------------
Um "Flappy Bird" com os times do Campeonato Brasileiro.
Escolha seu time e voe entre as traves dos rivais!

Controles:
  Menu:  SETA ESQ/DIR (ou A/D) escolhe o time, ENTER/ESPAÇO começa
  Jogo:  ESPAÇO, SETA CIMA ou CLIQUE para voar
         P pausa, ESC volta ao menu

Requer: pip install pygame
"""

import json
import math
import os
import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------
LARGURA, ALTURA = 420, 640
FPS = 60
CHAO_ALTURA = 90

GRAVIDADE = 0.45
FORCA_PULO = -8.2
VELOCIDADE_CANO = 3.0
LARGURA_CANO = 70
ESPACO_CANO = 165          # abertura entre o cano de cima e o de baixo
DISTANCIA_CANOS = 220      # distância horizontal entre pares de canos

def pasta_executavel():
    """Pasta do .exe quando empacotado (pyinstaller), ou do script em modo normal."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def caminho_recurso(*partes):
    """Pasta dos assets (sons, imagens): extraída pelo pyinstaller em modo --onefile."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *partes)


ARQUIVO_RECORDE = os.path.join(pasta_executavel(), "recordes.json")

BRANCO = (255, 255, 255)
PRETO = (20, 20, 20)
AMARELO = (255, 215, 0)
VERDE_CAMPO = (46, 139, 60)
VERDE_CAMPO_2 = (56, 158, 72)
CEU = (110, 190, 235)

# Cores reutilizadas pelos times
VERMELHO = (200, 16, 46)
VERDE = (0, 110, 60)
AZUL = (0, 70, 160)
AZUL_CLARO = (90, 170, 230)
GRENA = (130, 20, 50)
PRETO_T = (25, 25, 25)

# Cada time: nome, sigla, listras (cores verticais), cor do texto da sigla
TIMES = [
    {"nome": "Flamengo",      "sigla": "FLA", "listras": [VERMELHO, PRETO_T, VERMELHO, PRETO_T], "texto": BRANCO},
    {"nome": "Palmeiras",     "sigla": "PAL", "listras": [VERDE, VERDE, BRANCO, VERDE, VERDE], "texto": BRANCO},
    {"nome": "Corinthians",   "sigla": "COR", "listras": [BRANCO, BRANCO, PRETO_T, BRANCO, BRANCO], "texto": PRETO},
    {"nome": "São Paulo",     "sigla": "SAO", "listras": [BRANCO, VERMELHO, BRANCO, PRETO_T, BRANCO], "texto": PRETO},
    {"nome": "Santos",        "sigla": "SAN", "listras": [BRANCO, PRETO_T, BRANCO, PRETO_T, BRANCO], "texto": PRETO},
    {"nome": "Grêmio",        "sigla": "GRE", "listras": [AZUL_CLARO, PRETO_T, BRANCO, PRETO_T, AZUL_CLARO], "texto": BRANCO},
    {"nome": "Internacional", "sigla": "INT", "listras": [VERMELHO, VERMELHO, BRANCO, VERMELHO, VERMELHO], "texto": BRANCO},
    {"nome": "Atlético-MG",   "sigla": "CAM", "listras": [PRETO_T, BRANCO, PRETO_T, BRANCO, PRETO_T], "texto": BRANCO},
    {"nome": "Cruzeiro",      "sigla": "CRU", "listras": [AZUL, AZUL, BRANCO, AZUL, AZUL], "texto": BRANCO},
    {"nome": "Fluminense",    "sigla": "FLU", "listras": [GRENA, BRANCO, VERDE, BRANCO, GRENA], "texto": BRANCO},
    {"nome": "Botafogo",      "sigla": "BOT", "listras": [PRETO_T, BRANCO, PRETO_T, BRANCO, PRETO_T], "texto": AMARELO},
    {"nome": "Vasco",         "sigla": "VAS", "listras": [PRETO_T, BRANCO, PRETO_T], "texto": VERMELHO},
    {"nome": "Bahia",         "sigla": "BAH", "listras": [AZUL, VERMELHO, BRANCO, VERMELHO, AZUL], "texto": BRANCO},
    {"nome": "Fortaleza",     "sigla": "FOR", "listras": [VERMELHO, BRANCO, AZUL, BRANCO, VERMELHO], "texto": BRANCO},
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def carregar_recordes():
    try:
        with open(ARQUIVO_RECORDE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def salvar_recordes(recordes):
    try:
        with open(ARQUIVO_RECORDE, "w", encoding="utf-8") as f:
            json.dump(recordes, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def superficie_listrada(largura, altura, listras):
    """Retângulo preenchido com listras verticais nas cores do time."""
    surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
    n = len(listras)
    for i, cor in enumerate(listras):
        x0 = round(i * largura / n)
        x1 = round((i + 1) * largura / n)
        pygame.draw.rect(surf, cor, (x0, 0, x1 - x0, altura))
    return surf


def criar_escudo(time, raio, fonte):
    """Escudo redondo com as listras e a sigla do time."""
    d = raio * 2
    surf = superficie_listrada(d, d, time["listras"])

    # recorta em círculo
    mascara = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(mascara, (255, 255, 255, 255), (raio, raio), raio)
    surf.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    pygame.draw.circle(surf, AMARELO, (raio, raio), raio, 3)
    texto_com_contorno(surf, time["sigla"], fonte, time["texto"], (raio, raio))
    return surf


def texto_com_contorno(destino, texto, fonte, cor, centro, contorno=PRETO):
    base = fonte.render(texto, True, contorno)
    frente = fonte.render(texto, True, cor)
    rect = frente.get_rect(center=centro)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        destino.blit(base, rect.move(dx, dy))
    destino.blit(frente, rect)


def colide_circulo_retangulo(cx, cy, r, rect):
    px = max(rect.left, min(cx, rect.right))
    py = max(rect.top, min(cy, rect.bottom))
    return (cx - px) ** 2 + (cy - py) ** 2 < r * r


# ---------------------------------------------------------------------------
# Entidades
# ---------------------------------------------------------------------------
class Jogador:
    RAIO = 20

    def __init__(self, time, fonte):
        self.time = time
        self.imagem = criar_escudo(time, self.RAIO, fonte)
        self.reset()

    def reset(self):
        self.x = LARGURA * 0.28
        self.y = ALTURA * 0.42
        self.vel = 0.0
        self.angulo = 0.0

    def pular(self):
        self.vel = FORCA_PULO

    def atualizar(self):
        self.vel = min(self.vel + GRAVIDADE, 11)
        self.y += self.vel
        alvo = max(-70, min(25, -self.vel * 3.5))
        self.angulo += (alvo - self.angulo) * 0.2

    def flutuar(self, t):
        """Animação de espera antes de começar."""
        self.y = ALTURA * 0.42 + math.sin(t * 0.08) * 8
        self.angulo = math.sin(t * 0.05) * 10

    def desenhar(self, tela):
        img = pygame.transform.rotozoom(self.imagem, self.angulo, 1)
        tela.blit(img, img.get_rect(center=(int(self.x), int(self.y))))


class ParDeCanos:
    """Um par de 'traves' com as cores de um time rival."""

    def __init__(self, x, rival, fonte):
        self.x = float(x)
        self.rival = rival
        self.fonte = fonte
        margem = 70
        self.centro = random.randint(margem + ESPACO_CANO // 2,
                                     ALTURA - CHAO_ALTURA - margem - ESPACO_CANO // 2)
        self.passou = False
        self.corpo = superficie_listrada(LARGURA_CANO, ALTURA, rival["listras"])
        self.tampa = superficie_listrada(LARGURA_CANO + 12, 28, rival["listras"])

    @property
    def topo_rect(self):
        return pygame.Rect(int(self.x), 0, LARGURA_CANO, self.centro - ESPACO_CANO // 2)

    @property
    def base_rect(self):
        y = self.centro + ESPACO_CANO // 2
        return pygame.Rect(int(self.x), y, LARGURA_CANO, ALTURA - CHAO_ALTURA - y)

    def atualizar(self, vel):
        self.x -= vel

    def colide(self, jogador):
        r = jogador.RAIO - 3  # um pouco de tolerância
        return (colide_circulo_retangulo(jogador.x, jogador.y, r, self.topo_rect)
                or colide_circulo_retangulo(jogador.x, jogador.y, r, self.base_rect))

    def desenhar(self, tela):
        for rect, tampa_y in ((self.topo_rect, self.topo_rect.bottom - 28),
                              (self.base_rect, self.base_rect.top)):
            tela.blit(self.corpo, rect.topleft, area=pygame.Rect(0, 0, rect.w, rect.h))
            pygame.draw.rect(tela, PRETO, rect, 2)
            tampa_rect = pygame.Rect(rect.x - 6, tampa_y, LARGURA_CANO + 12, 28)
            tela.blit(self.tampa, tampa_rect.topleft)
            pygame.draw.rect(tela, PRETO, tampa_rect, 3)
            texto_com_contorno(tela, self.rival["sigla"], self.fonte,
                               self.rival["texto"], tampa_rect.center)


# ---------------------------------------------------------------------------
# Jogo
# ---------------------------------------------------------------------------
class Jogo:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flappy Brasileirão")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.relogio = pygame.time.Clock()
        self.sons = self._carregar_sons()

        self.fonte_gigante = pygame.font.SysFont("arial", 64, bold=True)
        self.fonte_grande = pygame.font.SysFont("arial", 40, bold=True)
        self.fonte_media = pygame.font.SysFont("arial", 24, bold=True)
        self.fonte_pequena = pygame.font.SysFont("arial", 16, bold=True)
        self.fonte_sigla = pygame.font.SysFont("arial", 13, bold=True)

        self.recordes = carregar_recordes()
        self.indice_time = 0
        self.estado = "menu"      # menu | pronto | jogando | pausado | fim
        self.tick = 0
        self.desloc_chao = 0.0
        self.torcida = self._gerar_torcida()
        self.mensagem = ""
        self.mensagem_timer = 0

    # ----- preparação -----------------------------------------------------
    def _carregar_sons(self):
        sons = {}
        try:
            for nome in ("pulo", "colisao", "gol"):
                sons[nome] = pygame.mixer.Sound(caminho_recurso("sons", f"{nome}.wav"))
        except pygame.error:
            pass  # sem placa de som / mixer indisponível: jogo continua mudo
        return sons

    def tocar(self, nome):
        som = self.sons.get(nome)
        if som:
            som.play()

    def _gerar_torcida(self):
        """Pontinhos coloridos simulando a arquibancada."""
        pontos = []
        for y in range(40, 150, 9):
            for x in range(0, LARGURA, 9):
                if random.random() < 0.85:
                    time = random.choice(TIMES)
                    pontos.append((x + random.randint(-2, 2), y, random.choice(time["listras"])))
        return pontos

    def iniciar_partida(self):
        self.time = TIMES[self.indice_time]
        self.jogador = Jogador(self.time, self.fonte_sigla)
        self.rivais = [t for t in TIMES if t is not self.time]
        self.canos = []
        self.pontos = 0
        self.velocidade = VELOCIDADE_CANO
        self.estado = "pronto"
        self.mensagem = ""
        self.mensagem_timer = 0

    def novo_cano(self, x):
        self.canos.append(ParDeCanos(x, random.choice(self.rivais), self.fonte_sigla))

    @property
    def recorde_atual(self):
        return self.recordes.get(TIMES[self.indice_time]["nome"], 0)

    # ----- loop principal -------------------------------------------------
    def rodar(self):
        while True:
            self.tick += 1
            self.tratar_eventos()
            self.atualizar()
            self.desenhar()
            pygame.display.flip()
            self.relogio.tick(FPS)

    def tratar_eventos(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            acao = (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1) or (
                ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w, pygame.K_RETURN))

            if self.estado == "menu":
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.indice_time = (self.indice_time - 1) % len(TIMES)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.indice_time = (self.indice_time + 1) % len(TIMES)
                    elif ev.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                if acao:
                    self.iniciar_partida()

            elif self.estado == "pronto":
                if acao:
                    self.estado = "jogando"
                    self.novo_cano(LARGURA + 40)
                    self.jogador.pular()
                    self.tocar("pulo")
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.estado = "menu"

            elif self.estado == "jogando":
                if acao:
                    self.jogador.pular()
                    self.tocar("pulo")
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_p:
                    self.estado = "pausado"
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.estado = "menu"

            elif self.estado == "pausado":
                if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_p, pygame.K_SPACE):
                    self.estado = "jogando"
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.estado = "menu"

            elif self.estado == "fim":
                # pequena espera para não reiniciar sem querer
                if self.tick - self.tick_fim > 30:
                    if acao:
                        self.iniciar_partida()
                    elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                        self.estado = "menu"

    def atualizar(self):
        if self.estado in ("menu", "pronto", "jogando"):
            self.desloc_chao = (self.desloc_chao + self.velocidade_atual()) % 40

        if self.mensagem_timer > 0:
            self.mensagem_timer -= 1

        if self.estado == "pronto":
            self.jogador.flutuar(self.tick)
            return
        if self.estado != "jogando":
            if self.estado == "fim" and self.jogador.y < ALTURA - CHAO_ALTURA - Jogador.RAIO:
                self.jogador.atualizar()  # cai até o chão
            return

        self.jogador.atualizar()

        for cano in self.canos:
            cano.atualizar(self.velocidade)
            if not cano.passou and cano.x + LARGURA_CANO < self.jogador.x:
                cano.passou = True
                self.pontos += 1
                self.mensagem = f"Passou o {cano.rival['nome']}!"
                self.mensagem_timer = 50
                if self.pontos % 10 == 0:
                    self.mensagem = "GOOOOL!"
                    self.mensagem_timer = 80
                    self.velocidade += 0.25   # fica mais difícil
                    self.tocar("gol")

        self.canos = [c for c in self.canos if c.x + LARGURA_CANO + 10 > 0]
        if not self.canos or self.canos[-1].x < LARGURA - DISTANCIA_CANOS:
            self.novo_cano(LARGURA + 10)

        bateu_cano = any(c.colide(self.jogador) for c in self.canos)
        bateu_chao = self.jogador.y + Jogador.RAIO >= ALTURA - CHAO_ALTURA
        saiu_topo = self.jogador.y < -Jogador.RAIO * 2
        if bateu_cano or bateu_chao or saiu_topo:
            self.fim_de_jogo()

    def velocidade_atual(self):
        return self.velocidade if self.estado in ("pronto", "jogando") else VELOCIDADE_CANO

    def fim_de_jogo(self):
        self.estado = "fim"
        self.tick_fim = self.tick
        self.tocar("colisao")
        nome = self.time["nome"]
        self.novo_recorde = self.pontos > self.recordes.get(nome, 0)
        if self.novo_recorde:
            self.recordes[nome] = self.pontos
            salvar_recordes(self.recordes)

    # ----- desenho --------------------------------------------------------
    def desenhar_cenario(self):
        self.tela.fill(CEU)

        # arquibancada
        pygame.draw.rect(self.tela, (70, 70, 80), (0, 30, LARGURA, 130))
        for x, y, cor in self.torcida:
            pulo = int(math.sin((self.tick + x) * 0.15) * 2) if self.mensagem == "GOOOOL!" and self.mensagem_timer else 0
            pygame.draw.circle(self.tela, cor, (x, y + pulo), 3)
        pygame.draw.rect(self.tela, (40, 40, 50), (0, 155, LARGURA, 8))

        # gramado com faixas
        campo_topo = 163
        faixa = 40
        for i, y in enumerate(range(campo_topo, ALTURA - CHAO_ALTURA, faixa)):
            cor = VERDE_CAMPO if i % 2 == 0 else VERDE_CAMPO_2
            pygame.draw.rect(self.tela, cor, (0, y, LARGURA, faixa))
        # círculo central decorativo
        pygame.draw.circle(self.tela, (220, 240, 220), (LARGURA // 2, 360), 70, 2)

    def desenhar_chao(self):
        y = ALTURA - CHAO_ALTURA
        pygame.draw.rect(self.tela, (34, 110, 45), (0, y, LARGURA, CHAO_ALTURA))
        pygame.draw.line(self.tela, BRANCO, (0, y), (LARGURA, y), 4)
        for x in range(-40, LARGURA + 40, 40):
            xx = x - int(self.desloc_chao)
            pygame.draw.polygon(self.tela, (28, 95, 38),
                                [(xx, y + 4), (xx + 20, y + 4), (xx + 5, y + 22), (xx - 15, y + 22)])
        txt = self.fonte_pequena.render("BRASILEIRÃO", True, (200, 230, 200))
        self.tela.blit(txt, txt.get_rect(center=(LARGURA // 2, y + 55)))

    def desenhar(self):
        self.desenhar_cenario()

        if self.estado == "menu":
            self.desenhar_chao()
            self.desenhar_menu()
            return

        for cano in self.canos:
            cano.desenhar(self.tela)
        self.desenhar_chao()
        self.jogador.desenhar(self.tela)

        if self.estado != "pronto":
            texto_com_contorno(self.tela, str(self.pontos), self.fonte_gigante, BRANCO, (LARGURA // 2, 70))

        if self.mensagem_timer > 0 and self.estado == "jogando":
            fonte = self.fonte_grande if self.mensagem == "GOOOOL!" else self.fonte_pequena
            cor = AMARELO if self.mensagem == "GOOOOL!" else BRANCO
            texto_com_contorno(self.tela, self.mensagem, fonte, cor, (LARGURA // 2, 130))

        if self.estado == "pronto":
            texto_com_contorno(self.tela, self.time["nome"], self.fonte_grande, AMARELO, (LARGURA // 2, 200))
            texto_com_contorno(self.tela, "ESPAÇO ou CLIQUE para voar", self.fonte_pequena, BRANCO,
                               (LARGURA // 2, 340))
        elif self.estado == "pausado":
            self.painel("PAUSADO", ["P para continuar", "ESC para o menu"])
        elif self.estado == "fim":
            linhas = [f"Rivais superados: {self.pontos}",
                      f"Recorde do {self.time['nome']}: {self.recordes.get(self.time['nome'], 0)}"]
            if self.novo_recorde and self.pontos > 0:
                linhas.insert(0, "NOVO RECORDE!")
            linhas += ["", "ESPAÇO: jogar de novo", "ESC: trocar de time"]
            self.painel("FIM DE JOGO", linhas)

    def painel(self, titulo, linhas):
        sombra = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 120))
        self.tela.blit(sombra, (0, 0))
        caixa = pygame.Rect(30, 190, LARGURA - 60, 60 + 32 * len(linhas))
        pygame.draw.rect(self.tela, (250, 245, 225), caixa, border_radius=14)
        pygame.draw.rect(self.tela, PRETO, caixa, 3, border_radius=14)
        texto_com_contorno(self.tela, titulo, self.fonte_grande, AMARELO, (LARGURA // 2, caixa.y + 34))
        for i, linha in enumerate(linhas):
            cor = (200, 30, 30) if linha == "NOVO RECORDE!" else PRETO
            img = self.fonte_pequena.render(linha, True, cor)
            self.tela.blit(img, img.get_rect(center=(LARGURA // 2, caixa.y + 78 + 32 * i)))

    def desenhar_menu(self):
        texto_com_contorno(self.tela, "FLAPPY", self.fonte_gigante, AMARELO, (LARGURA // 2, 90))
        texto_com_contorno(self.tela, "BRASILEIRÃO", self.fonte_grande, BRANCO, (LARGURA // 2, 145))

        time = TIMES[self.indice_time]
        escudo = criar_escudo(time, 55, self.fonte_media)
        y = 300 + math.sin(self.tick * 0.06) * 6
        self.tela.blit(escudo, escudo.get_rect(center=(LARGURA // 2, int(y))))

        texto_com_contorno(self.tela, "<", self.fonte_grande, BRANCO, (60, 300))
        texto_com_contorno(self.tela, ">", self.fonte_grande, BRANCO, (LARGURA - 60, 300))
        texto_com_contorno(self.tela, time["nome"], self.fonte_media, BRANCO, (LARGURA // 2, 385))
        texto_com_contorno(self.tela, f"Recorde: {self.recorde_atual}", self.fonte_pequena, AMARELO,
                           (LARGURA // 2, 415))
        texto_com_contorno(self.tela, "SETAS escolhem o time  •  ENTER começa", self.fonte_pequena, BRANCO,
                           (LARGURA // 2, 515))


if __name__ == "__main__":
    Jogo().rodar()
