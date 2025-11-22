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

# --- 폰트 설정 ---
def get_font_path():
    """시스템 폰트 안전 로드"""
    system = platform.system()
    font_candidates = []
    if system == 'Windows':
        win_font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        font_candidates = [os.path.join(win_font_dir, 'malgun.ttf'), os.path.join(win_font_dir, 'gulim.ttc')]
    elif system == 'Darwin':
        font_candidates = ['/System/Library/Fonts/AppleSDGothicNeo.ttc', '/Library/Fonts/Arial Unicode.ttf']
    else:
        font_candidates = ['/usr/share/fonts/truetype/nanum/NanumGothic.ttf']
    
    for font_path in font_candidates:
        if os.path.exists(font_path): return font_path
    return None

# ============================================================================
# NASA API 영역 (보안 패치 및 비디오 예외처리 적용)
# ============================================================================
NASA_API_KEY = os.environ.get("NASA_API_KEY")
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

if not NASA_API_KEY:
    print("[경고] NASA_API_KEY 환경변수가 설정되지 않았습니다. 기본 배경을 사용합니다.")

def fetch_nasa_apod_image():
    """
    [피드백 반영] NASA API 호출 및 예외 처리 강화
    - 이미지가 아닌 비디오(video) 타입이 올 경우 안전하게 None을 반환하여 게임 멈춤 방지
    """
    if not NASA_API_KEY: return None

    try:
        params = {'api_key': NASA_API_KEY}
        response = requests.get(NASA_APOD_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        # [친구 피드백 반영] 미디어 타입 확인 (Video일 경우 처리)
        if data.get('media_type') != 'image':
            print(f"[알림] 오늘은 NASA 사진 대신 영상({data.get('media_type')})이 있습니다. 기본 배경을 사용합니다.")
            return None

        image_url = data.get('hdurl') or data.get('url')
        if image_url:
            img_response = requests.get(image_url, timeout=10)
            return Image.open(BytesIO(img_response.content))
    except Exception as e:
        print(f"[오류] NASA 이미지 로드 실패: {e}")
        return None
    return None

def prepare_background_image(pil_image):
    if pil_image is None: return None
    try:
        pil_image = pil_image.convert('RGB').resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
        pygame_image = pygame.image.fromstring(pil_image.tobytes(), pil_image.size, pil_image.mode)
        dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        dark_overlay.fill((0, 0, 0))
        dark_overlay.set_alpha(150)
        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background.blit(pygame_image, (0, 0))
        background.blit(dark_overlay, (0, 0))
        return background
    except: return None

# --- 게임 초기화 ---
def game_setup(p1_total=0, p2_total=0):
    """
    [피드백 반영] 게임 재시작 시에도 전적(Total Score)이 유지되도록 매개변수 추가
    """
    return {
        'p1_hand': list(range(1, 10)),
        'p2_hand': list(range(1, 10)),
        'p1_choice': None, 'p2_choice': None,
        'p1_score': 0, 'p2_score': 0,
        'p1_total_wins': p1_total, # 누적 승리 (전적)
        'p2_total_wins': p2_total, # 누적 승리 (전적)
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
    if is_selected: pygame.draw.rect(screen, GOLD, rect, 4, border_radius=8)
    else: pygame.draw.rect(screen, GRAY if bg_color == BLACK else BLACK, rect, 1, border_radius=8)
    text_surf = font.render(str(tile_number), True, text_color)
    screen.blit(text_surf, text_surf.get_rect(center=rect.center))
    pygame.draw.rect(screen, player_accent, pygame.Rect(rect.x+10, rect.y+rect.height-8, rect.width-20, 4), border_radius=2)
    return rect

def draw_back_tile(screen, player_num, tile_number, position):
    rect = pygame.Rect(position[0], position[1], TILE_WIDTH, TILE_HEIGHT)
    is_odd = tile_number % 2 != 0
    bg_color = WHITE if is_odd else BLACK
    pygame.draw.rect(screen, bg_color, rect, border_radius=8)
    if not is_odd: pygame.draw.rect(screen, GRAY, rect, 1, border_radius=8)
    pygame.draw.rect(screen, RED if player_num == 1 else BLUE, rect, 3, border_radius=8)
    return rect

def draw_text(screen, text, font, color, center_pos, bold=False):
    font.set_bold(bold)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=center_pos))

def draw_button(screen, text, font, rect, bg_color=BLUE, text_color=WHITE):
    pygame.draw.rect(screen, bg_color, rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)
    draw_text(screen, text, font, text_color, rect.center, bold=True)
    return rect

# --- 화면 구성 함수 ---
def draw_rules_screen(screen, fonts, background=None):
    if background: screen.blit(background, (0, 0))
    draw_text(screen, "구룡투 (Guryongtu)", fonts['large'], GOLD, (SCREEN_WIDTH//2, 60), True)
    rules = [
        "1. 1~9 숫자 카드로 9번 대결합니다. (높은 수 승리)",
        "2. [전략] '1'은 '9'를 이깁니다!",
        "3. 뒷면 색상(흑/백)으로 상대 패의 홀짝을 예측하세요.",
        "4. 한 PC에서 번갈아 진행합니다 (Hot-seat).",
        "5. 게임이 끝나도 전적은 유지됩니다."
    ]
    for i, rule in enumerate(rules):
        draw_text(screen, rule, fonts['medium'], WHITE, (SCREEN_WIDTH//2, 140 + i*50))
    draw_text(screen, "화면을 클릭하여 게임 시작", fonts['medium'], GOLD, (SCREEN_WIDTH//2, SCREEN_HEIGHT-80), True)

def draw_waiting_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 230))
    screen.blit(overlay, (0, 0))
    next_p = gs['current_turn']
    color = RED if next_p == 1 else BLUE
    draw_text(screen, "STOP!", fonts['large'], RED, (SCREEN_WIDTH//2, 250), True)
    draw_text(screen, "화면을 가립니다. 순서를 넘겨주세요.", fonts['medium'], WHITE, (SCREEN_WIDTH//2, 320))
    button_rect = pygame.Rect(SCREEN_WIDTH//2-150, 500, 300, 60)
    gs['action_button'] = draw_button(screen, f"나는 Player {next_p} 입니다", fonts['medium'], button_rect, bg_color=color)

def draw_game_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    gs['clickable_elements'] = {'hand': []}
    curr = gs['current_turn']
    opp = 2 if curr == 1 else 1
    
    # [피드백 반영] 전적 표시 (상단에 누적 승수 표시)
    draw_text(screen, f"[Total] P1 {gs['p1_total_wins']}승 : {gs['p2_total_wins']}승 P2", fonts['small'], GOLD, (SCREEN_WIDTH//2, 30))
    
    draw_text(screen, f"Round {gs['current_round']} / 9", fonts['large'], WHITE, (SCREEN_WIDTH//2, 80), True)
    draw_text(screen, f"P1  {gs['p1_score']}  vs  {gs['p2_score']}  P2", fonts['medium'], WHITE, (SCREEN_WIDTH//2, 130))
    
    turn_color = RED if curr == 1 else BLUE
    draw_text(screen, f"Player {curr}의 차례", fonts['medium'], turn_color, (SCREEN_WIDTH//2, 170), True)

    if curr != gs['first_player'] and gs[f'p{opp}_choice']:
        draw_text(screen, "상대가 낸 패 (색상 힌트)", fonts['small'], GOLD, (SCREEN_WIDTH//2, 240))
        draw_back_tile(screen, opp, gs[f'p{opp}_choice'], (SCREEN_WIDTH//2-TILE_WIDTH//2, 270))
    elif curr == gs['first_player']:
         draw_text(screen, "상대방 대기 중", fonts['small'], GRAY, (SCREEN_WIDTH//2, 240))

    my_hand = gs[f'p{curr}_hand']
    start_x = (SCREEN_WIDTH - (len(my_hand)*(TILE_WIDTH+TILE_MARGIN)-TILE_MARGIN)) // 2
    for i, num in enumerate(my_hand):
        pos = (start_x + i*(TILE_WIDTH+TILE_MARGIN), SCREEN_HEIGHT-TILE_HEIGHT-50)
        rect = draw_tile(screen, fonts['tile'], curr, num, pos, gs[f'p{curr}_choice']==num)
        gs['clickable_elements']['hand'].append({'number': num, 'rect': rect})
    
    if gs[f'p{curr}_choice']:
        gs['action_button'] = draw_button(screen, "결정 (턴 종료)", fonts['medium'], pygame.Rect(SCREEN_WIDTH//2-100, SCREEN_HEIGHT-190, 200, 50), bg_color=turn_color)

def draw_result_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    p1c, p2c = gs['p1_choice'], gs['p2_choice']
    draw_text(screen, f"Round {gs['current_round']} 결과", fonts['large'], WHITE, (SCREEN_WIDTH//2, 100), True)
    draw_tile(screen, fonts['tile'], 1, p1c, (SCREEN_WIDTH//2-TILE_WIDTH-50, 250))
    draw_text(screen, "VS", fonts['large'], GOLD, (SCREEN_WIDTH//2, 295), True)
    draw_tile(screen, fonts['tile'], 2, p2c, (SCREEN_WIDTH//2+50, 250))
    
    winner = gs['round_winner']
    reason = "(무승부)" if winner == 0 else ("(1이 9를 이김!)" if {p1c,p2c}=={1,9} else "(높은 숫자 승리)")
    color = RED if winner == 1 else (BLUE if winner == 2 else GRAY)
    text = f"Player {winner} 승리!" if winner else "무승부!"
    
    draw_text(screen, text, fonts['large'], color, (SCREEN_WIDTH//2, 430), True)
    draw_text(screen, reason, fonts['small'], WHITE, (SCREEN_WIDTH//2, 480))
    draw_text(screen, f"현재 스코어 - P1 {gs['p1_score']} : {gs['p2_score']} P2", fonts['medium'], WHITE, (SCREEN_WIDTH//2, 550))

def draw_game_over_screen(screen, fonts, gs, background=None):
    if background: screen.blit(background, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    
    final_winner = 0
    if gs['p1_score'] > gs['p2_score']: final_winner = 1
    elif gs['p2_score'] > gs['p1_score']: final_winner = 2
    
    text = f"Player {final_winner} 최종 우승!" if final_winner else "최종 무승부!"
    color = RED if final_winner == 1 else (BLUE if final_winner == 2 else WHITE)
    
    draw_text(screen, "GAME OVER", fonts['large'], GOLD, (SCREEN_WIDTH//2, 150), True)
    draw_text(screen, text, fonts['large'], color, (SCREEN_WIDTH//2, 250), True)
    draw_text(screen, f"최종 점수: {gs['p1_score']} vs {gs['p2_score']}", fonts['medium'], WHITE, (SCREEN_WIDTH//2, 350))
    
    # [피드백 반영] 게임 종료 화면에도 누적 전적 표시
    draw_text(screen, f"[누적 전적] P1 {gs['p1_total_wins']}승 : {gs['p2_total_wins']}승 P2", fonts['medium'], GOLD, (SCREEN_WIDTH//2, 420))
    
    gs['action_button'] = draw_button(screen, "다시 시작하기", fonts['medium'], pygame.Rect(SCREEN_WIDTH//2-100, 500, 200, 50), bg_color=GRAY)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("구룡투 (Guryongtu) - Final Ver.")
    
    font_path = get_font_path()
    fonts = {k: (pygame.font.Font(font_path, v) if font_path else pygame.font.SysFont(FONT_NAME, v)) for k, v in {'tile':50,'small':20,'medium':28,'large':50}.items()}

    print("NASA 이미지 로딩 중...")
    nasa_img = fetch_nasa_apod_image()
    bg_surface = prepare_background_image(nasa_img)

    gs = game_setup()
    gs['background_image'] = bg_surface
    running = True
    last_click = 0

    while running:
        curr_time = time.time()
        state = gs['game_state']

        # 결과 화면 자동 넘김
        if state == 'SHOW_RESULT' and curr_time - gs['last_update_time'] > 3.0:
            rem_rounds = 9 - gs['current_round']
            if abs(gs['p1_score'] - gs['p2_score']) > rem_rounds or gs['current_round'] == 9:
                # 게임 종료 시 누적 전적 업데이트
                if gs['p1_score'] > gs['p2_score']: gs['p1_total_wins'] += 1
                elif gs['p2_score'] > gs['p1_score']: gs['p2_total_wins'] += 1
                gs['game_state'] = 'GAME_OVER'
            else:
                gs['current_round'] += 1
                if gs['round_winner']: gs['first_player'] = gs['round_winner']
                gs['current_turn'] = gs['first_player']
                gs['p1_choice'] = gs['p2_choice'] = gs['round_winner'] = None
                gs['game_state'] = 'WAITING_FOR_NEXT'
                gs['transition_message'] = f"{gs['current_round']}라운드 시작! Player {gs['first_player']} 선공"

        # 화면 그리기
        if gs['background_image']: screen.blit(gs['background_image'], (0, 0))
        else: screen.fill(BACKGROUND_COLOR)
        
        gs['action_button'] = None
        gs['clickable_elements'] = {}
        
        if state == 'SHOW_RULES': draw_rules_screen(screen, fonts, gs['background_image'])
        elif state == 'PLAYER_TURN': draw_game_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'WAITING_FOR_NEXT': draw_waiting_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'TRANSITION': # 메시지 표시용
            if gs['background_image']: screen.blit(gs['background_image'], (0, 0))
            draw_text(screen, gs['transition_message'], fonts['large'], WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), True)
            if curr_time - gs.get('transition_start', curr_time) > 1.5: gs['game_state'] = gs['next_state']
        elif state == 'SHOW_RESULT': draw_result_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'GAME_OVER': draw_game_over_screen(screen, fonts, gs, gs['background_image'])
        
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN and curr_time - last_click > 0.2:
                pos = pygame.mouse.get_pos()
                last_click = curr_time
                
                if state == 'SHOW_RULES':
                    gs['first_player'] = random.choice([1, 2])
                    gs['current_turn'] = gs['first_player']
                    
                    # [피드백 반영] 시작 전 누가 선공인지 명확히 보여주기 위해 TRANSITION 상태 추가
                    gs['game_state'] = 'TRANSITION'
                    gs['transition_message'] = f"첫 선공은 Player {gs['first_player']} 입니다!"
                    gs['next_state'] = 'WAITING_FOR_NEXT'
                    gs['transition_start'] = curr_time
                
                elif state == 'TRANSITION': pass # 자동 넘김 대기

                elif state == 'WAITING_FOR_NEXT':
                    if gs.get('action_button') and gs['action_button'].collidepoint(pos):
                        gs['game_state'] = 'PLAYER_TURN'

                elif state == 'PLAYER_TURN':
                    curr = gs['current_turn']
                    opp = 2 if curr == 1 else 1
                    for t in gs['clickable_elements'].get('hand', []):
                        if t['rect'].collidepoint(pos):
                            gs[f'p{curr}_choice'] = t['number']
                            break
                    if gs.get('action_button') and gs['action_button'].collidepoint(pos):
                        if curr == gs['first_player']:
                            gs['current_turn'] = opp
                            gs['game_state'] = 'WAITING_FOR_NEXT'
                        else:
                            gs['game_state'] = 'SHOW_RESULT'
                            gs['last_update_time'] = time.time()
                            p1, p2 = gs['p1_choice'], gs['p2_choice']
                            w = 1 if (p1>p2 and not(p1==9 and p2==1)) or (p1==1 and p2==9) else (2 if p1!=p2 else 0)
                            gs['round_winner'] = w
                            if w: gs[f'p{w}_score'] += 1
                            gs['p1_hand'].remove(p1); gs['p2_hand'].remove(p2)
                
                elif state == 'GAME_OVER':
                    if gs.get('action_button') and gs['action_button'].collidepoint(pos):
                        # [피드백 반영] 재시작 시 누적 전적 유지
                        bg = gs['background_image']
                        p1_tot, p2_tot = gs['p1_total_wins'], gs['p2_total_wins']
                        # 누적 점수를 넘겨주며 초기화
                        gs = game_setup(p1_tot, p2_tot)
                        gs['background_image'] = bg

    pygame.quit(); sys.exit()

if __name__ == '__main__': main()