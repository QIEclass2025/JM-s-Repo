import pygame
import sys
import random
import time
import requests
import os
from PIL import Image
from io import BytesIO
import platform
import zipfile
import urllib.request

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
# --- 폰트 다운로드 및 설정 ---
def download_nanum_font():
    """나눔고딕 폰트를 다운로드합니다."""
    font_dir = "fonts"
    font_path = os.path.join(font_dir, "NanumGothic.ttf")
    
    # 이미 폰트가 있으면 그대로 사용
    if os.path.exists(font_path):
        return font_path
    
    # fonts 디렉토리 생성
    if not os.path.exists(font_dir):
        os.makedirs(font_dir)
    
    try:
        print("나눔고딕 폰트를 다운로드하는 중...")
        # 나눔고딕 다운로드 URL (네이버 나눔폰트)
        url = "https://github.com/naver/nanumfont/releases/download/VER2.5/NanumFontSetup_TTF_GOTHIC.zip"
        
        # ZIP 파일 다운로드
        zip_path = os.path.join(font_dir, "nanum.zip")
        urllib.request.urlretrieve(url, zip_path)
        
        # ZIP 파일 압축 해제
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # NanumGothic.ttf 파일만 추출
            for file in zip_ref.namelist():
                if 'NanumGothic.ttf' in file and 'Bold' not in file:
                    with zip_ref.open(file) as source, open(font_path, 'wb') as target:
                        target.write(source.read())
                    break
        
        # ZIP 파일 삭제
        os.remove(zip_path)
        
        print("나눔고딕 폰트 다운로드 완료!")
        return font_path
        
    except Exception as e:
        print(f"폰트 다운로드 실패: {e}")
        return None

def get_font_path():
    """사용 가능한 한글 폰트 경로를 반환합니다."""
    # 1. 먼저 다운로드된 나눔고딕 확인
    local_font = os.path.join("fonts", "NanumGothic.ttf")
    if os.path.exists(local_font):
        return local_font
    
    # 2. 나눔고딕 다운로드 시도
    downloaded_font = download_nanum_font()
    if downloaded_font and os.path.exists(downloaded_font):
        return downloaded_font
    
    # 3. 시스템 폰트 확인 (폴백)
    system = platform.system()
    
    if system == 'Windows':
        win_font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        fallback_fonts = [
            os.path.join(win_font_dir, 'malgun.ttf'),
            os.path.join(win_font_dir, 'gulim.ttc'),
        ]
    elif system == 'Darwin':  # macOS
        fallback_fonts = [
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ]
    else:  # Linux
        fallback_fonts = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        ]
    
    for font_path in fallback_fonts:
        if os.path.exists(font_path):
            return font_path
    
    return None

# NASA API 설정 - 여기에 본인의 API 키를 입력하세요
NASA_API_KEY = "q3EvTmLhK3eFq2rIPNRyMdY2FeBvFG35PhNn91bG"  # 이 부분에 NASA API 키를 입력하세요
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

# --- NASA API 함수 ---
def fetch_nasa_apod_image():
    """NASA APOD API로부터 오늘의 우주 이미지를 가져옵니다."""
    try:
        params = {'api_key': NASA_API_KEY}
        response = requests.get(NASA_APOD_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 이미지 URL이 있는지 확인 (비디오인 경우도 있음)
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
        # 이미지 크기를 화면에 맞게 조정
        pil_image = pil_image.convert('RGB')
        pil_image = pil_image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)

        # PIL 이미지를 pygame surface로 변환
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()
        pygame_image = pygame.image.fromstring(data, size, mode)

        # 이미지를 어둡게 처리 (게임 UI가 잘 보이도록)
        dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        dark_overlay.fill((0, 0, 0))
        dark_overlay.set_alpha(150)  # 투명도 조절 (0-255, 높을수록 어두움)

        # 최종 배경 surface 생성
        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background.blit(pygame_image, (0, 0))
        background.blit(dark_overlay, (0, 0))

        return background
    except Exception as e:
        print(f"배경 이미지 처리 실패: {e}")
        return None

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
        'game_state': 'SHOW_RULES',  # SHOW_RULES, TRANSITION, PLAYER_TURN, SHOW_RESULT, GAME_OVER
        'action_button': None,
        'last_update_time': 0,
        'clickable_elements': {},
        'transition_message': '',
        'next_state': '',
        'background_image': None  # NASA 배경 이미지
    }

# --- 그리기 유틸리티 ---
def get_tile_colors(player_num, tile_number):
    is_odd = tile_number % 2 != 0
    bg_color = WHITE if is_odd else BLACK
    text_color = RED if player_num == 1 else BLUE
    return bg_color, text_color

def draw_tile(screen, font, player_num, tile_number, position, is_selected=False):
    rect = pygame.Rect(position[0], position[1], TILE_WIDTH, TILE_HEIGHT)
    bg_color, text_color = get_tile_colors(player_num, tile_number)
    pygame.draw.rect(screen, bg_color, rect, border_radius=8)
    border_color = GOLD if is_selected else GRAY
    pygame.draw.rect(screen, border_color, rect, 3 if is_selected else 2, border_radius=8)
    text_surf = font.render(str(tile_number), True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)
    return rect

def draw_back_tile(screen, player_num, tile_number, position):
    rect = pygame.Rect(position[0], position[1], TILE_WIDTH, TILE_HEIGHT)
    bg_color, _ = get_tile_colors(player_num, tile_number)
    pygame.draw.rect(screen, bg_color, rect, border_radius=8)

    # 타일 뒷면에 별 패턴 그리기
    random.seed(tile_number) # 각 숫자마다 고유한 별 패턴을 갖도록 시드 설정
    for _ in range(random.randint(4, 7)):
        star_x = random.randint(position[0] + 5, position[0] + TILE_WIDTH - 5)
        star_y = random.randint(position[1] + 5, position[1] + TILE_HEIGHT - 5)
        star_radius = random.randint(1, 2)
        pygame.draw.circle(screen, GOLD, (star_x, star_y), star_radius)

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
    draw_text(screen, text, font, text_color, rect.center, bold=True)
    return rect

# --- 화면 구성 함수 ---
def draw_rules_screen(screen, fonts, background=None):
    if background:
        screen.blit(background, (0, 0))
    draw_text(screen, "구룡투 (Guryongtu) 게임 규칙", fonts['large'], GOLD, (SCREEN_WIDTH // 2, 80), True)
    
    rules = [
        "1. 총 9라운드로 진행되며, 더 많은 라운드를 이기면 최종 승리합니다.",
        "2. 각 라운드마다 1~9까지의 블록 중 하나를 선택해서 냅니다.",
        "3. 더 높은 숫자를 낸 플레이어가 라운드에서 승리합니다.",
        "4. [특수 규칙] 가장 낮은 숫자인 1은 가장 높은 9를 이깁니다.",
        "5. 이전 라운드의 승자가 다음 라운드의 '선 플레이어'가 됩니다.",
        "6. '후 플레이어'는 선 플레이어가 낸 블록의 배경색으로 힌트를 얻을 수 있습니다.",
        "   (흰색 배경: 홀수 / 검은색 배경: 짝수)",
        "7. 만약 남은 라운드를 모두 이겨도 역전이 불가능하면 게임이 즉시 종료됩니다."
    ]
    
    start_y = 170
    line_height = 45
    for i, rule in enumerate(rules):
        if rule.strip().startswith('('):
            draw_text(screen, rule, fonts['small'], WHITE, (SCREEN_WIDTH // 2, start_y + (i-1) * line_height + 20), False)
        else:
            draw_text(screen, rule, fonts['medium'], WHITE, (SCREEN_WIDTH // 2, start_y + i * line_height))

    draw_text(screen, "화면을 클릭하면 게임을 시작합니다.", fonts['medium'], GOLD, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120), True)

def draw_game_screen(screen, fonts, gs, background=None):
    if background:
        screen.blit(background, (0, 0))
    gs['clickable_elements'] = {'hand': []}
    current_player = gs['current_turn']
    opponent = 2 if current_player == 1 else 1
    draw_text(screen, f"Round {gs['current_round']}", fonts['large'], WHITE, (SCREEN_WIDTH // 2, 50), True)
    draw_text(screen, f"P1 {gs['p1_score']} : {gs['p2_score']} P2", fonts['medium'], WHITE, (SCREEN_WIDTH // 2, 100))
    draw_text(screen, f"Player {current_player}의 턴", fonts['medium'], GOLD, (SCREEN_WIDTH // 2, 140))
    if current_player != gs['first_player'] and gs[f'p{opponent}_choice'] is not None:
        draw_text(screen, "선 플레이어의 블록", fonts['small'], WHITE, (SCREEN_WIDTH // 2, 220))
        draw_back_tile(screen, opponent, gs[f'p{opponent}_choice'], (SCREEN_WIDTH // 2 - TILE_WIDTH // 2, 250))
    my_hand = gs[f'p{current_player}_hand']
    total_width = len(my_hand) * (TILE_WIDTH + TILE_MARGIN) - TILE_MARGIN
    start_x = (SCREEN_WIDTH - total_width) // 2
    for i, num in enumerate(my_hand):
        pos = (start_x + i * (TILE_WIDTH + TILE_MARGIN), SCREEN_HEIGHT - TILE_HEIGHT - 40)
        is_selected = (gs[f'p{current_player}_choice'] == num)
        rect = draw_tile(screen, fonts['tile'], current_player, num, pos, is_selected)
        gs['clickable_elements']['hand'].append({'number': num, 'rect': rect})
    if gs[f'p{current_player}_choice'] is not None:
        button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 180, 200, 50)
        color = RED if current_player == 1 else BLUE
        gs['action_button'] = draw_button(screen, "결정", fonts['medium'], button_rect, bg_color=color)

def draw_result_screen(screen, fonts, gs, background=None):
    if background:
        screen.blit(background, (0, 0))
    p1c, p2c = gs['p1_choice'], gs['p2_choice']
    draw_text(screen, f"Round {gs['current_round']} 결과", fonts['large'], WHITE, (SCREEN_WIDTH // 2, 150), True)
    # 블록을 뒷면으로 표시 (숫자 숨김)
    draw_back_tile(screen, 1, p1c, (SCREEN_WIDTH // 2 - TILE_WIDTH - 30, 250))
    draw_back_tile(screen, 2, p2c, (SCREEN_WIDTH // 2 + 30, 250))
    winner = gs['round_winner']
    if winner == 1: text, color = "Player 1 승리!", RED
    elif winner == 2: text, color = "Player 2 승리!", BLUE
    else: text, color = "무승부!", WHITE
    draw_text(screen, text, fonts['large'], color, (SCREEN_WIDTH // 2, 400), True)
    draw_text(screen, f"P1 {gs['p1_score']} : {gs['p2_score']} P2", fonts['medium'], WHITE, (SCREEN_WIDTH // 2, 460))

def draw_game_over_screen(screen, fonts, gs, background=None):
    if background:
        screen.blit(background, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    if gs['p1_score'] > gs['p2_score']: text, color = "Player 1 최종 승리!", RED
    elif gs['p2_score'] > gs['p1_score']: text, color = "Player 2 최종 승리!", BLUE
    else: text, color = "최종 무승부!", WHITE
    draw_text(screen, "게임 종료", fonts['large'], WHITE, (SCREEN_WIDTH // 2, 200), True)
    draw_text(screen, text, fonts['large'], color, (SCREEN_WIDTH // 2, 300), True)
    draw_text(screen, f"최종 점수: P1 {gs['p1_score']} : {gs['p2_score']} P2", fonts['medium'], WHITE, (SCREEN_WIDTH // 2, 400))
    button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 500, 200, 50)
    gs['action_button'] = draw_button(screen, "다시 시작하기", fonts['medium'], button_rect)

# --- 메인 로직 ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("구룡투 (Guryongtu) - 최종본 with NASA APOD")

    # 한글 폰트 로드
    font_path = get_font_path()
    if font_path:
        print(f"폰트 로드: {font_path}")
        fonts = {k: pygame.font.Font(font_path, v) for k, v in {'tile': 40, 'small': 20, 'medium': 28, 'large': 42}.items()}
    else:
        print("한글 폰트를 찾을 수 없습니다. 시스템 기본 폰트를 사용합니다.")
        fonts = {k: pygame.font.SysFont(FONT_NAME, v) for k, v in {'tile': 40, 'small': 20, 'medium': 28, 'large': 42}.items()}

    # NASA APOD 배경 이미지 로드
    print("NASA APOD 이미지를 로드하는 중...")
    nasa_image = fetch_nasa_apod_image()
    background_surface = prepare_background_image(nasa_image)
    if background_surface:
        print("NASA 배경 이미지 로드 완료!")
    else:
        print("NASA 배경 이미지 로드 실패. 기본 배경을 사용합니다.")

    gs = game_setup()
    gs['background_image'] = background_surface
    running = True
    last_click_time = 0

    while running:
        current_time = time.time()
        state = gs['game_state']

        if state == 'SHOW_RESULT' and current_time - gs['last_update_time'] > 2.5:
            remaining_rounds = 9 - gs['current_round']
            score_diff = abs(gs['p1_score'] - gs['p2_score'])
            if score_diff > remaining_rounds:
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
                gs['game_state'] = 'TRANSITION'
                gs['transition_message'] = f"{gs['current_round']}라운드 선 플레이어: Player {gs['first_player']}"
                gs['next_state'] = 'PLAYER_TURN'

        # 배경 그리기 (NASA 이미지가 없으면 기본 배경색)
        if gs['background_image']:
            screen.blit(gs['background_image'], (0, 0))
        else:
            screen.fill(BACKGROUND_COLOR)

        gs['action_button'] = None
        gs['clickable_elements'] = {}
        state = gs['game_state']

        if state == 'SHOW_RULES': draw_rules_screen(screen, fonts, gs['background_image'])
        elif state == 'PLAYER_TURN': draw_game_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'TRANSITION':
            if gs['background_image']:
                screen.blit(gs['background_image'], (0, 0))
            draw_text(screen, gs['transition_message'], fonts['large'], WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), True)
        elif state == 'SHOW_RESULT': draw_result_screen(screen, fonts, gs, gs['background_image'])
        elif state == 'GAME_OVER': draw_game_over_screen(screen, fonts, gs, gs['background_image'])

        pygame.display.update()

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
                    gs['game_state'] = 'TRANSITION'
                    gs['transition_message'] = f"1라운드 선 플레이어는 Player {gs['first_player']} 입니다."
                    gs['next_state'] = 'PLAYER_TURN'
                
                elif state == 'TRANSITION':
                    gs['game_state'] = gs['next_state']

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
                        else:
                            gs['game_state'] = 'SHOW_RESULT'
                            gs['last_update_time'] = time.time()
                            p1c, p2c = gs['p1_choice'], gs['p2_choice']
                            winner = 0
                            if (p1c > p2c and not (p1c == 9 and p2c == 1)) or (p1c == 1 and p2c == 9): winner = 1
                            elif (p2c > p1c and not (p2c == 9 and p1c == 1)) or (p2c == 1 and p1c == 9): winner = 2
                            gs['round_winner'] = winner
                            if winner != 0: gs[f'p{winner}_score'] += 1
                            gs['p1_hand'].remove(p1c)
                            gs['p2_hand'].remove(p2c)

                elif state == 'GAME_OVER':
                    if gs.get('action_button') and gs['action_button'].collidepoint(pos):
                        gs = game_setup()
                        gs['background_image'] = background_surface

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()