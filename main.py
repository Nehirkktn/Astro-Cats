import pygame
import sys
import random
import os
import math

# --- AYARLAR ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Renkler
COLOR_BG = (15, 15, 40)
COLOR_TUBE = (200, 200, 255)
COLOR_TUBE_HOVER = (255, 255, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_ACCENT = (50, 255, 200)

# Buton Renkleri
BTN_COLOR_NORMAL = (70, 170, 70) 
BTN_COLOR_HOVER = (90, 200, 90)
BTN_COLOR_SHADOW = (30, 80, 30)
BTN_TEXT_COLOR = (255, 255, 255)

BTN_RED_NORMAL = (200, 60, 60)
BTN_RED_HOVER = (230, 80, 80)
BTN_RED_SHADOW = (100, 30, 30)

BTN_MENU_NORMAL = (100, 100, 120)
BTN_MENU_HOVER = (120, 120, 150)
BTN_MENU_SHADOW = (50, 50, 70)

# Kilitli Bölüm Rengi
BTN_LOCKED = (50, 50, 60)
BTN_LOCKED_TEXT = (100, 100, 100)

# Neon Renkleri
NEON_BLUE = (0, 255, 255)
NEON_PURPLE = (255, 0, 255)
NEON_GLOW_BLUE = (0, 150, 150)
NEON_GLOW_PURPLE = (150, 0, 150)

ALIEN_COLORS = [
    (255, 60, 60), (60, 255, 60), (60, 60, 255),
    (255, 255, 60), (255, 60, 255), (60, 255, 255)
]

# Boyutlar
TUBE_WIDTH = 70
TUBE_HEIGHT = 250
BLOCK_SIZE = 50
MAX_CAPACITY = 4
TUBE_SPACING = 100
TUBE_Y_POS = 250 
HOVER_HEIGHT = 180 

# --- FİZİK AYARLARI ---
GRAVITY = 2.5          
MAX_FALL_SPEED = 40    
LIFT_SPEED = 20        
TRANSFER_SPEED = 25    

# --- BUTON SINIFI ---
class Button:
    def __init__(self, text, x, y, width, height, color_base, color_hover, color_shadow, is_locked=False):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.shadow_rect = pygame.Rect(x, y + 5, width, height)
        self.color_base = color_base
        self.color_hover = color_hover
        self.color_shadow = color_shadow
        self.font = pygame.font.SysFont('Consolas', 24, bold=True)
        self.is_hovered = False
        self.is_locked = is_locked # Kilitli mi özelliği eklendi

    def draw(self, screen):
        # Eğer kilitliyse gri çiz
        if self.is_locked:
            pygame.draw.rect(screen, (30, 30, 40), self.shadow_rect, border_radius=8)
            pygame.draw.rect(screen, BTN_LOCKED, self.rect, border_radius=8)
            pygame.draw.rect(screen, (70, 70, 80), self.rect, 2, border_radius=8)
            text_surf = self.font.render(self.text, True, BTN_LOCKED_TEXT)
        else:
            pygame.draw.rect(screen, self.color_shadow, self.shadow_rect, border_radius=8)
            current_color = self.color_hover if self.is_hovered else self.color_base
            draw_rect = self.rect
            if self.is_hovered and pygame.mouse.get_pressed()[0]:
                draw_rect = pygame.Rect(self.rect.x, self.rect.y + 3, self.rect.width, self.rect.height)
            pygame.draw.rect(screen, current_color, draw_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_WHITE, draw_rect, 3, border_radius=8)
            text_surf = self.font.render(self.text, True, BTN_TEXT_COLOR)
        
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        if not self.is_locked:
            self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos):
        if self.is_locked: return False
        return self.rect.collidepoint(mouse_pos)

# --- OYUN SINIFI ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ASTRO CATS - Puzzle Mode")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Consolas', 24, bold=True)
        self.large_font = pygame.font.SysFont('Consolas', 40, bold=True)

        self.title_img = self.create_pixel_logo()
        self.alien_img = None
        self.load_alien_images()

        self.game_state = "MENU" # MENU, LEVEL_SELECT, PLAYING, WIN_SCREEN
        self.level = 1
        self.max_level_reached = 1 # Oyuncunun ulaştığı en yüksek seviye
        self.tubes = []
        
        self.active_block = None 
        
        self.stars = []
        for _ in range(80):
            self.stars.append([random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(1, 3), random.uniform(0.2, 1.0)])

        # --- BUTONLAR ---
        # Ana Menü Butonları
        self.btn_start = Button("CONTINUE", SCREEN_WIDTH//2 - 100, 380, 200, 60, BTN_COLOR_NORMAL, BTN_COLOR_HOVER, BTN_COLOR_SHADOW)
        self.btn_levels = Button("LEVELS", SCREEN_WIDTH//2 - 100, 460, 200, 60, BTN_MENU_NORMAL, BTN_MENU_HOVER, BTN_MENU_SHADOW)
        
        # Oyun İçi Butonlar
        self.btn_reset = Button("RESET", SCREEN_WIDTH - 240, 20, 100, 40, BTN_RED_NORMAL, BTN_RED_HOVER, BTN_RED_SHADOW)
        self.btn_menu = Button("MENU", SCREEN_WIDTH - 120, 20, 100, 40, BTN_MENU_NORMAL, BTN_MENU_HOVER, BTN_MENU_SHADOW)
        
        # Kazanma Ekranı Butonları
        self.btn_next = Button("NEXT LEVEL >>", SCREEN_WIDTH//2 - 120, 400, 240, 70, BTN_COLOR_NORMAL, BTN_COLOR_HOVER, BTN_COLOR_SHADOW)
        self.btn_levels_win = Button("LEVELS", SCREEN_WIDTH//2 - 80, 500, 160, 50, BTN_MENU_NORMAL, BTN_MENU_HOVER, BTN_MENU_SHADOW)

        # Bölüm Seçme Ekranı Butonları
        self.btn_back = Button("<< BACK", 20, 20, 120, 50, BTN_RED_NORMAL, BTN_RED_HOVER, BTN_RED_SHADOW)
        self.level_buttons = [] # Dinamik olarak oluşturulacak

    def load_alien_images(self):
        possible_files = ['alien.png.png', 'alien.png', 'Alien.png']
        loaded_surface = None
        for filename in possible_files:
            if os.path.exists(filename):
                try:
                    loaded_surface = pygame.image.load(filename).convert_alpha()
                    break
                except: continue
        if loaded_surface:
            self.alien_img = pygame.transform.scale(loaded_surface, (BLOCK_SIZE, BLOCK_SIZE))

    def create_pixel_logo(self):
        chars = {'A': [[0,1,1,0],[1,0,0,1],[1,1,1,1],[1,0,0,1],[1,0,0,1]], 'S': [[0,1,1,1],[1,0,0,0],[0,1,1,0],[0,0,0,1],[1,1,1,0]], 'T': [[1,1,1,1,1],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]], 'R': [[1,1,1,0],[1,0,0,1],[1,1,1,0],[1,0,1,0],[1,0,0,1]], 'O': [[0,1,1,0],[1,0,0,1],[1,0,0,1],[1,0,0,1],[0,1,1,0]], 'C': [[0,1,1,1],[1,0,0,0],[1,0,0,0],[1,0,0,0],[0,1,1,1]], ' ': [[0,0,0]]}
        word1, word2 = "ASTRO", "CATS"
        pixel_size = 10
        total_w = sum([len(chars.get(c, chars[' '])[0])+1 for c in word1+" "+word2])
        surf = pygame.Surface((total_w * pixel_size, 7 * pixel_size), pygame.SRCALPHA)
        def draw_word(word, main_c, glow_c, start_x):
            x_off = start_x
            for char in word:
                grid = chars.get(char, chars[' '])
                for r in range(len(grid)):
                    for c in range(len(grid[0])):
                        if grid[r][c]:
                            px, py = x_off + c * pixel_size, r * pixel_size
                            pygame.draw.rect(surf, (*glow_c, 150), (px-2, py-2, pixel_size+4, pixel_size+4), 2)
                            pygame.draw.rect(surf, main_c, (px, py, pixel_size-1, pixel_size-1))
                x_off += (len(grid[0]) + 1) * pixel_size
            return x_off
        end_x = draw_word(word1, NEON_BLUE, NEON_GLOW_BLUE, 0)
        draw_word(word2, NEON_PURPLE, NEON_GLOW_PURPLE, end_x + pixel_size*2)
        return surf

    def get_colored_alien(self, color):
        if self.alien_img is None:
            size = BLOCK_SIZE
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0,0,size,size), border_radius=8)
            pygame.draw.rect(surf, (255,255,255), (0,0,size,size), 2, border_radius=8)
            # Basit yüz
            pygame.draw.rect(surf, (0,0,0), (12, 18, 8, 8))
            pygame.draw.rect(surf, (0,0,0), (30, 18, 8, 8))
            return surf
        colored = self.alien_img.copy()
        c_surf = pygame.Surface(colored.get_size()).convert_alpha()
        c_surf.fill(color)
        colored.blit(c_surf, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        return colored

    def generate_level(self):
        difficulty_step = (self.level - 1) // 3
        num_colors = min(3 + difficulty_step, len(ALIEN_COLORS))
        
        items = [c for c in ALIEN_COLORS[:num_colors] for _ in range(MAX_CAPACITY)]
        random.shuffle(items)
        
        self.tubes = [items[i*MAX_CAPACITY:(i+1)*MAX_CAPACITY] for i in range(num_colors)]
        for _ in range(2): self.tubes.append([])
        
        self.active_block = None

    def init_level_select_buttons(self):
        # 20 Seviyelik buton oluştur
        self.level_buttons = []
        rows = 4
        cols = 5
        start_x = 150
        start_y = 150
        btn_size = 80
        gap = 20
        
        for i in range(20):
            lvl_num = i + 1
            x = start_x + (i % cols) * (btn_size + gap)
            y = start_y + (i // cols) * (btn_size + gap)
            
            # Eğer seviye, ulaşılan max seviyeden büyükse kilitli yap
            is_locked = lvl_num > self.max_level_reached
            
            # Renk belirle (Kilitli değilse)
            base = BTN_MENU_NORMAL
            hover = BTN_MENU_HOVER
            if lvl_num == self.level: # Seçili olan (oynanan) farklı renk
                base = BTN_COLOR_NORMAL
                hover = BTN_COLOR_HOVER
                
            btn = Button(str(lvl_num), x, y, btn_size, btn_size, base, hover, BTN_MENU_SHADOW, is_locked)
            self.level_buttons.append(btn)

    def draw_stars(self):
        for star in self.stars:
            star[1] += star[3]
            if star[1] > SCREEN_HEIGHT:
                star[1] = -5
                star[0] = random.randint(0, SCREEN_WIDTH)
            brightness = int(150 + star[3] * 100)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (int(star[0]), int(star[1])), star[2])

    def update_block_animation(self):
        if not self.active_block: return
        ab = self.active_block
        target_reached = False

        if ab['state'] == 'LIFTING':
            if ab['y'] > HOVER_HEIGHT: ab['y'] -= LIFT_SPEED
            else:
                ab['y'] = HOVER_HEIGHT; ab['state'] = 'HOVERING'; ab['vy'] = 0
        elif ab['state'] == 'HOVERING':
            ab['hover_tick'] += 0.1
            ab['y'] = HOVER_HEIGHT + math.sin(ab['hover_tick']) * 5
        elif ab['state'] == 'TRANSFERRING':
            dx = ab['target_x'] - ab['x']
            if abs(dx) < TRANSFER_SPEED:
                ab['x'] = ab['target_x']; ab['state'] = 'DROPPING'; ab['vy'] = 0
            else:
                ab['x'] += TRANSFER_SPEED if dx > 0 else -TRANSFER_SPEED
                ab['y'] = HOVER_HEIGHT
        elif ab['state'] == 'DROPPING' or ab['state'] == 'RETURNING':
            ab['vy'] += GRAVITY
            if ab['vy'] > MAX_FALL_SPEED: ab['vy'] = MAX_FALL_SPEED
            ab['y'] += ab['vy']
            if ab['y'] >= ab['target_y']:
                ab['y'] = ab['target_y']; target_reached = True

        if target_reached:
            dest_idx = ab['dest_idx']
            self.tubes[dest_idx].append(ab['color'])
            if ab['state'] == 'DROPPING': 
                if self.check_win(): 
                    # KAZANMA DURUMUNDA MAX LEVEL GÜNCELLE
                    if self.level == self.max_level_reached:
                        self.max_level_reached += 1
                    self.game_state = "WIN_SCREEN"
            self.active_block = None

    def handle_game_click(self, pos):
        if self.btn_reset.is_clicked(pos):
            self.generate_level()
            return
        if self.btn_menu.is_clicked(pos):
            self.game_state = "MENU"
            return
        
        if self.active_block and self.active_block['state'] not in ['HOVERING']: return
        
        total_w = len(self.tubes) * TUBE_SPACING
        start_x_global = (SCREEN_WIDTH - total_w) // 2 + (TUBE_SPACING - TUBE_WIDTH) // 2
        
        clicked_tube_idx = -1
        for i in range(len(self.tubes)):
            rect = pygame.Rect(start_x_global + i * TUBE_SPACING, TUBE_Y_POS, TUBE_WIDTH, TUBE_HEIGHT)
            if rect.collidepoint(pos):
                clicked_tube_idx = i; break
        
        if clicked_tube_idx == -1: return

        if self.active_block is None:
            src_tube = self.tubes[clicked_tube_idx]
            if src_tube:
                color = src_tube.pop()
                start_x = start_x_global + clicked_tube_idx * TUBE_SPACING + (TUBE_WIDTH - BLOCK_SIZE) // 2
                start_y = TUBE_Y_POS + TUBE_HEIGHT - (len(src_tube) + 1) * (BLOCK_SIZE + 5) - 5
                self.active_block = {'state': 'LIFTING', 'color': color, 'x': start_x, 'y': start_y, 'vy': 0, 'source_idx': clicked_tube_idx, 'dest_idx': None, 'hover_tick': 0}
        elif self.active_block['state'] == 'HOVERING':
            src_idx = self.active_block['source_idx']; dest_idx = clicked_tube_idx
            dest_tube = self.tubes[dest_idx]
            dest_x = start_x_global + dest_idx * TUBE_SPACING + (TUBE_WIDTH - BLOCK_SIZE) // 2
            
            is_valid = False
            if src_idx != dest_idx:
                if len(dest_tube) < MAX_CAPACITY:
                    if not dest_tube or dest_tube[-1] == self.active_block['color']: is_valid = True
            
            if is_valid:
                target_y = TUBE_Y_POS + TUBE_HEIGHT - (len(dest_tube) + 1) * (BLOCK_SIZE + 5) - 5
                self.active_block.update({'state': 'TRANSFERRING', 'target_x': dest_x, 'target_y': target_y, 'dest_idx': dest_idx, 'vy': 0})
            else:
                target_y = TUBE_Y_POS + TUBE_HEIGHT - (len(self.tubes[src_idx]) + 1) * (BLOCK_SIZE + 5) - 5
                self.active_block.update({'state': 'RETURNING', 'target_y': target_y, 'dest_idx': src_idx, 'vy': 0})

    def check_win(self):
        for tube in self.tubes:
            if len(tube) == 0: continue
            if len(tube) != MAX_CAPACITY or any(c != tube[0] for c in tube): return False
        return True

    def draw_game(self):
        self.screen.fill(COLOR_BG)
        self.draw_stars()
        self.update_block_animation()
        
        mouse_pos = pygame.mouse.get_pos()
        self.btn_reset.check_hover(mouse_pos); self.btn_reset.draw(self.screen)
        self.btn_menu.check_hover(mouse_pos); self.btn_menu.draw(self.screen)
        
        lvl_txt = self.font.render(f"LEVEL: {self.level}", True, COLOR_ACCENT)
        self.screen.blit(lvl_txt, (30, 30))
        
        total_w = len(self.tubes) * TUBE_SPACING
        start_x_global = (SCREEN_WIDTH - total_w) // 2 + (TUBE_SPACING - TUBE_WIDTH) // 2
        
        for i, tube in enumerate(self.tubes):
            tx = start_x_global + i * TUBE_SPACING
            ty = TUBE_Y_POS
            tube_rect = pygame.Rect(tx, ty, TUBE_WIDTH, TUBE_HEIGHT)
            border_color = COLOR_TUBE
            is_valid_target = False
            
            if self.active_block and self.active_block['state'] == 'HOVERING':
                if i != self.active_block['source_idx'] and len(tube) < MAX_CAPACITY:
                     if not tube or tube[-1] == self.active_block['color']: is_valid_target = True
                if tube_rect.collidepoint(mouse_pos):
                    border_color = NEON_BLUE if is_valid_target else (100, 50, 50)
            elif tube_rect.collidepoint(mouse_pos) and not self.active_block: border_color = COLOR_TUBE_HOVER
            if self.active_block and self.active_block['source_idx'] == i: border_color = COLOR_ACCENT

            pygame.draw.rect(self.screen, (30, 30, 60), tube_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, tube_rect, 3, border_radius=10)
            for j, color in enumerate(tube):
                alien = self.get_colored_alien(color)
                ax = tx + (TUBE_WIDTH - BLOCK_SIZE) // 2
                ay = ty + TUBE_HEIGHT - (j + 1) * (BLOCK_SIZE + 5) - 5
                self.screen.blit(alien, (ax, ay))
        if self.active_block:
            alien = self.get_colored_alien(self.active_block['color'])
            self.screen.blit(alien, (self.active_block['x'], self.active_block['y']))
        pygame.display.flip()

    def draw_menu(self):
        self.screen.fill(COLOR_BG)
        self.draw_stars()
        if self.title_img:
            title_rect = self.title_img.get_rect(center=(SCREEN_WIDTH // 2, 180))
            self.screen.blit(self.title_img, title_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        self.btn_start.check_hover(mouse_pos)
        self.btn_start.draw(self.screen)
        
        self.btn_levels.check_hover(mouse_pos)
        self.btn_levels.draw(self.screen)
        
        pygame.display.flip()

    # --- YENİ EKLENEN LEVEL SEÇİM EKRANI ---
    def draw_level_select(self):
        self.screen.fill(COLOR_BG)
        self.draw_stars()
        
        # Başlık
        title = self.large_font.render("SELECT LEVEL", True, NEON_PURPLE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 80)))
        
        # Geri butonu
        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.check_hover(mouse_pos)
        self.btn_back.draw(self.screen)
        
        # Seviye butonlarını çiz
        for btn in self.level_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)
            
        pygame.display.flip()

    def draw_win_screen(self):
        self.draw_game()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0, 180))
        self.screen.blit(overlay, (0,0))
        
        title = self.font.render("LEVEL COMPLETED!", True, NEON_BLUE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 250)))
        
        mouse_pos = pygame.mouse.get_pos()
        self.btn_next.check_hover(mouse_pos)
        self.btn_next.draw(self.screen)
        
        # Kazanma ekranına da levels butonu ekleyelim
        self.btn_levels_win.check_hover(mouse_pos)
        self.btn_levels_win.draw(self.screen)
        
        pygame.display.flip()

    def run(self):
        while True:
            pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(), sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # --- MENÜ ETKİLEŞİMLERİ ---
                    if self.game_state == "MENU":
                        if self.btn_start.is_clicked(pos):
                            self.generate_level()
                            self.game_state = "PLAYING"
                        if self.btn_levels.is_clicked(pos):
                            self.init_level_select_buttons() # Butonları güncelle
                            self.game_state = "LEVEL_SELECT"
                    
                    # --- OYUN ETKİLEŞİMLERİ ---
                    elif self.game_state == "PLAYING":
                        self.handle_game_click(pos)
                        
                    # --- KAZANMA EKRANI ETKİLEŞİMLERİ ---
                    elif self.game_state == "WIN_SCREEN":
                        if self.btn_next.is_clicked(pos):
                            self.level += 1
                            if self.level > self.max_level_reached:
                                self.max_level_reached = self.level
                            self.generate_level()
                            self.game_state = "PLAYING"
                        if self.btn_levels_win.is_clicked(pos):
                            self.init_level_select_buttons()
                            self.game_state = "LEVEL_SELECT"

                    # --- LEVEL SEÇİM EKRANI ETKİLEŞİMLERİ ---
                    elif self.game_state == "LEVEL_SELECT":
                        if self.btn_back.is_clicked(pos):
                            self.game_state = "MENU"
                        
                        # Bölüm numarasına tıklandı mı?
                        for i, btn in enumerate(self.level_buttons):
                            if btn.is_clicked(pos):
                                self.level = i + 1
                                self.generate_level()
                                self.game_state = "PLAYING"

            if self.game_state == "MENU": self.draw_menu()
            elif self.game_state == "PLAYING": self.draw_game()
            elif self.game_state == "WIN_SCREEN": self.draw_win_screen()
            elif self.game_state == "LEVEL_SELECT": self.draw_level_select()
            
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()