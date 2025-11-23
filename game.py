import pygame
import sys
import random
import time
import requests
import os
from PIL import Image
from io import BytesIO
import platform

# --- 상수 ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
BACKGROUND_COLOR = (30, 30, 30)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
RED = (220, 20, 60)
BLUE = (65, 105, 225)
GOLD = (255, 215, 0)

TILE_WIDTH = 60
TILE_HEIGHT = 90
TILE_MARGIN = 15

# --- 폰트 설정 (시스템 내장 폰트 자동 탐색) ---
def get_system_korean_font_name():
    """
    OS에 설치된 폰트 목록을 검색하여 한글 지원 폰트 이름을 반환합니다.
    """
    available_fonts = pygame.font.get_fonts()
    
    candidates = [
        'malgungothic', 'malgun', 'gulim', 'batang', 'dotum', # Windows
        'applegothic', 'applemyeongjo', # Mac
        'nanumgothic', 'nanummyeongjo', 'notosanscjk' # Linux/Common
    ]
    
    for font in candidates:
        if font in available_fonts:
            return font
            
    return None

# ============================================================================
# NASA API 영역 (환경변수 적용됨)
# ============================================================================
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

def fetch_nasa_apod_image():
    # [수정됨] 코드 내 하드코딩 제거 -> 환경변수에서 가져오기
    api_key = os.environ.get("NASA_API_KEY")

    # 환경변수가 없으면 API 호출을 하지 않고 None 반환 (검은 배경 사용)
    if not api_key:
        print("경고: 환경변수 'NASA_API_KEY'가 설정되지 않았습니다. 기본 배경을 사용합니다.")
        return None

    try:
        params = {'api_key': api_key}
        response = requests.get(NASA_APOD_URL, params=params, timeout=5)
        if response.status_code != 200: return None
        data = response.json()

        if data.get('media_type') == 'image':
            image_url = data.get('hdurl') or data.get('url')
            if image_url:
                img_response = requests.get(image_url, timeout=10)
                if img_response.status_code == 200:
                    return Image.open(BytesIO(img_response.content))
        return None
    except Exception as e:
        print(f"이미지 로드 실패: {e}")
        return None

def prepare_background_image(pil_image):
    if pil_image is None: return None
    try:
        pil_image = pil_image.convert('RGB')
        pil_image = pil_image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()
        pygame_image = pygame.image.fromstring(data, size, mode)

        dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        dark_overlay.fill((0, 0, 0))
        dark_overlay.set_alpha(150)

        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background.blit(pygame_image, (0, 0))
        background.blit(dark_overlay, (0, 0))
        return background
    except Exception:
        return None
# ============================================================================

# --- 게임 초기화 ---
def game_setup():
    return {
        'p1_hand': list(range(1, 10)),
        'p2_hand': list(range(1, 10)),
        'p1_choice': None,
        'p2_choice': None,
        'p1_score': 0,
        'p2_score': 0,
        'current_round': 1,
        'round_winner': None,
        'first_player': None,
        'current_turn': None,
        'game_state': 'SHOW_RULES',
        'action_button': None,
        'last_update_time': 0,
        'clickable_elements': {},
        'transition_message': '',
        'next_state': '',
        'background_image': None
    }

# --- 그리기 유틸리티 ---
def get_tile_colors(player_num, tile_number):
    is_odd = tile_number % 2 != 0
    bg_color = WHITE if is_odd else BLACK
    text_color = BLACK if is_odd else WHITE
    player_accent = RED if player_num == 1 else BLUE
    return bg_color, text_color, player_accent

def draw_tile(screen, font, player_num, tile_number, position, is_selected=False):
    rect = pygame.Rect(position[0], position[1], TILE_WIDTH, TILE_HEIGHT)
    bg_color, text_color, player_accent = get_tile_colors(player_num, tile_number)
    
    pygame.draw.rect(screen, bg_color, rect, border_radius=8)
    
    if is_selected:
        border_color = GOLD
        thickness = 4
    else:
        border_color = GRAY if bg_color == BLACK else BLACK
        thickness = 1
        
    pygame.draw.rect(screen, border_color, rect, thickness, border_radius=8)
    
    text_surf = font.render(str(tile_number), True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)
    
    bar_rect = pygame.Rect(rect.x + 10, rect.y + rect.height - 8, rect.width - 20, 4)
    pygame.draw.rect(screen, player_accent, bar_rect, border_radius=2)
    return rect

def draw_back_tile(screen, player_num, tile_number, position):
    if tile_number is None:
        return pygame.Rect(position[0], position[1], TILE_WIDTH, TILE_HEIGHT)

    rect = pygame.Rect(position[0], position[1], TILE_WIDTH, TILE_HEIGHT)
    is_odd = tile_number % 2 != 0
    bg_color = WHITE if is_odd else BLACK
    
    pygame.draw.rect(screen, bg_color, rect, border_radius=8)
    
    if not is_odd: 
        pygame.draw.rect(screen, GRAY, rect, 1, border_radius=8)

    player_color = RED if player_num == 1 else BLUE
    pygame.draw.rect(screen, player_color, rect, 3, border_radius=8)
    return rect

def draw_text(screen, text, font, color, center_pos, bold=False):
    font.set_bold(bold)
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=center_pos)
    screen.blit(text_surf, text_rect)

def draw_button(screen, text, font, rect, bg_color=BLUE, text_color=WHITE):
    pygame.draw.rect(screen, bg_color, rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)
    draw_text(screen, text, font, text_color, rect.center, bold=True)
    return rect

# --- 화면 구성 함수 ---

def draw_rules_screen(screen, fonts, background=None):
    if background: screen.blit(background, (0, 0))
    
    draw_text(screen, "구룡투 (Guryongtu)", fonts['large'], GOLD, (SCREEN_WIDTH // 2, 80), True)
    
    rules = [
        "1. 1~9의 숫자 카드를 사용하여 9번의 대결을 펼칩니다.",
        "2. 더 높은 숫자를 낸 사람이 승리합니다.",
        "3. [필승 전략] 가장 낮은 '1'은 가장 높은 '9'를 이깁니다.",
        "4. 카드 뒷면 색상 규칙:",
        "   - 홀수(1,3,5...) : 흰색 (白)",
        "   - 짝수(2,4,6...) : 흑색 (黑)",
        "5. 결과 화면에서는 숫자 대신 뒷면 색상만 공개됩니다.",
        "6. 한 PC에서 번갈아 진행합니다 (Hot-seat 방식)."
    ]
    
    start_y = 180
    for i, rule in enumerate(rules):
        color = GOLD if "필승" in rule or "뒷면" in rule else WHITE
        draw_text(screen, rule, fonts['medium'], color, (SCREEN_WIDTH // 2, start_y + i * 50))

    draw_text(screen, "화면을 클릭하여 게임 시작", fonts['medium'], GOLD, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100), True)

def draw_waiting_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 230))
    screen.blit(overlay, (0, 0))
    
    next_player = gs['current_turn']
    color = RED if next_player == 1 else BLUE
    
    draw_text(screen, "STOP!", fonts['large'], RED, (SCREEN_WIDTH // 2, 250), True)
    draw_text(screen, "화면을 가립니다.", fonts['medium'], WHITE, (SCREEN_WIDTH // 2, 320))
    draw_text(screen, f"Player {next_player}에게 순서를 넘겨주세요.", fonts['medium'], color, (SCREEN_WIDTH // 2, 370), True)
    
    button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 500, 300, 60)
    gs['action_button'] = draw_button(screen, f"나는 Player {next_player} 입니다", fonts['medium'], button_rect, bg_color=color)

def draw_game_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    
    gs['clickable_elements'] = {'hand': []}
    current_player = gs['current_turn']
    opponent = 2 if current_player == 1 else 1
    
    draw_text(screen, f"Round {gs['current_round']} / 9", fonts['large'], WHITE, (SCREEN_WIDTH // 2, 50), True)
    draw_text(screen, f"P1  {gs['p1_score']}  vs  {gs['p2_score']}  P2", fonts['medium'], WHITE, (SCREEN_WIDTH // 2, 100))
    
    turn_color = RED if current_player == 1 else BLUE
    draw_text(screen, f"Player {current_player}의 차례입니다", fonts['medium'], turn_color, (SCREEN_WIDTH // 2, 140), True)
    
    if current_player != gs['first_player'] and gs[f'p{opponent}_choice'] is not None:
        draw_text(screen, "상대가 낸 패 (색상 힌트!)", fonts['small'], GOLD, (SCREEN_WIDTH // 2, 220))
        draw_back_tile(screen, opponent, gs[f'p{opponent}_choice'], (SCREEN_WIDTH // 2 - TILE_WIDTH // 2, 250))
    elif current_player == gs['first_player']:
         draw_text(screen, "상대방이 대기 중입니다.", fonts['small'], GRAY, (SCREEN_WIDTH // 2, 220))

    my_hand = gs[f'p{current_player}_hand']
    total_width = len(my_hand) * (TILE_WIDTH + TILE_MARGIN) - TILE_MARGIN
    start_x = (SCREEN_WIDTH - total_width) // 2
    
    for i, num in enumerate(my_hand):
        pos = (start_x + i * (TILE_WIDTH + TILE_MARGIN), SCREEN_HEIGHT - TILE_HEIGHT - 50)
        is_selected = (gs[f'p{current_player}_choice'] == num)
        rect = draw_tile(screen, fonts['tile'], current_player, num, pos, is_selected)
        gs['clickable_elements']['hand'].append({'number': num, 'rect': rect})
    
    if gs[f'p{current_player}_choice'] is not None:
        button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 190, 200, 50)
        color = RED if current_player == 1 else BLUE
        gs['action_button'] = draw_button(screen, "결정 (턴 종료)", fonts['medium'], button_rect, bg_color=color)

def draw_result_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    p1c, p2c = gs['p1_choice'], gs['p2_choice']
    
    draw_text(screen, f"Round {gs['current_round']} 결과", fonts['large'], WHITE, (SCREEN_WIDTH // 2, 100), True)
    
    draw_back_tile(screen, 1, p1c, (SCREEN_WIDTH // 2 - TILE_WIDTH - 50, 250))
    draw_text(screen, "P1", fonts['small'], RED, (SCREEN_WIDTH // 2 - TILE_WIDTH - 20, 360))
    
    draw_text(screen, "VS", fonts['large'], GOLD, (SCREEN_WIDTH // 2, 295), True)
    
    draw_back_tile(screen, 2, p2c, (SCREEN_WIDTH // 2 + 50, 250))
    draw_text(screen, "P2", fonts['small'], BLUE, (SCREEN_WIDTH // 2 + 80, 360))

    winner = gs['round_winner']
    
    if winner == 1: text, color = "Player 1 승리!", RED
    elif winner == 2: text, color = "Player 2 승리!", BLUE
    else: text, color = "무승부!", GRAY
        
    draw_text(screen, text, fonts['large'], color, (SCREEN_WIDTH // 2, 450), True)
    draw_text(screen, f"현재 스코어 - P1 {gs['p1_score']} : {gs['p2_score']} P2", fonts['medium'], WHITE, (SCREEN_WIDTH // 2, 550))

def draw_game_over_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    
    if gs['p1_score'] > gs['p2_score']: text, color = "Player 1 최종 우승!", RED
    elif gs['p2_score'] > gs['p1_score']: text, color = "Player 2 최종 우승!", BLUE
    else: text, color = "최종 무승부!", WHITE
    
    draw_text(screen, "GAME OVER", fonts['large'], GOLD, (SCREEN_WIDTH // 2, 150), True)
    draw_text(screen, text, fonts['large'], color, (SCREEN_WIDTH // 2, 250), True)
    draw_text(screen, f"최종 점수: {gs['p1_score']} vs {gs['p2_score']}", fonts['medium'], WHITE, (SCREEN_WIDTH // 2, 350))
    
    button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 500, 200, 50)
    gs['action_button'] = draw_button(screen, "다시 시작하기", fonts['medium'], button_rect, bg_color=GRAY)

# --- 메인 로직 ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("구룡투 (Guryongtu) - Final Ver.")

    font_name = get_system_korean_font_name()
    print(f"감지된 폰트: {font_name}")

    fonts = {
        'tile': pygame.font.SysFont(font_name, 50),
        'small': pygame.font.SysFont(font_name, 20),
        'medium': pygame.font.SysFont(font_name, 28),
        'large': pygame.font.SysFont(font_name, 50, bold=True)
    }

    print("NASA APOD 이미지를 로드하는 중... (환경변수 확인 필요)")
    nasa_image = fetch_nasa_apod_image()
    background_surface = prepare_background_image(nasa_image)

    gs = game_setup()
    gs['background_image'] = background_surface
    running = True
    last_click_time = 0

    while running:
        current_time = time.time()
        state = gs['game_state']

        if state == 'SHOW_RESULT' and current_time - gs['last_update_time'] > 3.0:
            remaining_rounds = 9 - gs['current_round']
            p1_sc = gs['p1_score']
            p2_sc = gs['p2_score']
            
            if p1_sc > p2_sc + remaining_rounds or p2_sc > p1_sc + remaining_rounds:
                 gs['game_state'] = 'GAME_OVER'
            elif gs['current_round'] == 9:
                gs['game_state'] = 'GAME_OVER'
            else:
                gs['current_round'] += 1
                if gs['round_winner'] != 0:
                    gs['first_player'] = gs['round_winner']
                
                gs['current_turn'] = gs['first_player']
                gs['p1_choice'], gs['p2_choice'] = None, None
                gs['round_winner'] = None
                
                gs['game_state'] = 'WAITING_FOR_NEXT'
                gs['transition_message'] = f"{gs['current_round']}라운드 시작! Player {gs['first_player']} 선공"
            
            state = gs['game_state']

        if gs['background_image']: screen.blit(gs['background_image'], (0, 0))
        else: screen.fill(BACKGROUND_COLOR)

        gs['action_button'] = None
        gs['clickable_elements'] = {}
        
        if state == 'SHOW_RULES': draw_rules_screen(screen, fonts, gs['background_image'])
        elif state == 'PLAYER_TURN': draw_game_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'WAITING_FOR_NEXT': draw_waiting_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'SHOW_RESULT': draw_result_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'GAME_OVER': draw_game_over_screen(screen, fonts, gs, gs['background_image'])

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and current_time - last_click_time > 0.2:
                pos = pygame.mouse.get_pos()
                last_click_time = current_time
                
                if state == 'SHOW_RULES':
                    gs['first_player'] = random.choice([1, 2])
                    gs['current_turn'] = gs['first_player']
                    gs['game_state'] = 'WAITING_FOR_NEXT' 
                
                elif state == 'WAITING_FOR_NEXT':
                    if gs.get('action_button') and gs['action_button'].collidepoint(pos):
                        gs['game_state'] = 'PLAYER_TURN'

                elif state == 'PLAYER_TURN':
                    player = gs['current_turn']
                    opponent = 2 if player == 1 else 1
                    
                    for tile in gs['clickable_elements'].get('hand', []):
                        if tile['rect'].collidepoint(pos):
                            gs[f'p{player}_choice'] = tile['number']
                            break
                    
                    if gs.get('action_button') and gs['action_button'].collidepoint(pos):
                        if player == gs['first_player']:
                            gs['current_turn'] = opponent
                            gs['game_state'] = 'WAITING_FOR_NEXT'
                        else:
                            gs['game_state'] = 'SHOW_RESULT'
                            gs['last_update_time'] = time.time()
                            
                            p1c, p2c = gs['p1_choice'], gs['p2_choice']
                            winner = 0
                            if p1c > p2c: winner = 1
                            elif p2c > p1c: winner = 2
                            
                            if p1c == 1 and p2c == 9: winner = 1
                            if p1c == 9 and p2c == 1: winner = 2
                            if p1c == p2c: winner = 0
                            
                            gs['round_winner'] = winner
                            if winner != 0: gs[f'p{winner}_score'] += 1
                            gs['p1_hand'].remove(p1c)
                            gs['p2_hand'].remove(p2c)

                elif state == 'GAME_OVER':
                    if gs.get('action_button') and gs['action_button'].collidepoint(pos):
                        bg = gs['background_image']
                        gs = game_setup()
                        gs['background_image'] = bg

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()