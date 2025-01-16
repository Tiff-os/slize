import pygame
import random
import math
from enum import Enum
import numpy as np

pygame.init()

# Константы
WINDOW_SIZE = 1200
GRID_SIZE = 12
GRID_COUNT = WINDOW_SIZE // GRID_SIZE

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GOLD = (255, 215, 0)
ORANGE = (255, 69, 0)

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Snake:
    def __init__(self, x, y, color, is_bot=False):
        self.body = [(x, y)]
        self.direction = Direction.RIGHT
        self.color = color
        self.is_bot = is_bot
        self.alive = True
        self.speed = 0.2 if is_bot else 0.5  # Увеличили скорость игрока
        self.length = 15
        self.score = 0
        self.radius = 6
        self.random_direction = random.random() * math.pi * 2
        self.direction_change_timer = 0
        self.invulnerable_time = 300
        
        for i in range(self.length):
            self.body.append((x-i, y))

    def move(self, food_positions, mouse_pos=None):
        if not self.alive:
            return

        head = self.body[0]

        if self.is_bot:
            self.direction_change_timer += 1
            if self.direction_change_timer >= 50:
                self.random_direction = random.random() * math.pi * 2
                self.direction_change_timer = 0

            if food_positions and random.random() < 0.2:
                nearest_food = min(food_positions, key=lambda food: 
                    math.sqrt((head[0] - food[0])**2 + (head[1] - food[1])**2))
                dx = nearest_food[0] - head[0]
                dy = nearest_food[1] - head[1]
                target_angle = math.atan2(dy, dx)
                self.random_direction = (self.random_direction * 0.95 + target_angle * 0.05)
            
            new_x = head[0] + math.cos(self.random_direction) * self.speed
            new_y = head[1] + math.sin(self.random_direction) * self.speed
            
        elif mouse_pos:
            # Простая логика движения за курсором
            target_x = mouse_pos[0] / GRID_SIZE
            target_y = mouse_pos[1] / GRID_SIZE
            dx = target_x - head[0]
            dy = target_y - head[1]
            angle = math.atan2(dy, dx)
            new_x = head[0] + math.cos(angle) * self.speed
            new_y = head[1] + math.sin(angle) * self.speed

        new_head = (new_x % GRID_COUNT, new_y % GRID_COUNT)
        self.body.insert(0, new_head)
        if len(self.body) > self.length:
            self.body.pop()

    def grow(self, amount):
        self.length += amount
        self.score += amount
        self.radius = min(10, 6 + self.score // 20)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Змейки")
        self.state = "START"  # START, PLAYING, WIN, GAME_OVER
        self.init_game()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 48)

    def init_game(self):
        self.player = Snake(GRID_COUNT//2, GRID_COUNT//2, GREEN)
        self.bots = []
        for i in range(4):
            x = random.randint(0, GRID_COUNT-1)
            y = random.randint(0, GRID_COUNT-1)
            color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            while math.dist((x, y), (GRID_COUNT//2, GRID_COUNT//2)) < GRID_COUNT//4:
                x = random.randint(0, GRID_COUNT-1)
                y = random.randint(0, GRID_COUNT-1)
            self.bots.append(Snake(x, y, color, True))
        
        self.food = []
        self.spawn_food(30)
        self.game_time = 0

    def draw_button(self, text, y_position):
        button_text = self.font.render(text, True, WHITE)
        text_rect = button_text.get_rect(center=(WINDOW_SIZE//2, y_position))
        pygame.draw.rect(self.screen, WHITE, text_rect.inflate(20, 20), 2)
        self.screen.blit(button_text, text_rect)
        return text_rect

    def check_game_state(self):
        if not self.player.alive:
            self.state = "GAME_OVER"
            return
        
        alive_snakes = [snake for snake in [self.player] + self.bots if snake.alive]
        if len(alive_snakes) == 1 and alive_snakes[0] == self.player:
            self.state = "WIN"

    def spawn_food(self, amount=1):
        for _ in range(amount):
            if len(self.food) < 40:
                x = random.randint(0, GRID_COUNT-1)
                y = random.randint(0, GRID_COUNT-1)
                food_type = random.choice(['small', 'medium', 'large'])
                self.food.append((x, y, food_type))

    def check_collisions(self, snake):
        head = snake.body[0]
        
        # Проверка столкновения с едой
        for food in self.food[:]:
            if math.dist((head[0], head[1]), (food[0], food[1])) < 2:
                self.food.remove(food)
                if food[2] == 'small':
                    snake.grow(1)
                elif food[2] == 'medium':
                    snake.grow(2)
                else:
                    snake.grow(3)
                self.spawn_food()

        # Проверка столкновения с другими змейками (только голова с телом)
        for other_snake in [self.player] + self.bots:
            if other_snake != snake and other_snake.alive:
                # Проверяем столкновение только с телом другой змеи (без головы)
                for segment in other_snake.body[1:]:
                    if math.dist((head[0], head[1]), segment) < 1:
                        snake.alive = False
                        for body_segment in snake.body:
                            if random.random() < 0.3:
                                food_type = random.choice(['small', 'medium', 'large'])
                                self.food.append((body_segment[0], body_segment[1], food_type))
                        return

    def draw_scores(self):
        # Отдельно отображаем счет игрока сверху
        player_score_text = self.font.render(f"Ваш счет: {self.player.score}", True, GREEN)
        self.screen.blit(player_score_text, (10, 10))

        # Отображаем счет всех змей
        all_scores = [(self.player.score, "ВЫ", GREEN)]
        for i, bot in enumerate(self.bots):
            if bot.alive:
                all_scores.append((bot.score, f"Бот {i+1}", bot.color))
        
        all_scores.sort(reverse=True)
        
        # Отображаем таблицу лидеров
        y = 70  # Сдвигаем вниз, чтобы не перекрывать счет игрока
        for i, (score, name, color) in enumerate(all_scores[:5]):
            position = f"{i+1}."
            score_text = self.small_font.render(f"{position} {name}: {score}", True, color)
            self.screen.blit(score_text, (10, y))
            y += 40

    def draw_snake(self, snake):
        if snake.alive:
            for i, segment in enumerate(snake.body):
                color = snake.color
                if i == 0:
                    radius = snake.radius + 1
                else:
                    radius = max(4, snake.radius - 1)
                    fade = min(1.0, i / len(snake.body))
                    color = tuple(max(0, min(255, c * (1 - fade * 0.3))) for c in snake.color)
                pygame.draw.circle(self.screen, color,
                    (int(segment[0] * GRID_SIZE), int(segment[1] * GRID_SIZE)), radius)

    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_clicked = True

            self.screen.fill(BLACK)

            if self.state == "START":
                title = self.font.render("Змейки", True, WHITE)
                title_rect = title.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//3))
                self.screen.blit(title, title_rect)
                
                start_rect = self.draw_button("СТАРТ", WINDOW_SIZE//2)
                
                if mouse_clicked and start_rect.collidepoint(mouse_pos):
                    self.state = "PLAYING"
                    self.init_game()

            elif self.state == "PLAYING":
                self.game_time += 1

                if self.player.alive:
                    self.player.move(self.food, mouse_pos)
                
                for bot in self.bots:
                    if bot.alive:
                        bot.move(self.food)

                self.check_collisions(self.player)
                for bot in self.bots:
                    if bot.alive:
                        self.check_collisions(bot)

                # Отрисовка еды
                for food in self.food:
                    color = WHITE
                    size = 3
                    if food[2] == 'medium':
                        color = GOLD
                        size = 4
                    elif food[2] == 'large':
                        color = ORANGE
                        size = 5
                    pygame.draw.circle(self.screen, color,
                        (int(food[0] * GRID_SIZE), int(food[1] * GRID_SIZE)), size)

                # Отрисовка змеек
                if self.player.alive:
                    self.draw_snake(self.player)

                for bot in self.bots:
                    if bot.alive:
                        self.draw_snake(bot)

                self.draw_scores()

                if self.game_time < self.player.invulnerable_time:
                    invuln_text = self.font.render("Неуязвимость!", True, (255, 255, 0))
                    self.screen.blit(invuln_text, (WINDOW_SIZE//2 - 100, 10))

                self.check_game_state()

            elif self.state == "WIN":
                win_text = self.font.render("ПОБЕДА!", True, GREEN)
                win_rect = win_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//3))
                self.screen.blit(win_text, win_rect)
                
                restart_rect = self.draw_button("Играть снова", WINDOW_SIZE//2)
                
                if mouse_clicked and restart_rect.collidepoint(mouse_pos):
                    self.state = "PLAYING"
                    self.init_game()

            elif self.state == "GAME_OVER":
                game_over_text = self.font.render("GAME OVER", True, RED)
                game_over_rect = game_over_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//3))
                self.screen.blit(game_over_text, game_over_rect)
                
                restart_rect = self.draw_button("Играть снова", WINDOW_SIZE//2)
                
                if mouse_clicked and restart_rect.collidepoint(mouse_pos):
                    self.state = "PLAYING"
                    self.init_game()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()