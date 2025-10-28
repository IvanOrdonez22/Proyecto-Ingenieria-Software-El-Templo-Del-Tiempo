# main.py — Vertical build with enemies, ladders, traps, saws, falling platforms, checkpoints, exit
import os, sys, csv, json, pygame, math

from menu_screen import MenuScreen
from level_select_screen import LevelSelectScreen

ASSETS = "assets"
PLAYER = os.path.join(ASSETS, "player")
TILES  = os.path.join(ASSETS, "tiles")
MAPS   = os.path.join(ASSETS, "maps")

# Vertical
W, H = 480, 800
TILE = 32
FPS  = 60

# Tile semantics (IDs in CSV)
SOLIDS = {1,2,3,4}
TRAPS  = {5}
CHECKS = {6}
SIGNS  = {7}
ENEMY_SPAWNS = {8}
EXIT   = {9}
LADDERS= {10}
FALLING_SPAWN = {11}
SAW_SPAWN = {12}

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("El Templo del Tiempo (Vertical+)")
clock = pygame.time.Clock()

def load_csv(path):
    with open(path) as f:
        rows = list(csv.reader(f))
    return [list(map(int, r)) for r in rows][::-1]

def slice_tiles(png):
    tw, th = png.get_size()
    cols = tw // TILE
    rows = th // TILE
    return [png.subsurface((x*TILE, y*TILE, TILE, TILE))
            for y in range(rows) for x in range(cols)]

class Saw(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.base = pygame.Vector2(x, y)
        self.t = 0.0
        self.image = pygame.Surface((26,26), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200,200,210), (13,13), 13)
        for i in range(8):
            ang = i*(360/8)
            dx = int(13 + 11*math.cos(math.radians(ang)))
            dy = int(13 + 11*math.sin(math.radians(ang)))
            pygame.draw.line(self.image, (240,240,250), (13,13), (dx,dy), 2)
        self.rect = self.image.get_rect(center=(x, y))
    def update(self, dt):
        self.t += dt
        amp = 48; speed = 1.3
        x = self.base.x + math.sin(self.t*speed)*amp
        self.rect.centerx = int(x)

class FallingPlatform:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE, TILE)
        self.falling = False
        self.timer = 0.0
        self.vy = 0.0
    def update(self, dt):
        if self.falling:
            self.timer += dt
            if self.timer > 0.25:
                self.vy += 980*dt
                self.rect.y += int(self.vy*dt)
    def trigger(self):
        if not self.falling:
            self.falling = True
            self.timer = 0.0
            self.vy = -120

class Level:
    def __init__(self, tiles_png, csv_file):
        img = pygame.image.load(tiles_png).convert_alpha()
        self.tiles = slice_tiles(img)
        self.grid = load_csv(csv_file)
        self.h = len(self.grid)
        self.w = len(self.grid[0]) if self.h else 0
        self.idx = {1:0,2:1,3:2,4:3,5:4,6:5,7:7,8:8,9:9,10:2,11:3,12:2}
        self.solid_rects=[]; self.trap_rects=[]; self.check_rects=[]; self.exit_rects=[]
        self.ladder_rects=[]; self.enemy_spawns=[]; self.saw_spawns=[]; self.fall_spawns=[]
        for y,row in enumerate(self.grid):
            for x,tid in enumerate(row):
                px, py = x*TILE, y*TILE
                if tid in SOLIDS: self.solid_rects.append(pygame.Rect(px, py, TILE, TILE))
                if tid in TRAPS:  self.trap_rects.append(pygame.Rect(px+6, py+8, TILE-12, TILE-10))
                if tid in CHECKS: self.check_rects.append(pygame.Rect(px+6, py+6, TILE-12, TILE-12))
                if tid in EXIT:   self.exit_rects.append(pygame.Rect(px, py, TILE, TILE))
                if tid in LADDERS:self.ladder_rects.append(pygame.Rect(px+10, py, TILE-20, TILE))
                if tid in ENEMY_SPAWNS: self.enemy_spawns.append((px, py))
                if tid in SAW_SPAWN:    self.saw_spawns.append((px+TILE//2, py+TILE//2))
                if tid in FALLING_SPAWN:self.fall_spawns.append((px, py))
        self.saws = pygame.sprite.Group([Saw(x,y) for x,y in self.saw_spawns])
        self.falls = [FallingPlatform(x,y) for x,y in self.fall_spawns]
    def draw(self, surf, camx, camy):
        start_x = max(0, int(camx // TILE) - 1)
        end_x   = min(self.w, int((camx+W)//TILE) + 2)
        start_y = max(0, int(camy // TILE) - 1)
        end_y   = min(self.h, int((camy+H)//TILE) + 2)
        for y in range(start_y, end_y):
            row = self.grid[y]
            for x in range(start_x, end_x):
                tid = row[x]
                if tid == 0: continue
                idx = self.idx.get(tid)
                if idx is None or idx >= len(self.tiles): continue
                surf.blit(self.tiles[idx], (x*TILE-camx, y*TILE-camy))
        for fp in self.falls:
            pygame.draw.rect(surf, (180,140,40), (fp.rect.x-camx, fp.rect.y-camy, fp.rect.w, fp.rect.h), 2)
        for s in self.saws:
            surf.blit(s.image, (s.rect.x - camx, s.rect.y - camy))
    def update(self, dt):
        self.saws.update(dt)
        for fp in self.falls: fp.update(dt)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((26,26), pygame.SRCALPHA)
        self.image.fill((160, 30, 30))
        pygame.draw.rect(self.image, (220,80,80), (2,2,22,22), 2)
        self.rect = self.image.get_rect(topleft=(x+3, y+6))
        self.vx = 90; self.vy = 0; self.g=980; self.dir=1
    def update(self, dt, level: 'Level'):
        self.vy += self.g*dt
        ahead = self.rect.move(self.dir*12, 1)
        foot  = ahead.move(0, 22)
        ground_ahead = any(foot.colliderect(r) for r in level.solid_rects)
        if not ground_ahead: self.dir *= -1
        dx = int(self.dir*self.vx*dt); s = 1 if dx>0 else -1
        for _ in range(abs(dx)):
            self.rect.x += s
            if self.rect.collidelist(level.solid_rects)>=0:
                self.rect.x -= s; self.dir *= -1; break
        dy = int(self.vy*dt); s = 1 if dy>0 else -1
        for _ in range(abs(dy)):
            self.rect.y += s
            if self.rect.collidelist(level.solid_rects)>=0:
                self.rect.y -= s; self.vy = 0; break

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        meta = json.load(open(os.path.join(PLAYER,"player_meta.json")))
        self.frames = {anim:[pygame.image.load(os.path.join(PLAYER,f)).convert_alpha()
                              for f in files]
                       for anim,files in meta["animations"].items()}
        self.anim="idle"; self.fps=6; self.fi=0; self.ft=0
        self.image=self.frames["idle"][0]
        self.rect=self.image.get_rect(topleft=(x,y))
        self.vx=0; self.vy=0; self.g=980; self.speed=180; self.jump=360; self.on_ground=False
        self.on_ladder=False; self.climb_speed=120
        self.history=[]; self.maxhist=90; self.rew=False
        self.max_hp=5; self.hp=self.max_hp; self.inv_ms=800; self.last_hit=-99999
        self.spawn = pygame.Vector2(x,y); self.checkpoint = pygame.Vector2(x,y)
        self.dead=False; self.death_timer=0
    def step(self,dx,dy,solids):
        if dx:
            s = 1 if dx>0 else -1
            for _ in range(abs(dx)):
                self.rect.x += s
                if self.rect.collidelist(solids)>=0:
                    self.rect.x-=s; break
        if dy:
            s = 1 if dy>0 else -1
            for _ in range(abs(dy)):
                self.rect.y += s
                if self.rect.collidelist(solids)>=0:
                    self.rect.y-=s
                    if s>0: self.on_ground=True
                    self.vy=0; break
    def set_anim(self,name,fps):
        if name!=self.anim:
            self.anim=name; self.fps=fps; self.fi=0; self.ft=0
    def animate(self,dt):
        fs=self.frames[self.anim]
        self.ft+=dt
        if self.ft>=1/self.fps:
            self.ft=0; self.fi=(self.fi+1)%len(fs)
            self.image=fs[self.fi]
    def take_damage(self, amount, now_ms, knockback=(0,-240)):
        if now_ms - self.last_hit < self.inv_ms or self.dead: return
        self.last_hit = now_ms
        self.hp = max(0, self.hp - amount)
        self.vx += knockback[0]; self.vy += knockback[1]
        if self.hp<=0: self.dead=True; self.death_timer=0
    def do_respawn(self):
        self.hp=self.max_hp; self.dead=False
        self.rect.topleft=(int(self.checkpoint.x), int(self.checkpoint.y))
        self.vx=self.vy=0; self.history.clear()
    def update_alive(self,dt,keys,level:'Level'):
        self.on_ladder = any(self.rect.colliderect(r) for r in level.ladder_rects)
        if self.on_ladder and (keys[pygame.K_UP] or keys[pygame.K_DOWN]):
            self.vx = 0
            self.vy = (-self.climb_speed if keys[pygame.K_UP] else self.climb_speed)
            self.set_anim("idle",6)
            self.rect.y += int(self.vy*dt)
            return
        if keys[pygame.K_r] and self.history:
            self.rew=True; self.set_anim("rewind",12)
            for _ in range(3):
                if self.history: self.rect.topleft=self.history.pop()
            self.animate(dt); return
        self.rew=False; self.history.append(self.rect.topleft)
        if len(self.history)>self.maxhist: self.history.pop(0)
        self.vx=0
        if keys[pygame.K_LEFT]:  self.vx=-self.speed
        if keys[pygame.K_RIGHT]: self.vx= self.speed
        if keys[pygame.K_UP] and self.on_ground:
            self.vy=-self.jump; self.on_ground=False
        if not self.on_ground: self.set_anim("jump",8)
        elif self.vx: self.set_anim("run",12)
        else: self.set_anim("idle",6)
        self.vy += self.g*dt
        self.step(int(self.vx*dt),0,level.solid_rects)
        self.on_ground=False
        self.step(0,int(self.vy*dt),level.solid_rects)
        self.animate(dt)
    def update(self,dt,keys,level:'Level'):
        if self.dead:
            self.death_timer += dt
            if int(self.death_timer*10)%2==0: self.image.set_alpha(60)
            else: self.image.set_alpha(255)
            if self.death_timer>=1.1:
                self.image.set_alpha(255); self.do_respawn()
            return
        else:
            self.image.set_alpha(255)
        self.update_alive(dt,keys,level)
        # ✅ CAÍDA AL VACÍO = RESPAWN EN EL SPWAN ORIGINAL
        if self.rect.y > level.h * TILE:
            self.rect.topleft = (int(self.spawn.x), int(self.spawn.y))
            self.vx = 0
            self.vy = 0
            self.dead = False
            self.death_timer = 0
            self.hp = self.max_hp
            self.history.clear()
            return

def draw_heart(surf, x, y, filled=True):
    c = (220,60,80) if filled else (90,90,100)
    pygame.draw.polygon(surf, c, [(x+7,y+9),(x+15,y+2),(x+23,y+9),(x+15,y+21)])
    pygame.draw.circle(surf, c, (x+11,y+7), 6)
    pygame.draw.circle(surf, c, (x+19,y+7), 6)
def draw_hud(surf, hp, max_hp):
    for i in range(max_hp):
        draw_heart(surf, 16 + i*26, 16, filled=(i < hp))

def run():
    mode="menu"
    level=None; player=None
    camx=camy=0.0
    enemies = pygame.sprite.Group()
    level_index = 1
    def start_level(n):
        nonlocal level,player,mode,camx,camy,enemies,level_index
        level_index = n
        if n==1:
            lvl=os.path.join(MAPS,"level1_temple.csv")
            til=os.path.join(TILES,"temple_tiles.png")
        elif n==2:
            lvl=os.path.join(MAPS,"level2_ruins.csv")
            til=os.path.join(TILES,"ruins_tiles.png")
        else:
            lvl=os.path.join(MAPS,"level3_crypt.csv")
            til=os.path.join(TILES,"crypt_tiles.png")
        level=Level(til,lvl)
        player=Player(64,120)
        player.spawn.update(64,160); player.checkpoint.update(64,160)
        camx=camy=0.0
        enemies.empty()
        for ex,ey in level.enemy_spawns:
            enemies.add(Enemy(ex, ey))
        try: menu.stop_music()
        except: pass
        mode="game"
    def go_levels():
        nonlocal mode; mode="levelselect"
    def go_options():
        print("Opciones próximamente...")
    def quit_game():
        pygame.quit(); sys.exit()
    menu = MenuScreen(lambda:start_level(1), go_levels, go_options, quit_game)
    level_select = LevelSelectScreen(back_cb=lambda:_back_to_menu(),
                                     start_level_cb=start_level)
    def _back_to_menu():
        nonlocal mode; mode="menu"
    running=True
    while running:
        dt=clock.tick(FPS)/1000.0
        keys=pygame.key.get_pressed()
        events=pygame.event.get()
        for e in events:
            if e.type==pygame.QUIT: running=False
        if mode=="menu":
            menu.update(dt); menu.handle(events); menu.draw(screen)
        elif mode=="levelselect":
            level_select.update(dt); level_select.handle(events); level_select.draw(screen)
        elif mode=="game":
            if keys[pygame.K_ESCAPE]:
                mode="menu"
                try: pygame.mixer.music.play(-1)
                except: pass
            level.update(dt)
            player.update(dt,keys,level)
            enemies.update(dt, level)
            now = pygame.time.get_ticks()
            if any(player.rect.colliderect(r) for r in level.trap_rects):
                player.take_damage(1, now, knockback=(0,-240))
            for s in level.saws:
                if player.rect.colliderect(s.rect):
                    direction = 1 if player.rect.centerx < s.rect.centerx else -1
                    player.take_damage(1, now, knockback=(-200*direction, -220))
            for enemy in enemies:
                if player.rect.colliderect(enemy.rect):
                    direction = 1 if player.rect.centerx < enemy.rect.centerx else -1
                    player.take_damage(1, now, knockback=(-200*direction, -220))
            for r in level.check_rects:
                if player.rect.colliderect(r):
                    player.checkpoint.update(r.x, r.y)
            if any(player.rect.colliderect(r) for r in level.exit_rects):
                nxt = 1 if level_index>=3 else level_index+1
                start_level(nxt)
            tgtx = max(0, min(player.rect.centerx - W//2, level.w*TILE - W))
            tgty = max(0, min(player.rect.centery - H//2 + 20, level.h*TILE - H))
            camx += (tgtx - camx) * min(1.0, 6.0*dt)
            camy += (tgty - camy) * min(1.0, 6.0*dt)
            screen.fill((25,30,45))
            level.draw(screen, int(camx), int(camy))
            for enemy in enemies:
                screen.blit(enemy.image, (enemy.rect.x-int(camx), enemy.rect.y-int(camy)))
            screen.blit(player.image,(player.rect.x-int(camx), player.rect.y-int(camy)))
            if pygame.time.get_ticks() - player.last_hit < player.inv_ms and not player.dead:
                overlay = pygame.Surface((W,H), pygame.SRCALPHA)
                overlay.fill((255,255,255,35))
                screen.blit(overlay,(0,0))
            draw_hud(screen, player.hp, player.max_hp)
        pygame.display.flip()
    pygame.quit()

if __name__=="__main__":
    run()
