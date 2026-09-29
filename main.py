import pygame
import random
import math

pygame.init()

SCREEN_W, SCREEN_H = 960, 640
FPS = 60
WHITE = (255, 255, 255)
BLACK = (20, 20, 30)
GRAY = (60, 60, 80)
GREEN = (60, 180, 90)
RED = (220, 60, 60)
BLUE = (60, 120, 220)
ORANGE = (230, 140, 40)
YELLOW = (240, 210, 60)
PURPLE = (160, 80, 220)
CYAN = (60, 200, 220)

TOWER_TYPES = {
    "fire":  {"cost": 100, "damage": 12, "range": 130, "cooldown": 0.6, "color": ORANGE, "effect": "burn"},
    "ice":   {"cost": 120, "damage": 8,  "range": 120, "cooldown": 0.8, "color": CYAN,   "effect": "slow"},
    "earth": {"cost": 150, "damage": 20, "range": 100, "cooldown": 1.2, "color": GREEN,  "effect": "stun"},
    "wind":  {"cost": 90,  "damage": 6,  "range": 150, "cooldown": 0.3, "color": PURPLE, "effect": "none"},
}

PATH = [
    (0, 320), (200, 320), (200, 160), (480, 160), (480, 480),
    (720, 480), (720, 240), (960, 240)
]

class Enemy:
    def __init__(self, wave):
        self.path_index = 0
        self.x, self.y = PATH[0]
        self.speed = 60 + wave * 8
        self.max_hp = 40 + wave * 15
        self.hp = self.max_hp
        self.slow_timer = 0
        self.stun_timer = 0
        self.burn_timer = 0
        self.burn_damage = 0
        self.alive = True

    def update(self, dt):
        if not self.alive:
            return
        if self.stun_timer > 0:
            self.stun_timer -= dt
            return
        speed = self.speed
        if self.slow_timer > 0:
            speed *= 0.5
            self.slow_timer -= dt
        if self.burn_timer > 0:
            self.hp -= self.burn_damage * dt
            self.burn_timer -= dt
            if self.hp <= 0:
                self.alive = False
                return
        if self.path_index >= len(PATH) - 1:
            self.alive = False
            return
        tx, ty = PATH[self.path_index + 1]
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist < speed * dt:
            self.x, self.y = tx, ty
            self.path_index += 1
        else:
            self.x += dx / dist * speed * dt
            self.y += dy / dist * speed * dt

    def draw(self, screen):
        if not self.alive:
            return
        color = RED
        if self.burn_timer > 0:
            color = ORANGE
        elif self.slow_timer > 0:
            color = CYAN
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 12)
        bar_w = 24
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, GRAY, (self.x - bar_w/2, self.y - 20, bar_w, 4))
        pygame.draw.rect(screen, GREEN, (self.x - bar_w/2, self.y - 20, bar_w * hp_ratio, 4))

class Tower:
    def __init__(self, x, y, tower_type):
        self.x, self.y = x, y
        self.type = tower_type
        data = TOWER_TYPES[tower_type]
        self.damage = data["damage"]
        self.range = data["range"]
        self.cooldown = data["cooldown"]
        self.timer = 0
        self.color = data["color"]
        self.effect = data["effect"]
        self.total_damage = 0

    def update(self, dt, enemies):
        self.timer -= dt
        if self.timer > 0:
            return
        target = None
        best_dist = self.range
        for e in enemies:
            if not e.alive:
                continue
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < best_dist:
                best_dist = d
                target = e
        if target:
            target.hp -= self.damage
            self.total_damage += self.damage
            if target.hp <= 0:
                target.alive = False
            if self.effect == "burn":
                target.burn_timer = 2.0
                target.burn_damage = 4
            elif self.effect == "slow":
                target.slow_timer = 1.5
            elif self.effect == "stun":
                target.stun_timer = 0.8
            self.timer = self.cooldown

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 16)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 16, 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Elemental Tower Defense")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 48)
        self.towers = []
        self.enemies = []
        self.money = 250
        self.lives = 20
        self.wave = 0
        self.spawn_timer = 0
        self.spawns_left = 0
        self.selected_type = "fire"
        self.ad_active = False
        self.ad_timer = 0
        self.game_over = False
        self.wave_active = False

    def start_wave(self):
        self.wave += 1
        self.spawns_left = 5 + self.wave * 2
        self.spawn_timer = 0
        self.wave_active = True

    def update(self, dt):
        if self.game_over:
            return
        if self.spawns_left > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.enemies.append(Enemy(self.wave))
                self.spawns_left -= 1
                self.spawn_timer = 1.0
        for e in self.enemies:
            e.update(dt)
            if not e.alive and e.path_index >= len(PATH) - 1:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
        self.enemies = [e for e in self.enemies if e.alive]
        for t in self.towers:
            t.update(dt, self.enemies)
        if self.ad_active:
            self.ad_timer -= dt
            if self.ad_timer <= 0:
                self.ad_active = False
        if self.wave_active and self.spawns_left == 0 and len(self.enemies) == 0:
            self.wave_active = False
            self.money += 50 + self.wave * 10

    def draw(self):
        self.screen.fill(BLACK)
        for i in range(len(PATH) - 1):
            pygame.draw.line(self.screen, GRAY, PATH[i], PATH[i+1], 40)
        for t in self.towers:
            t.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        self.screen.blit(self.font.render(f"Money: {self.money}", True, YELLOW), (10, 10))
        self.screen.blit(self.font.render(f"Lives: {self.lives}", True, RED), (10, 40))
        self.screen.blit(self.font.render(f"Wave: {self.wave}", True, WHITE), (10, 70))
        x = 200
        for name, data in TOWER_TYPES.items():
            color = data["color"]
            if name == self.selected_type:
                pygame.draw.rect(self.screen, WHITE, (x - 2, 8, 84, 44), 3)
            pygame.draw.rect(self.screen, color, (x, 10, 80, 40))
            self.screen.blit(self.font.render(name.capitalize(), True, WHITE), (x + 8, 16))
            self.screen.blit(self.font.render(str(data["cost"]), True, WHITE), (x + 8, 36))
            x += 90
        pygame.draw.rect(self.screen, BLUE, (SCREEN_W - 160, 10, 150, 40))
        self.screen.blit(self.font.render("Next Wave", True, WHITE), (SCREEN_W - 145, 16))
        ad_color = GREEN if not self.ad_active else GRAY
        pygame.draw.rect(self.screen, ad_color, (SCREEN_W - 160, 60, 150, 40))
        label = "Watch Ad (x2 dmg)" if not self.ad_active else f"Ad: {self.ad_timer:.1f}s"
        self.screen.blit(self.font.render(label, True, WHITE), (SCREEN_W - 150, 66))
        if self.ad_active:
            self.screen.blit(self.font.render("DOUBLE DAMAGE ACTIVE", True, ORANGE), (SCREEN_W // 2 - 120, SCREEN_H - 40))
        if self.game_over:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(self.big_font.render("GAME OVER", True, RED), (SCREEN_W // 2 - 120, SCREEN_H // 2 - 40))
            self.screen.blit(self.font.render(f"Reached wave {self.wave}", True, WHITE), (SCREEN_W // 2 - 80, SCREEN_H // 2 + 20))
        pygame.display.flip()

    def handle_click(self, pos):
        mx, my = pos
        x = 200
        for name in TOWER_TYPES:
            if x <= mx <= x + 80 and 10 <= my <= 50:
                self.selected_type = name
                return
            x += 90
        if SCREEN_W - 160 <= mx <= SCREEN_W - 10 and 10 <= my <= 50:
            if not self.wave_active:
                self.start_wave()
            return
        if SCREEN_W - 160 <= mx <= SCREEN_W - 10 and 60 <= my <= 100:
            if not self.ad_active:
                self.ad_active = True
                self.ad_timer = 30
            return
        if my > 100:
            cost = TOWER_TYPES[self.selected_type]["cost"]
            if self.money >= cost:
                on_path = False
                for i in range(len(PATH) - 1):
                    x1, y1 = PATH[i]
                    x2, y2 = PATH[i + 1]
                    if min(x1, x2) - 20 <= mx <= max(x1, x2) + 20 and min(y1, y2) - 20 <= my <= max(y1, y2) + 20:
                        on_path = True
                        break
                if not on_path:
                    self.towers.append(Tower(mx, my, self.selected_type))
                    self.money -= cost

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.wave_active:
                        self.start_wave()
                    elif event.key == pygame.K_a and not self.ad_active:
                        self.ad_active = True
                        self.ad_timer = 30
            self.update(dt)
            self.draw()
        pygame.quit()

if __name__ == "__main__":
    Game().run()
