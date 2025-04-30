import pygame
import sys
import math
import random
from pygame.locals import *

# 초기화
pygame.init()

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
COLORS = [RED, BLUE, GREEN, YELLOW, (255, 165, 0), (128, 0, 128), (255, 192, 203)]

# 화면 설정
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("로또 물리 시뮬레이션")
clock = pygame.time.Clock()

# 물리적 상수들
CONTAINER_RADIUS = 350  # 로또 통의 반지름 (픽셀)
BALL_RADIUS = 15        # 로또 공의 반지름 (픽셀)
BALL_COUNT = 45         # 로또 공의 개수
GRAVITY = 0.2           # 중력 계수
FRICTION = 0.99         # 마찰 계수
AIR_RESISTANCE = 0.995  # 공기 저항 계수
WIND_FORCE = 0.08       # 바람 세기
WIND_DIRECTION_CHANGE_PROB = 0.01  # 바람 방향 변화 확률
TURBULENCE_STRENGTH = 0.1  # 난류 강도

# 추첨 관련 변수
DRAW_INTERVAL = 3000    # 추첨 간격 (밀리초)
MAX_DRAWS = 6           # 최대 추첨 수
draw_timer = 0          # 추첨 타이머
draw_count = 0          # 현재 추첨 수
drawn_balls = []        # 추첨된 공 목록
extraction_in_progress = False  # 추출 진행 중 플래그
current_extraction_ball = None  # 현재 추출 중인 공
extraction_path = []    # 추출 경로

drawing_active = False  # 추첨 시작 여부
start_time = 0          # 시작 시간

# 로또 공 클래스
class LottoBall:
    def __init__(self, x, y, number):
        self.x = x
        self.y = y
        self.number = number
        self.radius = BALL_RADIUS
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.color = COLORS[number % len(COLORS)]
        self.drawn = False
        self.extracting = False
    
    def update(self, wind_x, wind_y):
        if self.drawn or self.extracting:
            return
            
        # 바람과 난류의 영향
        turbulence_x = random.uniform(-TURBULENCE_STRENGTH, TURBULENCE_STRENGTH)
        turbulence_y = random.uniform(-TURBULENCE_STRENGTH, TURBULENCE_STRENGTH)
        
        self.vx += wind_x + turbulence_x
        self.vy += wind_y + turbulence_y
        
        # 속도 업데이트
        self.vx *= AIR_RESISTANCE
        self.vy *= AIR_RESISTANCE
        
        # 위치 업데이트
        self.x += self.vx
        self.y += self.vy
        
        # 컨테이너 경계와 충돌 검사
        distance = math.sqrt((self.x - WIDTH/2)**2 + (self.y - HEIGHT/2)**2)
        if distance + self.radius > CONTAINER_RADIUS:
            # 충돌 지점과 방향 계산
            nx = (self.x - WIDTH/2) / distance
            ny = (self.y - HEIGHT/2) / distance
            
            # 위치 조정
            self.x = WIDTH/2 + nx * (CONTAINER_RADIUS - self.radius)
            self.y = HEIGHT/2 + ny * (CONTAINER_RADIUS - self.radius)
            
            # 속도 반사
            dot_product = self.vx * nx + self.vy * ny
            self.vx = (self.vx - 2 * dot_product * nx) * FRICTION
            self.vy = (self.vy - 2 * dot_product * ny) * FRICTION
    
    def draw(self):
        if self.drawn:
            return
            
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        font = pygame.font.SysFont('Arial', 12)
        text = font.render(str(self.number), True, WHITE)
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, text_rect)
    
    def check_collision(self, other):
        if self.drawn or other.drawn or self.extracting or other.extracting:
            return
            
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < self.radius + other.radius:
            # 충돌 응답
            collision_angle = math.atan2(dy, dx)
            magnitude1 = math.sqrt(self.vx**2 + self.vy**2)
            magnitude2 = math.sqrt(other.vx**2 + other.vy**2)
            direction1 = math.atan2(self.vy, self.vx)
            direction2 = math.atan2(other.vy, other.vx)
            
            # 새로운 속도 계산
            new_vx1 = magnitude2 * math.cos(direction2 - collision_angle) * math.cos(collision_angle) + \
                     magnitude1 * math.sin(direction1 - collision_angle) * math.cos(collision_angle + math.pi/2)
            new_vy1 = magnitude2 * math.cos(direction2 - collision_angle) * math.sin(collision_angle) + \
                     magnitude1 * math.sin(direction1 - collision_angle) * math.sin(collision_angle + math.pi/2)
            
            new_vx2 = magnitude1 * math.cos(direction1 - collision_angle) * math.cos(collision_angle) + \
                     magnitude2 * math.sin(direction2 - collision_angle) * math.cos(collision_angle + math.pi/2)
            new_vy2 = magnitude1 * math.cos(direction1 - collision_angle) * math.sin(collision_angle) + \
                     magnitude2 * math.sin(direction2 - collision_angle) * math.sin(collision_angle + math.pi/2)
            
            # 속도 업데이트
            self.vx = new_vx1 * FRICTION
            self.vy = new_vy1 * FRICTION
            other.vx = new_vx2 * FRICTION
            other.vy = new_vy2 * FRICTION
            
            # 겹침 해결
            overlap = 0.5 * (self.radius + other.radius - distance + 1)
            self.x -= overlap * math.cos(collision_angle)
            self.y -= overlap * math.sin(collision_angle)
            other.x += overlap * math.cos(collision_angle)
            other.y += overlap * math.sin(collision_angle)

# 공 초기화
balls = []
for i in range(BALL_COUNT):
    while True:
        # 랜덤 위치 생성
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, CONTAINER_RADIUS - BALL_RADIUS)
        x = WIDTH/2 + distance * math.cos(angle)
        y = HEIGHT/2 + distance * math.sin(angle)
        
        # 다른 공과 겹치지 않는지 확인
        overlap = False
        for ball in balls:
            dx = x - ball.x
            dy = y - ball.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 2 * BALL_RADIUS:
                overlap = True
                break
        
        if not overlap:
            balls.append(LottoBall(x, y, i+1))
            break

# 바람 초기화
wind_angle = random.uniform(0, 2 * math.pi)
wind_x = WIND_FORCE * math.cos(wind_angle)
wind_y = WIND_FORCE * math.sin(wind_angle)

# 결과 표시 함수
def display_results():
    result_width = 300
    result_height = 120
    result_x = WIDTH - result_width - 20
    result_y = 20
    
    pygame.draw.rect(screen, (50, 50, 50), (result_x, result_y, result_width, result_height))
    pygame.draw.rect(screen, WHITE, (result_x, result_y, result_width, result_height), 2)
    
    font = pygame.font.SysFont('Arial', 24)
    text = font.render("추첨 결과", True, WHITE)
    screen.blit(text, (result_x + 10, result_y + 10))
    
    if drawn_balls:
        ball_width = (result_width - 20) // 6 if len(drawn_balls) > 0 else 0
        for i, ball in enumerate(drawn_balls):
            if i < 6:  # 최대 6개만 표시
                ball_x = result_x + 10 + i * ball_width
                ball_y = result_y + 50
                
                pygame.draw.circle(screen, ball.color, (ball_x + ball_width//2, ball_y + ball_width//2), ball_width//2 - 2)
                num_font = pygame.font.SysFont('Arial', 16)
                num_text = num_font.render(str(ball.number), True, WHITE)
                num_rect = num_text.get_rect(center=(ball_x + ball_width//2, ball_y + ball_width//2))
                screen.blit(num_text, num_rect)

# 메인 루프
running = True
paused = False

while running:
    # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not drawing_active:
                    drawing_active = True
                    start_time = pygame.time.get_ticks()
                paused = not paused
            elif event.key == pygame.K_r:
                # 재시작
                draw_count = 0
                drawn_balls = []
                extraction_in_progress = False
                current_extraction_ball = None
                drawing_active = False
                
                # 공 초기화
                balls = []
                for i in range(BALL_COUNT):
                    while True:
                        angle = random.uniform(0, 2 * math.pi)
                        distance = random.uniform(0, CONTAINER_RADIUS - BALL_RADIUS)
                        x = WIDTH/2 + distance * math.cos(angle)
                        y = HEIGHT/2 + distance * math.sin(angle)
                        
                        overlap = False
                        for ball in balls:
                            dx = x - ball.x
                            dy = y - ball.y
                            dist = math.sqrt(dx**2 + dy**2)
                            if dist < 2 * BALL_RADIUS:
                                overlap = True
                                break
                        
                        if not overlap:
                            balls.append(LottoBall(x, y, i+1))
                            break
    
    if paused:
        # 일시 정지 텍스트 표시
        font = pygame.font.SysFont('Arial', 30)
        pause_text = font.render("일시 정지됨 (Space 키로 재개)", True, WHITE)
        screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, 50))
        pygame.display.flip()
        continue
    
    # 화면 지우기
    screen.fill(BLACK)
    
    # 컨테이너 그리기
    pygame.draw.circle(screen, WHITE, (WIDTH//2, HEIGHT//2), CONTAINER_RADIUS, 2)
    
    # 추첨 시작했고 최대 추첨 수에 도달하지 않았을 때
    current_time = pygame.time.get_ticks()
    
    if drawing_active and draw_count < MAX_DRAWS:
        # 타이머 업데이트
        if not extraction_in_progress:
            if current_time - start_time >= draw_timer:
                # 새로운 공 추첨
                draw_timer = current_time
                extraction_in_progress = True
                
                # 아직 뽑히지 않은 공들 중에서 선택
                available_balls = [ball for ball in balls if not ball.drawn and not ball.extracting]
                if available_balls:
                    current_extraction_ball = random.choice(available_balls)
                    current_extraction_ball.extracting = True
                    
                    # 추출 경로 계산 (원 가운데에서 상단 중앙으로)
                    extraction_path = [(WIDTH//2, HEIGHT//2), (WIDTH//2, 100)]
        
        # 추출 진행 중일 때
        elif current_extraction_ball:
            # 추출 애니메이션
            target_x, target_y = extraction_path[0]
            dx = target_x - current_extraction_ball.x
            dy = target_y - current_extraction_ball.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 5:  # 타겟에 도달
                extraction_path.pop(0)
                
                if not extraction_path:  # 경로 끝
                    current_extraction_ball.drawn = True
                    drawn_balls.append(current_extraction_ball)
                    current_extraction_ball.extracting = False
                    current_extraction_ball = None
                    extraction_in_progress = False
                    draw_count += 1
                    draw_timer = current_time + DRAW_INTERVAL
            else:
                # 추출 경로를 따라 이동
                speed = 5.0
                current_extraction_ball.x += (dx / distance) * speed
                current_extraction_ball.y += (dy / distance) * speed
    
    # 바람 방향 업데이트
    if random.random() < WIND_DIRECTION_CHANGE_PROB:
        wind_angle += random.uniform(-0.2, 0.2)
        wind_x = WIND_FORCE * math.cos(wind_angle)
        wind_y = WIND_FORCE * math.sin(wind_angle)
    
    # 공 업데이트 및 그리기
    for i, ball in enumerate(balls):
        ball.update(wind_x, wind_y)
        
        # 다른 공들과의 충돌 검사
        for j in range(i+1, len(balls)):
            ball.check_collision(balls[j])
        
        ball.draw()
    
    # 결과 표시
    display_results()
    
    # 추첨 상태 표시
    font = pygame.font.SysFont('Arial', 24)
    status_text = ""
    
    if not drawing_active:
        status_text = "Space 키를 눌러 시작하세요"
    elif draw_count >= MAX_DRAWS:
        status_text = "추첨 완료! R 키를 눌러 재시작"
    else:
        status_text = f"추첨 진행 중... ({draw_count}/{MAX_DRAWS})"
    
    text = font.render(status_text, True, WHITE)
    screen.blit(text, (20, 20))
    
    # 조작법 안내
    controls_font = pygame.font.SysFont('Arial', 16)
    controls_text = "Space: 시작/일시정지  |  R: 재시작"
    controls = controls_font.render(controls_text, True, WHITE)
    screen.blit(controls, (20, HEIGHT - 30))
    
    # 화면 업데이트
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
