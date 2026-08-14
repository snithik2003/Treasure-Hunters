from __future__ import annotations
import sys

import pygame

from config import (
    Difficulty, TILE_PIXELS, FPS, COLOR_BG, COLOR_GRID_LINE, COLOR_TERRAIN,
    COLOR_TREASURE, COLOR_TRAP, COLOR_DOOR, COLOR_POWERUP, COLOR_TEXT,
)
from models.game import Game
from models.treasure import Treasure
from models.trap import Trap
from models.door import Door
from models.powerup import PowerUp

SIDEBAR_WIDTH = 300
BUTTON_HEIGHT = 42
BUTTON_GAP = 12


class GameApp:
    def __init__(self, difficulty: Difficulty = Difficulty.EASY):
        pygame.init()
        pygame.display.set_caption("AI Treasure Hunters")

        self.difficulty = difficulty
        self.game = Game(difficulty=difficulty)

        self.windowed_size = (1280, 800)
        self.fullscreen = True
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 16)
        self.big_font = pygame.font.SysFont("consolas", 22, bold=True)

        self.ai_move_delay_ms = 350
        self._ai_timer = 0

    @property
    def layout(self) -> tuple[int, int, int, int, int]:
        screen_w, screen_h = self.screen.get_size()
        available_w = screen_w - SIDEBAR_WIDTH - 80
        available_h = screen_h - 80
        tile_pixels = min(
            TILE_PIXELS,
            max(20, available_w // self.game.board.cols),
            max(20, available_h // self.game.board.rows),
        )
        board_w = self.game.board.cols * tile_pixels
        board_h = self.game.board.rows * tile_pixels
        total_w = board_w + SIDEBAR_WIDTH
        origin_x = max(20, (screen_w - total_w) // 2)
        origin_y = max(20, (screen_h - board_h) // 2)
        return origin_x, origin_y, tile_pixels, board_w, board_h

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size)

    # -----------------------------------
    # Input handling
    # ---------------------------------------
    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                self.running = False
                self.result = "back"
            elif self.close_button.collidepoint(event.pos):
                self.running = False
                self.result = "close"
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return
        if not self.game.current_player_is_human or self.game.game_over:
            if event.key == pygame.K_r:
                self.game = Game(difficulty=self.difficulty)
            return

        r, c = self.game.human.position
        target = None
        if event.key in (pygame.K_UP, pygame.K_w):
            target = (r - 1, c)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            target = (r + 1, c)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            target = (r, c - 1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            target = (r, c + 1)
        elif event.key == pygame.K_r:
            self.game = Game(difficulty=self.difficulty)
            return

        if target is not None:
            self.game.human_action("move", target=target)

    # -------------------------
    # Update
    # --------------------------------------
    def update(self, dt_ms: int) -> None:
        if self.game.game_over:
            return
        if not self.game.current_player_is_human:
            self._ai_timer += dt_ms
            if self._ai_timer >= self.ai_move_delay_ms:
                self._ai_timer = 0
                self.game.ai_take_turn()

    # --------------------------------
    # Rendering
    # ---------------------------------------
    def draw_board(self) -> None:
        board = self.game.board
        origin_x, origin_y, tile_pixels, _, _ = self.layout
        for r in range(board.rows):
            for c in range(board.cols):
                tile = board.get_tile(r, c)
                x = origin_x + c * tile_pixels
                y = origin_y + r * tile_pixels
                color = COLOR_TERRAIN[tile.terrain]
                if tile.temp_obstacle_turns_left > 0:
                    color = (90, 30, 30)
                pygame.draw.rect(self.screen, color, (x, y, tile_pixels, tile_pixels))
                pygame.draw.rect(self.screen, COLOR_GRID_LINE, (x, y, tile_pixels, tile_pixels), 1)

                occ = tile.occupant
                cx, cy = x + tile_pixels // 2, y + tile_pixels // 2
                if isinstance(occ, Treasure) and not occ.collected:
                    pygame.draw.circle(self.screen, COLOR_TREASURE, (cx, cy), tile_pixels // 3)
                elif isinstance(occ, Trap):
                    pygame.draw.polygon(
                        self.screen, COLOR_TRAP,
                        [(cx, y + 6), (x + 6, y + tile_pixels - 6), (x + tile_pixels - 6, y + tile_pixels - 6)],
                    )
                elif isinstance(occ, Door):
                    color = COLOR_DOOR if occ.locked else (255, 200, 80)
                    pygame.draw.rect(self.screen, color, (x + 8, y + 4, tile_pixels - 16, tile_pixels - 8))
                elif isinstance(occ, PowerUp):
                    pygame.draw.circle(self.screen, COLOR_POWERUP, (cx, cy), tile_pixels // 4, 3)

    def draw_players(self) -> None:
        origin_x, origin_y, tile_pixels, _, _ = self.layout
        for player, is_ai in ((self.game.human, False), (self.game.ai, True)):
            r, c = player.position
            cx = origin_x + c * tile_pixels + tile_pixels // 2
            cy = origin_y + r * tile_pixels + tile_pixels // 2
            radius = tile_pixels // 2 - 4
            pygame.draw.circle(self.screen, player.color, (cx, cy), radius)
            label = "AI" if is_ai else "H"
            text = self.font.render(label, True, (10, 10, 10))
            self.screen.blit(text, (cx - text.get_width() // 2, cy - text.get_height() // 2))

    def draw_sidebar(self) -> None:
        origin_x, origin_y, _, board_w, board_h = self.layout
        sidebar_x = origin_x + board_w
        x0 = sidebar_x + 18
        pygame.draw.rect(self.screen, (24, 24, 30), (sidebar_x, origin_y, SIDEBAR_WIDTH, board_h))

        lines = [
            "AI TREASURE HUNTERS",
            "",
            f"Difficulty: {self.difficulty.name}",
            f"Turn: {self.game.turn_count}",
            f"Active: {'HUMAN' if self.game.current_player_is_human else 'AI'}",
            "",
            f"Human score: {self.game.human.score}",
            f"AI score:    {self.game.ai.score}",
            "",
            "Controls:",
            "Arrows: move",
            "R: restart",
            "F11: window/fullscreen",
            "",
        ]
        y = origin_y + 16
        for i, line in enumerate(lines):
            font = self.big_font if i == 0 else self.font
            text = font.render(line, True, COLOR_TEXT)
            self.screen.blit(text, (x0, y))
            y += text.get_height() + 6

        button_width = SIDEBAR_WIDTH - 36
        button_y = origin_y + board_h - BUTTON_HEIGHT
        self.back_button = pygame.Rect(x0, button_y, button_width, BUTTON_HEIGHT)
        self.close_button = pygame.Rect(
            x0, button_y - BUTTON_HEIGHT - BUTTON_GAP, button_width, BUTTON_HEIGHT
        )
        self._draw_button(self.close_button, "CLOSE GAME", COLOR_TRAP)
        self._draw_button(self.back_button, "BACK TO DIFFICULTY", COLOR_DOOR)

        if self.game.game_over:
            y += 10
            text = self.big_font.render(f"WINNER: {self.game.winner}", True, (255, 220, 90))
            self.screen.blit(text, (x0, y))
            y += text.get_height() + 6
            hint = self.font.render("Press R to play again", True, COLOR_TEXT)
            self.screen.blit(hint, (x0, y))

    def _draw_button(self, rect: pygame.Rect, label: str, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_TEXT, rect, 2, border_radius=6)
        text = self.font.render(label, True, (10, 10, 10))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def render(self) -> None:
        self.screen.fill(COLOR_BG)
        self.draw_board()
        self.draw_players()
        self.draw_sidebar()
        pygame.display.flip()

    # ----------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> str:
        self.running = True
        self.result = "close"
        while self.running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.result = "close"
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    self.result = "close"
                else:
                    self.handle_input(event)

            self.update(dt)
            self.render()

        return self.result


def draw_symbol_tile(screen: pygame.Surface, rect: pygame.Rect, kind: str) -> None:
    colors = {
        "treasure": COLOR_TREASURE,
        "trap": COLOR_TRAP,
        "powerup": COLOR_POWERUP,
        "mud": COLOR_TERRAIN[next(key for key in COLOR_TERRAIN if key.value == "mud")],
        "water": COLOR_TERRAIN[next(key for key in COLOR_TERRAIN if key.value == "water")],
        "door": COLOR_DOOR,
        "wall": COLOR_TERRAIN[next(key for key in COLOR_TERRAIN if key.value == "wall")],
    }
    pygame.draw.rect(screen, colors[kind], rect)
    pygame.draw.rect(screen, COLOR_GRID_LINE, rect, 1)
    center = rect.center
    if kind == "treasure":
        pygame.draw.circle(screen, (30, 30, 30), center, rect.width // 4)
    elif kind == "trap":
        pygame.draw.polygon(screen, (30, 30, 30), [
            (center[0], rect.top + 6),
            (rect.left + 6, rect.bottom - 6),
            (rect.right - 6, rect.bottom - 6),
        ])
    elif kind == "powerup":
        pygame.draw.circle(screen, (30, 30, 30), center, rect.width // 4, 2)
    elif kind == "door":
        pygame.draw.rect(screen, (30, 30, 30), rect.inflate(-12, -6), 3)


def select_difficulty() -> Difficulty | None:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    font = pygame.font.SysFont("consolas", 20)
    title_font = pygame.font.SysFont("consolas", 34, bold=True)
    clock = pygame.time.Clock()
    choices = (
        (pygame.K_1, "1  EASY", "Fewer obstacles"),
        (pygame.K_2, "2  MEDIUM", "More obstacles and hazards"),
        (pygame.K_3, "3  HARD", "Dense obstacles and hazards"),
    )
    legend = (
        ("treasure", "Treasure: +10 points"),
        ("trap", "Trap: -10 points"),
        ("powerup", "Circle power-up: +5 points"),
        ("door", "Locked door: -5 points to unlock"),
        ("mud", "Mud: wait one move after entering"),
        ("water", "Water: wait one move after entering"),
        ("wall", "Wall: blocked tile"),
    )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                for key, _, _ in choices:
                    if event.key == key:
                        return Difficulty(event.key - pygame.K_0)

        screen.fill(COLOR_BG)
        screen_w, screen_h = screen.get_size()
        title = title_font.render("AI TREASURE HUNTERS", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(screen_w // 2, 58)))
        prompt = font.render("Choose difficulty: press 1, 2, or 3", True, COLOR_TEXT)
        screen.blit(prompt, prompt.get_rect(center=(screen_w // 2, 108)))

        left = screen_w // 2 - 420
        for index, (_, label, description) in enumerate(choices):
            y = 160 + index * 48
            screen.blit(font.render(label, True, COLOR_TREASURE), (left, y))
            screen.blit(font.render(description, True, COLOR_TEXT), (left + 180, y))

        legend_title = font.render("Game tiles and rules", True, COLOR_TEXT)
        screen.blit(legend_title, (left, 330))
        tile_rect = pygame.Rect(left, 370, 32, 32)
        for index, (kind, description) in enumerate(legend):
            column = index // 4
            row = index % 4
            rect = tile_rect.move(column * 360, row * 48)
            draw_symbol_tile(screen, rect, kind)
            screen.blit(font.render(description, True, COLOR_TEXT), (rect.right + 10, rect.y + 5))

        footer = font.render("Arrow keys move  |  R restarts  |  F11 toggles window mode  |  Esc closes", True, COLOR_TEXT)
        screen.blit(footer, footer.get_rect(center=(screen_w // 2, screen_h - 42)))
        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    pygame.init()
    while True:
        selected_difficulty = select_difficulty()
        if selected_difficulty is None:
            break
        result = GameApp(difficulty=selected_difficulty).run()
        if result == "close":
            break
    pygame.quit()
