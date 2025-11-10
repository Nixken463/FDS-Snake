#!/usr/bin/env python3
import pygame
from pygame.math import Vector2
from enum import Enum, auto

from functions.get_asset_path import get_asset_path
from functions.body import SNAKE
from functions.fruit import FRUIT
from functions.controls import read_button_input
from functions.directions import draw_direction_buttons, update_arrow_directions
from functions.name import NameInputManager
from functions.database import DataBase
from functions.utils import shuffle_list

class GameState(Enum):
    """Manages the game's current state."""
    PLAYING = auto()
    GAME_OVER = auto()
    NAME_INPUT = auto()

class Game:
    """
    Main game class to manage state, logic, and rendering.
    """
    def __init__(self):
        pygame.init()

        self.info = pygame.display.Info()
        self.screen_width, self.screen_height = self.info.current_w, self.info.current_h
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.running = True
         
        self.cell_size = 40
        self.cell_number_x = self.screen_width // self.cell_size
        self.cell_number_y = (self.screen_height - self.cell_size * 2) // self.cell_size
        self.base_speed = 140
        self.min_speed = 75
        self.speed_increment = 5
        self.input_delay = 20

        self.apple_image = self.load_image("assets/apple.png")
        self.apple_image_for_score = self.scale_image(self.apple_image, 0.8)
        self.crown_image = self.load_image("assets/crown.png")
        self.crown_image_for_score = self.scale_image(self.crown_image, 0.8)
        self.game_font = self.load_font("Font/PoetsenOne-Regular.ttf", 0.8)
        self.game_over_title_font = self.load_font("Font/PoetsenOne-Regular.ttf", 3.0)
        self.game_over_msg_font = self.load_font("Font/PoetsenOne-Regular.ttf", 1.2)

        self.db = DataBase()
        self.name_manager = NameInputManager(self.db, get_asset_path)
        
        self.start_vectors = [
            Vector2(-1, 0),  # Index 0: LEFT
            Vector2(0, 1),   # Index 1: DOWN
            Vector2(0, -1),  # Index 2: UP
            Vector2(1, 0),   # Index 3: RIGHT
        ]
        
        self.SCREEN_UPDATE = pygame.USEREVENT
        
        self.reset_game()

    def load_image(self, path):
        """Helper to load and convert images."""
        return pygame.image.load(get_asset_path(path)).convert_alpha()

    def scale_image(self, image, scale_factor):
        """Helper to scale images relative to cell size."""
        size = int(self.cell_size * scale_factor)
        return pygame.transform.scale(image, (size, size))

    def load_font(self, path, scale_factor):
        """Helper to load fonts relative to cell size."""
        try:
            return pygame.font.Font(get_asset_path(path), int(self.cell_size * scale_factor))
        except (pygame.error, FileNotFoundError):
            print(f"Warning: Font not found at {path}. Falling back to Arial.")
            return pygame.font.SysFont("Arial", int(self.cell_size * scale_factor))

    def reset_game(self):
        """Resets the game to the initial state."""
        self.vectors = self.start_vectors[:]
        update_arrow_directions(self.vectors) # Syncs UI
        self.snake = SNAKE(self.screen, self.cell_size)
        self.fruit = FRUIT(self.screen, self.cell_size, self.apple_image, self.cell_number_x, self.cell_number_y)
        
        self.current_speed = self.base_speed
        pygame.time.set_timer(self.SCREEN_UPDATE, self.current_speed)
        
        self.game_state = GameState.PLAYING
        self.name_manager.deactivate()
        self.new_direction = Vector2(1, 0) # Start moving right
        self.last_input_time = 0

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(60)
        
        self.db.close()
        pygame.quit()

    def handle_events(self):
        """Processes all pygame events and serial input."""
        current_time_ms = pygame.time.get_ticks()
        processed_action_this_frame = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == self.SCREEN_UPDATE:
                self.handle_screen_update()

            if event.type == pygame.KEYDOWN:
                if current_time_ms - self.last_input_time >= self.input_delay:
                    processed_action_this_frame = self.handle_keydown(event.key, current_time_ms)
        
        if not processed_action_this_frame and (current_time_ms - self.last_input_time >= self.input_delay):
            button_command = read_button_input()
            if button_command:
                self.handle_button_input(button_command, current_time_ms)

    def handle_screen_update(self):
        """Handles the game logic update tied to the custom timer."""
        if self.game_state == GameState.PLAYING:
            self.snake.direction = self.new_direction
            self.update_game_logic()

    def handle_keydown(self, key, current_time_ms):
        """Dispatches keydown events based on game state."""
        action_taken = False
        if self.game_state == GameState.NAME_INPUT:
            result = self.name_manager.handle_input(key)
            if result:
                action_taken = True
                if result in ("NAME_ENTERED", "ESC_PRESSED"):
                    print(f"Player: {self.name_manager.get_final_name()} | Score: {self.name_manager.current_score}")
                    self.reset_game()
        
        elif self.game_state == GameState.PLAYING:
            action_taken = self.handle_playing_keydown(key)

        elif self.game_state == GameState.GAME_OVER:
            if key == pygame.K_ESCAPE:
                self.running = False
            else:
                self.reset_game()
            action_taken = True

        if action_taken:
            self.last_input_time = current_time_ms
        return action_taken

    def handle_playing_keydown(self, key):
        """Handles key presses during the 'PLAYING' state."""
        current_direction = self.snake.direction
        potential_new_direction = None
        action_taken = True
        
        if key == pygame.K_LEFT:
            potential_new_direction = self.vectors[0] # Index 0: LEFT
        elif key == pygame.K_DOWN:
            potential_new_direction = self.vectors[1] # Index 1: DOWN
        elif key == pygame.K_UP:
            potential_new_direction = self.vectors[2] # Index 2: UP
        elif key == pygame.K_RIGHT:
            potential_new_direction = self.vectors[3] # Index 3: RIGHT
        elif key == pygame.K_ESCAPE:
            self.running = False
            return True 
        else:
            action_taken = False
            return False 
        
        if potential_new_direction and potential_new_direction + current_direction != Vector2(0, 0):
            self.new_direction = potential_new_direction
        else:
            action_taken = False 

        return action_taken

    def handle_button_input(self, command, current_time_ms):
        """Dispatches serial button commands based on game state."""
        action_taken = False
        if self.game_state == GameState.NAME_INPUT:
            result = self.name_manager.handle_input(command)
            if result:
                action_taken = True
                if result in ("NAME_ENTERED", "ESC_PRESSED"):
                    print(f"Player: {self.name_manager.get_final_name()} | Score: {self.name_manager.current_score}")
                    self.reset_game()

        elif self.game_state == GameState.PLAYING:
            current_direction = self.snake.direction
            potential_new_direction = None
            action_taken = True
            
            if command == "LEFT":
                potential_new_direction = self.vectors[0] # Index 0: LEFT (Blue)
            elif command == "DOWN":
                potential_new_direction = self.vectors[1] # Index 1: DOWN (Red)
            elif command == "UP":
                potential_new_direction = self.vectors[2] # Index 2: UP (Green)
            elif command == "RIGHT":
                potential_new_direction = self.vectors[3] # Index 3: RIGHT (Yellow)
            else:
                action_taken = False
            
            if potential_new_direction and potential_new_direction + current_direction != Vector2(0, 0):
                self.new_direction = potential_new_direction
            else:
                action_taken = False 
        
        elif self.game_state == GameState.GAME_OVER:
            self.reset_game()
            action_taken = True

        if action_taken:
            self.last_input_time = current_time_ms

    def update_game_logic(self):
        """Updates snake movement and checks for collisions."""
        self.snake.move_snake(self.cell_number_x, self.cell_number_y)
        self.check_fruit_collision()
        self.check_fail_collision()

    def check_fruit_collision(self):
        """Checks for fruit collision and updates game accordingly."""
        if self.fruit.position == self.snake.body[0]:
            self.fruit.randomize()
            self.snake.add_block()
            score = len(self.snake.body) - 2
            if score % 5 == 0 and score != 0:
                print(f"Score: {score}. Shuffling directions!")
                self.vectors = shuffle_list(self.start_vectors[:])
                update_arrow_directions(self.vectors)
            
            for b in self.snake.body:
                if self.fruit.position == b:
                    self.fruit.randomize()
            
            self.update_speed()

    def check_fail_collision(self):
        """Checks for wall or self collision."""
        head = self.snake.body[0]
        # Check wall collision
        if not (0 <= head.x < self.cell_number_x and 0 <= head.y < self.cell_number_y):
            self.game_over()
        # Check self collision
        for b in self.snake.body[1:]:
            if b == head:
                self.game_over()

    def game_over(self):
        """Handles the game over logic."""
        self.game_state = GameState.GAME_OVER
        current_score_val = len(self.snake.body) - 3
        
        self.vectors = self.start_vectors[:] 
        update_arrow_directions(self.vectors)

        if self.db.in_top10(current_score_val):
            self.name_manager.activate(current_score_val)
            self.game_state = GameState.NAME_INPUT

    def update_speed(self):
        """Increases game speed based on snake length."""
        score = len(self.snake.body) - 3
        new_speed = max(self.min_speed, self.base_speed - (score * self.speed_increment))
        if new_speed != self.current_speed:
            self.current_speed = new_speed
            pygame.time.set_timer(self.SCREEN_UPDATE, self.current_speed)

    def render(self):
        """Renders all game elements based on the current state."""
        
        if self.game_state == GameState.PLAYING:
            self.screen.fill((175, 215, 70))
            self.fruit.draw_fruit()
            self.snake.draw_snake()
            self.draw_score()
            self.draw_highscore()

        elif self.game_state == GameState.NAME_INPUT:
            self.screen.fill((175, 215, 70))
            self.name_manager.draw(
                self.screen, self.screen_width, self.screen_height, self.cell_size
            )

        elif self.game_state == GameState.GAME_OVER:
            self.render_game_over_screen()

        draw_direction_buttons(self.screen, self.screen_width, self.screen_height, self.cell_size)
        pygame.display.update()

    def render_game_over_screen(self):
        """Renders the 'Game Over' message."""
        self.screen.fill((0, 0, 0))
        
        ts = self.game_over_title_font.render("Game Over!", True, (190, 0, 0))
        isf_text = "Drücke einen Knopf zum starten"
        isf = self.game_over_msg_font.render(isf_text, True, (200, 200, 200))

        tr = ts.get_rect(center=(self.screen_width / 2, self.screen_height / 2 - self.cell_size * 2.5))
        ir = isf.get_rect(center=(self.screen_width / 2, self.screen_height / 2 + self.cell_size * 1.5))

        self.screen.blit(ts, tr)
        self.screen.blit(isf, ir)

    def draw_score(self):
        """Draws the current game score."""
        s = str(len(self.snake.body) - 3)
        surf = self.game_font.render(s, True, (56, 74, 12))
        sx = self.screen_width - (self.cell_size * 2.5)
        sy = self.cell_size * 1.5
        rect = surf.get_rect(center=(sx, sy))
        
        bg_rect_width = surf.get_width() + self.cell_size
        bg = pygame.Rect(0, 0, bg_rect_width + 40, rect.height + 30)
        bg.midright = (self.screen_width - self.cell_size * 0.5, rect.centery)

        pygame.draw.rect(self.screen, (167, 209, 61), bg, border_radius=5)
        self.screen.blit(surf, surf.get_rect(midright=(bg.right - 10, bg.centery)))
        
        apple_width = int(self.cell_size * 1.5)
        apple_height = int(self.cell_size * 1.5)
        scaled_apple = pygame.transform.scale(self.apple_image_for_score, (apple_width, apple_height))
        ar = scaled_apple.get_rect(midright=(bg.left + scaled_apple.get_width() + 10, bg.centery))
        self.screen.blit(scaled_apple, ar)

    def draw_highscore(self):
        """Draws the all-time high score."""
        x = self.cell_size * 1.5
        y = self.cell_size * 1.5

        top_score = self.db.get_top_score()
        score_str = str(top_score)

        surf = self.game_font.render(score_str, True, (56, 74, 12))
        rect = surf.get_rect(center=(x, y))

        bg_rect_width = surf.get_width() + self.cell_size
        bg = pygame.Rect(0, 0, bg_rect_width + 40, rect.height + 30)
        bg.midleft = (x, y)

        pygame.draw.rect(self.screen, (167, 209, 61), bg, border_radius=5)
        self.screen.blit(surf, surf.get_rect(midleft=(bg.left + 10, bg.centery)))

        crown_width = int(self.cell_size * 1.5)
        crown_height = int(self.cell_size * 1.5)
        scaled_crown = pygame.transform.scale(self.crown_image_for_score, (crown_width, crown_height))
        ar = scaled_crown.get_rect(midright=(bg.right - 10, bg.centery))

        screen.blit(scaled_crown, ar)

    def game_over(self):
        global game_active
        game_active = False
        current_score_val = len(self.snake.body) - 3
        if self.db.in_top10(current_score_val):
            name_system.initialize_state(current_score_val)


def reset_game():
    global main_game, game_active, current_speed, new_direction
    main_game = MAIN()
    new_direction = main_game.snake.direction
    current_speed = 140
    pygame.time.set_timer(SCREEN_UPDATE, current_speed)
    game_active = True
    name_system.NAME_INPUT_MODE = False


def update_speed():
    global current_speed, main_game
    new_speed = max(75, 140 - (len(main_game.snake.body) - 3) * 5)
    if new_speed != current_speed:
        current_speed = new_speed
        pygame.time.set_timer(SCREEN_UPDATE, current_speed)


clock = pygame.time.Clock()
main_game = MAIN()
pygame.time.set_timer(SCREEN_UPDATE, current_speed)

last_input_time = 0
INPUT_DELAY = 20


running = True
new_direction = main_game.snake.direction
while running:
    current_time_ms = pygame.time.get_ticks()
    processed_action_this_frame = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pass

        if (
            event.type == SCREEN_UPDATE
            and game_active
            and not name_system.NAME_INPUT_MODE
        ):
            main_game.snake.direction = new_direction
            main_game.update()

        if event.type == pygame.KEYDOWN:
            if name_system.NAME_INPUT_MODE:
                if current_time_ms - last_input_time >= INPUT_DELAY:
                    result = name_system.process_input(event.key)
                    if result:
                        last_input_time = current_time_ms
                        processed_action_this_frame = True
                        if result == "NAME_ENTERED":
                            player_name = name_system.get_name()
                            print(
                                f"Player: {player_name} | Score: {len(main_game.snake.body) - 3}"
                            )
                            reset_game()
                        elif result == "ESC_PRESSED":
                            pass
            elif game_active:
                if current_time_ms - last_input_time >= INPUT_DELAY:
                    d = main_game.snake.direction
                    action_taken_game = False
                    if event.key == pygame.K_UP and d.y != 1:
                        new_direction = Vector2(0, -1)
                        action_taken_game = True
                    elif event.key == pygame.K_RIGHT and d.x != -1:
                        new_direction = Vector2(1, 0)
                        action_taken_game = True
                    elif event.key == pygame.K_DOWN and d.y != -1:
                        new_direction = Vector2(0, 1)
                        action_taken_game = True
                    elif event.key == pygame.K_LEFT and d.x != 1:
                        new_direction = Vector2(-1, 0)
                        action_taken_game = True
                    elif event.key == pygame.K_ESCAPE:
                        pass
                        action_taken_game = True

                    if action_taken_game:
                        last_input_time = current_time_ms
                        processed_action_this_frame = True
            else:
                if event.key == pygame.K_ESCAPE:
                    reset_game()
                else:
                    if not name_system.NAME_INPUT_MODE:
                        reset_game()

    if not processed_action_this_frame and (
        current_time_ms - last_input_time >= INPUT_DELAY
    ):
        button_command = read_button_input()

        if button_command:
            if name_system.NAME_INPUT_MODE:
                result = name_system.process_input(button_command)
                if result:
                    last_input_time = current_time_ms
                    if result == "NAME_ENTERED":
                        player_name = name_system.get_name()
                        print(
                            f"Player: {player_name} | Score: {len(main_game.snake.body) - 3}"
                        )
                        reset_game()
                    elif result == "ESC_PRESSED":
                        reset_game()
            elif game_active:
                d = main_game.snake.direction
                action_taken_button = False
                if button_command == "UP" and d.y != 1:
                    new_direction = Vector2(0, -1)
                    action_taken_button = True
                elif button_command == "RIGHT" and d.x != -1:
                    new_direction = Vector2(1, 0)
                    action_taken_button = True
                elif button_command == "DOWN" and d.y != -1:
                    new_direction = Vector2(0, 1)
                    action_taken_button = True
                elif button_command == "LEFT" and d.x != 1:
                    new_direction = Vector2(-1, 0)
                    action_taken_button = True

                if action_taken_button:
                    last_input_time = current_time_ms
            else:
                if not name_system.NAME_INPUT_MODE:
                    reset_game()

    screen.fill((175, 215, 70))

    if name_system.NAME_INPUT_MODE:
        name_system.draw_ui(
            screen, screen_width, screen_height, cell_size, game_font, get_asset_path
        )
    elif game_active:
        main_game.draw_elements()
    else:
        screen.fill((0, 0, 0))
        try:
            go_t = pygame.font.Font(
                get_asset_path("Font/PoetsenOne-Regular.ttf"), int(cell_size * 3.0)
            )
            go_m = pygame.font.Font(
                get_asset_path("Font/PoetsenOne-Regular.ttf"), int(cell_size * 1.2)
            )
        except Exception as e:
            print(f"DEBUG: Could not load custom font. Error: {e}")
            go_t = pygame.font.SysFont("Arial", int(cell_size * 3.0))
            go_m = pygame.font.SysFont("Arial", int(cell_size * 1.2))

        ts = go_t.render("Game Over!", True, (190, 0, 0))
        isf_text = "Drücke einen Knopf zum starten"
        isf = go_m.render(isf_text, True, (200, 200, 200))

        tr = ts.get_rect(center=(screen_width / 2, screen_height / 2 - cell_size * 2.5))
        ir = isf.get_rect(
            center=(screen_width / 2, screen_height / 2 + cell_size * 1.5)
        )

        screen.blit(ts, tr)
        screen.blit(isf, ir)


if __name__ == "__main__":
    game = Game()
    game.run()
