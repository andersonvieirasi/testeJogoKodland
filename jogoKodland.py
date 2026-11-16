import math
import random
import pgzrun
from pygame import Rect

# Constantes da janela
WIDTH = 800
HEIGHT = 600
TITLE = "Crystal Cavern Platformer"

# Constantes de física
GRAVITY = 0.6
JUMP_FORCE = -13.5
PLAYER_SPEED = 4.0

# Estados do jogo
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_VICTORY = "victory"


class AnimatedEntity:
    """Classe base responsável pela troca cíclica de sprites e limites de movimento."""

    def __init__(self, x, y, width, height, idle_frames, walk_frames):
        self.rect = Rect(x, y, width, height)
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        self.current_frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.18
        self.is_moving = False
        self.facing_right = True

    def update_animation(self, dt):
        """Alterna ciclicamente entre os quadros do estado ativo (parado ou andando)."""
        self.animation_timer += dt
        active_frames = self.walk_frames if self.is_moving else self.idle_frames

        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            self.current_frame_index = (self.current_frame_index + 1) % len(active_frames)

    def get_current_sprite(self):
        """Retorna o nome do sprite correspondente ao quadro atual da animação."""
        active_frames = self.walk_frames if self.is_moving else self.idle_frames
        index = self.current_frame_index % len(active_frames)
        return active_frames[index]

    def draw(self):
        """Renderiza o sprite atual na posição da entidade."""
        sprite_name = self.get_current_sprite()
        screen.blit(sprite_name, (self.rect.x, self.rect.y))


class Hero(AnimatedEntity):
    """Personagem controlado pelo jogador com física de plataforma e colisões."""

    def __init__(self, x, y):
        idle_sprites = ["hero_idle_1", "hero_idle_2"]
        walk_sprites = ["hero_walk_1", "hero_walk_2"]
        super().__init__(x, y, 36, 48, idle_sprites, walk_sprites)
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False

    def handle_input(self, sound_enabled):
        """Processa os comandos de movimento horizontal e pulo."""
        self.velocity_x = 0.0
        if keyboard.left or keyboard.a:
            self.velocity_x = -PLAYER_SPEED
            self.facing_right = False
        if keyboard.right or keyboard.d:
            self.velocity_x = PLAYER_SPEED
            self.facing_right = True

        if (keyboard.space or keyboard.up or keyboard.w) and self.on_ground:
            self.velocity_y = JUMP_FORCE
            self.on_ground = False
            if sound_enabled:
                sounds.jump.play()

        self.is_moving = self.velocity_x != 0.0

    def update(self, dt, platforms):
        """Aplica a gravidade e resolve as colisões com as plataformas."""
        # Movimento horizontal
        self.rect.x += int(self.velocity_x)
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH

        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity_x > 0:
                    self.rect.right = platform.left
                elif self.velocity_x < 0:
                    self.rect.left = platform.right

        # Movimento vertical
        self.velocity_y += GRAVITY
        self.rect.y += int(self.velocity_y)
        self.on_ground = False

        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.top
                    self.velocity_y = 0.0
                    self.on_ground = True
                elif self.velocity_y < 0:
                    self.rect.top = platform.bottom
                    self.velocity_y = 0.0

        self.update_animation(dt)


class Enemy(AnimatedEntity):
    """Inimigo autônomo que patrulha um território horizontal definido."""

    def __init__(self, x, y, min_x, max_x, speed):
        idle_sprites = ["enemy_idle_1", "enemy_idle_2"]
        walk_sprites = ["enemy_walk_1", "enemy_walk_2"]
        super().__init__(x, y, 36, 36, idle_sprites, walk_sprites)
        self.min_x = min_x
        self.max_x = max_x
        self.speed = speed
        self.direction = random.choice([-1, 1])
        self.pause_timer = 0.0
        self.is_moving = True

    def update(self, dt):
        """Patrulha o território com pausas ocasionais para exibir a animação parado."""
        if self.pause_timer > 0:
            self.pause_timer -= dt
            self.is_moving = False
            self.update_animation(dt)
            return

        self.is_moving = True
        self.rect.x += int(self.speed * self.direction)

        if self.rect.left <= self.min_x:
            self.rect.left = self.min_x
            self.direction = 1
            self.pause_timer = random.uniform(0.4, 1.0)
        elif self.rect.right >= self.max_x:
            self.rect.right = self.max_x
            self.direction = -1
            self.pause_timer = random.uniform(0.4, 1.0)

        self.update_animation(dt)


class Button:
    """Botão clicável da interface do menu principal."""

    def __init__(self, x, y, width, height, text, color):
        self.rect = Rect(x, y, width, height)
        self.text = text
        self.color = color

    def draw(self):
        screen.draw.filled_rect(self.rect, self.color)
        screen.draw.rect(self.rect, (255, 255, 255))
        screen.draw.text(
            self.text,
            center=self.rect.center,
            fontsize=28,
            color=(255, 255, 255),
        )

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# Variáveis globais de estado do jogo
game_state = STATE_MENU
audio_enabled = True
score = 0
bobbing_timer = 0.0

# Geometria das plataformas do cenário
platforms = [
    Rect(0, 560, 800, 40),      # Chão principal
    Rect(80, 440, 220, 20),     # Plataforma inferior esquerda
    Rect(480, 420, 240, 20),    # Plataforma inferior direita
    Rect(260, 310, 260, 20),    # Plataforma central
    Rect(60, 200, 200, 20),     # Plataforma superior esquerda
    Rect(520, 180, 220, 20),    # Plataforma superior direita
]

hero = None
enemies = []
crystals = []

# Botões do menu principal
btn_start = Button(275, 230, 250, 55, "Start Game", (46, 139, 87))
btn_audio = Button(275, 310, 250, 55, "Audio: ON", (70, 130, 180))
btn_exit = Button(275, 390, 250, 55, "Exit", (178, 34, 34))


def start_music():
    """Inicia a música de fundo caso o áudio esteja ativado."""
    if audio_enabled:
        music.play("background_theme")
        music.set_volume(0.4)


def reset_level():
    """Inicializa ou reinicia o herói, os inimigos e os cristais coletáveis."""
    global hero, enemies, crystals, score
    score = 0
    hero = Hero(60, 480)

    enemies = [
        Enemy(100, 404, 80, 300, 2.0),
        Enemy(500, 384, 480, 720, 2.5),
        Enemy(280, 274, 260, 520, 2.2),
        Enemy(540, 144, 520, 740, 2.8),
    ]

    crystals = [
        Rect(170, 405, 18, 18),
        Rect(600, 385, 18, 18),
        Rect(380, 275, 18, 18),
        Rect(140, 165, 18, 18),
        Rect(630, 145, 18, 18),
    ]


def toggle_audio():
    """Liga ou desliga a música e os efeitos sonoros."""
    global audio_enabled
    audio_enabled = not audio_enabled
    btn_audio.text = "Audio: ON" if audio_enabled else "Audio: OFF"
    if audio_enabled:
        start_music()
    else:
        music.stop()


def update(dt):
    """Loop principal de atualização lógica do PgZero."""
    global game_state, score, bobbing_timer
    bobbing_timer += dt

    if game_state == STATE_PLAYING:
        hero.handle_input(audio_enabled)
        hero.update(dt, platforms)

        for enemy in enemies:
            enemy.update(dt)
            if hero.rect.colliderect(enemy.rect):
                if audio_enabled:
                    sounds.hit.play()
                game_state = STATE_GAME_OVER

        for crystal in crystals[:]:
            if hero.rect.colliderect(crystal):
                crystals.remove(crystal)
                score += 10
                if audio_enabled:
                    sounds.coin.play()

        if not crystals:
            game_state = STATE_VICTORY


def draw():
    """Rotina principal de renderização na tela do PgZero."""
    screen.fill((25, 28, 42))

    if game_state == STATE_MENU:
        screen.draw.text(
            "CRYSTAL CAVERN",
            center=(WIDTH // 2, 130),
            fontsize=56,
            color=(255, 215, 0),
        )
        btn_start.draw()
        btn_audio.draw()
        btn_exit.draw()

    elif game_state == STATE_PLAYING:
        for platform in platforms:
            screen.draw.filled_rect(platform, (95, 105, 125))
            screen.draw.rect(platform, (160, 175, 195))

        # Movimento suave de flutuação vertical usando math.sin
        offset_y = int(math.sin(bobbing_timer * 5.0) * 4)
        for crystal in crystals:
            draw_rect = Rect(crystal.x, crystal.y + offset_y, crystal.width, crystal.height)
            screen.draw.filled_rect(draw_rect, (0, 230, 230))

        for enemy in enemies:
            enemy.draw()

        hero.draw()
        screen.draw.text(f"Score: {score}", (20, 15), fontsize=30, color=(255, 255, 255))

    elif game_state in (STATE_GAME_OVER, STATE_VICTORY):
        title_text = "VICTORY!" if game_state == STATE_VICTORY else "GAME OVER"
        title_color = (50, 220, 100) if game_state == STATE_VICTORY else (235, 65, 65)

        screen.draw.text(title_text, center=(WIDTH // 2, 230), fontsize=64, color=title_color)
        screen.draw.text(
            f"Final Score: {score}",
            center=(WIDTH // 2, 300),
            fontsize=34,
            color=(255, 255, 255),
        )
        screen.draw.text(
            "Click anywhere to return to Main Menu",
            center=(WIDTH // 2, 370),
            fontsize=26,
            color=(200, 200, 200),
        )


def on_mouse_down(pos):
    """Gerencia os cliques do mouse nos botões do menu e nas telas finais."""
    global game_state

    if game_state == STATE_MENU:
        if btn_start.is_clicked(pos):
            reset_level()
            game_state = STATE_PLAYING
        elif btn_audio.is_clicked(pos):
            toggle_audio()
        elif btn_exit.is_clicked(pos):
            raise SystemExit

    elif game_state in (STATE_GAME_OVER, STATE_VICTORY):
        game_state = STATE_MENU


start_music()
pgzrun.go()

