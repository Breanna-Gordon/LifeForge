import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, LIGHT_GREY,
    DARK_GREY, GREEN, font, small_font, title_font, draw_text
)

def load_image(path, size=None):
    try:
        image = pygame.image.load(path).convert()
        if size:
            image = pygame.transform.scale(image, size)
        return image
    except (pygame.error, FileNotFoundError):
        return None

def character_selection_screen(screen):
    background = load_image("images/selection_background.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
    male_image = load_image("images/male_image.jpg", (180, 180))
    female_image = load_image("images/female_image.jpg", (180, 180))

    name = ""
    gender = None
    clock = pygame.time.Clock()

    male_rect = pygame.Rect(150, 210, 250, 230)
    female_rect = pygame.Rect(500, 210, 250, 230)
    continue_rect = pygame.Rect(325, 485, 250, 55)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None, None
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.key == pygame.K_RETURN and name.strip() and gender:
                    return gender, name.strip()
                elif event.unicode.isprintable() and len(name) < 20:
                    name += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if male_rect.collidepoint(event.pos):
                    gender = "Male"
                elif female_rect.collidepoint(event.pos):
                    gender = "Female"
                elif continue_rect.collidepoint(event.pos) and name.strip() and gender:
                    return gender, name.strip()

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(WHITE)

        draw_text(screen, "Create Your Character", title_font, BLACK,
                  SCREEN_WIDTH // 2, 45, centre=True)

        draw_text(screen, "Name:", font, BLACK, 150, 115)
        pygame.draw.rect(screen, WHITE, (230, 108, 520, 42))
        pygame.draw.rect(screen, BLACK, (230, 108, 520, 42), 2)
        draw_text(screen, name or "Type your name...", font,
                  DARK_GREY if not name else BLACK, 242, 116)

        pygame.draw.rect(screen, WHITE, male_rect)
        pygame.draw.rect(screen, GREEN if gender == "Male" else BLACK, male_rect, 4)
        if male_image:
            screen.blit(male_image, male_image.get_rect(center=(275, 300)))
        draw_text(screen, "Male", font, BLACK, 275, 405, centre=True)

        pygame.draw.rect(screen, WHITE, female_rect)
        pygame.draw.rect(screen, GREEN if gender == "Female" else BLACK, female_rect, 4)
        if female_image:
            screen.blit(female_image, female_image.get_rect(center=(625, 300)))
        draw_text(screen, "Female", font, BLACK, 625, 405, centre=True)

        enabled = bool(name.strip() and gender)
        pygame.draw.rect(screen, GREEN if enabled else LIGHT_GREY, continue_rect)
        draw_text(screen, "Continue", font, BLACK,
                  continue_rect.centerx, continue_rect.centery, centre=True)

        draw_text(screen, "Press ESC to return to the menu.",
                  small_font, BLACK, SCREEN_WIDTH // 2, 570, centre=True)

        pygame.display.flip()
        clock.tick(60)
