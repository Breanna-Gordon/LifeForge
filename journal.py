from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow
import pygame
from constants import (WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT,
                       font, small_font, draw_text, draw_rounded_rect)

LINE_H = 22

def draw_journal_tab(screen, rect, journal, scroll):
    draw_text(screen, "Journal", font, INK, rect.x, rect.y)
    box = pygame.Rect(rect.x, rect.y + 28, rect.width, rect.height - 32)
    draw_rounded_rect(screen, WHITE, box, radius=8)
    pygame.draw.rect(screen, OUTLINE, box, 2, border_radius=8)
    visible = (box.height - 12) // LINE_H
    entries = list(reversed(journal))           # newest first
    max_scroll = max(0, len(entries) - visible)
    scroll = max(0, min(scroll, max_scroll))
    if not entries:
        draw_text(screen, "Nothing yet. Your life story will appear here.", small_font, DARK_GREY, box.x + 12, box.y + 10)
    y = box.y + 8
    for age, text in entries[scroll:scroll + visible]:
        draw_text(screen, f"Age {age}", small_font, ACCENT, box.x + 12, y)
        clipped = text if small_font.size(text)[0] < box.width - 100 else text[:70] + "…"
        draw_text(screen, clipped, small_font, INK, box.x + 80, y)
        y += LINE_H
    if max_scroll:
        draw_text(screen, "Scroll for more", small_font, DARK_GREY, box.right - 110, box.bottom - 18)
    return scroll
