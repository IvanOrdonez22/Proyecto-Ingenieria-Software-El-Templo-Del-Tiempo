# level_select_screen.py
import os, pygame

ASSETS = "assets"
TILES  = os.path.join(ASSETS, "tiles")
MAPS   = os.path.join(ASSETS, "maps")
MENU   = os.path.join(ASSETS, "menu")

W, H = 480, 800


class LevelButton:
    def __init__(self, text, level_id, y, img, sound, on_click):
        self.level_id = level_id
        self.text = text

        # mini previsualización
        self.thumbnail = pygame.transform.scale(
            img.subsurface((0,0,96,64)), (96,64)
        )

        self.normal = pygame.image.load(os.path.join(MENU, "btn_stone.png")).convert_alpha()
        self.hover  = pygame.image.load(os.path.join(MENU, "btn_stone_hover.png")).convert_alpha()
        self.image  = self.normal
        self.rect   = self.image.get_rect(center=(W//2, y))

        self.font   = pygame.font.SysFont("arial", 24, bold=True)
        self.sound  = sound
        self.on_click = on_click
        self._pressed = False

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

        # mini preview a la izquierda
        screen.blit(self.thumbnail, (self.rect.x + 10, self.rect.y + 16))

        # texto del nivel
        label = self.font.render(self.text, True, (20,18,16))
        screen.blit(label,
                    (self.rect.x + 120,
                     self.rect.y + self.rect.height//2 - label.get_height()//2))

    def handle(self, events):
        mx, my = pygame.mouse.get_pos()
        inside = self.rect.collidepoint(mx,my)
        self.image = self.hover if inside else self.normal

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and inside:
                self._pressed = True
            if e.type == pygame.MOUSEBUTTONUP:
                if inside and self._pressed:
                    if self.sound:
                        self.sound.play()
                    self.on_click(self.level_id)
                self._pressed = False


class LevelSelectScreen:
    def __init__(self, back_cb, start_level_cb):
        self.start_level_cb = start_level_cb
        self.back_cb = back_cb

        # fondos animados
        self.bg  = pygame.image.load(os.path.join(MENU, "background.png")).convert_alpha()
        self.fog = pygame.image.load(os.path.join(MENU, "fog.png")).convert_alpha()
        self.fog_x = 0

        # efectos
        try:
            self.sfx = pygame.mixer.Sound(os.path.join(MENU, "sound_select.wav"))
            self.sfx.set_volume(0.7)
        except:
            self.sfx = None

        # cargar tiles para mini previews
        tile_imgs = [
            pygame.image.load(os.path.join(TILES,"temple_tiles.png")).convert_alpha(),
            pygame.image.load(os.path.join(TILES,"ruins_tiles.png")).convert_alpha(),
            pygame.image.load(os.path.join(TILES,"crypt_tiles.png")).convert_alpha()
        ]

        by = 300
        gap = 88

        # botones de niveles
        self.level_buttons = [
            LevelButton("Nivel 1 - Templo", 1, by + 0*gap, tile_imgs[0], self.sfx, self.start_level_cb),
            LevelButton("Nivel 2 - Ruinas", 2, by + 1*gap, tile_imgs[1], self.sfx, self.start_level_cb),
            LevelButton("Nivel 3 - Cripta", 3, by + 2*gap, tile_imgs[2], self.sfx, self.start_level_cb),
        ]

        # botón de volver
        self.back = LevelButton("← Volver", 0, 300 + 3*gap + 80,
                                pygame.Surface((96,64)), self.sfx,
                                lambda _ : self.back_cb())

        self.title_font = pygame.font.SysFont("georgia", 34, bold=True)

    def update(self, dt):
        self.fog_x = (self.fog_x + 18 * dt) % self.fog.get_width()

    def draw(self, screen):
        # fondo
        screen.blit(self.bg, (0,0))

        # niebla
        fx = int(self.fog_x)
        screen.blit(self.fog, (-fx, 250), special_flags=pygame.BLEND_PREMULTIPLIED)
        screen.blit(self.fog,
                    (self.fog.get_width()-fx, 250),
                    special_flags=pygame.BLEND_PREMULTIPLIED)

        # título
        t = self.title_font.render("Seleccionar nivel", True, (235,220,200))
        screen.blit(t, (W//2 - t.get_width()//2, 140))

        # botones
        for b in self.level_buttons:
            b.draw(screen)

        self.back.draw(screen)

    def handle(self, events):
        for b in self.level_buttons: b.handle(events)
        self.back.handle(events)