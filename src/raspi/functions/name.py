import pygame
from .database import DataBase

class NameInputManager:
    def __init__(self, db: DataBase, get_asset_path_func):
        self.db = db
        self.get_asset_path_func = get_asset_path_func
        
        self.active = False
        self.allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        self.name_length = 5
        self.player_name_chars = ["A"] * self.name_length
        self.current_focus_index = 0
        self.final_entered_name = ""
        self.current_score = 0

        self.ok_button_index = self.name_length
        self.num_focus_items = self.name_length + 1

        self.last_input_time = 0
        self.input_delay = 20 
        
        self.fonts = {}

    def _load_fonts(self, cell_size):
        """Loads and caches fonts for the UI."""
        if cell_size in self.fonts:
            return self.fonts[cell_size]
        
        try:
            font_path = self.get_asset_path_func("Font/PoetsenOne-Regular.ttf")
            title_font = pygame.font.Font(font_path, int(cell_size * 1.2))
            char_font = pygame.font.Font(font_path, int(cell_size * 1.5))
            ok_font = pygame.font.Font(font_path, int(cell_size * 1.0))
        except (pygame.error, FileNotFoundError, TypeError):
            title_font = pygame.font.SysFont("Arial", int(cell_size * 1.2))
            char_font = pygame.font.SysFont("Arial", int(cell_size * 1.5))
            ok_font = pygame.font.SysFont("Arial", int(cell_size * 1.0))
            
        self.fonts[cell_size] = (title_font, char_font, ok_font)
        return self.fonts[cell_size]

    def activate(self, score_value):
        """Activates the name input screen."""
        self.active = True
        self.player_name_chars = ["A"] * self.name_length
        self.current_focus_index = 0
        self.current_score = score_value
        self.last_input_time = pygame.time.get_ticks()

    def deactivate(self):
        """Deactivates the name input screen."""
        self.active = False

    def get_final_name(self):
        return self.final_entered_name

    def handle_input(self, input_signal):
        """
        Processes key or button input.
        Returns a status string: "NAME_ENTERED", "ESC_PRESSED", "ACTION_TAKEN", or None.
        """
        if not self.active:
            return None

        now = pygame.time.get_ticks()
        if now - self.last_input_time < self.input_delay:
            return None  # Debounce

        self.last_input_time = now

        action = None
        if isinstance(input_signal, int):  # Pygame key
            if input_signal == pygame.K_UP:
                action = "UP"
            elif input_signal == pygame.K_DOWN:
                action = "DOWN"
            elif input_signal == pygame.K_LEFT:
                action = "LEFT"
            elif input_signal == pygame.K_RIGHT:
                action = "RIGHT"
            elif input_signal == pygame.K_RETURN:
                action = "CONFIRM_GLOBAL"
            elif input_signal == pygame.K_ESCAPE:
                action = "ESCAPE"
        elif isinstance(input_signal, str):  # Serial button
            if input_signal in {"UP", "DOWN", "LEFT", "RIGHT"}:
                action = input_signal

        if action == "LEFT":
            self.current_focus_index = (
                self.current_focus_index - 1 + self.num_focus_items
            ) % self.num_focus_items
            return "ACTION_TAKEN"

        elif action == "RIGHT":
            self.current_focus_index = (self.current_focus_index + 1) % self.num_focus_items
            return "ACTION_TAKEN"

        elif action in {"UP", "DOWN"}:
            if self.current_focus_index < self.name_length:
                # Change character
                char_idx = self.allowed_chars.find(self.player_name_chars[self.current_focus_index])
                if action == "UP":
                    char_idx = (char_idx - 1) % len(self.allowed_chars)
                else: # DOWN
                    char_idx = (char_idx + 1) % len(self.allowed_chars)
                self.player_name_chars[self.current_focus_index] = self.allowed_chars[char_idx]
                return "ACTION_TAKEN"
            
            elif self.current_focus_index == self.ok_button_index:
                # "Press" OK button
                self.final_entered_name = "".join(self.player_name_chars)
                self.db.append_team(self.final_entered_name, self.current_score)
                self.deactivate()
                return "NAME_ENTERED"

        elif action == "CONFIRM_GLOBAL":
            # Handle Enter key (confirm)
            if self.current_focus_index == self.ok_button_index:
                self.final_entered_name = "".join(self.player_name_chars)
                self.db.append_team(self.final_entered_name, self.current_score)
                self.deactivate()
                return "NAME_ENTERED"
            else:
                # Move to OK button if Enter is pressed on a char
                self.current_focus_index = self.ok_button_index
                return "ACTION_TAKEN"


        elif action == "ESCAPE":
            self.deactivate()
            return "ESC_PRESSED"

        return None

    def draw(self, screen, screen_width, screen_height, cell_size):
        """Draws the name input UI."""
        if not self.active:
            return

        title_font, char_font, ok_font = self._load_fonts(cell_size)

        title_surf = title_font.render("Teamnamen eingeben", True, (56, 74, 12))
        title_rect = title_surf.get_rect(center=(screen_width / 2, screen_height / 2 - cell_size * 3.5))
        screen.blit(title_surf, title_rect)

        char_width = char_font.size("W")[0]
        spacing = cell_size // 1.5
        total_name_width = self.name_length * char_width + (self.name_length - 1) * spacing
        
        ok_text_surf = ok_font.render("OK", True, (56, 74, 12))
        ok_width = ok_text_surf.get_width() + cell_size
        ok_spacing = spacing * 1.5

        block_width = total_name_width + ok_spacing + ok_width
        x_start = screen_width / 2 - block_width / 2
        x_offset = x_start
        char_y_center = screen_height / 2 - cell_size * 0.5

        for i in range(self.name_length):
            char = self.player_name_chars[i]
            char_surf = char_font.render(char, True, (56, 74, 12))
            char_center = (x_offset + char_width / 2, char_y_center)
            char_rect = char_surf.get_rect(center=char_center)
            screen.blit(char_surf, char_rect)

            if i == self.current_focus_index:
                underline = pygame.Rect(char_rect.left, char_rect.bottom + 2, char_rect.width, 4)
                pygame.draw.rect(screen, (56, 74, 12), underline)

            x_offset += char_width + spacing

        x_offset -= spacing
        x_offset += ok_spacing
        
        ok_color = (167, 209, 61)
        text_color = (56, 74, 12)

        example_height = char_font.render("A", True, (0, 0, 0)).get_height()
        ok_height = example_height + cell_size * 0.5

        ok_rect = pygame.Rect(
            x_offset,
            char_y_center - ok_height / 2,
            ok_width,
            ok_height,
        )

        if self.current_focus_index == self.ok_button_index:
            ok_color = (56, 74, 12)
            text_color = (220, 220, 220)
            pygame.draw.rect(screen, (255, 255, 255), ok_rect.inflate(6, 6), border_radius=7)

        pygame.draw.rect(screen, ok_color, ok_rect, border_radius=5)
        ok_final_surf = ok_font.render("OK", True, text_color)
        ok_text_rect = ok_final_surf.get_rect(center=ok_rect.center)
        screen.blit(ok_final_surf, ok_text_rect)
