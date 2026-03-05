"""
SHADOW REALM - RPG de Plataforma
Um jogo de plataforma com elementos de RPG
"""

import pygame
import random
import json
import os
import math
from datetime import datetime

# ==================== INICIALIZAÇÃO ====================
pygame.init()

# Cores
COLORS = {
    'background': (26, 26, 46),
    'platform': (22, 33, 62),
    'platform_highlight': (60, 80, 120),
    'player': (233, 69, 96),
    'player_flip': (180, 50, 80),
    'monster_slime': (50, 200, 100),
    'monster_goblin': (100, 150, 50),
    'monster_skeleton': (200, 200, 200),
    'monster_orc': (80, 40, 20),
    'boss': (123, 44, 191),
    'xp_gold': (255, 215, 0),
    'hud': (15, 52, 96),
    'text': (255, 255, 255),
    'health': (231, 76, 60),
    'mana': (52, 152, 219),
    'damage': (255, 100, 100),
    'heal': (100, 255, 100),
    'white': (255, 255, 255),
    'chest': (218, 165, 32),
    'door': (139, 69, 19),
}

# Configurações de tela
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shadow Realm - RPG de Plataforma")
clock = pygame.time.Clock()
FPS = 60

# Fontes
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 28)
font_hud = pygame.font.Font(None, 22)

# ==================== CLASSES ====================

class Particle:
    def __init__(self, x, y, color, velocity_x, velocity_y, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.lifetime = lifetime
        self.current_time = 0
        self.size = random.randint(3, 8)
    
    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.2
        self.current_time += 1
        return self.current_time < self.lifetime
    
    def draw(self, surface):
        alpha = max(0, 255 - (self.current_time / self.lifetime) * 255)
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(alpha)), (self.size//2, self.size//2), self.size//2)
        surface.blit(s, (int(self.x), int(self.y)))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 60
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = -18
        self.gravity = 0.8
        self.grounded = False
        self.facing_right = True
        
        # Atributos RPG
        self.max_hp = 100
        self.hp = 100
        self.max_mp = 50
        self.mp = 50
        self.base_attack = 10
        self.base_defense = 5
        self.level = 1
        self.xp = 0
        self.xp_to_next = 100
        
        # Itens equipados
        self.attack_boost = 0
        self.defense_boost = 0
        
        # Inventário
        self.inventory = {
            'health_potion': 3,
            'mana_potion': 2,
        }
        
        # Estado
        self.attacking = False
        self.attack_timer = 0
        self.invincible = False
        self.invincible_timer = 0
        self.hurt = False
        self.hurt_timer = 0
        
        # Animação
        self.anim_timer = 0
        self.is_moving = False
    
    @property
    def attack(self):
        return self.base_attack + self.attack_boost + (self.level * 2)
    
    @property
    def defense(self):
        return self.base_defense + self.defense_boost + self.level
    
    def get_damage(self, amount):
        if self.invincible:
            return 0
        damage = max(1, amount - self.defense)
        self.hp -= damage
        self.invincible = True
        self.invincible_timer = 30
        self.hurt = True
        self.hurt_timer = 10
        return damage
    
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
    
    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.max_hp += 10
        self.hp = self.max_hp
        self.max_mp += 5
        self.mp = self.max_mp
        self.base_attack += 2
        self.base_defense += 1
        self.xp_to_next = self.level * 100
    
    def update(self, platforms):
        self.vel_x = 0
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
            self.facing_right = False
            self.is_moving = True
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
            self.facing_right = True
            self.is_moving = True
        else:
            self.is_moving = False
        
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.grounded:
            self.vel_y = self.jump_power
            self.grounded = False
        
        self.vel_y += self.gravity
        
        self.x += self.vel_x
        self.check_horizontal_collisions(platforms)
        
        self.y += self.vel_y
        self.grounded = False
        self.check_vertical_collisions(platforms)
        
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        if self.y > SCREEN_HEIGHT:
            self.hp = 0
        
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
        
        if self.hurt:
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.hurt = False
        
        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False
        
        self.anim_timer += 1
    
    def check_horizontal_collisions(self, platforms):
        for plat in platforms:
            if self.rect().colliderect(plat.rect()):
                if self.vel_x > 0:
                    self.x = plat.x - self.width
                elif self.vel_x < 0:
                    self.x = plat.x + plat.width
    
    def check_vertical_collisions(self, platforms):
        for plat in platforms:
            if self.rect().colliderect(plat.rect()):
                if self.vel_y > 0:
                    self.y = plat.y - self.height
                    self.vel_y = 0
                    self.grounded = True
                elif self.vel_y < 0:
                    self.y = plat.y + plat.height
                    self.vel_y = 0
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
    
    def attack_rect(self):
        if self.facing_right:
            return pygame.Rect(self.x + self.width, self.y, 40, self.height)
        else:
            return pygame.Rect(self.x - 40, self.y, 40, self.height)
    
    def draw(self, surface):
        if self.hurt and self.anim_timer % 4 < 2:
            return
        
        color = COLORS['player']
        if not self.facing_right:
            color = COLORS['player_flip']
        
        offset = 0
        if self.is_moving:
            offset = abs(int(pygame.math.Vector2(0, 3).rotate(self.anim_timer * 20).y))
        
        pygame.draw.rect(surface, color, (int(self.x), int(self.y + offset), int(self.width), int(self.height - offset)))
        
        pygame.draw.circle(surface, color, (int(self.x + self.width // 2), int(self.y + 8 + offset)), 12)
        
        eye_x = self.x + self.width // 2 + 4 if self.facing_right else self.x + self.width // 2 - 8
        pygame.draw.circle(surface, COLORS['white'], (int(eye_x), int(self.y + 6 + offset)), 4)
        
        if self.attacking:
            attack_color = (255, 200, 100)
            atk_rect = self.attack_rect()
            pygame.draw.rect(surface, attack_color, atk_rect)
    
    def use_item(self, item_name):
        if item_name == 'health_potion' and self.inventory.get(item_name, 0) > 0:
            self.heal(30)
            self.inventory[item_name] -= 1
            return True
        elif item_name == 'mana_potion' and self.inventory.get(item_name, 0) > 0:
            self.mp = min(self.max_mp, self.mp + 20)
            self.inventory[item_name] -= 1
            return True
        return False

class Platform:
    def __init__(self, x, y, width, height):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
    
    def draw(self, surface):
        pygame.draw.rect(surface, COLORS['platform'], self.rect())
        pygame.draw.rect(surface, COLORS['platform_highlight'], 
                        (int(self.x), int(self.y), int(self.width), 4))
        
        for i in range(0, int(self.width), 30):
            pygame.draw.line(surface, (30, 40, 70), 
                           (self.x + i, self.y + 5), 
                           (self.x + i + 15, self.y + 5), 1)

class Monster:
    def __init__(self, x, y, monster_type, level):
        self.x = x
        self.y = y
        self.type = monster_type
        self.level = level
        self.width = 40
        self.height = 40
        
        if monster_type == 'slime':
            self.color = COLORS['monster_slime']
            self.max_hp = 20 + level * 5
            self.attack = 5 + level * 2
            self.xp_reward = level * 15
            self.name = "Slime"
        elif monster_type == 'goblin':
            self.color = COLORS['monster_goblin']
            self.max_hp = 20 + level * 8
            self.attack = 8 + level * 3
            self.xp_reward = level * 20
            self.name = "Goblin"
        elif monster_type == 'skeleton':
            self.color = COLORS['monster_skeleton']
            self.max_hp = 20 + level * 8
            self.attack = 12 + level * 3
            self.xp_reward = level * 25
            self.name = "Esqueleto"
        elif monster_type == 'orc':
            self.color = COLORS['monster_orc']
            self.max_hp = 20 + level * 8
            self.attack = 15 + level * 4
            self.xp_reward = level * 30
            self.name = "Orc"
        elif monster_type == "Boss":
            self.color = COLORS['boss']
            self.max_hp = 180 + level * 10
            self.attack = 20 + level * 4
            self.xp_reward = level * 30
            self.name = "Boss"
        
        self.hp = self.max_hp
        self.vel_x = 2
        self.anim_timer = 0
        self.alive = True
        self.flash_timer = 0
    
    def update(self, player):
        if not self.alive:
            return
        
        self.x += self.vel_x
        
        if self.x <= 0 or self.x + self.width >= SCREEN_WIDTH:
            self.vel_x *= -1
        
        dist = abs(self.x - player.x)
        if dist < 300 and dist > 50:
            if self.x < player.x:
                self.vel_x = 3
            else:
                self.vel_x = -3
        
        self.anim_timer += 1
        
        if self.flash_timer > 0:
            self.flash_timer -= 1
    
    def take_damage(self, damage):
        self.hp -= damage
        self.flash_timer = 10
        if self.hp <= 0:
            self.alive = False
        return self.hp
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
    
    def draw(self, surface):
        if not self.alive:
            return
        
        color = self.color
        if self.flash_timer > 0:
            color = COLORS['white']
        
        bounce = abs(int(pygame.math.Vector2(0, 3).rotate(self.anim_timer * 10).y))
        pygame.draw.rect(surface, color, 
                        (int(self.x), int(self.y + bounce), int(self.width), int(self.height - bounce)))
        
        eye_y = self.y + 10 + bounce
        pygame.draw.circle(surface, (255, 0, 0), (int(self.x + 10), int(eye_y)), 4)
        pygame.draw.circle(surface, (255, 0, 0), (int(self.x + 30), int(eye_y)), 4)
        
        bar_width = self.width
        hp_percent = self.hp / self.max_hp
        pygame.draw.rect(surface, (50, 0, 0), (int(self.x), int(self.y - 10), int(bar_width), 5))
        pygame.draw.rect(surface, COLORS['health'], (int(self.x), int(self.y - 10), int(bar_width * hp_percent), 5))

class Door:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.width = 50.0
        self.height = 80.0
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
    
    def draw(self, surface):
        pygame.draw.rect(surface, COLORS['door'], self.rect())
        pygame.draw.rect(surface, (100, 50, 10), (int(self.x + 5), int(self.y + 5), int(self.width - 10), int(self.height - 10)))
        pygame.draw.circle(surface, (255, 215, 0), (int(self.x + 40), int(self.y + 45)), 5)

class Chest:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 30
        self.opened = False
        self.items = ['health_potion', 'mana_potion']
    
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, surface):
        color = COLORS['chest']
        if self.opened:
            color = (150, 120, 20)
        pygame.draw.rect(surface, color, self.rect())
        pygame.draw.rect(surface, (100, 80, 10), (self.x, self.y + 10, self.width, 3))
        if not self.opened:
            pygame.draw.circle(surface, (255, 215, 0), (self.x + self.width//2, self.y + 12), 4)

class Combat:
    # Phases: 'player_turn' | 'player_anim' | 'monster_anim' | 'flee_anim' | 'victory' | 'defeat'
    def __init__(self, player, monster):
        self.player = player
        self.monster = monster
        self.phase = 'player_turn'
        self.selected_option = 0
        self.log = []
        self.anim_timer = 0
        self.show_victory = False   # kept for Game compatibility
        self.victory_timer = 0
        self.xp_gained = 0
        self.items_dropped = []
        # visual flash effect
        self.flash_color = None
        self.flash_timer = 0
        # flee failure penalty
        self.flee_fail_damage = 0
        self.log.append(f"Encontrou {self.monster.name}! (Nivel {self.monster.level})")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _monster_attack_damage(self):
        return max(1, self.monster.attack - self.player.defense + random.randint(-3, 5))

    def _start_monster_turn(self):
        self.phase = 'monster_anim'
        self.anim_timer = 0

    def _resolve_victory(self):
        self.show_victory = True
        self.phase = 'victory'
        self.victory_timer = 0
        self.xp_gained = self.monster.xp_reward
        self.player.gain_xp(self.xp_gained)
        if random.random() < 0.35:
            self.items_dropped.append('health_potion')
        if random.random() < 0.25:
            self.items_dropped.append('mana_potion')
        for item in self.items_dropped:
            self.player.inventory[item] = self.player.inventory.get(item, 0) + 1
        drop_msg = ""
        if self.items_dropped:
            drop_msg = " | Drop: " + ", ".join(
                "Pocao HP" if i == 'health_potion' else "Pocao MP" for i in self.items_dropped)
        self.log.append(f"Vitoria! +{self.xp_gained} XP{drop_msg}")

    # ── update ────────────────────────────────────────────────────────────────

    def update(self):
        self.anim_timer += 1

        # flash effect countdown
        if self.flash_timer > 0:
            self.flash_timer -= 1

        # ── victory hold then close ──────────────────────────────────────────
        if self.phase == 'victory':
            self.victory_timer += 1
            if self.victory_timer > 100:
                return 'victory_done'
            return True

        # ── player attack animation then monster counter-attacks ─────────────
        if self.phase == 'player_anim':
            if self.anim_timer >= 30:
                self.anim_timer = 0
                if not self.monster.alive:
                    self._resolve_victory()
                else:
                    self._start_monster_turn()
            return None

        # ── monster attack animation ─────────────────────────────────────────
        if self.phase == 'monster_anim':
            if self.anim_timer >= 35:
                self.anim_timer = 0
                damage = self._monster_attack_damage()
                self.player.get_damage(damage)
                self.flash_color = COLORS['damage']
                self.flash_timer = 8
                self.log.append(f"{self.monster.name} ataca! -{damage} HP")
                if self.player.hp <= 0:
                    self.phase = 'defeat'
                    return 'game_over'
                self.phase = 'player_turn'
            return None

        # ── flee animation (shows message, then monster punishes) ─────────────
        if self.phase == 'flee_anim':
            if self.anim_timer >= 40:
                self.anim_timer = 0
                # monster gets a free hit for the failed flee
                damage = self.flee_fail_damage
                self.player.get_damage(damage)
                self.flash_color = COLORS['damage']
                self.flash_timer = 8
                self.log.append(f"{self.monster.name} bloqueia e ataca! -{damage} HP")
                if self.player.hp <= 0:
                    self.phase = 'defeat'
                    return 'game_over'
                self.phase = 'player_turn'
            return None

        return None

    # ── actions (called from handle_event) ────────────────────────────────────

    def player_attack(self):
        if self.phase != 'player_turn':
            return
        damage = max(1, self.player.attack - self.monster.attack // 3 + random.randint(-2, 5))
        self.monster.take_damage(damage)
        self.flash_color = COLORS['xp_gold']
        self.flash_timer = 6
        self.log.append(f"Voce ataca {self.monster.name}! -{damage} HP")
        self.phase = 'player_anim'
        self.anim_timer = 0

    def player_item(self, item):
        if self.phase != 'player_turn':
            return
        if self.player.use_item(item):
            if item == 'health_potion':
                self.log.append("Pocao de Vida! +30 HP")
            elif item == 'mana_potion':
                self.log.append("Pocao de Mana! +20 MP")
            self._start_monster_turn()
        else:
            self.log.append("Sem itens disponiveis!")

    def run_away(self):
        """Returns 'fled' on success, None otherwise (failure handled internally)."""
        if self.phase != 'player_turn':
            return None
        # Chance de fuga baseada no nivel relativo
        level_diff = self.monster.level - self.player.level
        flee_chance = max(0.2, 0.6 - level_diff * 0.1)
        if random.random() < flee_chance:
            self.log.append("Voce fugiu com sucesso!")
            return 'fled'
        else:
            penalty = self._monster_attack_damage()
            self.flee_fail_damage = penalty
            self.log.append(f"Fuga falhou! ({int(flee_chance*100)}% chance)")
            self.phase = 'flee_anim'
            self.anim_timer = 0
            return None

    # ── draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface):
        # dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))

        # flash overlay when hit
        if self.flash_timer > 0 and self.flash_color:
            alpha = int(160 * (self.flash_timer / 8))
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((*self.flash_color, alpha))
            surface.blit(flash, (0, 0))

        box_w, box_h = 640, 480
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = (SCREEN_HEIGHT - box_h) // 2

        # border glow
        glow_color = COLORS['xp_gold'] if self.phase == 'victory' else COLORS['hud']
        pygame.draw.rect(surface, glow_color, (box_x - 2, box_y - 2, box_w + 4, box_h + 4), 3)
        pygame.draw.rect(surface, (15, 25, 50), (box_x, box_y, box_w, box_h))

        # ── title bar ────────────────────────────────────────────────────────
        pygame.draw.rect(surface, COLORS['hud'], (box_x, box_y, box_w, 50))
        title = font_medium.render(f"⚔  {self.monster.name}  (Lv.{self.monster.level})", True, COLORS['text'])
        surface.blit(title, (box_x + box_w // 2 - title.get_width() // 2, box_y + 12))

        # ── monster stats (left) ─────────────────────────────────────────────
        mx, my = box_x + 40, box_y + 70
        mon_lbl = font_hud.render("INIMIGO", True, (180, 120, 60))
        surface.blit(mon_lbl, (mx, my))

        hp_bar_w = 220
        hp_pct = max(0, self.monster.hp / self.monster.max_hp)
        bar_color = (200, 50, 50) if hp_pct > 0.3 else (220, 80, 20)
        pygame.draw.rect(surface, (60, 10, 10), (mx, my + 22, hp_bar_w, 18))
        pygame.draw.rect(surface, bar_color, (mx, my + 22, int(hp_bar_w * hp_pct), 18))
        pygame.draw.rect(surface, (100, 30, 30), (mx, my + 22, hp_bar_w, 18), 1)
        hp_txt = font_hud.render(f"HP  {max(0,self.monster.hp)} / {self.monster.max_hp}", True, COLORS['text'])
        surface.blit(hp_txt, (mx, my + 44))

        atk_txt = font_hud.render(f"ATK {self.monster.attack}   DEF {getattr(self.monster,'defense',0)}", True, (180, 180, 180))
        surface.blit(atk_txt, (mx, my + 64))

        # draw monster mini-sprite (colored rect with eyes)
        sprite_x, sprite_y = mx + hp_bar_w + 30, my + 10
        sprite_color = getattr(self.monster, 'color', COLORS['monster_slime'])
        shake = random.randint(-1, 1) if self.phase == 'monster_anim' else 0
        pygame.draw.rect(surface, sprite_color, (sprite_x + shake, sprite_y, 50, 50))
        pygame.draw.circle(surface, (255,255,255), (sprite_x + 15 + shake, sprite_y + 18), 6)
        pygame.draw.circle(surface, (255,255,255), (sprite_x + 35 + shake, sprite_y + 18), 6)
        pygame.draw.circle(surface, (20,20,20), (sprite_x + 15 + shake, sprite_y + 18), 3)
        pygame.draw.circle(surface, (20,20,20), (sprite_x + 35 + shake, sprite_y + 18), 3)

        # ── player stats (right) ─────────────────────────────────────────────
        px, py = box_x + box_w - 280, box_y + 70
        pl_lbl = font_hud.render("JOGADOR", True, (60, 160, 220))
        surface.blit(pl_lbl, (px, py))

        hp_bar_w2 = 220
        hp_pct2 = max(0, self.player.hp / self.player.max_hp)
        hp_col = (50, 200, 80) if hp_pct2 > 0.5 else (200, 180, 30) if hp_pct2 > 0.25 else (200, 50, 50)
        pygame.draw.rect(surface, (10, 50, 10), (px, py + 22, hp_bar_w2, 18))
        pygame.draw.rect(surface, hp_col, (px, py + 22, int(hp_bar_w2 * hp_pct2), 18))
        pygame.draw.rect(surface, (30, 80, 30), (px, py + 22, hp_bar_w2, 18), 1)
        hp_txt2 = font_hud.render(f"HP  {self.player.hp} / {self.player.max_hp}", True, COLORS['text'])
        surface.blit(hp_txt2, (px, py + 44))

        mp_pct = max(0, self.player.mp / self.player.max_mp)
        pygame.draw.rect(surface, (10, 10, 60), (px, py + 68, hp_bar_w2, 12))
        pygame.draw.rect(surface, COLORS['mana'], (px, py + 68, int(hp_bar_w2 * mp_pct), 12))
        mp_txt = font_hud.render(f"MP  {self.player.mp} / {self.player.max_mp}", True, (100, 160, 255))
        surface.blit(mp_txt, (px, py + 64))

        atk_txt2 = font_hud.render(f"ATK {self.player.attack}   DEF {self.player.defense}   Lv.{self.player.level}", True, (180,180,180))
        surface.blit(atk_txt2, (px, py + 84))

        # ── divider ───────────────────────────────────────────────────────────
        pygame.draw.line(surface, (40, 60, 100), (box_x + 20, box_y + 170), (box_x + box_w - 20, box_y + 170), 1)

        # ── action buttons ────────────────────────────────────────────────────
        blocked = self.phase != 'player_turn'
        options_data = [
            ("ATACAR",   "⚔",  None),
            ("POCAO HP", "🧪", 'health_potion'),
            ("POCAO MP", "💧", 'mana_potion'),
            ("FUGIR",    "🏃", None),
        ]
        btn_w, btn_h = 130, 44
        btn_y = box_y + 182
        for i, (label, icon, item_key) in enumerate(options_data):
            bx = box_x + 20 + i * (btn_w + 10)
            selected = (i == self.selected_option)
            bg = (30, 50, 90) if selected else (20, 30, 55)
            border = COLORS['xp_gold'] if selected else (50, 70, 110)
            pygame.draw.rect(surface, bg, (bx, btn_y, btn_w, btn_h))
            pygame.draw.rect(surface, border, (bx, btn_y, btn_w, btn_h), 2)
            col = COLORS['xp_gold'] if selected and not blocked else (130,130,130) if blocked else COLORS['text']
            txt = font_hud.render(label, True, col)
            surface.blit(txt, (bx + btn_w // 2 - txt.get_width() // 2, btn_y + 8))
            if item_key is not None:
                qty = self.player.inventory.get(item_key, 0)
                qty_col = (100, 220, 100) if qty > 0 else (120, 60, 60)
                qty_t = font_hud.render(f"x{qty}", True, qty_col)
                surface.blit(qty_t, (bx + btn_w // 2 - qty_t.get_width() // 2, btn_y + 26))

        # ── combat log ────────────────────────────────────────────────────────
        log_y = box_y + 242
        log_h = 160
        pygame.draw.rect(surface, (12, 20, 38), (box_x + 20, log_y, box_w - 40, log_h))
        pygame.draw.rect(surface, (40, 60, 100), (box_x + 20, log_y, box_w - 40, log_h), 1)
        log_lbl = font_hud.render("LOG DE COMBATE", True, (80, 110, 160))
        surface.blit(log_lbl, (box_x + 28, log_y + 4))

        visible = self.log[-5:]
        for i, line in enumerate(visible):
            alpha_factor = (i + 1) / len(visible) if visible else 1
            r = int(200 * alpha_factor + 55)
            log_col = (r, r, r)
            if "ataca!" in line and "Voce" not in line:
                log_col = (255, 120, 80)
            elif "Voce ataca" in line:
                log_col = (120, 220, 120)
            elif "Vitoria" in line or "fugiu" in line:
                log_col = COLORS['xp_gold']
            elif "Falha" in line or "falhou" in line or "bloqueia" in line:
                log_col = (220, 100, 60)
            lt = font_hud.render(line, True, log_col)
            surface.blit(lt, (box_x + 28, log_y + 24 + i * 26))

        # ── animation indicator ───────────────────────────────────────────────
        phase_msgs = {
            'player_anim': "Aguardando resposta do inimigo...",
            'monster_anim': f"{self.monster.name} esta atacando!",
            'flee_anim':    "Tentando fugir...",
        }
        if self.phase in phase_msgs:
            dots = "." * (1 + (self.anim_timer // 8) % 3)
            msg = phase_msgs[self.phase].rstrip('.') + dots
            anim_txt = font_hud.render(msg, True, (200, 160, 60))
            surface.blit(anim_txt, (box_x + box_w // 2 - anim_txt.get_width() // 2, box_y + box_h - 52))

        # ── victory banner ────────────────────────────────────────────────────
        if self.phase == 'victory':
            pulse = abs(math.sin(self.victory_timer * 0.08))
            r = int(200 + 55 * pulse)
            g = int(180 + 35 * pulse)
            vic = font_large.render("✦ VITORIA! ✦", True, (r, g, 0))
            surface.blit(vic, (SCREEN_WIDTH // 2 - vic.get_width() // 2, box_y + box_h - 100))
            xp_t = font_small.render(f"+{self.xp_gained} XP", True, COLORS['xp_gold'])
            surface.blit(xp_t, (SCREEN_WIDTH // 2 - xp_t.get_width() // 2, box_y + box_h - 55))
            if self.items_dropped:
                drop_str = "  ".join("Pocao HP" if i == 'health_potion' else "Pocao MP" for i in self.items_dropped)
                dt = font_hud.render(f"Drop: {drop_str}", True, (120, 220, 120))
                surface.blit(dt, (SCREEN_WIDTH // 2 - dt.get_width() // 2, box_y + box_h - 30))

        # ── instructions ─────────────────────────────────────────────────────
        if self.phase == 'player_turn':
            inst = font_hud.render("◄ ► Selecionar   ENTER / ESPACO Confirmar", True, (100, 120, 160))
            surface.blit(inst, (SCREEN_WIDTH // 2 - inst.get_width() // 2, box_y + box_h - 22))

class Game:
    def __init__(self):
        self.state = 'menu'
        self.player = None
        self.platforms = []
        self.monsters = []
        self.boss = None
        self.doors = []
        self.chests = []
        self.particles = []
        self.combat = None
        self.current_level = 1
        self.screen_shake = 0
        self.level_text = None
        self.level_text_timer = 0
        self.save_file = 'savegame.json'
        self.menu_selection = 0
        
        self.load_game()
    
    def new_game(self):
        self.player = Player(100, 500)
        self.current_level = 1
        self.load_level(self.current_level)
        self.state = 'playing'
    
    def load_level(self, level_num):
        self.player = Player(100, 500)
        self.platforms = []
        self.current_level = 1
        self.monsters = []
        self.doors = []
        self.chests = []
        self.particles = []
        
        self.platforms.append(Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        
        if level_num == 1:
            self.platforms.append(Platform(200, 550, 200, 20))
            self.platforms.append(Platform(500, 480, 150, 20))
            self.platforms.append(Platform(700, 400, 200, 20))
            self.platforms.append(Platform(300, 320, 180, 20))
            self.platforms.append(Platform(50, 250, 150, 20))
            
            self.monsters.append(Monster(400, 510, 'slime', 1))
            self.monsters.append(Monster(750, 360, 'slime', 2))
            
            self.doors.append(Door(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 120))
            self.chests.append(Chest(100, 220))
            
        elif level_num == 2:
            self.platforms.append(Platform(150, 580, 180, 20))
            self.platforms.append(Platform(400, 520, 150, 20))
            self.platforms.append(Platform(650, 450, 200, 20))
            self.platforms.append(Platform(250, 380, 180, 20))
            self.platforms.append(Platform(550, 300, 150, 20))
            self.platforms.append(Platform(100, 220, 150, 20))
            self.platforms.append(Platform(400, 180, 200, 20))
            
            self.monsters.append(Monster(300, 540, 'slime', 2))
            self.monsters.append(Monster(700, 410, 'goblin', 3))
            self.monsters.append(Monster(350, 340, 'slime', 2))
            self.monsters.append(Monster(600, 260, 'goblin', 3))
            
            self.doors.append(Door(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 120))
            self.chests.append(Chest(450, 150))
            
        elif level_num == 3:
            self.platforms.append(Platform(100, 580, 200, 20))
            self.platforms.append(Platform(350, 500, 150, 20))
            self.platforms.append(Platform(600, 420, 180, 20))
            self.platforms.append(Platform(150, 340, 150, 20))
            self.platforms.append(Platform(450, 280, 200, 20))
            self.platforms.append(Platform(750, 200, 150, 20))
            
            self.monsters.append(Monster(200, 540, 'goblin', 4))
            self.monsters.append(Monster(400, 460, 'skeleton', 4))
            self.monsters.append(Monster(650, 380, 'goblin', 5))
            self.monsters.append(Monster(250, 300, 'skeleton', 5))
            self.monsters.append(Monster(550, 240, 'orc', 6))
            
            self.doors.append(Door(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 120))
            
        elif level_num == 4:
            self.platforms.append(Platform(100, 600, 300, 20))
            self.platforms.append(Platform(500, 550, 200, 20))
            self.platforms.append(Platform(800, 480, 300, 20))
            self.platforms.append(Platform(300, 400, 200, 20))
            self.platforms.append(Platform(650, 320, 200, 20))
            
            self.monsters.append(Monster(200, 560, 'orc', 8))
            self.monsters.append(Monster(550, 510, 'orc', 8))
            self.monsters.append(Monster(900, 440, 'skeleton', 7))
            self.monsters.append(Monster(400, 360, 'orc', 9))
            self.monsters.append(Monster(750, 280, 'orc', 9))
            
        
        self.level_text = f"Nivel {level_num}"
        self.level_text_timer = 120
        
        self.player.hp = min(self.player.max_hp, self.player.hp + 30)
        self.player.mp = min(self.player.max_mp, self.player.mp + 20)
    
    def update(self):
        if self.state == 'playing':
            self.player.update(self.platforms)
            
            self.particles = [p for p in self.particles if p.update()]
            
            for monster in self.monsters:
                monster.update(self.player)
                
                if monster.alive and self.player.rect().colliderect(monster.rect()):
                    damage = monster.attack - self.player.defense + random.randint(-2, 5)
                    self.player.get_damage(max(1, damage))
                    self.screen_shake = 10
                    
                    self.combat = Combat(self.player, monster)
                    self.state = 'combat'
            
            if self.boss and self.boss.alive:
                self.boss.update(self.player)
                if self.player.rect().colliderect(self.boss.rect()):
                    damage = self.boss.attack - self.player.defense + random.randint(-5, 10)
                    self.player.get_damage(max(1, damage))
                    self.screen_shake = 15
                    self.combat = Combat(self.player, self.boss)
                    self.state = 'combat'
            
            for door in self.doors:
                if self.player.rect().colliderect(door.rect()):
                    self.current_level += 1
                    if self.current_level > 4:
                        self.state = 'victory'
                    else:
                        self.load_level(self.current_level)
            
            for chest in self.chests:
                if not chest.opened and self.player.rect().colliderect(chest.rect()):
                    chest.opened = True
                    for item in chest.items:
                        self.player.inventory[item] = self.player.inventory.get(item, 0) + 1
                    self.level_text = f"+ {chest.items}"
                    self.level_text_timer = 60
            
            if self.player.hp <= 0:
                self.state = 'game_over'
            
            if self.level_text_timer > 0:
                self.level_text_timer -= 1
            
            if self.screen_shake > 0:
                self.screen_shake -= 1
            
            self.save_game()
        
        elif self.state == 'combat':
            result = self.combat.update()
            if result == 'game_over':
                self.state = 'game_over'
            elif result == 'victory_done':
                self.monsters = [m for m in self.monsters if m.alive]
                if self.combat.monster == self.boss or (self.boss and not self.boss.alive):
                    self.boss = None
                    self.state = 'victory'
                else:
                    self.state = 'playing'
                self.combat = None
        
        elif self.state == 'victory':
            self.particles = [p for p in self.particles if p.update()]
    
    def draw(self):
        offset_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        offset_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        
        screen.fill(COLORS['background'], (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        if self.state == 'menu':
            self.draw_menu()
        elif self.state in ['playing', 'combat', 'victory']:
            self.draw_game(offset_x, offset_y)
            self.draw_hud()
            
            if self.state == 'combat':
                self.combat.draw(screen)
            
            if self.level_text_timer > 0:
                text = font_medium.render(self.level_text, True, COLORS['xp_gold'])
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 100))
        
        elif self.state == 'game_over':
            self.draw_game(offset_x, offset_y)
            self.draw_hud()
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            go_text = font_large.render("GAME OVER", True, COLORS['damage'])
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
            
            restart_text = font_small.render("Pressione ENTER para reiniciar", True, COLORS['text'])
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
        
        elif self.state == 'victory':
            self.draw_game(offset_x, offset_y)
            
            if random.random() < 0.3:
                self.particles.append(Particle(
                    random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT,
                    COLORS['xp_gold'],
                    random.uniform(-3, 3),
                    random.uniform(-10, -5),
                    100
                ))
            
            for p in self.particles:
                p.draw(screen)
            
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            vic_text = font_large.render("VOCE VENCEU!", True, COLORS['xp_gold'])
            screen.blit(vic_text, (SCREEN_WIDTH//2 - vic_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
            
            sub_text = font_medium.render("O Dragao das Sombras foi derrotado!", True, COLORS['text'])
            screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, SCREEN_HEIGHT//2))
            
            stats_text = font_small.render(f"Nivel Final: {self.player.level} | XP Total: {self.player.xp + (self.player.level - 1) * 100}", True, COLORS['xp_gold'])
            screen.blit(stats_text, (SCREEN_WIDTH//2 - stats_text.get_width()//2, SCREEN_HEIGHT//2 + 60))
            
            restart_text = font_small.render("Pressione ENTER para jogar novamente", True, COLORS['text'])
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 120))
    
    def draw_menu(self):
        screen.fill(COLORS['background'])
        
        title = font_large.render("SHADOW REALM", True, COLORS['player'])
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        
        subtitle = font_medium.render("RPG de Plataforma", True, COLORS['xp_gold'])
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 220))
        
        options = ["NOVO JOGO", "CONTINUAR" if os.path.exists(self.save_file) else "", "SAIR"]
        options = [o for o in options if o]
        
        for i, option in enumerate(options):
            color = COLORS['xp_gold'] if i == self.menu_selection else COLORS['text']
            text = font_medium.render(option, True, color)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 350 + i * 60))
        
        controls = [
            "CONTROLES:",
            "A/D ou Setas: Mover",
            "W/Espaco: Pular",
            "K/Z: Atacar"
        ]
        for i, ctrl in enumerate(controls):
            text = font_hud.render(ctrl, True, (150, 150, 150))
            screen.blit(text, (50, SCREEN_HEIGHT - 150 + i * 25))
    
    def draw_game(self, offset_x, offset_y):
        for plat in self.platforms:
            plat.draw(screen)
        
        for door in self.doors:
            door.draw(screen)
        
        for chest in self.chests:
            chest.draw(screen)
        
        for monster in self.monsters:
            monster.draw(screen)
        
        if self.boss:
            self.boss.draw(screen)
        
        self.player.draw(screen)
        
        for p in self.particles:
            p.draw(screen)
    
    def draw_hud(self):
        pygame.draw.rect(screen, COLORS['hud'], (20, 20, 250, 35))
        hp_percent = self.player.hp / self.player.max_hp
        pygame.draw.rect(screen, (50, 0, 0), (25, 25, 240, 25))
        pygame.draw.rect(screen, COLORS['health'], (25, 25, int(240 * hp_percent), 25))
        
        hp_text = font_hud.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, COLORS['text'])
        screen.blit(hp_text, (30, 28))
        
        pygame.draw.rect(screen, COLORS['hud'], (20, 60, 200, 25))
        mp_percent = self.player.mp / self.player.max_mp
        pygame.draw.rect(screen, (0, 0, 50), (25, 65, 190, 15))
        pygame.draw.rect(screen, COLORS['mana'], (25, 65, int(190 * mp_percent), 15))
        
        mp_text = font_hud.render(f"MP: {self.player.mp}/{self.player.max_mp}", True, COLORS['text'])
        screen.blit(mp_text, (30, 63))
        
        level_text = font_small.render(f"Nivel {self.player.level}", True, COLORS['xp_gold'])
        screen.blit(level_text, (SCREEN_WIDTH - 150, 20))
        
        xp_percent = self.player.xp / self.player.xp_to_next
        pygame.draw.rect(screen, COLORS['hud'], (SCREEN_WIDTH - 150, 50, 130, 20))
        pygame.draw.rect(screen, (50, 50, 0), (SCREEN_WIDTH - 145, 55, 120, 10))
        pygame.draw.rect(screen, COLORS['xp_gold'], (SCREEN_WIDTH - 145, 55, int(120 * xp_percent), 10))
        
        xp_text = font_hud.render(f"XP: {self.player.xp}/{self.player.xp_to_next}", True, COLORS['text'])
        screen.blit(xp_text, (SCREEN_WIDTH - 145, 72))
        
        inv_y = 100
        inv_text = font_hud.render("Itens:", True, COLORS['text'])
        screen.blit(inv_text, (20, inv_y))
        
        items = [
            ("Pocao HP", self.player.inventory.get('health_potion', 0)),
            ("Pocao MP", self.player.inventory.get('mana_potion', 0)),
        ]
        
        for i, (name, qty) in enumerate(items):
            color = COLORS['heal'] if qty > 0 else (100, 100, 100)
            item_text = font_hud.render(f"{name}: {qty}", True, color)
            screen.blit(item_text, (20, inv_y + 25 + i * 20))
        
        level_hint = font_hud.render(f"Fase {self.current_level}/4", True, (150, 150, 150))
        screen.blit(level_hint, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30))
    
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            if self.state == 'menu':
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    options = ["NOVO JOGO", "CONTINUAR" if os.path.exists(self.save_file) else "", "SAIR"]
                    options = [o for o in options if o]
                    self.menu_selection = (self.menu_selection - 1) % len(options)
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    options = ["NOVO JOGO", "CONTINUAR" if os.path.exists(self.save_file) else "", "SAIR"]
                    options = [o for o in options if o]
                    self.menu_selection = (self.menu_selection + 1) % len(options)
                elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    options = ["NOVO JOGO", "CONTINUAR" if os.path.exists(self.save_file) else "", "SAIR"]
                    options = [o for o in options if o]
                    if options[self.menu_selection] == "NOVO JOGO":
                        self.new_game()
                    elif options[self.menu_selection] == "CONTINUAR":
                        self.load_game()
                        self.state = 'playing'
                    elif options[self.menu_selection] == "SAIR":
                        return False
            
            elif self.state == 'playing':
                if event.key == pygame.K_k or event.key == pygame.K_z:
                    self.player.attacking = True
                    self.player.attack_timer = 15
                    
                    attack_rect = self.player.attack_rect()
                    for monster in self.monsters:
                        if monster.alive and attack_rect.colliderect(monster.rect()):
                            damage = max(1, self.player.attack - monster.attack // 3 + random.randint(-2, 5))
                            monster.take_damage(damage)
                            self.screen_shake = 5
                            
                            for _ in range(5):
                                self.particles.append(Particle(
                                    monster.x + monster.width // 2,
                                    monster.y + monster.height // 2,
                                    COLORS['damage'],
                                    random.uniform(-5, 5),
                                    random.uniform(-5, 5),
                                    30
                                ))
                    
                    if self.boss and self.boss.alive and attack_rect.colliderect(self.boss.rect()):
                        damage = max(1, self.player.attack - self.boss.attack // 3 + random.randint(-2, 5))
                        self.boss.take_damage(damage)
                        self.screen_shake = 10
                        
                        for _ in range(10):
                            self.particles.append(Particle(
                                self.boss.x + self.boss.width // 2,
                                self.boss.y + self.boss.height // 2,
                                COLORS['damage'],
                                random.uniform(-5, 5),
                                random.uniform(-5, 5),
                                30
                            ))
                
                elif event.key == pygame.K_1:
                    self.player.use_item('health_potion')
                elif event.key == pygame.K_2:
                    self.player.use_item('mana_potion')
                
                elif event.key == pygame.K_ESCAPE:
                    self.save_game()
                    self.state = 'menu'
            
            elif self.state == 'combat':
                if self.combat.phase != 'player_turn':
                    return True  # ignora input durante animações
                if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.combat.selected_option = (self.combat.selected_option - 1) % 4
                elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.combat.selected_option = (self.combat.selected_option + 1) % 4
                elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if self.combat.selected_option == 0:
                        self.combat.player_attack()
                    elif self.combat.selected_option == 1:
                        self.combat.player_item('health_potion')
                    elif self.combat.selected_option == 2:
                        self.combat.player_item('mana_potion')
                    elif self.combat.selected_option == 3:
                        result = self.combat.run_away()
                        if result == 'fled':
                            self.state = 'playing'
                            self.combat = None
            
            elif self.state == 'game_over':
                if event.key == pygame.K_RETURN:
                    self.new_game()
            
            elif self.state == 'victory':
                if event.key == pygame.K_RETURN:
                    self.new_game()
        
        return True
    
    def save_game(self):
        if not self.player:
            return
        
        save_data = {
            'player': {
                'x': self.player.x,
                'y': self.player.y,
                'level': self.player.level,
                'xp': self.player.xp,
                'hp': self.player.hp,
                'mp': self.player.mp,
                'max_hp': self.player.max_hp,
                'max_mp': self.player.max_mp,
                'base_attack': self.player.base_attack,
                'base_defense': self.player.base_defense,
                'attack_boost': self.player.attack_boost,
                'defense_boost': self.player.defense_boost,
                'inventory': self.player.inventory
            },
            'current_level': self.current_level,
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(self.save_file, 'w') as f:
                json.dump(save_data, f)
        except:
            pass
    
    def load_game(self):
        self.menu_selection = 0
        
        if not os.path.exists(self.save_file):
            return
        
        try:
            with open(self.save_file, 'r') as f:
                save_data = json.load(f)
            
            self.player = Player(save_data['player']['x'], save_data['player']['y'])
            self.player.level = save_data['player']['level']
            self.player.xp = save_data['player']['xp']
            self.player.hp = save_data['player']['hp']
            self.player.mp = save_data['player']['mp']
            self.player.max_hp = save_data['player']['max_hp']
            self.player.max_mp = save_data['player']['max_mp']
            self.player.base_attack = save_data['player']['base_attack']
            self.player.base_defense = save_data['player']['base_defense']
            self.player.attack_boost = save_data['player']['attack_boost']
            self.player.defense_boost = save_data['player']['defense_boost']
            self.player.inventory = save_data['player']['inventory']
            self.player.xp_to_next = self.player.level * 100
            
            self.current_level = save_data['current_level']
            self.load_level(self.current_level)
            
        except:
            pass

# ==================== LOOP PRINCIPAL ====================

def main():
    game = Game()
    running = True
    
    while running:
        for event in pygame.event.get():
            running = game.handle_event(event)
        
        game.update()
        game.draw()
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()

