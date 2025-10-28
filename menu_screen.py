# menu_screen.py
import os, pygame, math

ASSETS = "assets"
MENU   = os.path.join(ASSETS, "menu")

W, H = 480, 800


class StoneButton:
    def __init__(self, text, y, sound, on_click):
        self.normal = pygame.image.load(os.path.join(MENU, "btn_stone.png")).convert_alpha()
        self.hover  = pygame.image.load(os.path.join(MENU, "btn_stone_hover.png")).convert_alpha()
        self.image  = self.normal
        self.rect   = self.image.get_rect(center=(W//2, y))
        self.font   = pygame.font.SysFont("arial", 28, bold=True)
        self.text   = text
        self.sound  = sound
        self.on_click = on_click
        self._pressed = False

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        label = self.font.render(self.text, True, (20,18,16))
        screen.blit(label,
                    (self.rect.centerx - label.get_width()//2,
                     self.rect.centery - label.get_height()//2))

    def handle(self, events):
        mx, my = pygame.mouse.get_pos()
        inside = self.rect.collidepoint(mx, my)
        self.image = self.hover if inside else self.normal

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and inside:
                self._pressed = True
            if e.type == pygame.MOUSEBUTTONUP:
                if inside and self._pressed:
                    if self.sound:
                        self.sound.play()
                    self.on_click()
                self._pressed = False


class MenuScreen:
    def __init__(self, start_game_cb, levels_cb, options_cb, quit_cb):
        self.start_game_cb = start_game_cb
        self.levels_cb = levels_cb
        self.options_cb = options_cb
        self.quit_cb = quit_cb

        self.bg = pygame.image.load(os.path.join(MENU, "background.png")).convert_alpha()
        self.fog = pygame.image.load(os.path.join(MENU, "fog.png")).convert_alpha()

        self.torch_frames = [
            pygame.image.load(os.path.join(MENU, f"torch_{i:02}.png")).convert_alpha()
            for i in range(1,5)
        ]
        self.torch_i = 0
        self.torch_time = 0

        try:
            pygame.mixer.music.load(os.path.join(MENU, "menu_music.mp3"))
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)
        except:
            pass

        try:
            self.sfx_select = pygame.mixer.Sound(os.path.join(MENU, "sound_select.wav"))
            self.sfx_select.set_volume(0.75)
        except:
            self.sfx_select = None

        base_y = 420
        gap = 90
        self.buttons = [
            StoneButton("Jugar", base_y + 0*gap, self.sfx_select, self.start_game_cb),
            StoneButton("Seleccionar Nivel", base_y + 1*gap, self.sfx_select, self.levels_cb),
            StoneButton("Opciones", base_y + 2*gap, self.sfx_select, self.options_cb),
            StoneButton("Salir", base_y + 3*gap, self.sfx_select, self.quit_cb),
        ]

        self.title_font = pygame.font.SysFont("georgia", 38, bold=True)
        self.sub_font   = pygame.font.SysFont("arial", 16)

        self.title_text = "El Templo del Tiempo"
        self.fog_x = 0

    def update(self, dt):
        self.torch_time += dt
        if self.torch_time >= 0.10:
            self.torch_time = 0
            self.torch_i = (self.torch_i + 1) % len(self.torch_frames)

        self.fog_x = (self.fog_x + 20*dt) % self.fog.get_width()

    def draw(self, screen):
        # Fondo negro (screen), luego muro del templo
        screen.fill((10,10,14))
        screen.blit(self.bg, (0,0))

        # Héroe frente al templo (quieto)
        try:
            hero_img = pygame.image.load(os.path.join(ASSETS, "player", "idle_01.png")).convert_alpha()
            hero_img = pygame.transform.scale(hero_img, (64, 96))
            screen.blit(hero_img, (W//2 - 45, 300))
        except:
            pass

        # Título
        title = self.title_font.render(self.title_text, True, (235,220,200))
        screen.blit(title, (W//2 - title.get_width()//2, 120))

        # Antorchas
        lf = self.torch_frames[self.torch_i]
        rf = pygame.transform.flip(lf, True, False)
        screen.blit(lf, (75, 135))
        screen.blit(rf, (W-75-32, 135))

        # 👁️ Ojos dentro del templo
        eye_color = (255,0,0)
        eye_alpha = 200
        eye_surface = pygame.Surface((200,80), pygame.SRCALPHA)
        pygame.draw.ellipse(eye_surface, (*eye_color, eye_alpha), (10, 20, 35, 20))
        pygame.draw.ellipse(eye_surface, (*eye_color, eye_alpha), (120, 20, 35, 20))
        screen.blit(eye_surface, (W//2 - 100, 260))

        # 🌫️ Niebla más suave + más arriba
        fx = int(self.fog_x)
        fog = self.fog.copy()
        fog.set_alpha(250)  # mucho más suave ✅

        fog_y = 200  # justo al nivel piso del templo ✅

        screen.blit(fog, (-fx, fog_y))
        screen.blit(fog, (self.fog.get_width()-fx, fog_y))

        # Botones
        for b in self.buttons:
            b.draw(screen)

        # Texto
        hint = self.sub_font.render("Toque para seleccionar", True, (210,210,210))
        screen.blit(hint, (W//2 - hint.get_width()//2, 760))

    def handle(self, events):
        for b in self.buttons:
            b.handle(events)

    def stop_music(self):
        try:
            pygame.mixer.music.stop()
        except:
            pass