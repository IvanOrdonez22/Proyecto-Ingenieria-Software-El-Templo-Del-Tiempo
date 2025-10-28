import os
import pygame

ASSETS = "assets"
MENU   = os.path.join(ASSETS, "menu")

W, H = 480, 800


class Command:
    def execute(self):
        raise NotImplementedError()


class StartGameCommand(Command):
    def __init__(self, callback): self.callback = callback
    def execute(self): self.callback()


class LevelsCommand(Command):
    def __init__(self, callback): self.callback = callback
    def execute(self): self.callback()


class OptionsCommand(Command):
    def __init__(self, callback): self.callback = callback
    def execute(self): self.callback()


class QuitCommand(Command):
    def __init__(self, callback): self.callback = callback
    def execute(self): self.callback()


class TorchAnimationStrategy:
    def __init__(self, frames, spd=0.10):
        self.frames = frames
        self.speed = spd
        self.frame_time = 0
        self.idx = 0

    def update(self, dt):
        self.frame_time += dt
        if self.frame_time >= self.speed:
            self.frame_time = 0
            self.idx = (self.idx + 1) % len(self.frames)

    def get_frame(self):
        return self.frames[self.idx]


class StoneButton:
    def __init__(self, text, y, sound, command: Command):
        self.command = command
        self.sound = sound

        self.normal = pygame.image.load(os.path.join(MENU, "btn_stone.png")).convert_alpha()
        self.hover  = pygame.image.load(os.path.join(MENU, "btn_stone_hover.png")).convert_alpha()
        self.image  = self.normal

        self.rect = self.image.get_rect(center=(W // 2, y))
        self.font = pygame.font.SysFont("arial", 28, bold=True)
        self.text = self.font.render(text, True, (20, 18, 16))

        self._pressed = False

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        screen.blit(self.text, (
            self.rect.centerx - self.text.get_width() // 2,
            self.rect.centery - self.text.get_height() // 2
        ))

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


class MenuScreen:
    def __init__(self, start_cb, levels_cb, options_cb, quit_cb):

        self.bg = pygame.image.load(os.path.join(MENU, "background.png")).convert_alpha()
        self.fog = pygame.image.load(os.path.join(MENU, "fog.png")).convert_alpha()

        self.hero_img = pygame.image.load(os.path.join(ASSETS, "player", "idle_01.png")).convert_alpha()
        self.hero_img = pygame.transform.scale(self.hero_img, (64, 96))

        self.title_font = pygame.font.SysFont("georgia", 38, bold=True)
        self.sub_font   = pygame.font.SysFont("arial", 16)
        self.title_text = self.title_font.render("El Templo del Tiempo", True, (235,220,200))

        try:
            pygame.mixer.music.load(os.path.join(MENU, "menu_music.mp3"))
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)
        except: pass

        try:
            self.sfx_select = pygame.mixer.Sound(os.path.join(MENU, "sound_select.wav"))
            self.sfx_select.set_volume(0.75)
        except:
            self.sfx_select = None

        torch_frames = [
            pygame.image.load(os.path.join(MENU, f"torch_{i:02}.png")).convert_alpha()
            for i in range(1,5)
        ]
        self.torch_animation = TorchAnimationStrategy(torch_frames)

        base_y = 420
        gap = 90
        self.buttons = [
            StoneButton("Jugar", base_y + 0*gap, self.sfx_select, StartGameCommand(start_cb)),
            StoneButton("Seleccionar Nivel", base_y + 1*gap, self.sfx_select, LevelsCommand(levels_cb)),
            StoneButton("Opciones", base_y + 2*gap, self.sfx_select, OptionsCommand(options_cb)),
            StoneButton("Salir", base_y + 3*gap, self.sfx_select, QuitCommand(quit_cb)),
        ]

        self.fog_x = 0

    def update(self, dt):
        self.torch_animation.update(dt)
        self.fog_x = (self.fog_x + 20*dt) % self.fog.get_width()

    def draw(self, screen):
        screen.fill((10,10,14))
        screen.blit(self.bg, (0,0))

        screen.blit(self.hero_img, (W//2 - 45, 300))
        screen.blit(self.title_text, (W//2 - self.title_text.get_width()//2, 120))

        # 🔥 Strategy
        lf = self.torch_animation.get_frame()
        screen.blit(lf, (75, 135))
        screen.blit(pygame.transform.flip(lf, True, False), (W-75-32, 135))

        # 👁️ Ojos del templo
        eye_surface = pygame.Surface((200,80), pygame.SRCALPHA)
        pygame.draw.ellipse(eye_surface, (255,0,0,200), (10, 20, 35, 20))
        pygame.draw.ellipse(eye_surface, (255,0,0,200), (120, 20, 35, 20))
        screen.blit(eye_surface, (W//2 - 100, 260))

        # 🌫️ Niebla
        fx = int(self.fog_x)
        screen.blit(self.fog, (-fx, 200))
        screen.blit(self.fog, (self.fog.get_width() - fx, 200))

        for b in self.buttons:
            b.draw(screen)

        hint = self.sub_font.render("Toque para seleccionar", True, (210,210,210))
        screen.blit(hint, (W//2 - hint.get_width()//2, 760))

    def handle(self, events):
        for b in self.buttons:
            b.handle(events)

    def stop_music(self):
        try: pygame.mixer.music.stop()
        except: pass
