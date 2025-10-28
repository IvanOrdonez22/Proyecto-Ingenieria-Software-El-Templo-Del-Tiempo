import os
import pygame

ASSETS = "assets"
TILES  = os.path.join(ASSETS, "tiles")
MENU   = os.path.join(ASSETS, "menu")

W, H = 480, 800


class SelectLevelCommand:
    def __init__(self, callback, level_id):
        self.callback = callback
        self.level_id = level_id

    def execute(self):
        self.callback(self.level_id)


class BackCommand:
    def __init__(self, callback):
        self.callback = callback

    def execute(self):
        self.callback()


class LevelButton:
    def __init__(self, text, thumbnail, pos_y, command, sound=None):

        self.command = command
        self.sound = sound

        self.thumbnail = pygame.transform.scale(thumbnail, (96, 64))

        self.normal = pygame.image.load(os.path.join(MENU, "btn_stone.png")).convert_alpha()
        self.hover = pygame.image.load(os.path.join(MENU, "btn_stone_hover.png")).convert_alpha()
        self.image = self.normal

        self.rect = self.image.get_rect(center=(W//2, pos_y))

        self.font = pygame.font.SysFont("arial", 24, bold=True)
        self.label = self.font.render(text, True, (20, 18, 16))

        self._pressed = False

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        screen.blit(self.thumbnail, (self.rect.x + 10, self.rect.y + 16))
        screen.blit(
            self.label,
            (self.rect.x + 120, self.rect.y + self.rect.height//2 - self.label.get_height()//2)
        )

    def handle(self, events):
        mx, my = pygame.mouse.get_pos()
        inside = self.rect.collidepoint(mx, my)

        self.image = self.hover if inside else self.normal

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and inside:
                self._pressed = True
            if e.type == pygame.MOUSEBUTTONUP:
                if inside and self._pressed:
                    if self.sound: self.sound.play()
                    self.command.execute()
                self._pressed = False


class LevelSelectScreen:
    def __init__(self, back_cb, start_level_cb):

        self.bg = pygame.image.load(os.path.join(MENU, "background.png")).convert_alpha()
        self.fog = pygame.image.load(os.path.join(MENU, "fog.png")).convert_alpha()
        self.fog_x = 0

        try:
            self.sfx_click = pygame.mixer.Sound(os.path.join(MENU, "sound_select.wav"))
            self.sfx_click.set_volume(0.7)
        except:
            self.sfx_click = None

        self.thumbs = [
            pygame.image.load(os.path.join(TILES, "temple_tiles.png")).convert_alpha(),
            pygame.image.load(os.path.join(TILES, "ruins_tiles.png")).convert_alpha(),
            pygame.image.load(os.path.join(TILES, "crypt_tiles.png")).convert_alpha(),
        ]

        spacing_y = 300
        gap = 88

        self.level_buttons = [
            LevelButton(
                "Nivel 1 - Templo",
                self.thumbs[0],
                spacing_y + 0*gap,
                SelectLevelCommand(start_level_cb, 1),
                self.sfx_click
            ),
            LevelButton(
                "Nivel 2 - Ruinas",
                self.thumbs[1],
                spacing_y + 1*gap,
                SelectLevelCommand(start_level_cb, 2),
                self.sfx_click
            ),
            LevelButton(
                "Nivel 3 - Cripta",
                self.thumbs[2],
                spacing_y + 2*gap,
                SelectLevelCommand(start_level_cb, 3),
                self.sfx_click
            ),
        ]

        self.back_button = LevelButton(
            "← Volver",
            pygame.Surface((96, 64)),
            spacing_y + 3*gap + 80,
            BackCommand(back_cb),
            self.sfx_click
        )

        self.title_font = pygame.font.SysFont("georgia", 34, bold=True)
        self.title = self.title_font.render("Seleccionar nivel", True, (235, 220, 200))

    def update(self, dt):
        self.fog_x = (self.fog_x + 18 * dt) % self.fog.get_width()

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))

        fx = int(self.fog_x)
        screen.blit(self.fog, (-fx, 250))
        screen.blit(self.fog, (self.fog.get_width() - fx, 250))

        screen.blit(self.title, (W//2 - self.title.get_width()//2, 140))

        for btn in self.level_buttons:
            btn.draw(screen)

        self.back_button.draw(screen)

    def handle(self, events):
        for btn in self.level_buttons:
            btn.handle(events)
        self.back_button.handle(events)
