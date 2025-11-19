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
FONT_NAME = 'malgungothic'

# --- 폰트 설정 (개선됨: 강제 다운로드 제거) ---
def get_font_path():
    """
    시스템에 설치된 한글 폰트를 안전하게 찾습니다.
    다운로드를 시도하지 않으므로 사용자 동의 없는 설치 문제를 방지합니다.
    """
    system = platform.system()
    
    # 우선순위 폰트 리스트
    font_candidates = []
    
    if system == 'Windows':
        win_font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        font_candidates = [
            os.path.join(win_font_dir, 'malgun.ttf'),    # 맑은 고딕
            os.path.join(win_font_dir, 'malgunbd.ttf'),  # 맑은 고딕 볼드
            os.path.join(win_font_dir, 'gulim.ttc'),     # 굴림
            os.path.join(win_font_dir, 'batang.ttc'),    # 바탕
        ]
    elif system == 'Darwin':  # macOS
        font_candidates = [
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ]
    else:  # Linux
        font_candidates = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        ]
    
    # 존재하는 폰트 반환
    for font_path in font_candidates:
        if os.path.exists(font_path):
            return font_path
            
    return None # 없으면 None 반환하여 Pygame 기본 폰트 사용

# ============================================================================
# NASA API 영역 (절대 수정 금지 구역)
# ============================================================================
NASA_API_KEY = "q3EvTmLhK3eFq2rIPNRyMdY2FeBvFG35PhNn91bG"
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

def fetch_nasa_apod_image():
    """NASA APOD API로부터 오늘의 우주 이미지를 가져옵니다."""
    try:
        params = {'api_key': NASA_API_KEY}
        response = requests.get(NASA_APOD_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('media_type') == 'image':
            image_url = data.get('hdurl') or data.get('url')
            if image_url:
                img_response = requests.get(image_url, timeout=15)
                img_response.raise_for_status()
                return Image.open(BytesIO(img_response.content))
        return None
    except Exception as e:
        print(f"NASA API 이미지 로드 실패: {e}")
        return None

def prepare_background_image(pil_image):
    """PIL 이미지를 pygame surface로 변환하고 화면 크기에 맞게 조정합니다."""
    if pil_image is None:
        return None
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
    except Exception as e:
        print(f"배경 이미지 처리 실패: {e}")
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
        # 상태 흐름: SHOW_RULES -> TRANSITION -> PLAYER_TURN -> WAITING_FOR_NEXT(프라이버시) -> PLAYER_TURN -> SHOW_RESULT
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
    return

def draw_button(screen, text, font, rect, bg_color=BLUE, text_color=WHITE):
    pygame.draw.rect(screen, bg_color, rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)
    draw_text(screen, text, font, text_color, rect.center, bold=True)
    return rect

# --- 화면 구성 함수 ---

def draw_rules_screen(screen, fonts, background=None):
    """
    [수정됨] 규칙 화면이 잘리지 않도록 레이아웃 조정
    """
    if background: screen.blit(background, (0, 0))
    
    # 제목 위치 상향 조정
    draw_text(screen, "구룡투 (Guryongtu)", fonts['large'], GOLD, (SCREEN_WIDTH // 2, 60), True)
    
    rules = [
        "1. 1~9의 숫자 카드를 사용하여 9번의 대결을 펼칩니다.",
        "2. 더 높은 숫자를 낸 사람이 승리합니다.",
        "3. [필승 전략] 가장 낮은 '1'은 가장 높은 '9'를 이깁니다.",
        "4. 카드 뒷면 색상 규칙 (정상적인 게임 요소):", # 설명 추가
        "   - 홀수(1,3,5...) : 흰색 (白)",
        "   - 짝수(2,4,6...) : 흑색 (黑)",
        "5. 상대 카드 뒷면의 흑/백을 보고 짝/홀을 예측하세요!",
        "6. 한 PC에서 번갈아 진행합니다 (Hot-seat 방식)."
    ]
    
    start_y = 140 # 시작 위치 위로 올림
    line_height = 45
    
    for i, rule in enumerate(rules):
        # 폰트 크기를 medium 대신 small과 medium 중간 정도로 조정하거나 그대로 유지하되 위치만 조정
        color = GOLD if "필승" in rule or "뒷면" in rule else WHITE
        draw_text(screen, rule, fonts['medium'], color, (SCREEN_WIDTH // 2, start_y + i * line_height))

    draw_text(screen, "화면을 클릭하여 게임 시작", fonts['medium'], GOLD, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80), True)

def draw_waiting_screen(screen, fonts, gs, background=None):
    """
    [신규] Hot-seat 방식을 위한 프라이버시 화면 (커튼 기능)
    """
    if background: screen.blit(background, (0, 0))
    
    # 화면을 어둡게 가림
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 230)) # 거의 안보이게 진하게 가림
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
    
    # 상대방이 이미 냈다면 뒷면 보여주기
    if current_player != gs['first_player'] and gs[f'p{opponent}_choice'] is not None:
        draw_text(screen, "상대가 낸 패 (색상 힌트!)", fonts['small'], GOLD, (SCREEN_WIDTH // 2, 220))
        draw_back_tile(screen, opponent, gs[f'p{opponent}_choice'], (SCREEN_WIDTH // 2 - TILE_WIDTH // 2, 250))
    elif current_player == gs['first_player']:
         draw_text(screen, "상대방이 대기 중입니다.", fonts['small'], GRAY, (SCREEN_WIDTH // 2, 220))

    # 내 핸드 그리기
    my_hand = gs[f'p{current_player}_hand']
    total_width = len(my_hand) * (TILE_WIDTH + TILE_MARGIN) - TILE_MARGIN
    start_x = (SCREEN_WIDTH - total_width) // 2
    
    for i, num in enumerate(my_hand):
        pos = (start_x + i * (TILE_WIDTH + TILE_MARGIN), SCREEN_HEIGHT - TILE_HEIGHT - 50)
        is_selected = (gs[f'p{current_player}_choice'] == num)
        rect = draw_tile(screen, fonts['tile'], current_player, num, pos, is_selected)
        gs['clickable_elements']['hand'].append({'number': num, 'rect': rect})
    
    # 결정 버튼
    if gs[f'p{current_player}_choice'] is not None:
        button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 190, 200, 50)
        color = RED if current_player == 1 else BLUE
        gs['action_button'] = draw_button(screen, "결정 (턴 종료)", fonts['medium'], button_rect, bg_color=color)

def draw_result_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    p1c, p2c = gs['p1_choice'], gs['p2_choice']
    
    draw_text(screen, f"Round {gs['current_round']} 결과", fonts['large'], WHITE, (SCREEN_WIDTH // 2, 100), True)
    
    draw_tile(screen, fonts['tile'], 1, p1c, (SCREEN_WIDTH // 2 - TILE_WIDTH - 50, 250))
    draw_text(screen, "P1", fonts['small'], RED, (SCREEN_WIDTH // 2 - TILE_WIDTH - 20, 360))
    draw_text(screen, "VS", fonts['large'], GOLD, (SCREEN_WIDTH // 2, 295), True)
    draw_tile(screen, fonts['tile'], 2, p2c, (SCREEN_WIDTH // 2 + 50, 250))
    draw_text(screen, "P2", fonts['small'], BLUE, (SCREEN_WIDTH // 2 + 80, 360))

    winner = gs['round_winner']
    reason = ""
    if p1c == p2c: reason = "(무승부)"
    elif (p1c == 1 and p2c == 9) or (p2c == 1 and p1c == 9): reason = "(1이 9를 이김!)"
    else: reason = "(높은 숫자 승리)"

    if winner == 1: text, color = "Player 1 승리!", RED
    elif winner == 2: text, color = "Player 2 승리!", BLUE
    else: text, color = "무승부!", GRAY
        
    draw_text(screen, text, fonts['large'], color, (SCREEN_WIDTH // 2, 430), True)
    draw_text(screen, reason, fonts['small'], WHITE, (SCREEN_WIDTH // 2, 480))
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

    # [수정됨] 안전한 폰트 로드 방식
    font_path = get_font_path()
    if font_path:
        print(f"폰트 로드 성공: {font_path}")
        fonts = {k: pygame.font.Font(font_path, v) for k, v in {'tile': 50, 'small': 20, 'medium': 28, 'large': 50}.items()}
    else:
        print("한글 폰트를 찾지 못해 기본 폰트를 사용합니다.")
        fonts = {k: pygame.font.SysFont(FONT_NAME, v) for k, v in {'tile': 50, 'small': 20, 'medium': 28, 'large': 50}.items()}

    print("NASA APOD 이미지를 로드하는 중...")
    nasa_image = fetch_nasa_apod_image()
    background_surface = prepare_background_image(nasa_image)

    gs = game_setup()
    gs['background_image'] = background_surface
    running = True
    last_click_time = 0

    while running:
        current_time = time.time()
        state = gs['game_state']

        # 결과 화면 자동 넘김 로직
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
                
                # 다음 라운드 시작 전에도 프라이버시(대기) 화면을 띄워줌
                gs['game_state'] = 'WAITING_FOR_NEXT'
                gs['transition_message'] = f"{gs['current_round']}라운드 시작! Player {gs['first_player']} 선공"

        # 렌더링
        if gs['background_image']: screen.blit(gs['background_image'], (0, 0))
        else: screen.fill(BACKGROUND_COLOR)

        gs['action_button'] = None
        gs['clickable_elements'] = {}
        state = gs['game_state']

        if state == 'SHOW_RULES': draw_rules_screen(screen, fonts, gs['background_image'])
        elif state == 'PLAYER_TURN': draw_game_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'WAITING_FOR_NEXT': draw_waiting_screen(screen, fonts, gs, gs['background_image']) # 신규 상태
        elif state == 'TRANSITION':
            # 기존 TRANSITION은 단순 메시지 용도로 남겨둠 (거의 안쓰임)
            if gs['background_image']: screen.blit(gs['background_image'], (0, 0))
            draw_text(screen, gs['transition_message'], fonts['large'], WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), True)
            if current_time - gs.get('transition_start_time', current_time) > 1.5: 
                 gs['game_state'] = gs['next_state']
        elif state == 'SHOW_RESULT': draw_result_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'GAME_OVER': draw_game_over_screen(screen, fonts, gs, gs['background_image'])

        pygame.display.update()

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and current_time - last_click_time > 0.2:
                pos = pygame.mouse.get_pos()
                last_click_time = current_time
                state = gs['game_state']

                if state == 'SHOW_RULES':
                    gs['first_player'] = random.choice([1, 2])
                    gs['current_turn'] = gs['first_player']
                    # 게임 시작 시 바로 패를 보여주지 않고 대기 화면으로 이동
                    gs['game_state'] = 'WAITING_FOR_NEXT' 
                
                elif state == 'WAITING_FOR_NEXT':
                    # "나는 Player X 입니다" 버튼 클릭 시 턴 시작
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
                            # 선공 후 바로 후공 패가 보이지 않게 WAITING 상태로 전환
                            gs['game_state'] = 'WAITING_FOR_NEXT'
                        else:
                            # 후공까지 완료 -> 결과 확인
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