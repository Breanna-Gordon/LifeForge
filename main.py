import pygame
import sys
import random

from character import character_selection_screen, load_image
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, LIGHT_GREY,
    DARK_GREY, GREEN, RED, font, small_font, title_font, draw_text
)
from choices import choice_events

def get_age_stage(age):
    if age < 7:
        return "Baby"
    if age < 13:
        return "Childhood"
    if age < 20:
        return "Teenage"
    if age < 30:
        return "Young Adult"
    if age < 65:
        return "Adult"
    return "Elderly"

def update_stats(stats, consequence):
    for stat, value in consequence.items():
        stats[stat] = max(0, min(100, stats[stat] + value))
    return stats

def apply_yearly_decline(stats, age):
    for stat in stats:
        stats[stat] = max(0, stats[stat] - 1)

    if age >= 50:
        stats["physical"] = max(0, stats["physical"] - 2)

    if age >= 65:
        stats["mental"] = max(0, stats["mental"] - 2)

    if age >= 70:
        stats["physical"] = max(0, stats["physical"] - 2)

    if age >= 80:
        stats["social"] = max(0, stats["social"] - 1)

def wrap_text(text, selected_font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word
        if selected_font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines

def draw_wrapped_text(screen, text, selected_font, colour, rect,
                      line_spacing=5, centre=True):
    lines = wrap_text(text, selected_font, rect.width - 20)
    line_height = selected_font.get_height() + line_spacing
    total_height = len(lines) * line_height
    y = rect.centery - total_height // 2

    for line in lines:
        if centre:
            draw_text(screen, line, selected_font, colour,
                      rect.centerx, y, centre=True)
        else:
            draw_text(screen, line, selected_font, colour,
                      rect.x + 10, y)
        y += line_height

def render_player_stats(screen, player_stats, icons):
    bar_width = 180
    bar_height = 22
    spacing = 48
    stats_x = SCREEN_WIDTH - bar_width - 30
    stats_y = 25

    for idx, stat in enumerate(["physical", "wealth", "mental", "social"]):
        y = stats_y + idx * spacing

        icon = icons.get(stat)
        if icon:
            icon = pygame.transform.scale(icon, (30, 30))
            screen.blit(icon, (stats_x - 40, y - 4))

        pygame.draw.rect(screen, BLACK, (stats_x, y, bar_width, bar_height), 2)
        filled_width = int(bar_width * player_stats[stat] / 100)
        pygame.draw.rect(screen, GREEN, (stats_x, y, filled_width, bar_height))

        draw_text(screen, f"{stat.title()}: {player_stats[stat]}",
                  small_font, BLACK, stats_x + 5, y + 2)

def draw_game_screen(screen, player_name, gender, age, stats,
                     choice_text, options, selected_option,
                     character_images, icons, background):
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.fill(WHITE)

    character_image = character_images.get(gender)
    if character_image:
        screen.blit(character_image, (25, 25))

    draw_text(screen, f"Name: {player_name}", font, BLACK, 25, 220)
    draw_text(screen, f"Age: {age}", font, BLACK, 25, 255)

    render_player_stats(screen, stats, icons)

    event_rect = pygame.Rect(120, 315, 660, 90)
    pygame.draw.rect(screen, WHITE, event_rect)
    pygame.draw.rect(screen, BLACK, event_rect, 2)
    draw_wrapped_text(screen, choice_text, font, BLACK, event_rect)

    option_width = 310
    option_height = 65
    gap = 25
    start_x = (SCREEN_WIDTH - (option_width * 2 + gap)) // 2
    y = 435

    for index, option_text in enumerate(options):
        x = start_x + index * (option_width + gap)
        rect = pygame.Rect(x, y, option_width, option_height)
        selected = selected_option == index
        pygame.draw.rect(screen, LIGHT_GREY if not selected else GREEN, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        draw_wrapped_text(screen, option_text, small_font, BLACK, rect)

    draw_text(screen, "Click an option to continue. Press ESC to quit.",
              small_font, DARK_GREY, SCREEN_WIDTH // 2, 570, centre=True)

def game_over(screen, age, failed_stat):
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    return

        screen.fill(WHITE)
        draw_text(screen, "Game Over", title_font, RED,
                  SCREEN_WIDTH // 2, 210, centre=True)
        draw_text(screen, f"Your life ended at age {age}.",
                  font, BLACK, SCREEN_WIDTH // 2, 280, centre=True)
        draw_text(screen, f"{failed_stat.title()} reached 0.",
                  font, BLACK, SCREEN_WIDTH // 2, 325, centre=True)
        draw_text(screen, "Press ENTER to return to the menu.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 400, centre=True)
        draw_text(screen, "Press ESC to return to the menu.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 430, centre=True)

        pygame.display.flip()
        clock.tick(60)

def instructions_screen(screen):
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        screen.fill(WHITE)
        draw_text(screen, "How to Play", title_font, BLACK,
                  SCREEN_WIDTH // 2, 70, centre=True)

        instructions = [
            "Create a character by entering a name and choosing a gender.",
            "Each year of your life presents a random event.",
            "Click one of the available choices to decide what happens.",
            "Your choices change your physical, wealth, mental and social stats.",
            "Stats also decline naturally as you get older.",
            "If any stat reaches 0, the game ends.",
            "Try different choices to see how long you can keep your character going."
        ]

        y = 145
        for line in instructions:
            draw_text(screen, line, font, BLACK, 70, y)
            y += 48

        draw_text(screen, "Press ESC to return to the menu.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 550, centre=True)

        pygame.display.flip()
        clock.tick(60)

def menu_screen(screen):
    background = load_image("images/menu_background.jpg",
                             (SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    button_width = 300
    button_height = 65
    x = (SCREEN_WIDTH - button_width) // 2

    buttons = {
        "Start": pygame.Rect(x, 260, button_width, button_height),
        "Instructions": pygame.Rect(x, 345, button_width, button_height),
        "Exit": pygame.Rect(x, 430, button_width, button_height)
    }

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for label, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if label == "Start":
                            return "start"
                        if label == "Instructions":
                            instructions_screen(screen)
                        if label == "Exit":
                            pygame.quit()
                            raise SystemExit

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(WHITE)

        draw_text(screen, "LifeForge", title_font, BLACK,
                  SCREEN_WIDTH // 2, 120, centre=True)

        for label, rect in buttons.items():
            pygame.draw.rect(screen, WHITE, rect)
            pygame.draw.rect(screen, BLACK, rect, 2)
            draw_text(screen, label, font, BLACK,
                      rect.centerx, rect.centery, centre=True)

        pygame.display.flip()
        clock.tick(60)

def run_game(screen):
    gender, player_name = character_selection_screen(screen)

    if gender is None:
        return

    character_images = {
        "Male": load_image("images/male_image.jpg", (180, 180)),
        "Female": load_image("images/female_image.jpg", (180, 180))
    }

    icons = {
        "physical": load_image("images/physical_icon.png"),
        "wealth": load_image("images/wealth_icon.png"),
        "mental": load_image("images/mental_icon.png"),
        "social": load_image("images/social_icon.png")
    }

    background = load_image("images/background.png",
                             (SCREEN_WIDTH, SCREEN_HEIGHT))

    stats = {
        "physical": 50,
        "wealth": 50,
        "mental": 50,
        "social": 50
    }

    age = 0
    clock = pygame.time.Clock()

    while True:
        stage = get_age_stage(age)
        choices = choice_events[stage]["choices"]
        choice_text, option_data = random.choice(list(choices.items()))
        options = list(option_data.keys())
        selected_option = None

        waiting = True

        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

                if event.type == pygame.MOUSEMOTION:
                    selected_option = None
                    for index in range(len(options)):
                        option_width = 310
                        option_height = 65
                        gap = 25
                        start_x = (SCREEN_WIDTH - (option_width * 2 + gap)) // 2
                        rect = pygame.Rect(
                            start_x + index * (option_width + gap),
                            435, option_width, option_height
                        )
                        if rect.collidepoint(event.pos):
                            selected_option = index

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for index, option_text in enumerate(options):
                        option_width = 310
                        option_height = 65
                        gap = 25
                        start_x = (SCREEN_WIDTH - (option_width * 2 + gap)) // 2
                        rect = pygame.Rect(
                            start_x + index * (option_width + gap),
                            435, option_width, option_height
                        )
                        if rect.collidepoint(event.pos):
                            stats = update_stats(stats, option_data[option_text])
                            waiting = False
                            break

            draw_game_screen(
                screen, player_name, gender, age, stats,
                choice_text, options, selected_option,
                character_images, icons, background
            )
            pygame.display.flip()
            clock.tick(60)

        apply_yearly_decline(stats, age)

        failed_stat = next((stat for stat, value in stats.items() if value <= 0), None)
        if failed_stat:
            game_over(screen, age, failed_stat)
            return

        age += 1

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("LifeForge")

    while True:
        action = menu_screen(screen)
        if action == "start":
            run_game(screen)

if __name__ == "__main__":
    main()
