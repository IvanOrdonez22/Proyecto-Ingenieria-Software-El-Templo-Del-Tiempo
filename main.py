import os, sys, csv, json, pygame, math
from abc import ABC, abstractmethod
from typing import Optional
from menu_screen import MenuScreen
from level_select_screen import LevelSelectScreen

ASSETS = "assets"
PLAYER = os.path.join(ASSETS, "player")
TILES  = os.path.join(ASSETS, "tiles")
MAPS   = os.path.join(ASSETS, "maps")

W, H = 480, 800
TILE = 32
FPS  = 60

# Cerca de la línea 16 en main.py:
SOLIDS = {1,2,3,4, 14, 18} # 14 (Borde Sup) y 18 (Trampa Invisible) son sólidos
TRAPS  = {5, 10, 15}      # 10 (Pinchos) y 15 (Agua) ahora son trampas
CHECKS = {6}
SIGNS  = {7, 13, 16}      # 7 (Monedas), 13 (Antorchas), 16 (Cadenas) son objetos simples
ENEMY_SPAWNS = {8}
EXIT   = {9}
LADDERS= {10, 17}         # 17 (Lianas) ahora son escaleras
FALLING_SPAWN = {11}
SAW_SPAWN = {12}


pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("El Templo del Tiempo (Vertical+)")
clock = pygame.time.Clock()


def _rect_hits_any(rect, rects):
    return rect.collidelist(rects) >= 0

def find_safe_spawn(level, x, y, pw=32, ph=48, max_probe=80):
    r = pygame.Rect(int(x), int(y), pw, ph)
    solids = level.solid_rects

    for _ in range(max_probe):
        if not _rect_hits_any(r, solids): break
        r.y -= 1

    for _ in range(max_probe):
        if _rect_hits_any(r.move(0,1), solids): break
        r.y += 1

    return (r.x, r.y)


def load_csv(path):
    with open(path) as f:
        return [list(map(int, r)) for r in csv.reader(f)]

def slice_tiles(img):
    tw, th = img.get_size()
    return [
        img.subsurface((x*TILE, y*TILE, TILE, TILE))
        for y in range(th//TILE) for x in range(tw//TILE)
    ]


class Saw(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.base = pygame.Vector2(x,y)
        self.t=0
        self.image = pygame.Surface((26,26), pygame.SRCALPHA)
        pygame.draw.circle(self.image,(200,200,210),(13,13),13)
        for i in range(8):
            ang=i*(360/8)
            dx=int(13+11*math.cos(math.radians(ang)))
            dy=int(13+11*math.sin(math.radians(ang)))
            pygame.draw.line(self.image,(240,240,250),(13,13),(dx,dy),2)
        self.rect=self.image.get_rect(center=(x,y))
    def update(self,dt):
        self.t+=dt
        self.rect.centerx=int(self.base.x+math.sin(self.t*1.3)*48)

class FallingPlatform:
    def __init__(self,x,y):
        self.rect=pygame.Rect(x,y,TILE,TILE)
        self.falling=False
        self.timer=0
        self.vy=0
    def update(self,dt):
        if self.falling:
            self.timer+=dt
            if self.timer>0.25:
                self.vy+=980*dt
                self.rect.y+=int(self.vy*dt)
    def trigger(self):
        self.falling=True
        self.timer=0
        self.vy=-120

class Level:
    def __init__(self,tiles_png,csv_file):
        img = pygame.image.load(tiles_png).convert_alpha()
        self.tiles=slice_tiles(img)
        self.grid=load_csv(csv_file)

        self.h = len(self.grid)
        self.w = max((len(row) for row in self.grid), default=0)

        self.idx={
    1:0, 2:1, 3:2, 4:3, 5:4, 6:5, 7:7, 8:8, 9:9,  # Tiles originales
    10: 4,  # Pinchos (usando el mismo sprite que el original 5/4, quizás necesites uno nuevo)
    11: 10, # Roca de Fondo
    12: 11, # Caja de Madera
    13: 12, # Antorcha
    14: 3,  # Borde Superior (usando el mismo sprite que 4, por ejemplo)
    15: 13, # Agua
    16: 14, # Cadena Colgante
    17: 15, # Liana/Escalera
    18: 0,  # Bloque Invisible (mapeado a aire/transparente para que no se vea)
}

        self.solid_rects=[]; self.trap_rects=[]
        self.check_rects=[]; self.exit_rects=[]
        self.ladder_rects=[]
        self.enemy_spawns=[]
        self.saw_spawns=[]
        self.fall_spawns=[]

        for y,row in enumerate(self.grid):
            for x,tid in enumerate(row):
                px,py=x*TILE,y*TILE
                if tid in SOLIDS: self.solid_rects.append(pygame.Rect(px,py,TILE,TILE))
                if tid in TRAPS: self.trap_rects.append(pygame.Rect(px+6,py+8,TILE-12,TILE-10))
                if tid in CHECKS: self.check_rects.append(pygame.Rect(px+6,py+6,TILE-12,TILE-12))
                if tid in EXIT: self.exit_rects.append(pygame.Rect(px,py,TILE,TILE))
                if tid in LADDERS: self.ladder_rects.append(pygame.Rect(px+10,py,TILE-20,TILE))
                if tid in ENEMY_SPAWNS: self.enemy_spawns.append((px,py))
                if tid in SAW_SPAWN: self.saw_spawns.append((px+16,py+16))
                if tid in FALLING_SPAWN: self.fall_spawns.append((px,py))

        self.saws=pygame.sprite.Group([Saw(x,y) for (x,y) in self.saw_spawns])
        self.falls=[FallingPlatform(x,y) for (x,y) in self.fall_spawns]

    def draw(self,surf,camx,camy):
        for y, row in enumerate(self.grid):
            for x, tid in enumerate(row):
                if tid==0: continue
                idx=self.idx.get(tid)
                if idx is None or idx>=len(self.tiles): continue
                surf.blit(self.tiles[idx],(x*TILE-camx,y*TILE-camy))
        for fp in self.falls:
            pygame.draw.rect(surf,(200,160,50),(fp.rect.x-camx,fp.rect.y-camy,TILE,TILE),2)
        for s in self.saws:
            surf.blit(s.image,(s.rect.x-camx,s.rect.y-camy))

    def update(self,dt):
        self.saws.update(dt)
        for fp in self.falls: fp.update(dt)


class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.image=pygame.Surface((26,26),pygame.SRCALPHA)
        pygame.draw.rect(self.image,(200,50,50),(0,0,26,26))
        self.rect=self.image.get_rect(topleft=(x,y))
        self.vx=100
        self.vy=0
        self.g=980
        self.dir=1

    def update(self,dt,level:'Level'):
        self.vy+=self.g*dt
        ahead=self.rect.move(self.dir*20,1)
        foot=ahead.move(0,22)
        if not any(foot.colliderect(r) for r in level.solid_rects):
            self.dir*=-1
        dx=int(self.dir*self.vx*dt)
        self.rect.x+=dx
        if self.rect.collidelist(level.solid_rects)>=0:
            self.rect.x-=dx; self.dir*=-1
        dy=int(self.vy*dt)
        self.rect.y+=dy
        if self.rect.collidelist(level.solid_rects)>=0:
            self.rect.y-=dy; self.vy=0


class BossGuardian(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.max_hp=7
        self.hp=self.max_hp
        self.image=pygame.Surface((48,64),pygame.SRCALPHA)
        pygame.draw.rect(self.image,(90,80,150),(0,0,48,64))
        pygame.draw.circle(self.image,(255,0,0),(24,20),6)
        self.rect=self.image.get_rect(midbottom=(x,y))
        self.vx=100
        self.vy=0
        self.g=980
        self.dir=1
        self.enraged=False
        self.teleport_cd=0
        self.flash=0

    def take_hit(self):
        self.hp-=1
        self.flash=0.4
        if self.hp <= self.max_hp//2:
            self.enraged=True
            self.vx=150

    def update(self,dt,level:'Level',player:'Player'):
        if self.flash>0:
            self.flash-=dt
            self.image.set_alpha(120 if int(self.flash*10)%2==0 else 255)
        else:
            self.image.set_alpha(255)

        self.vy+=self.g*dt
        ahead=self.rect.move(self.dir*20,1)
        foot=ahead.move(0,40)
        if not any(foot.colliderect(r) for r in level.solid_rects):
            self.dir*=-1

        dx=int(self.dir*self.vx*dt)
        self.rect.x+=dx
        if self.rect.collidelist(level.solid_rects)>=0:
            self.rect.x-=dx; self.dir*=-1

        dy=int(self.vy*dt)
        self.rect.y+=dy
        if self.rect.collidelist(level.solid_rects)>=0:
            self.rect.y-=dy; self.vy=0

        if self.enraged:
            self.teleport_cd-=dt
            if self.teleport_cd<=0:
                self.rect.centerx=player.rect.centerx+self.dir*80
                self.teleport_cd=2.5

    def draw(self,surf,camx,camy):
        surf.blit(self.image,(self.rect.x-camx,self.rect.y-camy))


class Player(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()

        meta=json.load(open(os.path.join(PLAYER,"player_meta.json")))
        ss=pygame.image.load(os.path.join(PLAYER,meta["spritesheet"])).convert_alpha()

        self.frames={}
        for anim, rects in meta["rects"].items():
            self.frames[anim]=[
                ss.subsurface((r["x"],r["y"],r["w"],r["h"]))
                for r in rects
            ]

        self.anim="idle"
        self.fps=6
        self.fi=0
        self.ft=0
        self.image=self.frames["idle"][0]
        self.rect=self.image.get_rect(topleft=(x,y))

        self.vx=0; self.vy=0
        self.speed=180
        self.jump=360
        self.g=980
        self.on_ground=False
        self.on_ladder=False
        self.climb_speed=120

        self.max_hp=5
        self.hp=self.max_hp
        self.inv_ms=800
        self.last_hit=-9999

        self.dead=False
        self.death_timer=0

        self.history=[]
        self.maxhist=120
        self.rewinding=False

        self.checkpoint=pygame.Vector2(x,y)

    def has_anim(self, name):
        return name in self.frames and len(self.frames[name])>0

    def set_anim(self,name,fps):
        if name!=self.anim and self.has_anim(name):
            self.anim=name
            self.fps=fps
            self.fi=0
            self.ft=0

    def animate(self,dt):
        frames=self.frames[self.anim]
        self.ft+=dt
        if self.ft>=1/self.fps:
            self.ft=0
            self.fi=(self.fi+1)%len(frames)
            self.image=frames[self.fi]
        if self.vx<0:
            self.image=pygame.transform.flip(frames[self.fi],True,False)

    def step(self,dx,dy,solids):
        if dx:
            s=1 if dx>0 else -1
            for _ in range(abs(dx)):
                self.rect.x+=s
                if self.rect.collidelist(solids)>=0:
                    self.rect.x-=s; break
        if dy:
            s=1 if dy>0 else -1
            for _ in range(abs(dy)):
                self.rect.y+=s
                if self.rect.collidelist(solids)>=0:
                    self.rect.y-=s
                    if s>0: self.on_ground=True
                    self.vy=0;break

    def take_damage(self, amount, now_ms, knockback=(0, -240)):
        if self.dead: return
        if now_ms - self.last_hit < self.inv_ms: return
        self.last_hit = now_ms
        self.hp = max(0, self.hp - amount)
        self.vx += knockback[0]
        self.vy += knockback[1]
        if self.hp <= 0:
            self.dead = True
            self.death_timer = 0.0

    def update_alive(self,dt,keys,level):
        if keys[pygame.K_r] and self.history:
            self.rewinding=True
            if self.has_anim("rewind"):
                self.set_anim("rewind", 12)
            self.vx=0; self.vy=0; self.on_ground=False
            for _ in range(3):
                if self.history:
                    self.rect.topleft=self.history.pop()
            self.animate(dt)
            return
        else:
            if self.rewinding:
                self.rewinding=False
                self.set_anim("idle", 6)

        # Guardar posición
        self.history.append(self.rect.topleft)
        if len(self.history) > self.maxhist:
            self.history.pop(0)

        # Escaleras
        self.on_ladder=any(self.rect.colliderect(r) for r in level.ladder_rects)
        if self.on_ladder and (keys[pygame.K_UP] or keys[pygame.K_DOWN]):
            self.vy=(-self.climb_speed if keys[pygame.K_UP] else self.climb_speed)
            self.vx=0
            self.set_anim("idle",6)
            self.rect.y+=int(self.vy*dt)
            return

        # Movimiento normal
        self.vx=0
        if keys[pygame.K_LEFT]: self.vx=-self.speed
        if keys[pygame.K_RIGHT]: self.vx=self.speed
        if keys[pygame.K_UP] and self.on_ground:
            self.vy=-self.jump; self.on_ground=False

        if not self.on_ground: self.set_anim("jump",8)
        elif self.vx: self.set_anim("run",12)
        else: self.set_anim("idle",6)

        self.vy+=self.g*dt
        self.step(int(self.vx*dt),0,level.solid_rects)
        self.on_ground=False
        self.step(0,int(self.vy*dt),level.solid_rects)
        self.animate(dt)

    def update(self,dt,keys,level):
        if self.dead:
            self.death_timer+=dt
            if int(self.death_timer*10)%2==0:
                self.image.set_alpha(80)
            else:
                self.image.set_alpha(255)
            if self.death_timer>=1.0:
                self.image.set_alpha(255)
                self.hp=self.max_hp
                self.dead=False
                self.rect.topleft=(int(self.checkpoint.x),int(self.checkpoint.y-TILE))
                self.history.clear()
            return
        else:
            self.image.set_alpha(255)

        self.update_alive(dt,keys,level)

        if self.rect.y>level.h*TILE:
            self.rect.topleft=(int(self.checkpoint.x),int(self.checkpoint.y-TILE))
            self.hp=self.max_hp
            self.history.clear()

def draw_heart(surf,x,y,filled=True):
    c=(220,60,80) if filled else (90,90,100)
    pygame.draw.polygon(surf,c,[(x+7,y+9),(x+15,y+2),(x+23,y+9),(x+15,y+21)])
    pygame.draw.circle(surf,c,(x+11,y+7),6)
    pygame.draw.circle(surf,c,(x+19,y+7),6)

def draw_hud(surf,hp,max_hp):
    for i in range(max_hp):
        draw_heart(surf,16+i*26,16,filled=(i<hp))


class DamageStrategy(ABC):
    @abstractmethod
    def apply(self, player:'Player', now_ms:int): ...

class TrapDamage(DamageStrategy):
    def __init__(self, level:'Level'): self.level = level
    def apply(self, player:'Player', now_ms:int):
        if any(player.rect.colliderect(r) for r in self.level.trap_rects):
            player.take_damage(1, now_ms, knockback=(0,-240))

class EnemyCollisionDamage(DamageStrategy):
    def __init__(self, enemies:pygame.sprite.Group): self.enemies = enemies
    def apply(self, player:'Player', now_ms:int):
        for e in self.enemies:
            if player.rect.colliderect(e.rect):
                direction = 1 if player.rect.centerx < e.rect.centerx else -1
                player.take_damage(1, now_ms, knockback=(-200*direction, -220))

class CombatSystem:
    def __init__(self): self.strategies:list[DamageStrategy]=[]
    def add(self, strat:DamageStrategy): self.strategies.append(strat)
    def clear(self): self.strategies.clear()
    def apply_all(self, player:'Player', now_ms:int):
        for s in self.strategies: s.apply(player, now_ms)

class Command(ABC):
    @abstractmethod
    def execute(self): ...

class RewindCommand(Command):
    def __init__(self, player:'Player', keys):
        self.player=player; self.keys=keys
    def execute(self):
        return

class AttackCommand(Command):
    def __init__(self, player:'Player', boss: Optional['BossGuardian'], keys):
        self.player = player
        self.boss = boss
        self.keys = keys

    def execute(self):
        if not self.boss:
            return
        if self.keys[pygame.K_SPACE]:
            whip = self.player.rect.copy()
            whip.width += 40
            if self.player.vx >= 0:
                whip.x += 20
            else:
                whip.x -= 40
            if whip.colliderect(self.boss.rect):
                self.boss.take_hit()


def run():
    mode="menu"
    level=None
    player=None
    camx=camy=0
    enemies=pygame.sprite.Group()
    level_index=1
    cinema_timer=0.0
    self_boss=None
    
    # ¡ESTO ES CRUCIAL! DEBE ESTAR INICIALIZADO.
    bg_img = None 

    combat = CombatSystem()


    def start_level(n):
        nonlocal level,player,mode,camx,camy,enemies,level_index,self_boss,combat, bg_img 
        level_index=n

        if n==1:
            lvl=os.path.join(MAPS,"level1_temple.csv")
            til=os.path.join(TILES,"temple_tiles.png")
            bg_path = os.path.join(TILES, "fondo_juego.png") # Cambia "temple_bg.png" si tienes otro nombre
        elif n==2:
            lvl=os.path.join(MAPS,"level2_ruins.csv")
            til=os.path.join(TILES,"ruins_tiles.png")
            bg_path = os.path.join(TILES, "fondo_juego.png") # ⬅️ Usa el nombre de tu archivo aquí
        else:
            lvl=os.path.join(MAPS,"level3_crypt.csv")
            til=os.path.join(TILES,"crypt_tiles.png")
            bg_path = os.path.join(TILES, "fondo_juego.png") # Cambia "crypt_bg.png" si tienes otro nombre

        level=Level(til,lvl)
        
        try:
            bg_img = pygame.image.load(bg_path).convert()
            
            # AÑADIR: Habilitar la transparencia y establecer el valor (200 es semi-transparente)
            bg_img.set_alpha(200) 
            
        except pygame.error:
            bg_img = None
            print(f"Advertencia: No se pudo cargar el fondo {bg_path}")

        sx,sy=find_safe_spawn(level,64,100,32,48)
        player=Player(sx,sy)
        player.checkpoint.update(sx,sy)

        enemies.empty()
        for ex,ey in level.enemy_spawns:
            enemies.add(Enemy(ex,ey))

        if n==3:
            bx=(level.w//2)*TILE
            by=(level.h-4)*TILE
            self_boss=BossGuardian(bx,by)
        else:
            self_boss=None

        combat.clear()
        combat.add(TrapDamage(level))
        combat.add(EnemyCollisionDamage(enemies))

        camx=camy=0
        mode="game"

    def go_levels():
        nonlocal mode
        mode="levelselect"

    def _back_to_menu():
        nonlocal mode
        mode="menu"

    def quit_game():
        pygame.quit(); sys.exit()

    menu=MenuScreen(lambda:start_level(1), go_levels, lambda:None, quit_game)
    level_select=LevelSelectScreen(_back_to_menu, start_level)

    running=True
    while running:
        dt=clock.tick(FPS)/1000.0
        keys=pygame.key.get_pressed()
        events=pygame.event.get()
        for e in events:
            if e.type==pygame.QUIT: running=False

        # Menu
        if mode=="menu":
            menu.update(dt); menu.handle(events); menu.draw(screen)

        # Level Select
        elif mode=="levelselect":
            level_select.update(dt); level_select.handle(events); level_select.draw(screen)

        # Juego
        elif mode=="game":
            level.update(dt)
            player.update(dt,keys,level)
            enemies.update(dt,level)

            # Daño (Strategy)
            now = pygame.time.get_ticks()
            combat.apply_all(player, now)

            # Checkpoints
            for r in level.check_rects:
                if player.rect.colliderect(r):
                    player.checkpoint.update(r.x,r.y)

            # Salida
            if any(player.rect.colliderect(r) for r in level.exit_rects):
                nxt = 1 if level_index>=3 else level_index+1
                start_level(nxt) # <-- Esto te lleva al siguiente nivel (o al nivel 1 si terminaste el 3)

            # Boss Logic + Command(Attack)
            if self_boss:
                self_boss.update(dt,level,player)
                AttackCommand(player, self_boss, keys).execute()
                if self_boss.hp<=0:
                    mode="cinema"
                    cinema_timer=0.0

            # Cámara
            tgtx=max(0,min(player.rect.centerx-W//2,level.w*TILE-W))
            tgty=max(0,min(player.rect.centery-H//2,level.h*TILE-H))
            camx+=(tgtx-camx)*6*dt
            camy+=(tgty-camy)*6*dt

            # Dibujo
            if bg_img:
                # 1. Obtener ancho del fondo (bg_w)
                bg_w, bg_h = bg_img.get_size()
                
                # 2. Calcular el desplazamiento horizontal para centrar la imagen
                # W (480) - bg_w dividido por 2
                dx = (W - bg_w) // 2

                # 3. Dibuja el fondo usando el desplazamiento dx para centrarlo.
                # El paralaje vertical sigue intacto (camy * 0.3).
                screen.blit(bg_img, (dx, 0 - int(camy * 0.3)))
            else:
                screen.fill((20,20,30)) # Color sólido de respaldo si no hay imagen

            level.draw(screen,int(camx),int(camy))
            # ...
            level.draw(screen,int(camx),int(camy)) # Dibuja los tiles/plataformas
            for enemy in enemies:
                screen.blit(enemy.image,(enemy.rect.x-int(camx),enemy.rect.y-int(camy)))
            if self_boss:
                self_boss.draw(screen,int(camx),int(camy))
            # ESTA LÍNEA DEBE SER LA ÚLTIMA EN DIBUJAR EL JUGADOR
            screen.blit(player.image,(player.rect.x-int(camx),player.rect.y-int(camy)))

            # Overlay de i-frames (feedback visual)
            if pygame.time.get_ticks() - player.last_hit < player.inv_ms and not player.dead:
                overlay = pygame.Surface((W,H), pygame.SRCALPHA)
                overlay.fill((255,255,255,35))
                screen.blit(overlay,(0,0))

            draw_hud(screen,player.hp,player.max_hp)

        #  Cinemática Final
        elif mode=="cinema":
            cinema_timer+=dt
            screen.fill((255,255,255))
            font=pygame.font.SysFont("georgia",38,bold=True)

            if cinema_timer<2:
                txt=font.render("¡Has vencido al Guardián del Tiempo!",True,(0,0,0))
            elif cinema_timer<4:
                txt=font.render("El templo se derrumba...",True,(0,0,0))
            else:
                txt=font.render("✨ FIN ✨",True,(0,0,0))

            screen.blit(txt,(W//2-txt.get_width()//2,H//2-40))

        pygame.display.flip()
    pygame.quit()

if __name__=="__main__":
    run()
