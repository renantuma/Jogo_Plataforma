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
        """Dano no mundo de plataforma - ativa invencibilidade temporaria."""
        if self.invincible:
            return 0
        damage = max(1, amount - self.defense)
        self.hp -= damage
        self.invincible = True
        self.invincible_timer = 60
        self.hurt = True
        self.hurt_timer = 15
        return damage

    def get_damage_combat(self, amount):
        """Dano no combate por turno - sem invencibilidade, sempre aplica."""
        damage = max(1, amount - self.defense)
        self.hp = max(0, self.hp - damage)
        self.hurt = True
        self.hurt_timer = 15
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
        self.max_hp += 15
        self.hp = self.max_hp  # cura total ao subir de nível
        self.max_mp += 8
        self.mp = self.max_mp
        self.base_attack += 3
        self.base_defense += 2
        self.xp_to_next = int(self.level * 100 * 1.2)
    
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
        # Pisca quando machucado
        if self.hurt and self.anim_timer % 4 < 2:
            return

        t = self.anim_timer
        cx = int(self.x + self.width // 2)
        # Bob animado ao se mover, leve ao parar
        if self.is_moving:
            bob = int(math.sin(t * 0.35) * 3)
            leg_swing = int(math.sin(t * 0.35) * 8)
        else:
            bob = int(math.sin(t * 0.08) * 1)
            leg_swing = 0

        # Sombra no chão
        shadow_surf = pygame.Surface((self.width + 8, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, self.width + 8, 6))
        surface.blit(shadow_surf, (int(self.x) - 4, int(self.y + self.height) - 2))

        base_color  = (233, 69, 96)
        dark_color  = (160, 40, 65)
        light_color = (255, 120, 140)
        armor_color = (40, 60, 110)
        armor_light = (70, 100, 170)

        by = int(self.y) + bob  # base y com bob

        # --- PERNAS ---
        leg_w, leg_h = 10, 22
        lleg_x = cx - 14
        rleg_x = cx + 4
        lleg_y = by + self.height - leg_h
        rleg_y = by + self.height - leg_h
        pygame.draw.rect(surface, dark_color,  (lleg_x, int(lleg_y - leg_swing * 0.4), leg_w, leg_h))
        pygame.draw.rect(surface, dark_color,  (rleg_x, int(rleg_y + leg_swing * 0.4), leg_w, leg_h))
        # botas
        pygame.draw.rect(surface, (20, 20, 40), (lleg_x - 1, int(lleg_y - leg_swing * 0.4) + leg_h - 7, leg_w + 2, 8))
        pygame.draw.rect(surface, (20, 20, 40), (rleg_x - 1, int(rleg_y + leg_swing * 0.4) + leg_h - 7, leg_w + 2, 8))

        # --- CORPO (armadura) ---
        body_rect = pygame.Rect(int(self.x) + 3, by + 22, self.width - 6, 28)
        pygame.draw.rect(surface, armor_color, body_rect, border_radius=4)
        pygame.draw.rect(surface, armor_light, (body_rect.x + 3, body_rect.y + 3, body_rect.width - 6, 8), border_radius=3)
        # detalhe central
        pygame.draw.line(surface, armor_light, (cx, by + 26), (cx, by + 46), 2)

        # --- BRAÇOS ---
        arm_w, arm_h = 9, 20
        if self.facing_right:
            larm_x, rarm_x = int(self.x) - 4, int(self.x) + self.width - 5
            arm_swing_l, arm_swing_r = leg_swing * 0.5, -leg_swing * 0.5
        else:
            larm_x, rarm_x = int(self.x) - 4, int(self.x) + self.width - 5
            arm_swing_l, arm_swing_r = -leg_swing * 0.5, leg_swing * 0.5
        pygame.draw.rect(surface, base_color, (larm_x, by + 24 + int(arm_swing_l), arm_w, arm_h), border_radius=3)
        pygame.draw.rect(surface, base_color, (rarm_x, by + 24 + int(arm_swing_r), arm_w, arm_h), border_radius=3)

        # --- CABEÇA ---
        head_cx, head_cy = cx, by + 14
        pygame.draw.circle(surface, base_color, (head_cx, head_cy), 14)
        pygame.draw.circle(surface, light_color, (head_cx - 3, head_cy - 3), 6)  # highlight
        # capacete
        helm_pts = [(head_cx - 12, head_cy - 2), (head_cx - 8, head_cy - 14),
                    (head_cx, head_cy - 17), (head_cx + 8, head_cy - 14), (head_cx + 12, head_cy - 2)]
        pygame.draw.polygon(surface, armor_color, helm_pts)
        pygame.draw.polygon(surface, armor_light, helm_pts, 1)

        # olho
        if self.facing_right:
            eye_x = head_cx + 5
        else:
            eye_x = head_cx - 5
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, head_cy + 1), 5)
        pygame.draw.circle(surface, (20, 20, 80), (eye_x + (1 if self.facing_right else -1), head_cy + 1), 3)
        pygame.draw.circle(surface, (255, 255, 255), (eye_x + (1 if self.facing_right else -1), head_cy), 1)

        # --- ATAQUE: arco de luz ---
        if self.attacking:
            atk_rect = self.attack_rect()
            slash_surf = pygame.Surface((atk_rect.width + 10, atk_rect.height + 10), pygame.SRCALPHA)
            glow_col = (255, 220, 80, 120)
            for r in range(4, 0, -1):
                pygame.draw.ellipse(slash_surf, (*glow_col[:3], 40 * r),
                                    (2, 2, atk_rect.width + 6, atk_rect.height + 6))
            pygame.draw.rect(slash_surf, (255, 240, 120, 180),
                             (4, atk_rect.height // 2 - 3, atk_rect.width, 6), border_radius=3)
            surface.blit(slash_surf, (atk_rect.x - 5, atk_rect.y - 5))
    
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
    
    def draw(self, surface, zone_cfg=None):
        if zone_cfg is None:
            zone_cfg = ZONE_CONFIG[1]
        rx, ry, rw, rh = int(self.x), int(self.y), int(self.width), int(self.height)
        pc  = zone_cfg['plat_col']
        phi = zone_cfg['plat_hi']
        crc = zone_cfg['crystal_col']
        # Corpo principal
        pygame.draw.rect(surface, pc, (rx, ry, rw, rh))
        # Brilho no topo
        pygame.draw.rect(surface, phi, (rx, ry, rw, 3))
        # Linha de highlight sutil
        pygame.draw.rect(surface, tuple(min(255,c+20) for c in phi), (rx+1, ry+3, rw-2, 2))
        # Sombra na base
        pygame.draw.rect(surface, tuple(max(0,c-20) for c in pc), (rx, ry+rh-3, rw, 3))
        # Bordas
        pygame.draw.rect(surface, tuple(min(255,c+20) for c in pc), (rx, ry, 2, rh))
        pygame.draw.rect(surface, tuple(min(255,c+20) for c in pc), (rx+rw-2, ry, 2, rh))
        # Divisórias
        for i in range(rx+25, rx+rw-10, 30):
            pygame.draw.line(surface, tuple(max(0,c-10) for c in pc), (i,ry+5),(i,ry+rh-3), 1)
        # Cristais decorativos
        for i in range(rx+20, rx+rw-10, 55):
            pts = [(i,ry-4),(i-4,ry+1),(i,ry+3),(i+4,ry+1)]
            pygame.draw.polygon(surface, crc, pts)
            pygame.draw.polygon(surface, tuple(min(255,c+60) for c in crc), pts, 1)

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
            self.max_hp = 30 + level * 8
            self.attack = 6 + level * 2
            self.defense = max(0, level - 1)
            self.xp_reward = level * 18
            self.speed = 1.5
            self.name = "Slime"
        elif monster_type == 'goblin':
            self.color = COLORS['monster_goblin']
            self.max_hp = 40 + level * 10
            self.attack = 10 + level * 3
            self.defense = level
            self.xp_reward = level * 22
            self.speed = 2.5
            self.name = "Goblin"
        elif monster_type == 'skeleton':
            self.color = COLORS['monster_skeleton']
            self.max_hp = 45 + level * 10
            self.attack = 14 + level * 3
            self.defense = level + 1
            self.xp_reward = level * 28
            self.speed = 2.0
            self.name = "Esqueleto"
        elif monster_type == 'orc':
            self.color = COLORS['monster_orc']
            self.max_hp = 60 + level * 12
            self.attack = 18 + level * 4
            self.defense = level + 2
            self.xp_reward = level * 35
            self.speed = 1.8
            self.name = "Orc"
        elif monster_type == "Boss":
            self.color = COLORS['boss']
            self.max_hp = 250 + level * 15
            self.attack = 25 + level * 5
            self.defense = level * 2
            self.xp_reward = level * 50
            self.speed = 2.0
            self.name = "Boss"
        
        self.hp = self.max_hp
        self.vel_x = self.speed
        self.anim_timer = 0
        self.alive = True
        self.flash_timer = 0
    
    def update(self, player):
        if not self.alive:
            return
        
        dist_x = player.x - self.x
        dist_y = player.y - self.y
        dist = abs(dist_x)

        # Sempre persegue o player se estiver próximo (campo de visão 400px)
        if dist < 400:
            # Acelera quando está próximo
            chase_speed = self.speed * 1.5 if dist < 150 else self.speed
            if dist_x > 5:
                self.vel_x = chase_speed
            elif dist_x < -5:
                self.vel_x = -chase_speed
            else:
                self.vel_x = 0
        else:
            # Patrulha quando longe
            self.x += self.vel_x
            if self.x <= 0 or self.x + self.width >= SCREEN_WIDTH:
                self.vel_x *= -1
            # Resetar para patrulha normal
            if abs(self.vel_x) > self.speed:
                self.vel_x = self.speed if self.vel_x > 0 else -self.speed
        
        self.x += self.vel_x
        # Não sair da tela
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        
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

        t = self.anim_timer
        bounce = int(math.sin(t * 0.15) * 3)
        mx = int(self.x + self.width // 2)
        my = int(self.y) + bounce

        flash = self.flash_timer > 0
        col = (255, 255, 255) if flash else self.color
        dark = tuple(max(0, c - 60) for c in col)
        light = tuple(min(255, c + 60) for c in col)

        # Sombra
        sh = pygame.Surface((self.width + 6, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 55), (0, 0, self.width + 6, 5))
        surface.blit(sh, (int(self.x) - 3, int(self.y + self.height) - 2))

        if self.type == 'slime':
            # Corpo gelatinoso
            body_h = int(self.height * 0.65) + abs(int(math.sin(t * 0.1) * 4))
            body_w = self.width + abs(int(math.sin(t * 0.1) * 5))
            body_y = my + self.height - body_h
            bx = mx - body_w // 2
            pygame.draw.ellipse(surface, dark, (bx + 2, body_y + 2, body_w, body_h))
            pygame.draw.ellipse(surface, col,  (bx, body_y, body_w, body_h))
            pygame.draw.ellipse(surface, light, (bx + 6, body_y + 4, body_w // 2, body_h // 3))
            # olhinhos
            eye_y = body_y + body_h // 3
            pygame.draw.circle(surface, (0, 0, 0), (mx - 7, eye_y), 5)
            pygame.draw.circle(surface, (0, 0, 0), (mx + 7, eye_y), 5)
            pygame.draw.circle(surface, (255, 80, 80), (mx - 7, eye_y), 3)
            pygame.draw.circle(surface, (255, 80, 80), (mx + 7, eye_y), 3)
            pygame.draw.circle(surface, (255, 200, 200), (mx - 6, eye_y - 1), 1)
            pygame.draw.circle(surface, (255, 200, 200), (mx + 8, eye_y - 1), 1)

        elif self.type == 'goblin':
            # Corpo
            body_r = pygame.Rect(int(self.x) + 4, my + 14, self.width - 8, 22)
            pygame.draw.rect(surface, dark, body_r, border_radius=4)
            pygame.draw.rect(surface, col,  (body_r.x - 1, body_r.y - 1, body_r.w + 2, body_r.h), border_radius=4)
            # Cabeça grande
            pygame.draw.circle(surface, col,  (mx, my + 10), 14)
            pygame.draw.circle(surface, light, (mx - 4, my + 5), 6)
            # Orelhas pontudas
            pygame.draw.polygon(surface, dark, [(mx - 14, my + 5), (mx - 20, my - 6), (mx - 8, my + 2)])
            pygame.draw.polygon(surface, dark, [(mx + 14, my + 5), (mx + 20, my - 6), (mx + 8, my + 2)])
            # Olhos
            pygame.draw.circle(surface, (255, 220, 0), (mx - 5, my + 8), 4)
            pygame.draw.circle(surface, (255, 220, 0), (mx + 5, my + 8), 4)
            pygame.draw.circle(surface, (0, 0, 0), (mx - 5, my + 8), 2)
            pygame.draw.circle(surface, (0, 0, 0), (mx + 5, my + 8), 2)
            # Dentes
            for dx in [-4, 0, 4]:
                pygame.draw.rect(surface, (240, 240, 220), (mx + dx - 2, my + 17, 3, 5))
            # Pernas
            pygame.draw.rect(surface, dark, (int(self.x) + 6, my + 34, 9, 14), border_radius=3)
            pygame.draw.rect(surface, dark, (int(self.x) + self.width - 15, my + 34, 9, 14), border_radius=3)

        elif self.type == 'skeleton':
            # Fêmur legs
            pygame.draw.rect(surface, col, (mx - 12, my + 32, 6, 18), border_radius=2)
            pygame.draw.rect(surface, col, (mx + 6, my + 32, 6, 18), border_radius=2)
            pygame.draw.circle(surface, col, (mx - 9, my + 33), 5)
            pygame.draw.circle(surface, col, (mx + 9, my + 33), 5)
            # Costelas / corpo
            pygame.draw.rect(surface, dark, (mx - 12, my + 14, 24, 20), border_radius=3)
            for ry2 in range(my + 16, my + 32, 5):
                pygame.draw.line(surface, col, (mx - 10, ry2), (mx + 10, ry2), 1)
            # Caveira
            pygame.draw.circle(surface, col, (mx, my + 8), 13)
            pygame.draw.circle(surface, light, (mx - 3, my + 4), 5)
            # Olhos cavados
            pygame.draw.ellipse(surface, (20, 20, 20), (mx - 9, my + 4, 7, 8))
            pygame.draw.ellipse(surface, (20, 20, 20), (mx + 2, my + 4, 7, 8))
            pygame.draw.circle(surface, (200, 50, 200), (mx - 5, my + 7), 2)
            pygame.draw.circle(surface, (200, 50, 200), (mx + 5, my + 7), 2)
            # Braços
            arm_angle = int(math.sin(t * 0.12) * 6)
            pygame.draw.line(surface, col, (mx - 12, my + 18), (mx - 20, my + 26 + arm_angle), 4)
            pygame.draw.line(surface, col, (mx + 12, my + 18), (mx + 20, my + 26 - arm_angle), 4)

        elif self.type in ('orc', 'Boss'):
            bw = self.width if self.type == 'orc' else self.width + 8
            boff = 0 if self.type == 'orc' else -4
            # Pernas largas
            pygame.draw.rect(surface, dark, (int(self.x) + boff + 2, my + 28, bw // 2 - 2, 20), border_radius=3)
            pygame.draw.rect(surface, dark, (int(self.x) + boff + bw // 2 + 1, my + 28, bw // 2 - 2, 20), border_radius=3)
            # Corpo musculoso
            body = pygame.Rect(int(self.x) + boff, my + 10, bw, 22)
            pygame.draw.rect(surface, dark, (body.x + 2, body.y + 2, body.w, body.h), border_radius=5)
            pygame.draw.rect(surface, col, body, border_radius=5)
            pygame.draw.rect(surface, light, (body.x + 4, body.y + 3, body.w // 2, 8), border_radius=3)
            # Braços
            arm_swing = int(math.sin(t * 0.12) * 5)
            pygame.draw.ellipse(surface, col, (int(self.x) + boff - 8, my + 12 + arm_swing, 10, 18))
            pygame.draw.ellipse(surface, col, (int(self.x) + boff + bw - 2, my + 12 - arm_swing, 10, 18))
            # Cabeça
            pygame.draw.circle(surface, col, (mx, my + 7), 14)
            pygame.draw.circle(surface, light, (mx - 4, my + 2), 6)
            # Presas
            pygame.draw.polygon(surface, (220, 220, 200), [(mx - 5, my + 14), (mx - 3, my + 20), (mx - 1, my + 14)])
            pygame.draw.polygon(surface, (220, 220, 200), [(mx + 1, my + 14), (mx + 3, my + 20), (mx + 5, my + 14)])
            # Olhos raivosos
            pygame.draw.circle(surface, (255, 60, 0), (mx - 5, my + 6), 4)
            pygame.draw.circle(surface, (255, 60, 0), (mx + 5, my + 6), 4)
            pygame.draw.circle(surface, (80, 0, 0), (mx - 5, my + 6), 2)
            pygame.draw.circle(surface, (80, 0, 0), (mx + 5, my + 6), 2)
            # Coroa de chamas no Boss
            if self.type == 'Boss':
                for fi in range(5):
                    fx = mx - 14 + fi * 7
                    fh = 8 + int(math.sin(t * 0.2 + fi) * 4)
                    pygame.draw.polygon(surface, (255, 120 + fi * 20, 0),
                                        [(fx, my - fh), (fx - 4, my), (fx + 4, my)])

        # Barra de HP (acima do monstro)
        bar_w = self.width + 8
        bx2 = int(self.x) - 4
        hp_pct = max(0, self.hp / self.max_hp)
        hp_col = (80, 200, 80) if hp_pct > 0.6 else (220, 200, 30) if hp_pct > 0.3 else (220, 60, 60)
        pygame.draw.rect(surface, (30, 10, 10), (bx2, int(self.y) - 12, bar_w, 6), border_radius=3)
        pygame.draw.rect(surface, hp_col, (bx2, int(self.y) - 12, int(bar_w * hp_pct), 6), border_radius=3)
        pygame.draw.rect(surface, (120, 120, 120), (bx2, int(self.y) - 12, bar_w, 6), 1, border_radius=3)
        # Nome
        name_surf = font_hud.render(self.name, True, (200, 200, 200))
        surface.blit(name_surf, (mx - name_surf.get_width() // 2, int(self.y) - 26))

class Door:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.width = 50.0
        self.height = 80.0
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
    
    def draw(self, surface):
        rx, ry = int(self.x), int(self.y)
        rw, rh = int(self.width), int(self.height)
        # Moldura de pedra
        pygame.draw.rect(surface, (40, 28, 12), (rx - 5, ry - 5, rw + 10, rh + 5), border_radius=3)
        # Porta principal
        pygame.draw.rect(surface, (90, 50, 15), (rx, ry, rw, rh), border_radius=4)
        pygame.draw.rect(surface, (60, 35, 8), (rx + 3, ry + 3, rw - 6, rh - 3), border_radius=3)
        # Tábuas horizontais
        for ty in range(ry + 10, ry + rh - 5, 12):
            pygame.draw.line(surface, (45, 25, 5), (rx + 4, ty), (rx + rw - 4, ty), 1)
        # Dobradiças
        for hy in [ry + 12, ry + rh - 20]:
            pygame.draw.rect(surface, (180, 140, 40), (rx + 2, hy, 6, 8), border_radius=2)
        # Maçaneta dourada brilhante
        pygame.draw.circle(surface, (255, 215, 0), (rx + rw - 8, ry + rh // 2), 6)
        pygame.draw.circle(surface, (255, 240, 160), (rx + rw - 9, ry + rh // 2 - 1), 2)
        # Brilho mágico no arco superior (pulsa)
        glow_alpha = 80 + int(math.sin(pygame.time.get_ticks() * 0.003) * 40)
        glow_surf = pygame.Surface((rw + 10, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (100, 200, 255, glow_alpha), (0, 0, rw + 10, 20))
        surface.blit(glow_surf, (rx - 5, ry - 12))

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
        rx, ry = self.x, self.y
        rw, rh = self.width, self.height
        if self.opened:
            # Baú aberto
            pygame.draw.rect(surface, (100, 75, 15), (rx, ry + 8, rw, rh - 8), border_radius=3)
            pygame.draw.rect(surface, (140, 105, 25), (rx, ry, rw, 10), border_radius=3)
            pygame.draw.line(surface, (200, 170, 50), (rx + 2, ry + 4), (rx + rw - 2, ry + 4), 1)
            # Brilho de XP saindo
            for gi in range(3):
                gx = rx + rw // 2 + int(math.sin(pygame.time.get_ticks() * 0.005 + gi) * 8)
                gy = ry - gi * 6
                gs = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(gs, (255, 215, 0, 120 - gi * 35), (4, 4), 4)
                surface.blit(gs, (gx - 4, gy))
        else:
            # Baú fechado
            pygame.draw.rect(surface, (160, 110, 20), (rx + 1, ry + 1, rw, rh), border_radius=3)  # sombra
            pygame.draw.rect(surface, (218, 165, 32), (rx, ry, rw, rh), border_radius=3)
            pygame.draw.rect(surface, (180, 135, 22), (rx, ry + rh // 2, rw, 3))
            pygame.draw.rect(surface, (240, 200, 80), (rx + 3, ry + 3, rw - 6, rh // 2 - 3), border_radius=2)
            # Fechadura
            pygame.draw.circle(surface, (255, 240, 100), (rx + rw // 2, ry + rh // 2 + 1), 4)
            pygame.draw.circle(surface, (180, 140, 10), (rx + rw // 2, ry + rh // 2 + 1), 2)
            # Rebites nos cantos
            for cx2, cy2 in [(rx + 3, ry + 3), (rx + rw - 5, ry + 3),
                             (rx + 3, ry + rh - 5), (rx + rw - 5, ry + rh - 5)]:
                pygame.draw.circle(surface, (255, 220, 60), (cx2, cy2), 3)

class DamageFloater:
    """Número de dano/cura que flutua na tela."""
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.timer = 0
        self.lifetime = 55
        self.vy = -1.8

    def update(self):
        self.y += self.vy
        self.vy *= 0.95
        self.timer += 1
        return self.timer < self.lifetime

    def draw(self, surface):
        alpha = max(0, 255 - int((self.timer / self.lifetime) * 255))
        surf = font_small.render(self.text, True, self.color)
        s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        s.blit(surf, (0, 0))
        s.set_alpha(alpha)
        surface.blit(s, (int(self.x) - surf.get_width() // 2, int(self.y)))


class Combat:
    """
    Sistema de combate por turnos expandido.

    Fases: 'player_turn' | 'player_anim' | 'monster_anim' | 'skill_anim'
           | 'flee_anim' | 'victory' | 'defeat'

    Habilidades do player (custo MP):
      0 – Atacar       (0 MP) – ataque físico normal
      1 – Golpe Forte  (8 MP) – 1.8× dano, chance de 20% crítico bônus
      2 – Escudo Mágico(6 MP) – reduz defesa do monstro por 2 turnos E recupera 5 MP
      3 – Cura Divina  (10 MP)– cura 45 HP + 8 MP
      4 – Pocao HP     (item)
      5 – Fugir

    Mecânicas especiais:
      • Crítico: 15% de chance de 2× dano (mostra "CRITICO!")
      • Enfraquecido: status no monstro (-30% ATK por 2 turnos)
      • Vulnerável: status no monstro (-30% DEF por 2 turnos)
      • Monstro usa ataque especial quando HP < 40% (mais forte, efeito visual diferente)
      • Contador de turnos e streak de acertos
      • Floaters de dano animados
      • Arena animada com partículas de batalha
    """

    # ── Definição de habilidades ──────────────────────────────────────────────
    # SKILLS base — substituído dinamicamente em get_skills()
    SKILLS = [
        ("ATACAR",     0,   "Ataque fisico basico",         (60,  40, 120)),
        ("GOLPE FORTE",8,   "1.8x dano, chance crit extra", (120, 40,  20)),
        ("ESCUDO MAG.",6,   "Enfraquece inimigo 3 turnos",  (20,  80, 140)),
        ("CURA DIVINA",10,  "+45 HP  +8 MP",                (20, 110,  60)),
        ("POCAO HP",   0,   "Usa pocao de vida (+30 HP)",   (80,  60,  20)),
        ("FUGIR",      0,   "Tenta escapar do combate",     (50,  50,  50)),
    ]

    def get_skills(self):
        """Retorna lista de habilidades, substituindo pelas especiais se desbloqueadas."""
        unlocked = getattr(self.player, 'unlocked_skills', set())
        s1 = ("BLITZ SOMBRIO",  12, "3x ataques rapidos",       (180, 40,  40)) if 'blitz'   in unlocked else self.SKILLS[1]
        s2 = ("METEORO",        18, "2.5x dano, ignora DEF",    (200,100,  20)) if 'meteor'  in unlocked else self.SKILLS[2]
        s3 = ("DRENAR VIDA",    10, "Rouba 25% do dano causado",(120, 40, 200)) if 'drain'   in unlocked else self.SKILLS[3]
        s4_name = "BARREIRA"  if ('barrier' in unlocked and not getattr(self.player,'barrier_active',False)) else "POCAO HP"
        s4_mp   = 15          if ('barrier' in unlocked and not getattr(self.player,'barrier_active',False)) else 0
        s4_desc = "Absorve 1 ataque inimigo" if ('barrier' in unlocked and not getattr(self.player,'barrier_active',False)) else "Usa pocao de vida (+30 HP)"
        s4_col  = (40,100,200) if ('barrier' in unlocked and not getattr(self.player,'barrier_active',False)) else (80,60,20)
        return [self.SKILLS[0], s1, s2, s3, (s4_name,s4_mp,s4_desc,s4_col), self.SKILLS[5]]

    def __init__(self, player, monster):
        self.player  = player
        self.monster = monster

        self.phase           = 'player_turn'
        self.selected_option = 0
        self.log             = []
        self.anim_timer      = 0
        self.show_victory    = False
        self.victory_timer   = 0
        self.xp_gained       = 0
        self.items_dropped   = []
        self.flash_color     = None
        self.flash_timer     = 0
        self.flee_fail_damage = 0

        # Floaters de dano
        self.floaters: list[DamageFloater] = []

        # Partículas da arena
        self.arena_particles = []

        # Status effects
        self.monster_weakened  = 0   # turnos restantes de ATK-30%
        self.monster_vulnerable = 0  # turnos restantes de DEF-30%
        self.player_shielded   = 0   # turnos restantes de DEF+50% (futuro)

        # Stats de combate
        self.turn_count   = 0
        self.hit_streak   = 0
        self.last_action  = ""        # texto descritivo da última ação
        self.action_flash = 0         # frames para mostrar a ação

        # Animação de ataque do player (posição de sprite)
        self.player_anim_x   = 0     # deslocamento horizontal do sprite do player
        self.monster_anim_x  = 0     # tremor do monstro
        self.monster_hp_prev = monster.hp  # para animar a barra

        # Se monstro entrou em fúria (HP < 40%)
        self.monster_enraged = False

        self.log.append(f"Encontrou {self.monster.name}! (Lv.{self.monster.level})")
        self._spawn_arena_particles(8)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _spawn_arena_particles(self, n, color=None):
        col = color or (80, 60, 160)
        cx = SCREEN_WIDTH // 2
        for _ in range(n):
            self.arena_particles.append({
                'x': cx + random.randint(-200, 200),
                'y': random.randint(80, 500),
                'vx': random.uniform(-0.6, 0.6),
                'vy': random.uniform(-0.8, -0.2),
                'life': random.randint(40, 90),
                'max_life': 90,
                'r': random.randint(2, 5),
                'col': col,
            })

    def _add_floater(self, x, y, text, color):
        self.floaters.append(DamageFloater(x + random.randint(-15, 15), y, text, color))

    def _raw_monster_attack(self):
        base = self.monster.attack
        if self.monster_weakened > 0:
            base = int(base * 0.70)
        dmg = max(1, base - self.player.defense + random.randint(-2, 4))
        # fúria: +40% quando HP < 40%
        if self.monster_enraged:
            dmg = int(dmg * 1.40)
        return dmg

    def _start_monster_turn(self):
        self._tick_status_effects()
        # Verificar se entrou em fúria agora
        hp_ratio = self.monster.hp / self.monster.max_hp
        if hp_ratio < 0.40 and not self.monster_enraged:
            self.monster_enraged = True
            self.log.append(f"{self.monster.name} entrou em FURIA! (+40% ATK)")
            self._spawn_arena_particles(12, (220, 60, 20))
        self.phase = 'monster_anim'
        self.anim_timer = 0

    def _tick_status_effects(self):
        if self.monster_weakened  > 0: self.monster_weakened  -= 1
        if self.monster_vulnerable > 0: self.monster_vulnerable -= 1

    def _resolve_victory(self):
        self.show_victory  = True
        self.phase         = 'victory'
        self.victory_timer = 0
        self.xp_gained     = self.monster.xp_reward
        if self.hit_streak >= 3:
            bonus = int(self.xp_gained * 0.25)
            self.xp_gained += bonus
            self.log.append(f"Bonus de streak! +{bonus} XP extra!")
        self.player.gain_xp(self.xp_gained)
        if random.random() < 0.40: self.items_dropped.append('health_potion')
        if random.random() < 0.30: self.items_dropped.append('mana_potion')
        for item in self.items_dropped:
            self.player.inventory[item] = self.player.inventory.get(item, 0) + 1
        drop_msg = ""
        if self.items_dropped:
            drop_msg = " | Drop: " + ", ".join(
                "Poc.HP" if i == 'health_potion' else "Poc.MP" for i in self.items_dropped)
        self.log.append(f"Vitoria! +{self.xp_gained} XP{drop_msg}")
        self._spawn_arena_particles(20, (220, 180, 0))

    # ── update ────────────────────────────────────────────────────────────────

    def update(self):
        self.anim_timer += 1
        if self.flash_timer  > 0: self.flash_timer  -= 1
        if self.action_flash > 0: self.action_flash -= 1

        # Atualizar partículas da arena
        self.arena_particles = [
            p for p in self.arena_particles
            if (p.update_fn(p) or True) and p['life'] > 0
        ] if False else []  # desativado abaixo — usa loop separado
        alive_parts = []
        for p in self.arena_particles:
            p['x']    += p['vx']
            p['y']    += p['vy']
            p['life'] -= 1
            if p['life'] > 0:
                alive_parts.append(p)
        self.arena_particles = alive_parts

        # Atualizar floaters
        self.floaters = [f for f in self.floaters if f.update()]

        # Animar sprite do player (avança durante player_anim)
        if self.phase == 'player_anim':
            progress = min(1.0, self.anim_timer / 15)
            if self.anim_timer < 15:
                self.player_anim_x = int(progress * 60)
            else:
                self.player_anim_x = max(0, 60 - int((self.anim_timer - 15) * 6))
        else:
            self.player_anim_x = 0

        # Animar tremor do monstro
        if self.phase == 'monster_anim' and self.anim_timer < 20:
            self.monster_anim_x = random.randint(-4, 4)
        else:
            self.monster_anim_x = 0

        # ── victory ──────────────────────────────────────────────────────────
        if self.phase == 'victory':
            self.victory_timer += 1
            if self.victory_timer > 130:
                return 'victory_done'
            return True

        # ── player_anim → monster counter ────────────────────────────────────
        if self.phase == 'player_anim':
            if self.anim_timer >= 35:
                self.anim_timer = 0
                if not self.monster.alive:
                    self._resolve_victory()
                else:
                    self._start_monster_turn()
            return None

        # ── skill_anim (habilidades especiais — delay visual extra) ──────────
        if self.phase == 'skill_anim':
            if self.anim_timer >= 40:
                self.anim_timer = 0
                if not self.monster.alive:
                    self._resolve_victory()
                else:
                    self._start_monster_turn()
            return None

        # ── monster_anim ─────────────────────────────────────────────────────
        if self.phase == 'monster_anim':
            if self.anim_timer >= 40:
                # Barreira bloqueia o ataque
                if getattr(self.player, 'barrier_active', False):
                    self.player.barrier_active = False
                    self.log.append("BARREIRA absorveu o ataque do inimigo!")
                    self._add_floater(350, 310, "BLOQUEADO!", (80,160,255))
                    self._spawn_arena_particles(8, (60,140,255))
                    self.flash_color=(60,140,255); self.flash_timer=8
                    self.anim_timer=0; self.phase='player_turn'
                    return None
                damage = self._raw_monster_attack()
                # Ataque especial quando em fúria
                is_special = self.monster_enraged and random.random() < 0.35
                if is_special:
                    damage = int(damage * 1.5)
                    self.log.append(f"{self.monster.name} usa ATAQUE ESPECIAL! -{damage} HP")
                    self.flash_color = (200, 100, 255)
                    self._spawn_arena_particles(8, (200, 80, 255))
                else:
                    self.log.append(f"{self.monster.name} ataca! -{damage} HP")
                    self.flash_color = COLORS['damage']
                self.player.get_damage_combat(damage)
                self.flash_timer = 10
                self._add_floater(350, 320, f"-{damage}", (255, 90, 90))
                self.anim_timer = 0
                if self.player.hp <= 0:
                    self.phase = 'defeat'
                    return 'game_over'
                self.phase = 'player_turn'
            return None

        # ── flee_anim ────────────────────────────────────────────────────────
        if self.phase == 'flee_anim':
            if self.anim_timer >= 45:
                self.anim_timer = 0
                damage = self.flee_fail_damage
                self.player.get_damage_combat(damage)
                self.flash_color = COLORS['damage']
                self.flash_timer = 10
                self.log.append(f"{self.monster.name} bloqueia! -{damage} HP")
                self._add_floater(350, 320, f"-{damage}", (255, 90, 90))
                if self.player.hp <= 0:
                    self.phase = 'defeat'
                    return 'game_over'
                self.phase = 'player_turn'
            return None

        return None

    # ── actions ──────────────────────────────────────────────────────────────

    def player_attack(self):
        """Ataque básico (opção 0)."""
        if self.phase != 'player_turn': return
        self.turn_count += 1
        mon_def = max(0, getattr(self.monster, 'defense', 0) -
                      (int(self.monster.defense * 0.30) if self.monster_vulnerable > 0 else 0))
        damage  = max(1, self.player.attack - mon_def + random.randint(-2, 5))
        # Crítico 15%
        crit = random.random() < 0.15
        if crit:
            damage = int(damage * 2.0)
            self.log.append(f"CRITICO! Voce ataca {self.monster.name}! -{damage} HP")
            self._add_floater(820, 250, f"CRIT! -{damage}", (255, 230, 50))
            self._spawn_arena_particles(6, (255, 220, 50))
            self.hit_streak += 1
        else:
            self.log.append(f"Voce ataca {self.monster.name}! -{damage} HP")
            self._add_floater(820, 250, f"-{damage}", (255, 180, 80))
            self.hit_streak += 1
        self.monster.take_damage(damage)
        self.flash_color = COLORS['xp_gold']
        self.flash_timer = 6
        self.last_action = "ATAQUE" + (" CRITICO!" if crit else "")
        self.action_flash = 30
        self.monster_hp_prev = self.monster.hp
        self.phase = 'player_anim'
        self.anim_timer = 0

    def player_heavy_attack(self):
        """Golpe Forte — 8 MP, 1.8× dano."""
        if self.phase != 'player_turn': return
        if self.player.mp < 8:
            self.log.append("MP insuficiente para Golpe Forte!")
            return
        self.player.mp -= 8
        self.turn_count += 1
        mon_def = max(0, getattr(self.monster, 'defense', 0) -
                      (int(self.monster.defense * 0.30) if self.monster_vulnerable > 0 else 0))
        damage = int(max(1, self.player.attack - mon_def + random.randint(0, 6)) * 1.8)
        crit = random.random() < 0.20  # chance extra de crit
        if crit:
            damage = int(damage * 1.5)
            self.log.append(f"GOLPE FORTE CRITICO em {self.monster.name}! -{damage} HP")
            self._add_floater(820, 240, f"CRIT FORTE -{damage}", (255, 100, 30))
        else:
            self.log.append(f"Golpe Forte em {self.monster.name}! -{damage} HP")
            self._add_floater(820, 240, f"FORTE -{damage}", (255, 140, 40))
        self._spawn_arena_particles(8, (255, 100, 20))
        self.monster.take_damage(damage)
        self.flash_color = (255, 120, 20)
        self.flash_timer = 8
        self.hit_streak += 1
        self.last_action = "GOLPE FORTE"
        self.action_flash = 30
        self.monster_hp_prev = self.monster.hp
        self.phase = 'skill_anim'
        self.anim_timer = 0

    def player_weaken(self):
        """Escudo Mágico — 6 MP, enfraquece inimigo 2 turnos."""
        if self.phase != 'player_turn': return
        if self.player.mp < 6:
            self.log.append("MP insuficiente para Escudo Magico!")
            return
        self.player.mp -= 6
        self.player.mp = min(self.player.max_mp, self.player.mp + 5)  # devolve 5 MP como regeneração
        self.monster_weakened   = 3
        self.monster_vulnerable = 3
        self.turn_count += 1
        self.hit_streak = 0
        self.log.append(f"Escudo Magico! {self.monster.name} enfraquecido por 3 turnos! (+5 MP regen)")
        self._add_floater(820, 260, "ENFRAQUECIDO!", (100, 200, 255))
        self._spawn_arena_particles(10, (60, 160, 255))
        self.flash_color = (80, 160, 255)
        self.flash_timer = 8
        self.last_action = "ESCUDO MAGICO"
        self.action_flash = 30
        self.phase = 'skill_anim'
        self.anim_timer = 0

    def player_divine_heal(self):
        """Cura Divina — 10 MP, cura 45 HP + regenera 8 MP."""
        if self.phase != 'player_turn': return
        if self.player.mp < 10:
            self.log.append("MP insuficiente para Cura Divina!")
            return
        self.player.mp -= 10
        heal_amount = 45
        self.player.heal(heal_amount)
        self.player.mp = min(self.player.max_mp, self.player.mp + 8)
        self.turn_count += 1
        self.hit_streak = 0
        self.log.append(f"Cura Divina! +{heal_amount} HP  +8 MP")
        self._add_floater(350, 320, f"+{heal_amount} HP", (80, 255, 120))
        self._spawn_arena_particles(10, (80, 230, 120))
        self.flash_color = (60, 220, 100)
        self.flash_timer = 8
        self.last_action = "CURA DIVINA"
        self.action_flash = 30
        self._start_monster_turn()

    def player_item(self, item):
        if self.phase != 'player_turn': return
        if self.player.use_item(item):
            if item == 'health_potion':
                self.log.append("Pocao de Vida! +30 HP")
                self._add_floater(350, 320, "+30 HP", (80, 230, 100))
            elif item == 'mana_potion':
                self.log.append("Pocao de Mana! +20 MP")
                self._add_floater(350, 320, "+20 MP", (80, 160, 255))
            self.hit_streak = 0
            self.turn_count += 1
            self._start_monster_turn()
        else:
            self.log.append("Sem itens disponiveis!")

    def run_away(self):
        if self.phase != 'player_turn': return None
        level_diff  = self.monster.level - self.player.level
        flee_chance = max(0.15, 0.60 - level_diff * 0.08)
        if random.random() < flee_chance:
            self.log.append("Voce fugiu com sucesso!")
            return 'fled'
        else:
            penalty = self._raw_monster_attack()
            self.flee_fail_damage = penalty
            self.log.append(f"Fuga falhou! ({int(flee_chance*100)}% chance)")
            self.phase = 'flee_anim'
            self.anim_timer = 0
            return None

    def player_blitz(self):
        """Blitz Sombrio — 3 ataques rápidos (12 MP)."""
        if self.phase != 'player_turn': return
        if self.player.mp < 12:
            self.log.append("MP insuficiente para Blitz Sombrio!"); return
        self.player.mp -= 12
        self.turn_count += 1
        total = 0
        mon_def = max(0, getattr(self.monster,'defense',0) -
                     (int(self.monster.defense*0.3) if self.monster_vulnerable>0 else 0))
        for i in range(3):
            dmg = max(1, self.player.attack - mon_def + random.randint(-1,4))
            crit_chance = 0.15 + getattr(self.player,'crit_bonus',0)/100
            if random.random() < crit_chance: dmg = int(dmg*2)
            total += dmg
            self.monster.take_damage(dmg)
            if not self.monster.alive: break
        self.log.append(f"BLITZ SOMBRIO! 3 golpes = {total} dano total!")
        self._add_floater(820, 230, f"BLITZ -{total}", (255,60,60))
        self._spawn_arena_particles(12, (220,50,50))
        self.flash_color=(220,50,50); self.flash_timer=10
        self.hit_streak+=1; self.last_action="BLITZ SOMBRIO"; self.action_flash=30
        self.monster_hp_prev=self.monster.hp
        self.phase='skill_anim'; self.anim_timer=0

    def player_meteor(self):
        """Meteoro — 2.5× dano, ignora DEF (18 MP)."""
        if self.phase != 'player_turn': return
        if self.player.mp < 18:
            self.log.append("MP insuficiente para Meteoro!"); return
        self.player.mp -= 18
        self.turn_count += 1
        damage = int(self.player.attack * 2.5 + random.randint(5,15))
        self.log.append(f"METEORO em {self.monster.name}! -{damage} HP (ignora DEF)")
        self._add_floater(820, 225, f"METEORO -{damage}", (255,140,0))
        self._spawn_arena_particles(15, (255,120,0))
        self.monster.take_damage(damage)
        self.flash_color=(255,120,0); self.flash_timer=12
        self.hit_streak+=1; self.last_action="METEORO"; self.action_flash=30
        self.monster_hp_prev=self.monster.hp
        self.phase='skill_anim'; self.anim_timer=0

    def player_drain(self):
        """Drenar Vida — rouba 25% do dano causado como HP (10 MP)."""
        if self.phase != 'player_turn': return
        if self.player.mp < 10:
            self.log.append("MP insuficiente para Drenar Vida!"); return
        self.player.mp -= 10
        self.turn_count += 1
        mon_def = max(0, getattr(self.monster,'defense',0) -
                     (int(self.monster.defense*0.3) if self.monster_vulnerable>0 else 0))
        damage = max(1, self.player.attack - mon_def + random.randint(-1,5))
        stolen = int(damage * 0.25)
        self.player.heal(stolen)
        self.monster.take_damage(damage)
        self.log.append(f"DRENAR VIDA! -{damage} HP ao inimigo, +{stolen} HP para voce!")
        self._add_floater(820, 240, f"DRENAR -{damage}", (150,50,220))
        self._add_floater(350, 320, f"+{stolen} HP", (180,100,255))
        self._spawn_arena_particles(8, (140,40,200))
        self.flash_color=(140,40,200); self.flash_timer=8
        self.hit_streak+=1; self.last_action="DRENAR VIDA"; self.action_flash=30
        self.monster_hp_prev=self.monster.hp
        self.phase='skill_anim'; self.anim_timer=0

    def player_barrier(self):
        """Barreira Arcana — absorve o próximo ataque (15 MP)."""
        if self.phase != 'player_turn': return
        if self.player.mp < 15:
            self.log.append("MP insuficiente para Barreira Arcana!"); return
        self.player.mp -= 15
        self.player.barrier_active = True
        self.turn_count += 1
        self.hit_streak = 0
        self.log.append("BARREIRA ARCANA ativada! Proximo ataque sera absorvido!")
        self._add_floater(350, 300, "BARREIRA!", (80,160,255))
        self._spawn_arena_particles(10, (60,140,255))
        self.flash_color=(60,140,255); self.flash_timer=8
        self.last_action="BARREIRA ARCANA"; self.action_flash=30
        self._start_monster_turn()

    # ── draw helpers ─────────────────────────────────────────────────────────

    def _draw_hp_bar(self, surface, x, y, w, h, current, maximum, color, bg_color=(40,10,10)):
        pct = max(0.0, current / maximum)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=4)
        if pct > 0:
            filled_w = int(w * pct)
            pygame.draw.rect(surface, color, (x, y, filled_w, h), border_radius=4)
            # brilho no topo da barra
            highlight = tuple(min(255, c + 60) for c in color)
            pygame.draw.rect(surface, highlight, (x, y, filled_w, max(1, h // 3)), border_radius=4)
        pygame.draw.rect(surface, (100, 100, 130), (x, y, w, h), 1, border_radius=4)

    def _draw_status_icons(self, surface, x, y):
        """Mostra ícones de status do monstro."""
        ix = x
        if self.monster_weakened > 0:
            s = font_hud.render(f"FRACO({self.monster_weakened})", True, (100, 200, 255))
            pygame.draw.rect(surface, (10, 30, 60), (ix - 2, y - 2, s.get_width() + 6, s.get_height() + 4), border_radius=3)
            surface.blit(s, (ix + 2, y))
            ix += s.get_width() + 12
        if self.monster_vulnerable > 0:
            s = font_hud.render(f"VULN({self.monster_vulnerable})", True, (255, 180, 60))
            pygame.draw.rect(surface, (50, 20, 0), (ix - 2, y - 2, s.get_width() + 6, s.get_height() + 4), border_radius=3)
            surface.blit(s, (ix + 2, y))
            ix += s.get_width() + 12
        if self.monster_enraged:
            s = font_hud.render("FURIOSO", True, (255, 60, 30))
            pygame.draw.rect(surface, (60, 10, 0), (ix - 2, y - 2, s.get_width() + 6, s.get_height() + 4), border_radius=3)
            surface.blit(s, (ix + 2, y))

    def _draw_monster_sprite(self, surface, cx, cy, size=90):
        """Desenha sprite escalado do monstro na arena de combate."""
        t  = self.anim_timer
        sx = self.monster_anim_x
        # avança ao ser atacado pelo player
        if self.phase == 'player_anim':
            sx += int(math.sin(t * 0.6) * 6)

        col   = self.monster.color
        dark  = tuple(max(0, c - 50) for c in col)
        light = tuple(min(255, c + 70) for c in col)
        bounce = int(math.sin(t * 0.08) * 5)
        my    = cy + bounce

        mtype = self.monster.type
        if mtype == 'slime':
            bw = size + int(math.sin(t * 0.07) * 8)
            bh = int(size * 0.65) + int(math.sin(t * 0.07) * 6)
            by = my + size - bh
            pygame.draw.ellipse(surface, dark,  (cx - bw//2 + 3 + sx, by + 3, bw, bh))
            pygame.draw.ellipse(surface, col,   (cx - bw//2 + sx,     by,     bw, bh))
            pygame.draw.ellipse(surface, light, (cx - bw//2 + 10 + sx, by + 6, bw//2, bh//3))
            ey = by + bh//3
            for ex2 in [cx - 16 + sx, cx + 16 + sx]:
                pygame.draw.circle(surface, (0,0,0), (ex2, ey), 8)
                pygame.draw.circle(surface, (255,60,60), (ex2, ey), 6)
                pygame.draw.circle(surface, (255,200,200), (ex2 - 2, ey - 2), 2)
        elif mtype == 'goblin':
            pygame.draw.rect(surface, dark, (cx - 18 + sx, my + 30, 36, 35), border_radius=5)
            pygame.draw.rect(surface, col,  (cx - 20 + sx, my + 28, 40, 35), border_radius=5)
            pygame.draw.circle(surface, col,   (cx + sx, my + 16), 22)
            pygame.draw.circle(surface, light, (cx - 6 + sx, my + 8), 10)
            pygame.draw.polygon(surface, dark, [(cx-22+sx, my+10),(cx-32+sx,my-6),(cx-12+sx,my+4)])
            pygame.draw.polygon(surface, dark, [(cx+22+sx, my+10),(cx+32+sx,my-6),(cx+12+sx,my+4)])
            for ex2 in [cx-8+sx, cx+8+sx]:
                pygame.draw.circle(surface, (255,220,0), (ex2, my+14), 7)
                pygame.draw.circle(surface, (0,0,0),     (ex2, my+14), 4)
            for dx in [-6,0,6]:
                pygame.draw.rect(surface, (240,240,210),(cx+dx-3+sx,my+28,4,7))
        elif mtype == 'skeleton':
            pygame.draw.rect(surface, dark, (cx-18+sx,my+28,16,30),border_radius=3)
            pygame.draw.rect(surface, dark, (cx+ 2+sx,my+28,16,30),border_radius=3)
            pygame.draw.circle(surface, col, (cx-10+sx,my+30),8)
            pygame.draw.circle(surface, col, (cx+10+sx,my+30),8)
            pygame.draw.rect(surface, dark,(cx-20+sx,my+10,40,22),border_radius=4)
            for ry3 in range(my+12, my+30, 7):
                pygame.draw.line(surface, col,(cx-18+sx,ry3),(cx+18+sx,ry3),2)
            pygame.draw.circle(surface, col,  (cx+sx, my+6), 20)
            pygame.draw.circle(surface, light,(cx-6+sx,my), 9)
            for ex2, eo in [(cx-8+sx,0),(cx+8+sx,0)]:
                pygame.draw.ellipse(surface,(20,20,20),(ex2-7,my+1,13,14))
                pygame.draw.circle(surface,(180,50,220),(ex2+eo,my+7),4)
            aa = int(math.sin(t*0.10)*8)
            pygame.draw.line(surface,col,(cx-20+sx,my+18),(cx-32+sx,my+36+aa),5)
            pygame.draw.line(surface,col,(cx+20+sx,my+18),(cx+32+sx,my+36-aa),5)
        else:  # orc / Boss
            is_boss = mtype == 'Boss'
            bw = size + (14 if is_boss else 0)
            pygame.draw.rect(surface, dark, (cx-bw//2+3+sx,my+22,bw,40),border_radius=6)
            pygame.draw.rect(surface, col,  (cx-bw//2+sx,  my+18,bw,40),border_radius=6)
            pygame.draw.rect(surface, light,(cx-bw//2+8+sx,my+20,bw//2,14),border_radius=4)
            aa2 = int(math.sin(t*0.09)*7)
            pygame.draw.ellipse(surface,col,(cx-bw//2-14+sx,my+20+aa2,16,30))
            pygame.draw.ellipse(surface,col,(cx+bw//2- 2+sx,my+20-aa2,16,30))
            pygame.draw.rect(surface, dark,(cx-bw//2+2+sx,my+56,bw//2-2,26),border_radius=4)
            pygame.draw.rect(surface, dark,(cx+2+sx,       my+56,bw//2-2,26),border_radius=4)
            pygame.draw.circle(surface, col,  (cx+sx, my+10), 22)
            pygame.draw.circle(surface, light,(cx-6+sx,my+2),10)
            for ex2 in [cx-8+sx,cx+8+sx]:
                pygame.draw.circle(surface,(255,60,0),(ex2,my+8),7)
                pygame.draw.circle(surface,(80,0,0),  (ex2,my+8),4)
            for pts in [[(cx-7+sx,my+22),(cx-5+sx,my+32),(cx-3+sx,my+22)],
                        [(cx+3+sx, my+22),(cx+5+sx,my+32),(cx+7+sx, my+22)]]:
                pygame.draw.polygon(surface,(220,220,200),pts)
            if is_boss:
                for fi in range(6):
                    fx = cx - 20 + fi * 8 + sx
                    fh = 12 + int(math.sin(t*0.15+fi)*6)
                    pygame.draw.polygon(surface,(255,100+fi*20,0),
                                        [(fx,my-fh),(fx-5,my),(fx+5,my)])

        # Brilho de hit
        if self.flash_timer > 4 and self.flash_color == COLORS['xp_gold']:
            hit_surf = pygame.Surface((size+20,size+20),pygame.SRCALPHA)
            pygame.draw.ellipse(hit_surf,(255,255,150,80),(0,0,size+20,size+20))
            surface.blit(hit_surf,(cx-size//2-10+sx,my-10))

    def _draw_player_sprite(self, surface, cx, cy):
        """Sprite do player no lado direito da arena."""
        t  = self.anim_timer
        px = cx + self.player_anim_x  # avança durante o ataque
        by = cy
        bob = int(math.sin(t * 0.07) * 4)
        py = by + bob

        # cores
        bc  = (233, 69, 96)
        dc  = (160, 40, 65)
        lc  = (255, 130, 150)
        ac  = (40, 60, 110)
        alc = (70, 100, 170)

        # sombra
        sh = pygame.Surface((52, 7), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,50), (0,0,52,7))
        surface.blit(sh, (px-26, py+72))

        # pernas
        ls = int(math.sin(t*0.15)*10) if self.phase in ('player_anim','skill_anim') else 0
        pygame.draw.rect(surface, dc, (px-18, py+50, 12, 24), border_radius=3)
        pygame.draw.rect(surface, dc, (px+6,  py+50, 12, 24), border_radius=3)
        pygame.draw.rect(surface, (20,20,40), (px-19, py+67, 14, 9), border_radius=2)
        pygame.draw.rect(surface, (20,20,40), (px+5,  py+67, 14, 9), border_radius=2)

        # corpo
        pygame.draw.rect(surface, ac,  (px-16, py+22, 32, 32), border_radius=5)
        pygame.draw.rect(surface, alc, (px-12, py+25, 16, 10), border_radius=3)
        pygame.draw.line(surface, alc, (px, py+27), (px, py+50), 2)

        # braços
        arm_s = int(math.sin(t*0.15)*8) if self.phase in ('player_anim','skill_anim') else 0
        pygame.draw.rect(surface, bc, (px-26, py+26+arm_s, 11, 22), border_radius=3)
        pygame.draw.rect(surface, bc, (px+15, py+26-arm_s, 11, 22), border_radius=3)

        # cabeça
        pygame.draw.circle(surface, bc,  (px, py+12), 16)
        pygame.draw.circle(surface, lc,  (px-4, py+7), 7)
        # capacete
        helm = [(px-14,py+10),(px-10,py-4),(px,py-8),(px+10,py-4),(px+14,py+10)]
        pygame.draw.polygon(surface, ac, helm)
        pygame.draw.polygon(surface, alc, helm, 1)
        # olho
        pygame.draw.circle(surface, (255,255,255),(px+6,py+13),6)
        pygame.draw.circle(surface, (20,20,80),   (px+7,py+13),3)
        pygame.draw.circle(surface, (255,255,255),(px+8,py+12),1)

        # espada (visível durante ataque)
        if self.phase in ('player_anim', 'skill_anim'):
            sword_glow = pygame.Surface((60, 12), pygame.SRCALPHA)
            pygame.draw.rect(sword_glow, (255, 230, 80, 160), (0, 2, 55, 8), border_radius=4)
            surface.blit(sword_glow, (px + 14, py + 25))
            pygame.draw.rect(surface, (200, 200, 230), (px+14, py+27, 50, 5), border_radius=2)
            pygame.draw.polygon(surface, (255,240,120), [(px+64,py+27),(px+64,py+32),(px+72,py+30)])

    # ── draw principal ────────────────────────────────────────────────────────

    def draw(self, surface):
        t = self.anim_timer

        # ── overlay escuro ───────────────────────────────────────────────────
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # ── flash de impacto ─────────────────────────────────────────────────
        if self.flash_timer > 0 and self.flash_color:
            alpha = int(130 * (self.flash_timer / 10))
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((*self.flash_color, alpha))
            surface.blit(flash, (0, 0))

        # ── arena de batalha (painel central largo) ──────────────────────────
        BOX_W, BOX_H = 1100, 640
        BOX_X = (SCREEN_WIDTH - BOX_W) // 2
        BOX_Y = (SCREEN_HEIGHT - BOX_H) // 2

        # Fundo da arena com gradiente
        arena_bg = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
        for row in range(BOX_H):
            ratio = row / BOX_H
            r = int(8  + ratio * 18)
            g = int(6  + ratio * 12)
            b = int(22 + ratio * 28)
            pygame.draw.rect(arena_bg, (r, g, b, 230), (0, row, BOX_W, 1))
        surface.blit(arena_bg, (BOX_X, BOX_Y))

        # Borda com glow colorido
        glow_col = (255, 200, 0) if self.phase == 'victory' \
                   else (220, 60, 20) if self.monster_enraged \
                   else (60, 100, 180)
        for thick, alpha_val in [(6, 40), (4, 80), (2, 180)]:
            gs = pygame.Surface((BOX_W + thick*2, BOX_H + thick*2), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*glow_col, alpha_val), (0, 0, BOX_W+thick*2, BOX_H+thick*2), thick, border_radius=6)
            surface.blit(gs, (BOX_X - thick, BOX_Y - thick))

        # ── partículas da arena ──────────────────────────────────────────────
        for p in self.arena_particles:
            alpha2 = int(200 * p['life'] / p['max_life'])
            ps = pygame.Surface((p['r']*2, p['r']*2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p['col'], alpha2), (p['r'], p['r']), p['r'])
            surface.blit(ps, (int(p['x']) - p['r'], int(p['y']) - p['r']))

        # ── título / barra de nome ───────────────────────────────────────────
        pygame.draw.rect(surface, (12, 18, 42), (BOX_X, BOX_Y, BOX_W, 52))
        pygame.draw.rect(surface, glow_col, (BOX_X, BOX_Y + 50, BOX_W, 2))
        enrage_tag = "  [FURIOSO]" if self.monster_enraged else ""
        title_txt = font_medium.render(
            f"COMBATE  —  {self.monster.name} (Lv.{self.monster.level}){enrage_tag}  —  Turno {self.turn_count+1}",
            True, (220, 200, 255))
        surface.blit(title_txt, (BOX_X + BOX_W//2 - title_txt.get_width()//2, BOX_Y + 12))

        # ── ZONA DE SPRITES (parte superior, ~metade da caixa) ───────────────
        ARENA_TOP = BOX_Y + 60
        ARENA_H   = 260

        # chão da arena
        floor_y = ARENA_TOP + ARENA_H - 15
        pygame.draw.rect(surface, (20, 28, 55), (BOX_X + 10, floor_y, BOX_W - 20, 14), border_radius=4)
        pygame.draw.rect(surface, (40, 55, 100), (BOX_X + 10, floor_y, BOX_W - 20, 3), border_radius=4)

        # --- Sprite do monstro (esquerda) ---
        mon_cx = BOX_X + 240
        mon_cy = ARENA_TOP + 60
        self._draw_monster_sprite(surface, mon_cx, mon_cy, size=90)

        # HP do monstro acima do sprite
        m_hp_w = 200
        m_hp_x = mon_cx - m_hp_w // 2
        m_hp_y = ARENA_TOP + 8
        hp_col_m = (60,200,80) if self.monster.hp/self.monster.max_hp > 0.6 \
                   else (220,200,30) if self.monster.hp/self.monster.max_hp > 0.3 else (220,60,60)
        self._draw_hp_bar(surface, m_hp_x, m_hp_y, m_hp_w, 14,
                          max(0, self.monster.hp), self.monster.max_hp, hp_col_m)
        hp_label = font_hud.render(f"HP {max(0,self.monster.hp)}/{self.monster.max_hp}", True, (220,220,220))
        surface.blit(hp_label, (m_hp_x + m_hp_w//2 - hp_label.get_width()//2, m_hp_y + 16))
        mon_name_t = font_small.render(self.monster.name, True, (200, 200, 240))
        surface.blit(mon_name_t, (mon_cx - mon_name_t.get_width()//2, m_hp_y + 32))
        # status icons abaixo do nome
        self._draw_status_icons(surface, mon_cx - 80, m_hp_y + 50)

        # --- Sprite do player (direita) ---
        pl_cx = BOX_X + BOX_W - 260
        pl_cy = ARENA_TOP + 70
        self._draw_player_sprite(surface, pl_cx, pl_cy)

        # HP / MP do player acima do sprite
        p_hp_w = 200
        p_hp_x = pl_cx - p_hp_w // 2
        p_hp_y = ARENA_TOP + 8
        hp_pct_p = self.player.hp / self.player.max_hp
        hp_col_p = (60,210,90) if hp_pct_p > 0.6 else (220,200,30) if hp_pct_p > 0.3 else (220,50,50)
        self._draw_hp_bar(surface, p_hp_x, p_hp_y, p_hp_w, 14,
                          self.player.hp, self.player.max_hp, hp_col_p, (10,40,10))
        hp_label_p = font_hud.render(f"HP {self.player.hp}/{self.player.max_hp}", True, (220,220,220))
        surface.blit(hp_label_p, (p_hp_x + p_hp_w//2 - hp_label_p.get_width()//2, p_hp_y + 16))
        self._draw_hp_bar(surface, p_hp_x, p_hp_y + 32, p_hp_w, 8,
                          self.player.mp, self.player.max_mp, (52,152,219), (10,10,50))
        mp_lbl = font_hud.render(f"MP {self.player.mp}/{self.player.max_mp}", True, (140,200,255))
        surface.blit(mp_lbl, (p_hp_x + p_hp_w//2 - mp_lbl.get_width()//2, p_hp_y + 42))
        pl_name_t = font_small.render(f"Lv.{self.player.level} Heroi", True, (200, 220, 255))
        surface.blit(pl_name_t, (pl_cx - pl_name_t.get_width()//2, p_hp_y + 56))

        # --- Stats no centro ---
        stats_cx = BOX_X + BOX_W // 2
        st_y = ARENA_TOP + 30
        atk_eff = self.monster.attack
        if self.monster_weakened > 0: atk_eff = int(atk_eff * 0.70)
        def_eff = getattr(self.monster, 'defense', 0)
        if self.monster_vulnerable > 0: def_eff = int(def_eff * 0.70)
        vs_t = font_medium.render("VS", True, (180, 80, 80))
        surface.blit(vs_t, (stats_cx - vs_t.get_width()//2, st_y + 50))
        streak_col = (255, 220, 50) if self.hit_streak >= 3 else (150, 150, 180)
        streak_t = font_hud.render(f"Streak: {self.hit_streak}x", True, streak_col)
        surface.blit(streak_t, (stats_cx - streak_t.get_width()//2, st_y + 100))
        m_stats = font_hud.render(f"ATK {atk_eff}  DEF {def_eff}", True, (200,150,150))
        surface.blit(m_stats, (stats_cx - m_stats.get_width()//2, st_y + 120))

        # ── Linha divisória ──────────────────────────────────────────────────
        DIV_Y = ARENA_TOP + ARENA_H
        pygame.draw.rect(surface, (40, 55, 100), (BOX_X + 10, DIV_Y, BOX_W - 20, 1))

        # ── ZONA DE AÇÃO (botões + log) ──────────────────────────────────────
        ACTION_Y = DIV_Y + 10
        blocked   = self.phase != 'player_turn'

        # Botões de habilidade (2 linhas × 3 colunas)
        BTN_W, BTN_H = 168, 52
        BTN_COLS     = 3
        BTN_ROWS     = 2
        total_btn_w  = BTN_COLS * BTN_W + (BTN_COLS - 1) * 8
        btn_start_x  = BOX_X + 12
        for idx, (skill_name, mp_cost, skill_desc, btn_base_col) in enumerate(self.get_skills()):
            col_i = idx % BTN_COLS
            row_i = idx // BTN_COLS
            bx    = btn_start_x + col_i * (BTN_W + 8)
            by2   = ACTION_Y + row_i * (BTN_H + 6)
            selected  = (idx == self.selected_option)
            can_use   = True
            if mp_cost > 0 and self.player.mp < mp_cost:
                can_use = False
            if idx == 4 and self.player.inventory.get('health_potion', 0) == 0:
                can_use = False

            # Fundo do botão
            if selected and not blocked:
                bg_col = tuple(min(255, c + 40) for c in btn_base_col)
                border_col = COLORS['xp_gold']
                # glow
                gs2 = pygame.Surface((BTN_W + 8, BTN_H + 8), pygame.SRCALPHA)
                pygame.draw.rect(gs2, (*COLORS['xp_gold'], 50), (0, 0, BTN_W+8, BTN_H+8), border_radius=7)
                surface.blit(gs2, (bx - 4, by2 - 4))
            elif blocked:
                bg_col = (18, 18, 30)
                border_col = (40, 40, 60)
            elif not can_use:
                bg_col = (20, 18, 28)
                border_col = (50, 40, 50)
            else:
                bg_col = btn_base_col
                border_col = tuple(min(255, c + 30) for c in btn_base_col)

            pygame.draw.rect(surface, bg_col, (bx, by2, BTN_W, BTN_H), border_radius=5)
            pygame.draw.rect(surface, border_col, (bx, by2, BTN_W, BTN_H), 2, border_radius=5)

            # Nome da habilidade
            name_col = COLORS['xp_gold'] if selected and not blocked \
                       else (80, 80, 100) if (blocked or not can_use) \
                       else (230, 230, 255)
            name_surf = font_small.render(skill_name, True, name_col)
            surface.blit(name_surf, (bx + BTN_W//2 - name_surf.get_width()//2, by2 + 5))

            # Custo de MP e disponibilidade de item
            if mp_cost > 0:
                mp_col = (100, 200, 255) if self.player.mp >= mp_cost else (180, 60, 60)
                mp_surf = font_hud.render(f"{mp_cost} MP", True, mp_col)
                surface.blit(mp_surf, (bx + BTN_W//2 - mp_surf.get_width()//2, by2 + 30))
            elif idx == 4:
                qty = self.player.inventory.get('health_potion', 0)
                qty_col = (100, 220, 100) if qty > 0 else (150, 60, 60)
                qty_surf = font_hud.render(f"x{qty}", True, qty_col)
                surface.blit(qty_surf, (bx + BTN_W//2 - qty_surf.get_width()//2, by2 + 30))
            else:
                free_surf = font_hud.render("Gratis", True, (100, 180, 100))
                surface.blit(free_surf, (bx + BTN_W//2 - free_surf.get_width()//2, by2 + 30))

        # ── LOG DE COMBATE (coluna direita) ──────────────────────────────────
        LOG_X  = btn_start_x + BTN_COLS * (BTN_W + 8) + 8
        LOG_W  = BOX_X + BOX_W - LOG_X - 10
        LOG_Y  = ACTION_Y
        LOG_H  = BTN_ROWS * (BTN_H + 6) - 2
        pygame.draw.rect(surface, (10, 14, 32), (LOG_X, LOG_Y, LOG_W, LOG_H), border_radius=5)
        pygame.draw.rect(surface, (40, 58, 100), (LOG_X, LOG_Y, LOG_W, LOG_H), 1, border_radius=5)
        log_title = font_hud.render("LOG", True, (80, 110, 160))
        surface.blit(log_title, (LOG_X + 8, LOG_Y + 5))

        visible = self.log[-6:]
        for i, line in enumerate(visible):
            age_frac = (i + 1) / max(1, len(visible))
            brightness = int(100 + age_frac * 155)
            if "CRITICO" in line or "FORTE" in line:
                log_col = (255, 220, 60)
            elif "FURIA" in line or "ESPECIAL" in line:
                log_col = (255, 100, 50)
            elif "ataca!" in line and "Voce" not in line:
                log_col = (255, int(100*age_frac+80), int(80*age_frac+60))
            elif "Voce ataca" in line or "Golpe" in line:
                log_col = (int(100*age_frac+60), 220, int(80*age_frac+60))
            elif "Vitoria" in line or "fugiu" in line:
                log_col = COLORS['xp_gold']
            elif "HP" in line and "+" in line:
                log_col = (80, 230, 120)
            elif "Escudo" in line or "enfraquecido" in line:
                log_col = (100, 200, 255)
            elif "falhou" in line or "bloqueia" in line:
                log_col = (220, 100, 60)
            else:
                log_col = (brightness, brightness, brightness)
            lt = font_hud.render(line, True, log_col)
            surface.blit(lt, (LOG_X + 8, LOG_Y + 20 + i * 19))

        # ── Instrução / status da fase ────────────────────────────────────────
        INST_Y = ACTION_Y + BTN_ROWS * (BTN_H + 6) + 4
        if self.phase == 'player_turn':
            inst = font_hud.render(
                "A/D  Selecionar    ENTER / ESPACO  Confirmar    (W/S  mudar linha)",
                True, (90, 110, 150))
            surface.blit(inst, (BOX_X + BOX_W//2 - inst.get_width()//2, INST_Y))
        else:
            phase_msgs = {
                'player_anim': "Executando acao...",
                'skill_anim':  "Habilidade ativada!",
                'monster_anim': f"{self.monster.name} esta atacando!",
                'flee_anim':   "Tentando fugir...",
            }
            if self.phase in phase_msgs:
                dots = "." * (1 + (t // 8) % 3)
                msg  = phase_msgs[self.phase].rstrip('.') + dots
                col_msg = (220, 80, 60) if 'atacando' in msg else (200, 180, 60)
                anim_txt = font_small.render(msg, True, col_msg)
                surface.blit(anim_txt, (BOX_X + BOX_W//2 - anim_txt.get_width()//2, INST_Y))

        # ── FLOATERS DE DANO ─────────────────────────────────────────────────
        for f in self.floaters:
            f.draw(surface)

        # ── BANNER DE VITÓRIA ─────────────────────────────────────────────────
        if self.phase == 'victory':
            pulse = abs(math.sin(self.victory_timer * 0.07))
            r_v = int(200 + 55 * pulse)
            g_v = int(180 + 35 * pulse)
            vic_bg = pygame.Surface((500, 120), pygame.SRCALPHA)
            pygame.draw.rect(vic_bg, (10, 8, 0, 200), (0, 0, 500, 120), border_radius=10)
            pygame.draw.rect(vic_bg, (r_v, g_v, 0, 200), (0, 0, 500, 120), 3, border_radius=10)
            surface.blit(vic_bg, (SCREEN_WIDTH//2 - 250, BOX_Y + BOX_H - 140))
            vic = font_large.render("VITORIA!", True, (r_v, g_v, 0))
            surface.blit(vic, (SCREEN_WIDTH//2 - vic.get_width()//2, BOX_Y + BOX_H - 130))
            xp_t = font_medium.render(f"+{self.xp_gained} XP", True, COLORS['xp_gold'])
            surface.blit(xp_t, (SCREEN_WIDTH//2 - xp_t.get_width()//2, BOX_Y + BOX_H - 75))
            if self.items_dropped:
                drop_str = "  +  ".join("Pocao HP" if i == 'health_potion' else "Pocao MP"
                                        for i in self.items_dropped)
                dt = font_small.render(f"Drop: {drop_str}", True, (120, 230, 130))
                surface.blit(dt, (SCREEN_WIDTH//2 - dt.get_width()//2, BOX_Y + BOX_H - 42))

# ==================== NARRATIVA E ZONAS ====================

# Historia completa — lista de (speaker, portrait_color, text)
# Acionada por trigger de fase
STORY = {
    # Prólogo (antes da fase 1)
    'prologue': [
        ("Anciao Gareth", (180,160,100), "Jovem... finalmente acordou. Achei que tivesse morrido."),
        ("Anciao Gareth", (180,160,100), "Voce caiu do ceu em chamas ha tres dias. Seu nome... voce lembra?"),
        ("Heroi",         (233, 69, 96), "Eu... Kael. Meu nome e Kael. Mas onde estou?"),
        ("Anciao Gareth", (180,160,100), "Na Vila de Cinzas. O ultimo refugio humano nas bordas do Shadow Realm."),
        ("Anciao Gareth", (180,160,100), "Uma escuridao chamada Sombra Eterna esta consumindo tudo. Florestas, masmorras, o proprio ceu."),
        ("Heroi",         (233, 69, 96), "Eu me lembro agora. Vim para acabar com isso. O Cristal da Aurora... preciso encontra-lo."),
        ("Anciao Gareth", (180,160,100), "O Cristal esta na Torre das Sombras, alem da Floresta Sombria, das Ruinas Antigas e das Cavernas de Gelo."),
        ("Anciao Gareth", (180,160,100), "Ninguem que foi la voltou. Mas voce... tem algo diferente nos olhos. Boa sorte, Kael."),
    ],
    # Entrada da Floresta (fase 2)
    'forest_enter': [
        ("Heroi",       (233, 69, 96), "Esta floresta... ela respira. Como se estivesse viva e com raiva."),
        ("??? (voz)",   (100, 220, 120), "Intruso! Voce viola o territorio sagrado dos Guardioes da Floresta!"),
        ("Heroi",       (233, 69, 96), "Quem esta ai? Mostre-se!"),
        ("Liria",       (100, 220, 120), "*uma elfa sai das sombras* Sou Liria, ultima guardia desta floresta corrompida."),
        ("Liria",       (100, 220, 120), "A Sombra Eterna transformou meus irmaos em monstros. Eu nao pude salva-los."),
        ("Heroi",       (233, 69, 96), "Sinto muito, Liria. Estou buscando o Cristal da Aurora para acabar com tudo isso."),
        ("Liria",       (100, 220, 120), "Entao voce precisa passar por aqui. Seja rapido — e cuidado com o Guardiao Corrompido la dentro."),
    ],
    # Chefe da Floresta derrotado
    'forest_boss': [
        ("Liria",  (100, 220, 120), "Voce... derrotou o Guardiao. Pela primeira vez em meses, sinto a floresta respirar."),
        ("Heroi",  (233, 69, 96), "Ele nao era o verdadeiro inimigo. Era apenas uma vitima."),
        ("Liria",  (100, 220, 120), "Tome este amuleto. Ele absorveu energia da floresta por seculos. Vai te proteger."),
        ("Heroi",  (233, 69, 96), "Obrigado, Liria. Continuarei em frente."),
        ("Liria",  (100, 220, 120), "As Ruinas Antigas estao alem da colina. Muito cuidado — os mortos caminham la."),
    ],
    # Entrada das Ruínas (fase 3)
    'ruins_enter': [
        ("Heroi",         (233, 69, 96), "Estas ruinas... sinto um frio que nao vem do vento."),
        ("Fantasma",      (180, 180, 255), "*materializa do nada* Vivo... Um vivo ousou entrar no Reino dos Esquecidos?"),
        ("Heroi",         (233, 69, 96), "Quem e voce?"),
        ("Fantasma",      (180, 180, 255), "Fui o rei deste lugar. Morto pela Sombra Eterna ha cem anos. Ela nos aprisiona aqui."),
        ("Fantasma",      (180, 180, 255), "Se voce destruir o Artefato Sombrio no centro das ruinas, nos libertara."),
        ("Heroi",         (233, 69, 96), "Eu destruirei o Artefato. Voce tem minha palavra."),
        ("Fantasma",      (180, 180, 255), "Seja bem-vindo ao meu reino de cinzas, jovem guerreiro. E... obrigado."),
    ],
    # Entrada das Cavernas (fase 4)
    'cavern_enter': [
        ("Heroi",      (233, 69, 96), "O frio aqui e absurdo. E essa escuridao... nao e natural."),
        ("Voz Sombria",(180,  50, 200), "Hahahaha... voce chegou ate aqui, pequena chama?"),
        ("Heroi",      (233, 69, 96), "A Sombra Eterna. Finalmente voce se mostra."),
        ("Voz Sombria",(180,  50, 200), "Mostrar? Eu SEREI tudo quando esse mundo morrer. O Cristal nao te salvara."),
        ("Heroi",      (233, 69, 96), "Entao terei que provar que voce esta errado."),
        ("Voz Sombria",(180,  50, 200), "Enfrente meu campeao, o Senhor do Gelo. Se sobreviver... nos encontraremos em breve."),
    ],
    # Antes do boss final (fase 5 — Torre)
    'tower_enter': [
        ("Heroi",       (233, 69, 96), "A Torre das Sombras. E aqui que tudo termina."),
        ("Liria",       (100, 220, 120), "*aparece atras* Kael! Vim te ajudar. A floresta esta se recuperando gracas a voce."),
        ("Heroi",       (233, 69, 96), "Liria... voce nao precisava vir."),
        ("Liria",       (100, 220, 120), "Precisava sim. O Cristal da Aurora esta no topo. Mas a Sombra Eterna esta la."),
        ("Liria",       (100, 220, 120), "Ela assume uma forma fisica quando se sente ameacada. Uma criatura de puro terror."),
        ("Heroi",       (233, 69, 96), "Seja la o que for... vou terminar isso hoje. Pelo rei fantasma, pela floresta, por todos."),
        ("Liria",       (100, 220, 120), "Eu estarei aqui. Vai, Kael. O mundo esta contando com voce."),
    ],
    # Final (vitória)
    'ending': [
        ("Heroi",       (233, 69, 96), "Esta... acabou. O Cristal da Aurora brilha novamente."),
        ("Voz Sombria", (180, 50, 200), "*voz se dissipando* Impossivel... eu sou eterno... eu sou..."),
        ("Liria",       (100, 220, 120), "Ela sumiu. A escuridao... esta recuando! Kael, voce conseguiu!"),
        ("Heroi",       (233, 69, 96), "O Cristal... esta quente. Como se o proprio sol estivesse dentro dele."),
        ("Liria",       (100, 220, 120), "O Shadow Realm nunca mais sera o mesmo. Gracas a voce."),
        ("Heroi",       (233, 69, 96), "Nao. Gracas a todos que acreditaram. O Anciao Gareth, o rei fantasma, voce..."),
        ("Liria",       (100, 220, 120), "Venha. Ha um mundo inteiro esperando para renascer."),
    ],
}

# Configuração visual de cada zona
ZONE_CONFIG = {
    # (sky_top, sky_bot, fog_col, plat_col, plat_hi, ground_col, name, subtitle)
    1: dict(
        sky_top=(15, 12, 35), sky_bot=(30, 20, 55),
        fog_col=(40, 30, 80), fog_alpha=40,
        plat_col=(22, 33, 62), plat_hi=(80, 110, 180),
        crystal_col=(100, 160, 255),
        ground_col=(18, 26, 52),
        name="Vila de Cinzas", subtitle="Zona 1 — Ruinas da Aldeia",
        name_col=(180, 160, 220),
        star_col=(220, 220, 255), star_alpha_base=80,
        has_stars=True, has_clouds=True,
        cloud_col=(30, 30, 60), cloud_alpha=40,
    ),
    2: dict(
        sky_top=(8, 28, 8), sky_bot=(20, 55, 15),
        fog_col=(20, 60, 20), fog_alpha=55,
        plat_col=(18, 55, 18), plat_hi=(60, 160, 60),
        crystal_col=(80, 220, 80),
        ground_col=(12, 42, 12),
        name="Floresta Sombria", subtitle="Zona 2 — Mata Corrompida",
        name_col=(80, 220, 80),
        star_col=(180, 255, 180), star_alpha_base=40,
        has_stars=True, has_clouds=True,
        cloud_col=(20, 60, 20), cloud_alpha=50,
    ),
    3: dict(
        sky_top=(35, 20, 10), sky_bot=(60, 35, 15),
        fog_col=(80, 50, 20), fog_alpha=45,
        plat_col=(70, 45, 20), plat_hi=(160, 110, 50),
        crystal_col=(255, 180, 80),
        ground_col=(55, 35, 14),
        name="Ruinas Antigas", subtitle="Zona 3 — Reino dos Esquecidos",
        name_col=(255, 180, 80),
        star_col=(255, 200, 150), star_alpha_base=50,
        has_stars=True, has_clouds=False,
        cloud_col=(80, 50, 20), cloud_alpha=30,
    ),
    4: dict(
        sky_top=(5, 18, 40), sky_bot=(10, 30, 70),
        fog_col=(30, 60, 100), fog_alpha=60,
        plat_col=(20, 40, 80), plat_hi=(60, 120, 200),
        crystal_col=(120, 200, 255),
        ground_col=(14, 30, 65),
        name="Cavernas de Gelo", subtitle="Zona 4 — Abismo Congelado",
        name_col=(120, 200, 255),
        star_col=(180, 220, 255), star_alpha_base=60,
        has_stars=True, has_clouds=True,
        cloud_col=(20, 40, 80), cloud_alpha=55,
    ),
    5: dict(
        sky_top=(20, 5, 35), sky_bot=(50, 10, 80),
        fog_col=(80, 20, 100), fog_alpha=50,
        plat_col=(55, 18, 80), plat_hi=(160, 60, 220),
        crystal_col=(220, 100, 255),
        ground_col=(40, 10, 65),
        name="Torre das Sombras", subtitle="Zona 5 — Sanctum Final",
        name_col=(220, 100, 255),
        star_col=(220, 150, 255), star_alpha_base=70,
        has_stars=True, has_clouds=True,
        cloud_col=(60, 10, 90), cloud_alpha=45,
    ),
}

TOTAL_LEVELS = 5   # agora o jogo tem 5 fases


class NPC:
    """Personagem com quem o player pode conversar (pressiona E)."""
    def __init__(self, x, y, name, color, dialogue_key):
        self.x = float(x)
        self.y = float(y)
        self.width  = 36
        self.height = 55
        self.name   = name
        self.color  = color
        self.dialogue_key = dialogue_key
        self.talked = False
        self.anim_timer = 0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self):
        self.anim_timer += 1

    def draw(self, surface):
        t   = self.anim_timer
        cx  = int(self.x + self.width // 2)
        bob = int(math.sin(t * 0.06) * 2)
        cy  = int(self.y) + bob
        col = self.color
        dk  = tuple(max(0, c - 50) for c in col)
        lk  = tuple(min(255, c + 60) for c in col)

        # Sombra
        sh = pygame.Surface((self.width + 4, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,50), (0,0,self.width+4,5))
        surface.blit(sh, (int(self.x)-2, int(self.y+self.height)-2))

        # Corpo (túnica)
        pygame.draw.rect(surface, dk,  (cx-13, cy+18, 26, 30), border_radius=4)
        pygame.draw.rect(surface, col, (cx-14, cy+16, 28, 30), border_radius=4)
        # Detalhe da túnica
        pygame.draw.line(surface, lk, (cx, cy+18), (cx, cy+44), 1)
        # Braços
        pygame.draw.rect(surface, col, (cx-22, cy+20, 10, 18), border_radius=3)
        pygame.draw.rect(surface, col, (cx+12, cy+20, 10, 18), border_radius=3)
        # Cabeça
        pygame.draw.circle(surface, col, (cx, cy+10), 13)
        pygame.draw.circle(surface, lk,  (cx-3, cy+6), 5)
        # Olhos
        pygame.draw.circle(surface, (30,30,30), (cx-4, cy+10), 3)
        pygame.draw.circle(surface, (30,30,30), (cx+4, cy+10), 3)

        # Balão de fala pulsante se não falou ainda
        if not self.talked:
            pulse = abs(math.sin(t * 0.08))
            bal_col = (255, 240, 80, int(160 + pulse * 95))
            bs = pygame.Surface((28, 22), pygame.SRCALPHA)
            pygame.draw.rect(bs, (20,20,20,160), (1,1,27,21), border_radius=5)
            pygame.draw.rect(bs, bal_col, (0,0,28,22), 2, border_radius=5)
            et = font_hud.render("E", True, (255, 240, 80))
            bs.blit(et, (28//2 - et.get_width()//2, 3))
            surface.blit(bs, (cx - 14, cy - 30))

        # Nome acima
        name_surf = font_hud.render(self.name, True, (220,220,220))
        surface.blit(name_surf, (cx - name_surf.get_width()//2, int(self.y) - 18))


class DialogueBox:
    """Caixa de diálogo estilo Pokémon."""
    CHARS_PER_TICK = 1     # velocidade de typewriter
    TICKS_PER_CHAR = 2     # frames por caractere

    def __init__(self, lines):
        # lines: lista de (speaker, portrait_color, text)
        self.lines    = lines
        self.index    = 0      # linha atual
        self.char_idx = 0      # chars revelados
        self.tick     = 0      # frame counter
        self.done     = False  # diálogo terminou

    @property
    def current(self):
        return self.lines[self.index]

    def advance(self):
        """Pressionar ENTER: avança texto ou vai para próxima linha."""
        spk, col, text = self.current
        if self.char_idx < len(text):
            # Pula animação de typewriter
            self.char_idx = len(text)
        else:
            self.index += 1
            if self.index >= len(self.lines):
                self.done = True
            else:
                self.char_idx = 0
                self.tick     = 0

    def update(self):
        if self.done: return
        spk, col, text = self.current
        if self.char_idx < len(text):
            self.tick += 1
            if self.tick >= self.TICKS_PER_CHAR:
                self.tick = 0
                self.char_idx += 1

    def draw(self, surface):
        if self.done: return
        spk, port_col, text = self.current

        # Painel principal
        BOX_W, BOX_H = 900, 140
        BOX_X = SCREEN_WIDTH // 2 - BOX_W // 2
        BOX_Y = SCREEN_HEIGHT - BOX_H - 18

        # Sombra
        sh = pygame.Surface((BOX_W + 6, BOX_H + 6), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0,0,0,100), (0,0,BOX_W+6,BOX_H+6), border_radius=10)
        surface.blit(sh, (BOX_X - 3, BOX_Y - 3))

        # Fundo
        bg = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
        pygame.draw.rect(bg, (8, 8, 22, 230), (0,0,BOX_W,BOX_H), border_radius=8)
        surface.blit(bg, (BOX_X, BOX_Y))

        # Borda colorida (cor do personagem)
        for tk, alp in [(3,40),(2,80),(1,200)]:
            bs2 = pygame.Surface((BOX_W+tk*2, BOX_H+tk*2), pygame.SRCALPHA)
            pygame.draw.rect(bs2, (*port_col, alp), (0,0,BOX_W+tk*2,BOX_H+tk*2), tk, border_radius=9)
            surface.blit(bs2, (BOX_X-tk, BOX_Y-tk))

        # Retrato (circle portrait)
        PORT_R = 40
        PORT_X = BOX_X + 20 + PORT_R
        PORT_Y = BOX_Y + BOX_H // 2
        # Fundo do retrato
        pygame.draw.circle(surface, tuple(max(0,c-60) for c in port_col), (PORT_X, PORT_Y), PORT_R+3)
        pygame.draw.circle(surface, port_col, (PORT_X, PORT_Y), PORT_R)
        pygame.draw.circle(surface, tuple(min(255,c+60) for c in port_col), (PORT_X-10, PORT_Y-12), PORT_R//3)
        # Rosto simples
        pygame.draw.circle(surface, (255,255,255), (PORT_X-8, PORT_Y-4), 6)
        pygame.draw.circle(surface, (255,255,255), (PORT_X+8, PORT_Y-4), 6)
        pygame.draw.circle(surface, (30,30,30),    (PORT_X-7, PORT_Y-3), 3)
        pygame.draw.circle(surface, (30,30,30),    (PORT_X+9, PORT_Y-3), 3)
        # Borda dourada no retrato
        pygame.draw.circle(surface, COLORS['xp_gold'], (PORT_X, PORT_Y), PORT_R+3, 2)

        # Nome do personagem
        TEXT_X = BOX_X + 20 + PORT_R*2 + 14
        name_bg = pygame.Surface((len(spk)*10+16, 22), pygame.SRCALPHA)
        pygame.draw.rect(name_bg, (*port_col, 180), (0,0,name_bg.get_width(),22), border_radius=4)
        surface.blit(name_bg, (TEXT_X - 4, BOX_Y + 10))
        name_surf = font_small.render(spk, True, (255,255,255))
        surface.blit(name_surf, (TEXT_X, BOX_Y + 12))

        # Texto com typewriter
        revealed = text[:self.char_idx]
        # Quebra em linhas de ~62 chars
        words = revealed.split(' ')
        lines_out, line = [], ''
        for w in words:
            test = (line + ' ' + w).strip()
            if len(test) <= 62:
                line = test
            else:
                lines_out.append(line)
                line = w
        if line:
            lines_out.append(line)
        for i, ln in enumerate(lines_out[:3]):
            txt_surf = font_small.render(ln, True, (230,230,250))
            surface.blit(txt_surf, (TEXT_X, BOX_Y + 38 + i * 28))

        # Indicador de avançar (pisca quando texto completo)
        if self.char_idx >= len(text):
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            arr_col = (255, 240, 80, int(150 + pulse * 105))
            arr_s = pygame.Surface((16, 12), pygame.SRCALPHA)
            pygame.draw.polygon(arr_s, arr_col, [(0,0),(16,0),(8,12)])
            surface.blit(arr_s, (BOX_X + BOX_W - 30, BOX_Y + BOX_H - 22))
            prog = font_hud.render(f"{self.index+1}/{len(self.lines)}", True, (120,120,140))
            surface.blit(prog, (BOX_X + BOX_W - 80, BOX_Y + BOX_H - 20))


# ==================== CUTSCENE ====================

CUTSCENE_FRAMES = [
    dict(duration=210, title="HA 100 ANOS...",
         narration="O mundo vivia em paz sob a luz do Cristal da Aurora,\numa gema que mantinha o equilibrio entre luz e trevas.",
         top=(5,5,20), bot=(15,10,40), visual='stars'),
    dict(duration=220, title="A QUEDA",
         narration="Mas uma entidade chamada Sombra Eterna emergiu das profundezas.\nEla corrompeu florestas, cidades e ate o proprio ceu.",
         top=(20,5,5), bot=(45,10,10), visual='shadow'),
    dict(duration=220, title="O ULTIMO BASTIAO",
         narration="A Vila de Cinzas tornou-se o ultimo refugio da humanidade.\nSeus habitantes vivem com medo... esperando um milagre.",
         top=(10,8,20), bot=(25,18,40), visual='village'),
    dict(duration=210, title="UM ESTRANHO CAI DO CEU",
         narration="Uma noite, um guerreiro desconhecido caiu em chamas sobre a vila.\nNinguem sabia de onde veio... mas ele carregava um proposito.",
         top=(5,10,25), bot=(10,20,50), visual='stars'),
    dict(duration=220, title="KAEL",
         narration="Seu nome e Kael. Ele e a unica esperanca.\nPara salvar o mundo ele deve encontrar o Cristal da Aurora\nna Torre das Sombras e destruir a Sombra Eterna.",
         top=(30,5,50), bot=(60,10,90), visual='crystal'),
    dict(duration=180, title="SHADOW REALM",
         narration="Sua jornada comeca agora.",
         top=(5,5,20), bot=(20,10,45), visual='stars'),
]


class Cutscene:
    def __init__(self):
        self.frame_idx   = 0
        self.frame_timer = 0
        self.done        = False
        self.fade_alpha  = 255
        self.fading_in   = True
        self.fading_out  = False
        self.fade_speed  = 5
        self._anim       = 0
        random.seed(99)
        self.particles = [
            {'x': random.randint(0, SCREEN_WIDTH), 'y': random.randint(0, SCREEN_HEIGHT),
             'vx': random.uniform(-0.3,0.3), 'vy': random.uniform(-0.8,-0.2),
             'r': random.randint(1,3), 'life': random.randint(60,200), 'max_life': 200,
             'col': random.choice([(200,180,255),(150,200,255),(255,220,150)])}
            for _ in range(80)]
        random.seed()

    @property
    def current(self):
        return CUTSCENE_FRAMES[self.frame_idx]

    def skip(self):
        self.done = True

    def update(self):
        if self.done: return
        self._anim += 1
        if self.fading_in:
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * 3)
            if self.fade_alpha == 0: self.fading_in = False
            return
        if self.fading_out:
            self.fade_alpha = min(255, self.fade_alpha + self.fade_speed * 3)
            if self.fade_alpha >= 255:
                self.fading_out = False
                self.frame_idx += 1
                if self.frame_idx >= len(CUTSCENE_FRAMES):
                    self.done = True; return
                self.fading_in = True; self.frame_timer = 0
            return
        alive = []
        for p in self.particles:
            p['x'] += p['vx']; p['y'] += p['vy']; p['life'] -= 1
            if p['life'] <= 0:
                p['x'] = random.randint(0, SCREEN_WIDTH)
                p['y'] = SCREEN_HEIGHT + 5; p['life'] = p['max_life']
            alive.append(p)
        self.particles = alive
        self.frame_timer += 1
        if self.frame_timer >= self.current['duration']:
            self.fading_out = True

    def _draw_visual(self, surface, visual, t):
        cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
        if visual == 'stars':
            for i in range(40):
                sx = (i*313+t//3) % SCREEN_WIDTH
                sy = (i*197+t//4) % (SCREEN_HEIGHT-100)
                br = abs(math.sin(t*0.04+i))*200+55
                sz = 1 + i % 3
                ss = pygame.Surface((sz*2+2,sz*2+2), pygame.SRCALPHA)
                pygame.draw.circle(ss, (int(br),int(br),255,int(br)), (sz+1,sz+1), sz)
                surface.blit(ss, (sx-sz, sy-sz))
        elif visual == 'village':
            for i,(bx,bw,bh) in enumerate([(80,120,90),(220,90,70),(330,140,110),
                                            (500,100,80),(630,130,100),(780,110,85),(920,95,75),(1050,130,95)]):
                bc = (15+i*2,12+i*2,28+i*3)
                pygame.draw.rect(surface, bc, (bx, SCREEN_HEIGHT//2+80-bh, bw, bh+40))
                pygame.draw.polygon(surface, (bc[0]+8,bc[1]+6,bc[2]+10),
                    [(bx-5,SCREEN_HEIGHT//2+80-bh),(bx+bw//2,SCREEN_HEIGHT//2+20-bh),(bx+bw+5,SCREEN_HEIGHT//2+80-bh)])
                pygame.draw.rect(surface, (50+i*5,40+i*4,20), (bx+bw//2-8,SCREEN_HEIGHT//2+40-bh,16,18))
            pygame.draw.circle(surface, (220,215,180), (cx,130), 50)
            pygame.draw.circle(surface, (180,175,140), (cx,130), 42)
        elif visual == 'shadow':
            for i in range(12):
                angle  = (i/12)*math.pi*2 + t*0.01
                length = 200 + math.sin(t*0.05+i)*60
                ex,ey  = cx+math.cos(angle)*length, cy+math.sin(angle)*length*0.6
                thick  = 6 + int(math.sin(t*0.08+i)*3)
                alp    = int(160+math.sin(t*0.06+i)*80)
                ls = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(ls,(80,20,120,alp),(cx,cy),(int(ex),int(ey)),thick)
                surface.blit(ls,(0,0))
            ep = abs(math.sin(t*0.06))*20
            pygame.draw.circle(surface,(120,30,180),(cx,cy),int(60+ep))
            pygame.draw.circle(surface,(200,80,255),(cx,cy),int(40+ep*0.6))
            pygame.draw.ellipse(surface,(10,0,20),(cx-18,cy-10,36,20))
        elif visual == 'crystal':
            pulse = abs(math.sin(t*0.05))*30
            gs = pygame.Surface((300,300), pygame.SRCALPHA)
            for gr in range(5,0,-1):
                pygame.draw.circle(gs,(180+gr*10,220-gr*10,255,int(30+pulse)),(150,150),int(80+pulse+gr*15))
            surface.blit(gs,(cx-150,cy-180))
            pts = [(cx,cy-110-int(pulse)),(cx+45,cy-50),(cx+55,cy+20),(cx,cy+80),(cx-55,cy+20),(cx-45,cy-50)]
            pygame.draw.polygon(surface,(180,240,255),pts)
            pygame.draw.polygon(surface,(220,255,255),pts,2)
            pygame.draw.polygon(surface,(255,255,255),[(cx,cy-70-int(pulse*0.5)),(cx+25,cy),(cx,cy+50),(cx-25,cy)])
            for i in range(8):
                angle  = (i/8)*math.pi*2+t*0.02
                rl     = 120+int(pulse*2)
                ex2,ey2 = cx+math.cos(angle)*rl, cy+math.sin(angle)*rl*0.7-30
                rs = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(rs,(220,255,255,60),(cx,cy-30),(int(ex2),int(ey2)),2)
                surface.blit(rs,(0,0))

    def draw(self, surface):
        if self.done: return
        f,t = self.current, self._anim
        for y in range(0,SCREEN_HEIGHT,3):
            ratio = y/SCREEN_HEIGHT
            r = int(f['top'][0]+ratio*(f['bot'][0]-f['top'][0]))
            g = int(f['top'][1]+ratio*(f['bot'][1]-f['top'][1]))
            b = int(f['top'][2]+ratio*(f['bot'][2]-f['top'][2]))
            pygame.draw.rect(surface,(r,g,b),(0,y,SCREEN_WIDTH,3))
        for p in self.particles:
            alpha = int(180*p['life']/p['max_life'])
            ps = pygame.Surface((p['r']*2,p['r']*2), pygame.SRCALPHA)
            pygame.draw.circle(ps,(*p['col'],alpha),(p['r'],p['r']),p['r'])
            surface.blit(ps,(int(p['x'])-p['r'],int(p['y'])-p['r']))
        self._draw_visual(surface, f['visual'], t)
        bar_h = 80
        pygame.draw.rect(surface,(0,0,0),(0,0,SCREEN_WIDTH,bar_h))
        pygame.draw.rect(surface,(0,0,0),(0,SCREEN_HEIGHT-bar_h,SCREEN_WIDTH,bar_h))
        pygame.draw.rect(surface,(60,50,20),(0,bar_h,SCREEN_WIDTH,1))
        pygame.draw.rect(surface,(60,50,20),(0,SCREEN_HEIGHT-bar_h-1,SCREEN_WIDTH,1))
        progress = min(1.0, self.frame_timer/40)
        ta = int(progress*255)
        ts = font_large.render(f['title'], True, COLORS['xp_gold'])
        tss = pygame.Surface(ts.get_size(), pygame.SRCALPHA); tss.blit(ts,(0,0)); tss.set_alpha(ta)
        surface.blit(tss,(SCREEN_WIDTH//2-ts.get_width()//2, 18))
        chars = min(len(f['narration']), int(self.frame_timer*1.2))
        lines = f['narration'][:chars].split('\n')
        narr_y = SCREEN_HEIGHT-bar_h+10
        for i,line in enumerate(lines[:3]):
            ns = font_small.render(line, True,(220,215,255)); ns.set_alpha(ta)
            surface.blit(ns,(SCREEN_WIDTH//2-ns.get_width()//2, narr_y+i*28))
        dot_y = SCREEN_HEIGHT-18
        for i in range(len(CUTSCENE_FRAMES)):
            dc = COLORS['xp_gold'] if i==self.frame_idx else (60,55,40)
            pygame.draw.circle(surface,dc,(SCREEN_WIDTH//2-len(CUTSCENE_FRAMES)*12+i*24,dot_y),5)
        sk = font_hud.render("SPACE / ENTER — Pular cutscene", True,(100,95,80))
        surface.blit(sk,(SCREEN_WIDTH-sk.get_width()-16, SCREEN_HEIGHT-bar_h+55))
        if self.fade_alpha > 0:
            fade = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.SRCALPHA)
            fade.fill((0,0,0,self.fade_alpha)); surface.blit(fade,(0,0))


# ==================== UPGRADE MENU ====================

UPGRADES = [
    dict(id='hp_up',    name="Vitalidade",    desc="+20 HP Maximo",       cost=80,  max_lvl=5, stat='max_hp',       amount=20),
    dict(id='mp_up',    name="Mana Pura",      desc="+15 MP Maximo",       cost=60,  max_lvl=5, stat='max_mp',       amount=15),
    dict(id='atk_up',   name="Forca Bruta",    desc="+4 Ataque Base",      cost=100, max_lvl=5, stat='base_attack',  amount=4),
    dict(id='def_up',   name="Armadura",       desc="+3 Defesa Base",      cost=80,  max_lvl=5, stat='base_defense', amount=3),
    dict(id='spd_up',   name="Agilidade",      desc="+1 Velocidade",       cost=70,  max_lvl=3, stat='speed',        amount=1),
    dict(id='crit_up',  name="Olho de Aguia",  desc="+10% Chance de Crit", cost=120, max_lvl=3, stat='crit_bonus',   amount=10),
    dict(id='regen_up', name="Regeneracao",    desc="+3 HP regen/turno",   cost=90,  max_lvl=3, stat='hp_regen',     amount=3),
    dict(id='mp_regen', name="Fluxo de Mana",  desc="+2 MP regen/turno",   cost=80,  max_lvl=3, stat='mp_regen',     amount=2),
]

SPECIAL_SKILLS = [
    dict(id='blitz',   name="Blitz Sombrio",  desc="Ataca 3x seguidas (12 MP)",        cost=200, mp_cost=12, icon_col=(255,80,80)),
    dict(id='barrier', name="Barreira Arcana", desc="Absorve 1 ataque (15 MP)",          cost=180, mp_cost=15, icon_col=(80,160,255)),
    dict(id='drain',   name="Drenar Vida",     desc="Rouba 25% do dano causado (10 MP)", cost=160, mp_cost=10, icon_col=(150,50,220)),
    dict(id='meteor',  name="Meteoro",         desc="2.5x dano, ignora DEF (18 MP)",     cost=250, mp_cost=18, icon_col=(255,140,0)),
    dict(id='revive',  name="Ressurreicao",    desc="Revive com 30% HP (1x/combate)",    cost=300, mp_cost=0,  icon_col=(255,220,80)),
]


class UpgradeMenu:
    def __init__(self, player):
        self.player    = player
        self.tab       = 0
        self.cursor    = 0
        self.msg       = ""
        self.msg_timer = 0
        for attr in ('gold','crit_bonus','hp_regen','mp_regen',
                     'upgrade_levels','unlocked_skills','barrier_active','revive_ready'):
            if not hasattr(player, attr):
                if attr == 'upgrade_levels':    setattr(player, attr, {})
                elif attr == 'unlocked_skills': setattr(player, attr, set())
                elif attr in ('barrier_active','revive_ready'): setattr(player, attr, False)
                else: setattr(player, attr, 0)

    def _upg_level(self, uid): return self.player.upgrade_levels.get(uid, 0)
    def _can_buy_upgrade(self, u): return self.player.gold >= u['cost'] and self._upg_level(u['id']) < u['max_lvl']
    def _can_buy_skill(self, s): return self.player.gold >= s['cost'] and s['id'] not in self.player.unlocked_skills

    def buy_upgrade(self):
        if self.cursor >= len(UPGRADES): return
        upg = UPGRADES[self.cursor]
        if not self._can_buy_upgrade(upg):
            self.msg = "Ouro insuficiente ou nivel maximo!"; self.msg_timer = 90; return
        self.player.gold -= upg['cost']
        lvl = self._upg_level(upg['id']) + 1
        self.player.upgrade_levels[upg['id']] = lvl
        s, a = upg['stat'], upg['amount']
        if s=='max_hp': self.player.max_hp+=a; self.player.hp=min(self.player.hp+a,self.player.max_hp)
        elif s=='max_mp': self.player.max_mp+=a; self.player.mp=min(self.player.mp+a,self.player.max_mp)
        elif s=='base_attack': self.player.base_attack+=a
        elif s=='base_defense': self.player.base_defense+=a
        elif s=='speed': self.player.speed+=a
        elif s=='crit_bonus': self.player.crit_bonus+=a
        elif s=='hp_regen': self.player.hp_regen+=a
        elif s=='mp_regen': self.player.mp_regen+=a
        self.msg = f"{upg['name']} nivel {lvl} comprado!"; self.msg_timer = 90

    def buy_skill(self):
        if self.cursor >= len(SPECIAL_SKILLS): return
        sk = SPECIAL_SKILLS[self.cursor]
        if not self._can_buy_skill(sk):
            self.msg = "Ouro insuficiente ou ja desbloqueado!"; self.msg_timer = 90; return
        self.player.gold -= sk['cost']
        self.player.unlocked_skills.add(sk['id'])
        self.msg = f"{sk['name']} desbloqueada!"; self.msg_timer = 90

    def handle_key(self, key):
        items = UPGRADES if self.tab==0 else SPECIAL_SKILLS
        if key in (pygame.K_LEFT, pygame.K_a):   self.tab=(self.tab-1)%2; self.cursor=0
        elif key in (pygame.K_RIGHT, pygame.K_d): self.tab=(self.tab+1)%2; self.cursor=0
        elif key in (pygame.K_UP, pygame.K_w):   self.cursor=(self.cursor-1)%len(items)
        elif key in (pygame.K_DOWN, pygame.K_s): self.cursor=(self.cursor+1)%len(items)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.tab==0: self.buy_upgrade()
            else: self.buy_skill()

    def draw(self, surface):
        t = pygame.time.get_ticks()//16
        ov = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,210)); surface.blit(ov,(0,0))
        W,H = 900,580; X,Y = SCREEN_WIDTH//2-W//2, SCREEN_HEIGHT//2-H//2
        panel = pygame.Surface((W,H), pygame.SRCALPHA)
        pygame.draw.rect(panel,(8,10,24,240),(0,0,W,H),border_radius=10)
        surface.blit(panel,(X,Y))
        pc = int(abs(math.sin(t*0.04))*40)
        for th,al in [(4,30),(3,60),(2,180)]:
            bs = pygame.Surface((W+th*2,H+th*2), pygame.SRCALPHA)
            pygame.draw.rect(bs,(100+pc,80,200+pc,al),(0,0,W+th*2,H+th*2),th,border_radius=11)
            surface.blit(bs,(X-th,Y-th))
        ttl = font_large.render("MELHORIAS & HABILIDADES", True, COLORS['xp_gold'])
        surface.blit(ttl,(X+W//2-ttl.get_width()//2, Y+10))
        gs2 = font_medium.render(f"Ouro: {self.player.gold}", True,(255,210,50))
        surface.blit(gs2,(X+W-gs2.get_width()-20, Y+12))
        for i,tn in enumerate(["ATRIBUTOS","HABILIDADES"]):
            bx,by = X+20+i*200, Y+68
            sel = (i==self.tab)
            pygame.draw.rect(surface,(30,25,60) if sel else (15,12,30),(bx,by,180,36),border_radius=5)
            if sel: pygame.draw.rect(surface,(100,80,200),(bx,by,180,36),2,border_radius=5)
            ts2 = font_small.render(tn, True,(255,215,0) if sel else (140,140,160))
            surface.blit(ts2,(bx+90-ts2.get_width()//2, by+8))
        pygame.draw.rect(surface,(40,35,80),(X+10,Y+108,W-20,1))
        items = UPGRADES if self.tab==0 else SPECIAL_SKILLS
        ITEM_H = 68; lx,ly = X+14, Y+116
        for i,item in enumerate(items):
            iy = ly+i*ITEM_H
            if iy+ITEM_H > Y+H-80: break
            sel = (i==self.cursor)
            if sel:
                gs3 = pygame.Surface((W-28,ITEM_H-4), pygame.SRCALPHA)
                pygame.draw.rect(gs3,(60,40,120,160),(0,0,W-28,ITEM_H-4),border_radius=6)
                pygame.draw.rect(gs3,COLORS['xp_gold'],(0,0,W-28,ITEM_H-4),1,border_radius=6)
                surface.blit(gs3,(lx,iy))
            else:
                pygame.draw.rect(surface,(14,12,28),(lx,iy,W-28,ITEM_H-4),border_radius=6)
                pygame.draw.rect(surface,(30,28,55),(lx,iy,W-28,ITEM_H-4),1,border_radius=6)
            if self.tab==0:
                upg = item; lvl = self._upg_level(upg['id']); can = self._can_buy_upgrade(upg)
                for li in range(upg['max_lvl']):
                    pygame.draw.rect(surface,(80,200,80) if li<lvl else (40,35,60),(lx+8+li*18,iy+44,14,10),border_radius=2)
                surface.blit(font_small.render(upg['name'],True,(255,230,80) if sel else (200,200,220)),(lx+10,iy+6))
                surface.blit(font_hud.render(upg['desc'],True,(160,160,190)),(lx+10,iy+28))
                cs2 = font_small.render(f"{upg['cost']} ouro  (Lv {lvl}/{upg['max_lvl']})",True,(80,200,80) if can else (180,60,60))
                surface.blit(cs2,(lx+W-28-cs2.get_width()-10,iy+24))
            else:
                sk=item; owned=sk['id'] in self.player.unlocked_skills; can2=self._can_buy_skill(sk)
                ic=pygame.Surface((40,40),pygame.SRCALPHA)
                pygame.draw.circle(ic,(*sk['icon_col'],200 if owned else 80),(20,20),18)
                pygame.draw.circle(ic,(255,255,255),(20,20),18,2); surface.blit(ic,(lx+8,iy+8))
                nc2 = sk['icon_col'] if owned else ((200,200,220) if can2 else (100,100,120))
                surface.blit(font_small.render(sk['name'],True,nc2),(lx+56,iy+6))
                surface.blit(font_hud.render(sk['desc'],True,(150,150,180)),(lx+56,iy+28))
                if owned:
                    tag2=font_hud.render("DESBLOQUEADO",True,(80,220,80)); surface.blit(tag2,(lx+W-28-tag2.get_width()-10,iy+24))
                else:
                    cs3=font_small.render(f"{sk['cost']} ouro",True,(80,200,80) if can2 else (180,60,60))
                    surface.blit(cs3,(lx+W-28-cs3.get_width()-10,iy+24))
                    if sk['mp_cost']>0:
                        mc2=font_hud.render(f"Custo: {sk['mp_cost']} MP",True,(100,160,255))
                        surface.blit(mc2,(lx+W-28-mc2.get_width()-10,iy+42))
        if self.msg_timer>0:
            self.msg_timer-=1
            ms2=font_small.render(self.msg,True,(100,255,150))
            msurf=pygame.Surface(ms2.get_size(),pygame.SRCALPHA); msurf.blit(ms2,(0,0))
            msurf.set_alpha(min(255,self.msg_timer*5)); surface.blit(msurf,(X+W//2-ms2.get_width()//2,Y+H-60))
        inst=font_hud.render("A/D: Trocar aba   W/S: Navegar   ENTER: Comprar   TAB: Fechar",True,(80,80,110))
        surface.blit(inst,(X+W//2-inst.get_width()//2,Y+H-28))


class Game:
    def __init__(self):
        self.state = 'menu'
        self.player = None
        self.platforms = []
        self.monsters = []
        self.boss = None
        self.doors = []
        self.chests = []
        self.npcs   = []
        self.particles = []
        self.combat = None
        self.current_level = 1
        self.screen_shake = 0
        self.level_text = None
        self.level_text_timer = 0
        self.save_file = 'savegame.json'
        self.menu_selection = 0
        self.game_timer = 0

        # Cutscene e diálogo
        self.cutscene: Cutscene | None = None
        self.dialogue: DialogueBox | None = None
        self.story_seen = set()

        # Upgrade menu
        self.upgrade_menu: UpgradeMenu | None = None

        # Fundo estrelado
        random.seed(42)
        self.bg_stars  = [(random.randint(0,SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT-100),
                           random.randint(1,3), random.uniform(0.3,1.0)) for _ in range(120)]
        self.bg_clouds = [(random.randint(0,SCREEN_WIDTH), random.randint(30,200),
                           random.uniform(0.2,0.6), random.randint(60,140)) for _ in range(10)]
        random.seed()

        self.load_game()
    
    def _ensure_player_extras(self):
        p = self.player
        for attr, default in [('gold',150),('crit_bonus',0),('hp_regen',0),('mp_regen',0),
                               ('upgrade_levels',{}),('unlocked_skills',set()),
                               ('barrier_active',False),('revive_ready',False)]:
            if not hasattr(p, attr):
                setattr(p, attr, default)

    def new_game(self):
        self.player = Player(100, 500)
        self._ensure_player_extras()
        self.current_level = 1
        self.story_seen = set()
        self.dialogue = None
        self.upgrade_menu = None
        self.load_level(self.current_level)
        self.cutscene = Cutscene()
        self.state = 'cutscene'

    def _trigger_story(self, key):
        """Inicia um diálogo se ainda não foi visto."""
        if key in self.story_seen or key not in STORY:
            return
        self.story_seen.add(key)
        self.dialogue = DialogueBox(STORY[key])

    def load_level(self, level_num):
        if self.player is None:
            self.player = Player(100, 500)
        else:
            self.player.x = 100
            self.player.y = 500
            self.player.vel_x = 0
            self.player.vel_y = 0
            self.player.attacking = False
            self.player.invincible = False
            self.player.invincible_timer = 0
            self.player.hurt = False
            self.player.hurt_timer = 0

        self.platforms = []
        self.current_level = level_num
        self.monsters = []
        self.doors = []
        self.chests = []
        self.npcs   = []
        self.particles = []
        self.boss = None

        # Chão base
        self.platforms.append(Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))

        # ── FASE 1: Vila de Cinzas ────────────────────────────────────────────
        if level_num == 1:
            self.platforms += [
                Platform(180, 555, 200, 20), Platform(460, 490, 160, 20),
                Platform(700, 415, 180, 20), Platform(300, 330, 170, 20),
                Platform(60,  260, 150, 20), Platform(550, 240, 130, 20),
                Platform(880, 350, 140, 20),
            ]
            self.monsters += [
                Monster(420, 515, 'slime', 1),
                Monster(760, 375, 'slime', 2),
                Monster(560, 200, 'goblin', 2),
            ]
            self.npcs.append(NPC(920, SCREEN_HEIGHT - 95, "Anciao Gareth", (180,160,100), 'prologue'))
            self.doors.append(Door(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 120))
            self.chests += [Chest(100, 230), Chest(550, 210)]

        # ── FASE 2: Floresta Sombria ─────────────────────────────────────────
        elif level_num == 2:
            self.platforms += [
                Platform(160, 570, 190, 20), Platform(400, 510, 160, 20),
                Platform(650, 445, 180, 20), Platform(250, 375, 160, 20),
                Platform(520, 300, 140, 20), Platform(800, 280, 150, 20),
                Platform(100, 215, 130, 20), Platform(400, 185, 180, 20),
                Platform(720, 195, 120, 20),
            ]
            self.monsters += [
                Monster(320, 530, 'slime',  2),
                Monster(700, 405, 'goblin', 3),
                Monster(360, 335, 'goblin', 3),
                Monster(560, 260, 'goblin', 4),
                Monster(840, 240, 'slime',  3),
            ]
            self.npcs.append(NPC(160, SCREEN_HEIGHT - 95, "Liria", (100,220,120), 'forest_enter'))
            self.doors.append(Door(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 120))
            self.chests += [Chest(450, 155), Chest(750, 165)]

        # ── FASE 3: Ruínas Antigas ────────────────────────────────────────────
        elif level_num == 3:
            self.platforms += [
                Platform(120, 575, 190, 20), Platform(360, 505, 160, 20),
                Platform(620, 430, 170, 20), Platform(160, 350, 150, 20),
                Platform(460, 285, 180, 20), Platform(780, 210, 150, 20),
                Platform(300, 195, 140, 20), Platform(600, 160, 160, 20),
            ]
            self.monsters += [
                Monster(210, 535, 'goblin',   4),
                Monster(410, 465, 'skeleton', 4),
                Monster(660, 390, 'skeleton', 5),
                Monster(260, 310, 'skeleton', 5),
                Monster(500, 245, 'orc',      6),
                Monster(820, 170, 'skeleton', 6),
            ]
            self.npcs.append(NPC(550, SCREEN_HEIGHT - 95, "Fantasma Rex", (180,180,255), 'ruins_enter'))
            self.doors.append(Door(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 120))
            self.chests += [Chest(310, 165), Chest(640, 130)]

        # ── FASE 4: Cavernas de Gelo ─────────────────────────────────────────
        elif level_num == 4:
            self.platforms += [
                Platform(100, 595, 280, 20), Platform(500, 545, 180, 20),
                Platform(820, 480, 250, 20), Platform(300, 405, 190, 20),
                Platform(660, 330, 190, 20), Platform(150, 260, 160, 20),
                Platform(500, 210, 160, 20), Platform(900, 200, 140, 20),
            ]
            self.monsters += [
                Monster(210, 555, 'orc',      7),
                Monster(560, 505, 'skeleton', 7),
                Monster(880, 440, 'orc',      8),
                Monster(380, 365, 'orc',      8),
                Monster(720, 290, 'skeleton', 8),
                Monster(200, 220, 'orc',      9),
                Monster(560, 170, 'orc',      9),
            ]
            # Boss de gelo
            ice_boss = Monster(900, SCREEN_HEIGHT - 120, 'Boss', 10)
            ice_boss.name = "Senhor do Gelo"
            ice_boss.color = (80, 180, 255)
            self.boss = ice_boss
            self.npcs.append(NPC(150, SCREEN_HEIGHT - 95, "Kael", (233,69,96), 'cavern_enter'))
            self.doors.append(Door(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 120))
            self.chests.append(Chest(500, 180))

        # ── FASE 5: Torre das Sombras (Boss Final) ───────────────────────────
        elif level_num == 5:
            self.platforms += [
                Platform(80,  590, 240, 20), Platform(440, 540, 160, 20),
                Platform(760, 475, 220, 20), Platform(250, 400, 170, 20),
                Platform(600, 335, 170, 20), Platform(100, 270, 150, 20),
                Platform(480, 215, 150, 20), Platform(850, 200, 130, 20),
                Platform(320, 145, 160, 20),
            ]
            self.monsters += [
                Monster(200, 550, 'orc',      10),
                Monster(500, 500, 'skeleton', 9),
                Monster(820, 435, 'orc',      10),
                Monster(310, 360, 'orc',      11),
                Monster(650, 295, 'skeleton', 10),
                Monster(160, 230, 'orc',      11),
            ]
            # Boss final — Sombra Eterna
            final_boss = Monster(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 130, 'Boss', 15)
            final_boss.name = "Sombra Eterna"
            final_boss.color = (120, 30, 200)
            final_boss.max_hp = 500
            final_boss.hp = 500
            final_boss.attack = 60
            final_boss.defense = 10
            final_boss.xp_reward = 800
            self.boss = final_boss
            self.npcs.append(NPC(200, SCREEN_HEIGHT - 95, "Liria", (100,220,120), 'tower_enter'))
            # Sem porta — chefe final precisa ser derrotado

        zone = ZONE_CONFIG.get(level_num, ZONE_CONFIG[1])
        self.level_text = f"{zone['name']}"
        self.level_text_timer = 150

        self.player.hp = min(self.player.max_hp, self.player.hp + 40)
        self.player.mp = min(self.player.max_mp, self.player.mp + 25)
    
    def update(self):
        self.game_timer += 1

        # ── Cutscene ─────────────────────────────────────────────────────────
        if self.state == 'cutscene':
            if self.cutscene:
                self.cutscene.update()
                if self.cutscene.done:
                    self.cutscene = None
                    self._trigger_story('prologue')
                    self.state = 'playing'
            return

        # ── Upgrade menu pausa o jogo ─────────────────────────────────────────
        if self.upgrade_menu:
            return

        # ── Diálogo ativo bloqueia tudo ──────────────────────────────────────
        if self.dialogue and not self.dialogue.done:
            self.dialogue.update()
            return

        if self.state == 'playing':
            self.player.update(self.platforms)
            self.particles = [p for p in self.particles if p.update()]

            # Regeneração passiva a cada 90 frames
            if self.game_timer % 90 == 0:
                regen_hp = getattr(self.player, 'hp_regen', 0)
                regen_mp = getattr(self.player, 'mp_regen', 0)
                if regen_hp > 0:
                    self.player.hp = min(self.player.max_hp, self.player.hp + regen_hp)
                if regen_mp > 0:
                    self.player.mp = min(self.player.max_mp, self.player.mp + regen_mp)

            for npc in self.npcs:
                npc.update()

            for monster in self.monsters:
                monster.update(self.player)
                if monster.alive and self.player.rect().colliderect(monster.rect()):
                    self.player.get_damage(max(1, monster.attack - self.player.defense + random.randint(-2,5)))
                    self.screen_shake = 10
                    self.combat = Combat(self.player, monster)
                    if hasattr(self.player, 'revive_used_this_combat'):
                        del self.player.revive_used_this_combat
                    self.state = 'combat'

            if self.boss and self.boss.alive:
                self.boss.update(self.player)
                if self.player.rect().colliderect(self.boss.rect()):
                    self.player.get_damage(max(1, self.boss.attack - self.player.defense + random.randint(-5,10)))
                    self.screen_shake = 15
                    self.combat = Combat(self.player, self.boss)
                    if hasattr(self.player, 'revive_used_this_combat'):
                        del self.player.revive_used_this_combat
                    self.state = 'combat'

            for door in self.doors:
                if self.player.rect().colliderect(door.rect()):
                    next_lvl = self.current_level + 1
                    if next_lvl > TOTAL_LEVELS:
                        self._trigger_story('ending')
                        self.state = 'victory'
                    else:
                        self.load_level(next_lvl)
                        triggers = {2:'forest_enter', 3:'ruins_enter', 4:'cavern_enter', 5:'tower_enter'}
                        if next_lvl in triggers:
                            self._trigger_story(triggers[next_lvl])

            for chest in self.chests:
                if not chest.opened and self.player.rect().colliderect(chest.rect()):
                    chest.opened = True
                    gold_found = random.randint(30, 80)
                    self.player.gold = getattr(self.player, 'gold', 0) + gold_found
                    for item in chest.items:
                        self.player.inventory[item] = self.player.inventory.get(item,0) + 1
                    self.level_text = f"Bau! +{gold_found} ouro  +Pocoes"
                    self.level_text_timer = 90

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
                # Ressurreição?
                revive_ok = (hasattr(self.player,'unlocked_skills') and
                             'revive' in self.player.unlocked_skills and
                             not getattr(self.player,'revive_used_this_combat',False))
                if revive_ok:
                    self.player.hp = int(self.player.max_hp * 0.30)
                    self.player.revive_used_this_combat = True
                    self.combat.log.append("RESSURREICAO! Voltou com 30% HP!")
                    self.combat.phase = 'player_turn'
                else:
                    self.state = 'game_over'
            elif result == 'victory_done':
                self.monsters = [m for m in self.monsters if m.alive]
                gold_drop = random.randint(self.combat.monster.level*8, self.combat.monster.level*18)
                self.player.gold = getattr(self.player,'gold',0) + gold_drop
                boss_killed = (self.combat.monster == self.boss or (self.boss and not self.boss.alive))
                self.combat = None
                if boss_killed:
                    self.boss = None
                    if self.current_level == 2:
                        self._trigger_story('forest_boss')
                    elif self.current_level == TOTAL_LEVELS:
                        self._trigger_story('ending')
                        self.state = 'victory'
                        return
                self.state = 'playing'

        elif self.state == 'victory':
            self.particles = [p for p in self.particles if p.update()]
    
    def draw_background(self):
        t  = self.game_timer
        z  = ZONE_CONFIG.get(self.current_level, ZONE_CONFIG[1])
        st = z['sky_top']
        sb = z['sky_bot']

        # Gradiente de céu temático
        for y in range(0, SCREEN_HEIGHT, 3):
            ratio = y / SCREEN_HEIGHT
            r = int(st[0] + ratio * (sb[0] - st[0]))
            g = int(st[1] + ratio * (sb[1] - st[1]))
            b = int(st[2] + ratio * (sb[2] - st[2]))
            pygame.draw.rect(screen, (r, g, b), (0, y, SCREEN_WIDTH, 3))

        # Decorações de fundo específicas por zona
        if self.current_level == 2:  # Floresta — árvores no fundo
            for i in range(12):
                tx = (i * 110 + 30) % SCREEN_WIDTH
                th = 80 + (i * 37) % 60
                tw = 14 + (i * 13) % 12
                # Tronco
                pygame.draw.rect(screen, (25, 55, 15), (tx, SCREEN_HEIGHT - 40 - th, tw, th))
                # Copa
                for ci in range(3):
                    cr = 28 + ci * 8
                    cy2 = SCREEN_HEIGHT - 40 - th - ci * 20
                    pygame.draw.circle(screen, (15 + ci*5, 55 + ci*10, 15 + ci*5), (tx + tw//2, cy2), cr)

        elif self.current_level == 3:  # Ruínas — colunas quebradas
            for i in range(7):
                cx2 = 80 + i * 160
                ch  = 100 + (i*47) % 80
                cw  = 22
                pygame.draw.rect(screen, (50, 35, 16), (cx2, SCREEN_HEIGHT - 40 - ch, cw, ch))
                # Topo da coluna
                pygame.draw.rect(screen, (70, 50, 22), (cx2-4, SCREEN_HEIGHT-40-ch-10, cw+8, 12), border_radius=2)
                # Trincas
                pygame.draw.line(screen, (30,20,8), (cx2+5, SCREEN_HEIGHT-40-ch+20), (cx2+12, SCREEN_HEIGHT-40-ch+50), 1)

        elif self.current_level == 4:  # Cavernas — estalactites
            for i in range(16):
                ex = 40 + i * 74
                eh  = 20 + (i * 29) % 45
                pygame.draw.polygon(screen, (18, 35, 65),
                    [(ex, 0), (ex + 10, eh), (ex + 20, 0)])
                pygame.draw.polygon(screen, (30, 55, 100),
                    [(ex+2, 0), (ex+10, eh-6), (ex+18, 0)])
                # gelo brilhando
                pygame.draw.line(screen, (140,210,255), (ex+10, 0), (ex+10, eh//2), 1)

        elif self.current_level == 5:  # Torre — janelas com chamas
            for i in range(5):
                wx = 150 + i * 220
                wy = 80 + (i % 2) * 60
                pygame.draw.rect(screen, (30, 12, 45), (wx, wy, 30, 50), border_radius=3)
                flame_y = wy + 45 - int(abs(math.sin(t*0.06+i))*12)
                pygame.draw.polygon(screen, (200, 80, 20),
                    [(wx+5, wy+50),(wx+15, flame_y),(wx+25, wy+50)])
                pygame.draw.polygon(screen, (255,180,50),
                    [(wx+9, wy+50),(wx+15, flame_y+8),(wx+21, wy+50)])

        # Nuvens / neblina
        if z['has_clouds']:
            for cx3, cy3, spd, sz in self.bg_clouds:
                nx = (cx3 + t * spd * 0.25) % (SCREEN_WIDTH + sz)
                cs = pygame.Surface((int(sz*2), int(sz*0.55)), pygame.SRCALPHA)
                pygame.draw.ellipse(cs, (*z['cloud_col'], z['cloud_alpha']),
                                    (0, 0, int(sz*2), int(sz*0.55)))
                screen.blit(cs, (int(nx - sz), int(cy3)))

        # Estrelas
        if z['has_stars']:
            sc = z['star_col']
            sa = z['star_alpha_base']
            for sx2, sy2, sr2, bright in self.bg_stars:
                if sy2 > SCREEN_HEIGHT - 120: continue
                twinkle = abs(math.sin(t*0.03 + sx2*0.1)) * bright
                alpha   = int(sa + twinkle * (255 - sa))
                ss = pygame.Surface((sr2*2+2, sr2*2+2), pygame.SRCALPHA)
                pygame.draw.circle(ss, (*sc, alpha), (sr2+1, sr2+1), sr2)
                screen.blit(ss, (sx2-sr2, sy2-sr2))

        # Névoa no chão
        fog_surf = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
        fc = z['fog_col']
        fa = z['fog_alpha']
        for fy in range(70):
            a2 = int((1 - fy/70) * fa)
            pygame.draw.rect(fog_surf, (*fc, a2), (0, fy, SCREEN_WIDTH, 1))
        screen.blit(fog_surf, (0, SCREEN_HEIGHT - 110))

    def draw(self):
        offset_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        offset_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0

        # ── Cutscene: desenha por cima de tudo ───────────────────────────────
        if self.state == 'cutscene':
            if self.cutscene:
                self.cutscene.draw(screen)
            return

        self.draw_background()

        if self.state == 'menu':
            self.draw_menu()
        elif self.state in ['playing', 'combat', 'victory']:
            self.draw_game(offset_x, offset_y)
            self.draw_hud()

            if self.state == 'combat':
                self.combat.draw(screen)

            if self.level_text_timer > 0:
                alpha = min(255, self.level_text_timer * 4)
                banner = pygame.Surface((500, 60), pygame.SRCALPHA)
                pygame.draw.rect(banner, (10, 10, 30, 180), (0, 0, 500, 60), border_radius=8)
                pygame.draw.rect(banner, (80, 120, 200, alpha), (0, 0, 500, 60), 2, border_radius=8)
                screen.blit(banner, (SCREEN_WIDTH // 2 - 250, 85))
                text = font_medium.render(self.level_text, True, COLORS['xp_gold'])
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 95))

        elif self.state == 'game_over':
            self.draw_game(offset_x, offset_y)
            self.draw_hud()
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            pulse = abs(math.sin(self.game_timer * 0.05))
            r = int(180 + 75 * pulse)
            go_text = font_large.render("GAME OVER", True, (r, 30, 30))
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
            pygame.draw.rect(screen, (80, 20, 20), (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2, 400, 2))
            restart_text = font_small.render("Pressione ENTER para reiniciar", True, (200, 180, 180))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))

        elif self.state == 'victory':
            self.draw_game(offset_x, offset_y)
            if random.random() < 0.3:
                self.particles.append(Particle(
                    random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT,
                    COLORS['xp_gold'], random.uniform(-3,3), random.uniform(-10,-5), 100))
            for p in self.particles:
                p.draw(screen)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            pulse = abs(math.sin(self.game_timer * 0.06))
            gy = int(180 + 75 * pulse)
            vic_text = font_large.render("VOCE VENCEU!", True, (255, gy, 0))
            screen.blit(vic_text, (SCREEN_WIDTH//2 - vic_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
            sub_text = font_medium.render("A Sombra Eterna foi destruida!", True, COLORS['text'])
            screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, SCREEN_HEIGHT//2))
            stats_text = font_small.render(
                f"Nivel: {self.player.level}  XP: {self.player.xp}  Ouro: {getattr(self.player,'gold',0)}",
                True, COLORS['xp_gold'])
            screen.blit(stats_text, (SCREEN_WIDTH//2 - stats_text.get_width()//2, SCREEN_HEIGHT//2 + 60))
            restart_text = font_small.render("Pressione ENTER para jogar novamente", True, COLORS['text'])
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 110))

        # ── Upgrade menu por cima do jogo ─────────────────────────────────────
        if self.upgrade_menu:
            self.upgrade_menu.draw(screen)
    
    def draw_menu(self):
        t = self.game_timer
        # Fundo já foi desenhado por draw_background()
        # Partículas de fundo flutuantes
        for i in range(15):
            px = (i * 137 + t // 2) % SCREEN_WIDTH
            py = (SCREEN_HEIGHT - 100) - ((t // 2 + i * 50) % (SCREEN_HEIGHT - 100))
            ps = pygame.Surface((4, 4), pygame.SRCALPHA)
            alpha = int(abs(math.sin(t * 0.02 + i)) * 120 + 60)
            pygame.draw.circle(ps, (100, 140, 255, alpha), (2, 2), 2)
            screen.blit(ps, (px, py))

        # Título com sombra e glow
        glow_r = int(abs(math.sin(t * 0.04)) * 30)
        for dx, dy in [(-2, 2), (2, 2), (0, 3)]:
            shadow = font_large.render("SHADOW REALM", True, (20, 10, 40))
            screen.blit(shadow, (SCREEN_WIDTH//2 - shadow.get_width()//2 + dx, 140 + dy))
        title_col = (220 + glow_r, 60, 80 + glow_r)
        title = font_large.render("SHADOW REALM", True, title_col)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 140))

        subtitle = font_medium.render("RPG de Plataforma", True, (180, 160, 60))
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 218))
        # linha decorativa
        line_w = 280
        pygame.draw.rect(screen, (80, 60, 20), (SCREEN_WIDTH//2 - line_w//2, 262, line_w, 2))
        pygame.draw.rect(screen, (180, 140, 40), (SCREEN_WIDTH//2 - line_w//2 + 20, 262, line_w - 40, 1))

        options = ["NOVO JOGO", "CONTINUAR" if os.path.exists(self.save_file) else "", "SAIR"]
        options = [o for o in options if o]

        for i, option in enumerate(options):
            selected = (i == self.menu_selection)
            btn_w, btn_h = 280, 46
            bx = SCREEN_WIDTH//2 - btn_w//2
            by = 320 + i * 62
            if selected:
                # Brilho ao redor do botão selecionado
                glow_s = pygame.Surface((btn_w + 10, btn_h + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, (255, 200, 0, 40), (0, 0, btn_w + 10, btn_h + 10), border_radius=8)
                screen.blit(glow_s, (bx - 5, by - 5))
                pygame.draw.rect(screen, (40, 32, 8), (bx + 2, by + 2, btn_w, btn_h), border_radius=6)
                pygame.draw.rect(screen, (60, 45, 10), (bx, by, btn_w, btn_h), border_radius=6)
                pygame.draw.rect(screen, COLORS['xp_gold'], (bx, by, btn_w, btn_h), 2, border_radius=6)
                color = COLORS['xp_gold']
            else:
                pygame.draw.rect(screen, (20, 18, 35), (bx, by, btn_w, btn_h), border_radius=6)
                pygame.draw.rect(screen, (50, 50, 80), (bx, by, btn_w, btn_h), 1, border_radius=6)
                color = (180, 180, 200)
            text = font_medium.render(option, True, color)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, by + 8))

        # Painel de controles
        ctrl_panel = pygame.Surface((220, 100), pygame.SRCALPHA)
        pygame.draw.rect(ctrl_panel, (10, 10, 25, 160), (0, 0, 220, 100), border_radius=6)
        pygame.draw.rect(ctrl_panel, (40, 40, 80, 120), (0, 0, 220, 100), 1, border_radius=6)
        screen.blit(ctrl_panel, (30, SCREEN_HEIGHT - 130))
        controls = ["CONTROLES:", "A/D ou Setas: Mover", "W/Espaco: Pular", "K/Z: Atacar"]
        for i, ctrl in enumerate(controls):
            col = (200, 180, 60) if i == 0 else (140, 140, 160)
            text = font_hud.render(ctrl, True, col)
            screen.blit(text, (45, SCREEN_HEIGHT - 122 + i * 22))
    
    def draw_game(self, offset_x, offset_y):
        zone_cfg = ZONE_CONFIG.get(self.current_level, ZONE_CONFIG[1])

        for plat in self.platforms:
            plat.draw(screen, zone_cfg)

        for door in self.doors:
            door.draw(screen)

        for chest in self.chests:
            chest.draw(screen)

        for npc in self.npcs:
            npc.draw(screen)

        # Indicador "E" perto de NPC próximo do player
        if self.player:
            for npc in self.npcs:
                if not npc.talked and abs(npc.x - self.player.x) < 80:
                    hint = font_small.render("[E] Falar", True, (255, 240, 80))
                    screen.blit(hint, (int(npc.x) - 20, int(npc.y) - 36))

        for monster in self.monsters:
            monster.draw(screen)

        if self.boss:
            self.boss.draw(screen)

        self.player.draw(screen)

        for p in self.particles:
            p.draw(screen)

        # Diálogo por cima de tudo
        if self.dialogue and not self.dialogue.done:
            self.dialogue.draw(screen)
    
    def draw_hud(self):
        # ── Painel esquerdo (HP / MP / Itens) ────────────────────────────────
        panel_w, panel_h = 265, 155
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 12, 28, 200), (0, 0, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(panel, (50, 70, 120, 180), (0, 0, panel_w, panel_h), 1, border_radius=8)
        screen.blit(panel, (12, 12))

        # HP bar
        hp_pct = max(0, self.player.hp / self.player.max_hp)
        hp_col = (60, 210, 90) if hp_pct > 0.6 else (220, 200, 30) if hp_pct > 0.3 else (220, 50, 50)
        hp_lbl = font_hud.render("HP", True, (220, 80, 80))
        screen.blit(hp_lbl, (22, 22))
        pygame.draw.rect(screen, (40, 8, 8), (42, 22, 220, 16), border_radius=4)
        if hp_pct > 0:
            pygame.draw.rect(screen, hp_col, (42, 22, int(220 * hp_pct), 16), border_radius=4)
            # brilho na barra
            pygame.draw.rect(screen, tuple(min(255, c + 60) for c in hp_col),
                             (42, 22, int(220 * hp_pct), 5), border_radius=4)
        pygame.draw.rect(screen, (100, 30, 30), (42, 22, 220, 16), 1, border_radius=4)
        hp_num = font_hud.render(f"{self.player.hp}/{self.player.max_hp}", True, (255, 255, 255))
        screen.blit(hp_num, (44, 24))

        # MP bar
        mp_pct = max(0, self.player.mp / self.player.max_mp)
        mp_lbl = font_hud.render("MP", True, (80, 140, 220))
        screen.blit(mp_lbl, (22, 46))
        pygame.draw.rect(screen, (8, 8, 50), (42, 46, 190, 12), border_radius=3)
        if mp_pct > 0:
            pygame.draw.rect(screen, (52, 152, 219), (42, 46, int(190 * mp_pct), 12), border_radius=3)
            pygame.draw.rect(screen, (120, 200, 255), (42, 46, int(190 * mp_pct), 4), border_radius=3)
        pygame.draw.rect(screen, (30, 50, 100), (42, 46, 190, 12), 1, border_radius=3)
        mp_num = font_hud.render(f"{self.player.mp}/{self.player.max_mp}", True, (180, 210, 255))
        screen.blit(mp_num, (44, 47))

        # ATK / DEF mini stats
        atk_t = font_hud.render(f"ATK {self.player.attack}", True, (255, 160, 80))
        def_t = font_hud.render(f"DEF {self.player.defense}", True, (100, 180, 255))
        screen.blit(atk_t, (22, 66))
        screen.blit(def_t, (110, 66))

        # Separador
        pygame.draw.rect(screen, (40, 55, 90), (22, 83, 240, 1))

        # Itens (teclas 1 e 2)
        items_data = [
            ("1", "Pocao HP", self.player.inventory.get('health_potion', 0), (80, 200, 100)),
            ("2", "Pocao MP", self.player.inventory.get('mana_potion', 0),   (80, 140, 220)),
        ]
        for i, (key, name, qty, col) in enumerate(items_data):
            iy = 90 + i * 26
            # tecla
            pygame.draw.rect(screen, (30, 30, 55), (22, iy, 18, 18), border_radius=3)
            pygame.draw.rect(screen, (80, 80, 120), (22, iy, 18, 18), 1, border_radius=3)
            k_t = font_hud.render(key, True, (200, 200, 200))
            screen.blit(k_t, (27, iy + 1))
            # nome e quantidade
            active = qty > 0
            name_t = font_hud.render(f"{name}: {qty}", True, col if active else (80, 80, 80))
            screen.blit(name_t, (44, iy + 1))

        # ── Painel direito (Level / XP / Fase) ───────────────────────────────
        rp_w, rp_h = 160, 80
        rp = pygame.Surface((rp_w, rp_h), pygame.SRCALPHA)
        pygame.draw.rect(rp, (10, 12, 28, 200), (0, 0, rp_w, rp_h), border_radius=8)
        pygame.draw.rect(rp, (80, 60, 20, 180), (0, 0, rp_w, rp_h), 1, border_radius=8)
        screen.blit(rp, (SCREEN_WIDTH - rp_w - 12, 12))

        lv_t = font_small.render(f"Nivel {self.player.level}", True, COLORS['xp_gold'])
        screen.blit(lv_t, (SCREEN_WIDTH - rp_w - 12 + rp_w//2 - lv_t.get_width()//2, 18))

        xp_pct = self.player.xp / self.player.xp_to_next
        xp_bw = rp_w - 20
        xp_bx = SCREEN_WIDTH - rp_w - 2
        pygame.draw.rect(screen, (40, 35, 5), (xp_bx, 46, xp_bw, 10), border_radius=3)
        pygame.draw.rect(screen, COLORS['xp_gold'], (xp_bx, 46, int(xp_bw * xp_pct), 10), border_radius=3)
        pygame.draw.rect(screen, (120, 100, 20), (xp_bx, 46, xp_bw, 10), 1, border_radius=3)

        xp_t = font_hud.render(f"XP {self.player.xp}/{self.player.xp_to_next}", True, (200, 180, 80))
        screen.blit(xp_t, (SCREEN_WIDTH - rp_w - 12 + rp_w//2 - xp_t.get_width()//2, 60))

        # Nome da zona (canto inferior direito) com cor temática
        zone_cfg = ZONE_CONFIG.get(self.current_level, ZONE_CONFIG[1])
        zona_t = font_hud.render(f"{zone_cfg['name']}  —  Fase {self.current_level}/{TOTAL_LEVELS}",
                                 True, zone_cfg['name_col'])
        screen.blit(zona_t, (SCREEN_WIDTH - zona_t.get_width() - 14, SCREEN_HEIGHT - 24))

        # Ouro (canto inferior direito acima da zona)
        gold_val = getattr(self.player, 'gold', 0)
        gold_t = font_hud.render(f"Ouro: {gold_val}", True, (255, 210, 50))
        screen.blit(gold_t, (SCREEN_WIDTH - gold_t.get_width() - 14, SCREEN_HEIGHT - 42))

        # Hint TAB
        tab_t = font_hud.render("[TAB] Upgrades", True, (100, 90, 140))
        screen.blit(tab_t, (SCREEN_WIDTH - tab_t.get_width() - 14, SCREEN_HEIGHT - 58))
    
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:

            # ── Cutscene: pular com SPACE/ENTER ──────────────────────────────
            if self.state == 'cutscene':
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    if self.cutscene:
                        self.cutscene.skip()
                return True

            # ── Upgrade menu aberto ───────────────────────────────────────────
            if self.upgrade_menu:
                if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
                    self.upgrade_menu = None
                else:
                    self.upgrade_menu.handle_key(event.key)
                return True

            # ── Diálogo ativo ─────────────────────────────────────────────────
            if self.dialogue and not self.dialogue.done:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e, pygame.K_z):
                    self.dialogue.advance()
                return True

            # ── Menu principal ────────────────────────────────────────────────
            if self.state == 'menu':
                if event.key in (pygame.K_w, pygame.K_UP):
                    options = ["NOVO JOGO", "CONTINUAR" if os.path.exists(self.save_file) else "", "SAIR"]
                    options = [o for o in options if o]
                    self.menu_selection = (self.menu_selection - 1) % len(options)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    options = ["NOVO JOGO", "CONTINUAR" if os.path.exists(self.save_file) else "", "SAIR"]
                    options = [o for o in options if o]
                    self.menu_selection = (self.menu_selection + 1) % len(options)
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
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
                # TAB: abrir upgrades
                if event.key == pygame.K_TAB:
                    self._ensure_player_extras()
                    self.upgrade_menu = UpgradeMenu(self.player)

                elif event.key in (pygame.K_k, pygame.K_z):
                    self.player.attacking = True
                    self.player.attack_timer = 15
                    attack_rect = self.player.attack_rect()
                    for monster in self.monsters:
                        if monster.alive and attack_rect.colliderect(monster.rect()):
                            mon_def = getattr(monster, 'defense', 0)
                            damage = max(1, self.player.attack - mon_def + random.randint(-2, 5))
                            monster.take_damage(damage)
                            self.screen_shake = 5
                            for _ in range(5):
                                self.particles.append(Particle(
                                    monster.x + monster.width//2, monster.y + monster.height//2,
                                    COLORS['damage'], random.uniform(-5,5), random.uniform(-5,5), 30))
                    if self.boss and self.boss.alive and attack_rect.colliderect(self.boss.rect()):
                        boss_def = getattr(self.boss, 'defense', 0)
                        damage = max(1, self.player.attack - boss_def + random.randint(-2, 5))
                        self.boss.take_damage(damage)
                        self.screen_shake = 10
                        for _ in range(10):
                            self.particles.append(Particle(
                                self.boss.x + self.boss.width//2, self.boss.y + self.boss.height//2,
                                COLORS['damage'], random.uniform(-5,5), random.uniform(-5,5), 30))

                elif event.key == pygame.K_e:
                    for npc in self.npcs:
                        if abs(npc.x - self.player.x) < 90:
                            npc.talked = True
                            self._trigger_story(npc.dialogue_key)
                            break

                elif event.key == pygame.K_1:
                    self.player.use_item('health_potion')
                elif event.key == pygame.K_2:
                    self.player.use_item('mana_potion')
                elif event.key == pygame.K_ESCAPE:
                    self.save_game()
                    self.state = 'menu'

            elif self.state == 'combat':
                if self.combat.phase != 'player_turn':
                    return True
                # Abrir upgrades no combate também
                if event.key == pygame.K_TAB:
                    self._ensure_player_extras()
                    self.upgrade_menu = UpgradeMenu(self.player)
                    return True
                # Grade 3×2 de habilidades
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.combat.selected_option = (self.combat.selected_option - 1) % 6
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.combat.selected_option = (self.combat.selected_option + 1) % 6
                elif event.key in (pygame.K_w, pygame.K_UP):
                    self.combat.selected_option = (self.combat.selected_option - 3) % 6
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.combat.selected_option = (self.combat.selected_option + 3) % 6
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    opt = self.combat.selected_option
                    skills = getattr(self.player, 'unlocked_skills', set())
                    if opt == 0:
                        self.combat.player_attack()
                    elif opt == 1:
                        # Blitz ou Golpe Forte
                        if 'blitz' in skills:
                            self.combat.player_blitz()
                        else:
                            self.combat.player_heavy_attack()
                    elif opt == 2:
                        # Meteoro ou Escudo
                        if 'meteor' in skills:
                            self.combat.player_meteor()
                        else:
                            self.combat.player_weaken()
                    elif opt == 3:
                        # Drenar ou Cura
                        if 'drain' in skills:
                            self.combat.player_drain()
                        else:
                            self.combat.player_divine_heal()
                    elif opt == 4:
                        # Barreira ou Poção
                        if 'barrier' in skills and not getattr(self.player,'barrier_active',False):
                            self.combat.player_barrier()
                        else:
                            self.combat.player_item('health_potion')
                    elif opt == 5:
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
                'inventory': self.player.inventory,
                'gold': getattr(self.player, 'gold', 0),
                'crit_bonus': getattr(self.player, 'crit_bonus', 0),
                'hp_regen': getattr(self.player, 'hp_regen', 0),
                'mp_regen': getattr(self.player, 'mp_regen', 0),
                'upgrade_levels': getattr(self.player, 'upgrade_levels', {}),
                'unlocked_skills': list(getattr(self.player, 'unlocked_skills', set())),
            },
            'current_level': self.current_level,
            'story_seen': list(self.story_seen),
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
            p = save_data['player']
            self.player = Player(p['x'], p['y'])
            self.player.level         = p['level']
            self.player.xp            = p['xp']
            self.player.hp            = p['hp']
            self.player.mp            = p['mp']
            self.player.max_hp        = p['max_hp']
            self.player.max_mp        = p['max_mp']
            self.player.base_attack   = p['base_attack']
            self.player.base_defense  = p['base_defense']
            self.player.attack_boost  = p['attack_boost']
            self.player.defense_boost = p['defense_boost']
            self.player.inventory     = p['inventory']
            self.player.xp_to_next    = self.player.level * 100
            self.player.gold          = p.get('gold', 150)
            self.player.crit_bonus    = p.get('crit_bonus', 0)
            self.player.hp_regen      = p.get('hp_regen', 0)
            self.player.mp_regen      = p.get('mp_regen', 0)
            self.player.upgrade_levels   = p.get('upgrade_levels', {})
            self.player.unlocked_skills  = set(p.get('unlocked_skills', []))
            self.player.barrier_active   = False
            self.player.revive_ready     = False
            self.story_seen = set(save_data.get('story_seen', []))
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