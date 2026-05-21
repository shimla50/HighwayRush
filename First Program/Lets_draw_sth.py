from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import os

WIN_W, WIN_H = 1000, 800
LANE_POSITIONS = [-120, 0, 120]
ROAD_WIDTH = 360
player_lane = 1
player_x = 0.0
INTERP_SPEED = 0.018
PLAYER_W = 55
PLAYER_D = 110
player_car_type = 0  
ROAD_SEG_LEN = 400
NUM_SEGS = 12
road_offsets = [(i - 2) * ROAD_SEG_LEN for i in range(NUM_SEGS)]
traffic = []
SPAWN_DIST = 3800
DESPAWN_DIST = -400
spawn_timer = 0
SPAWN_INTERVAL = 200
base_speed = 0.5
speed_mult = 0.3
MAX_MULT = 5.5
elapsed_time = 0.0
frame_count = 0
camera_mode = 0
game_state = "running"
high_score = 0.0
HIGHSCORE_FILE = "highscore.txt"
collision_count = 0
MAx_collision = 3
is_night_mode = False
orbs = []
particles = []
explosion_progress = 0
near_miss_display_timer = 0
bonus_display_timer = 0
womp_womp_display_timer = 0
score = 0.0 

def load_high_score():
    global high_score
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                high_score = float(f.read().strip())
        except:
            high_score = 0.0

def save_high_score():
    global high_score, score
    if score > high_score:
        high_score = score
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write(f"{high_score:.2f}")

VEHICLE_TYPES = [(60, 40, 110), (80, 55, 150), (50, 35, 90), (90, 65, 180), (55, 45, 100)]

VEHICLE_COLORS = [(0.9, 0.1, 0.1), (0.1, 0.7, 0.2), (0.1, 0.3, 0.9), (0.9, 0.6, 0.1), (0.7, 0.1, 0.8), (0.1, 0.8, 0.8), (0.9, 0.9, 0.1)]

def spawn_vehicle():
    if random.random() < 0.4:
        return
    MIN_SPACING = 950
    blocked_lanes = set()
    for i, lane_x in enumerate(LANE_POSITIONS):
        for v in traffic:
            if abs(v['x'] - lane_x) < 5 and (SPAWN_DIST - v['y']) < MIN_SPACING:
                blocked_lanes.add(i)
    if len(blocked_lanes) >= 2:
        return
    available_lanes = [i for i in range(3) if i not in blocked_lanes]
    if not available_lanes:
        return
    lane = random.choice(available_lanes)
    w, h, d = random.choice(VEHICLE_TYPES)
    traffic.append({
        'x': LANE_POSITIONS[lane],
        'y': SPAWN_DIST,
        'w': w, 'h': h, 'd': d,
        'color': random.choice(VEHICLE_COLORS),
        'speed_mult': random.uniform(0.75, 1.25)})

def aabb_hit(px, py, tx, ty, tw, td):
    return (abs(px - tx) < (PLAYER_W/2 + tw/2) and
            abs(py - ty) < (PLAYER_D/2 + td/2))

def update_road_segments(current_speed):
    global road_offsets
    for i in range(len(road_offsets)):
        road_offsets[i] -= current_speed
        if road_offsets[i] < -800:
            road_offsets[i] += NUM_SEGS * ROAD_SEG_LEN

def is_near_miss(px, py, tx, ty, tw, td):
    enlarged_w = tw + 90 
    enlarged_d = td + 120
    return (abs(px - tx) < (PLAYER_W/2 + enlarged_w/2) and
            abs(py - ty) < (PLAYER_D/2 + enlarged_d/2))

def spawn_orb():
    if len(orbs) == 0:
        available_lanes = [0, 1, 2]
        lane = random.choice(available_lanes)
        orbs.append({
            'x': LANE_POSITIONS[lane],
            'y': SPAWN_DIST,
            'radius': 20
        })

def handle_orb_collision(o):
    global score, bonus_display_timer, collision_count, womp_womp_display_timer
    if random.random() > 0.5:
        collision_count += 1
        womp_womp_display_timer = 400 
        if collision_count >= MAx_collision:
            trigger_explosion()
    else:
        score += 50
        bonus_display_timer = 400

def draw_orbs():
    for o in orbs:
        glPushMatrix()
        glTranslatef(o['x'], o['y'], 30)
        glColor3f(1.0, 0.8, 0.2) 
        gluSphere(gluNewQuadric(), o['radius'], 16, 16)
        glPopMatrix()

def trigger_explosion():
    global game_state, explosion_progress, particles
    game_state = "exploding"
    explosion_progress = 0
    particles = []
    for _ in range(80):
        particles.append({
            'dx': random.uniform(-12, 12), 
            'dy': random.uniform(-12, 12), 
            'dz': random.uniform(-5, 30), 
            'life': random.uniform(0.5, 1.8),
            'color': random.choice([(1.0, 0.2, 0.0), (1.0, 0.5, 0.0), (1.0, 0.9, 0.0), (0.3, 0.3, 0.3), (0.1, 0.1, 0.1)])
        })

def draw_explosion():
    if game_state == "exploding":
        glPushMatrix()
        glTranslatef(player_x, 0, 0)
        for p in particles:
            progress = explosion_progress * 0.4 
            if progress < p['life'] * 100:
                glColor3f(*p['color'])
                glPushMatrix()
                glTranslatef(p['dx'] * progress, p['dy'] * progress, p['dz'] * progress)
                gluSphere(gluNewQuadric(), max(2, 25 - progress * 0.15), 10, 10)
                glPopMatrix()
        glPopMatrix()

def draw_text(x, y, text):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_box(w, h, d):
    glPushMatrix()
    glScalef(w/50, d/50, h/50)
    glutSolidCube(50)
    glPopMatrix()

def draw_wheel(x_off, y_off, radius=10, length=12):
    glPushMatrix()
    glTranslatef(x_off, y_off, radius)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.1, 0.1, 0.1)
    gluCylinder(gluNewQuadric(), radius, radius, length, 8, 4)
    glPopMatrix()

def draw_player():
    if game_state == "exploding":
        return
    glPushMatrix()
    glTranslatef(player_x, 0, 0)
    hw, hd = PLAYER_W / 2, PLAYER_D / 2
    if player_car_type == 0:
        glColor3f(0.1, 0.4, 0.9)
        glPushMatrix()
        glTranslatef(0, 0, 15)
        draw_box(PLAYER_W, 20, PLAYER_D)
        glPopMatrix()
        glColor3f(0.7, 0.9, 1.0)
        glPushMatrix()
        glTranslatef(0, -10, 35)
        draw_box(PLAYER_W - 10, 20, PLAYER_D * 0.4)
        glPopMatrix()
        glColor3f(0.1, 0.3, 0.7)
        glPushMatrix()
        glTranslatef(0, -hd + 10, 40)
        draw_box(PLAYER_W, 5, 15)
        glPopMatrix()
        draw_wheel(-hw - 12, hd * 0.6, 10, 12)
        draw_wheel(hw, hd * 0.6, 10, 12)
        draw_wheel(-hw - 12, -hd * 0.6, 10, 12)
        draw_wheel(hw, -hd * 0.6, 10, 12)
    elif player_car_type == 1:
        glColor3f(0.9, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(0, 0, 15)
        draw_box(25, 18, PLAYER_D)
        glPopMatrix()
        glColor3f(0.9, 0.9, 0.9)
        glPushMatrix()
        glTranslatef(0, hd - 10, 12)
        draw_box(PLAYER_W + 10, 5, 20)
        glPopMatrix()
        glColor3f(0.9, 0.9, 0.9)
        glPushMatrix()
        glTranslatef(0, -hd + 10, 35)
        draw_box(PLAYER_W + 10, 5, 20)
        glPopMatrix()
        glColor3f(1.0, 1.0, 0.0)
        glPushMatrix()
        glTranslatef(0, -10, 30)
        gluSphere(gluNewQuadric(), 8, 10, 10)
        glPopMatrix()
        draw_wheel(-hw - 16, hd * 0.5, 12, 16)
        draw_wheel(hw, hd * 0.5, 12, 16)
        draw_wheel(-hw - 18, -hd * 0.6, 14, 18)
        draw_wheel(hw, -hd * 0.6, 14, 18)
    glPopMatrix()

def draw_npc(v):
    glPushMatrix()
    glTranslatef(v['x'], v['y'], 0)
    r, g, b = v['color']
    hw = v['w'] / 2
    hd = v['d'] / 2
    if v['w'] >= 80: 
        glColor3f(r, g, b)
        glPushMatrix()
        glTranslatef(0, 0, v['h']*0.3)
        draw_box(v['w'], v['h']*0.6, v['d'])
        glPopMatrix()  
        glColor3f(0.2, 0.2, 0.2)
        glPushMatrix()
        glTranslatef(0, -10, v['h']*0.7)
        draw_box(v['w']*0.8, v['h']*0.4, v['d']*0.5)
        glPopMatrix()
        glColor3f(1.0 - r*0.5, 1.0 - g*0.5, 1.0 - b*0.5)
        glPushMatrix()
        glTranslatef(0, hd - 10, v['h']*0.8)
        draw_box(v['w']*1.2, 8, 15)
        glPopMatrix()
    else:
        glColor3f(r, g, b)
        glPushMatrix()
        glTranslatef(0, 0, v['h']/2)
        draw_box(v['w'], v['h'], v['d'])
        glPopMatrix()
        glColor3f(r*0.7, g*0.7, b*0.7)
        glPushMatrix()
        glTranslatef(0, 10, v['h']+15)
        draw_box(v['w']*0.7, v['h']*0.6, v['d']*0.5)
        glPopMatrix()
        glColor3f(1.0, 1.0, 0.8)
        glPushMatrix()
        glTranslatef(-hw + 8, -hd, v['h'] * 0.4)
        draw_box(10, 8, 5)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(hw - 8, -hd, v['h'] * 0.4)
        draw_box(10, 8, 5)
        glPopMatrix()
    draw_wheel(-hw - 12, v['d']*0.3)
    draw_wheel(hw, v['d']*0.3)
    draw_wheel(-hw - 12, -v['d']*0.3)
    draw_wheel(hw, -v['d']*0.3)
    glPopMatrix()

def get_sky_color(is_night):
    return (0.05, 0.05, 0.15, 1.0) if is_night else (0.53, 0.81, 0.92, 1.0)

def get_env_color(is_night):
    return (0.06, 0.10, 0.06) if is_night else (0.15, 0.45, 0.2)

def get_road_color(is_night):
    return (0.10, 0.10, 0.10) if is_night else (0.22, 0.22, 0.22)

def get_lane_color(is_night):
    return (0.9, 0.9, 0.3) if is_night else (0.9, 0.85, 0.1)

def get_guardrail_color(is_night):
    return (0.4, 0.4, 0.4) if is_night else (0.7, 0.7, 0.7)

def get_mountain_color(index, is_night):
    if index == 1:
        return (0.02, 0.03, 0.02) if is_night else (0.1, 0.15, 0.1)
    elif index == 2:
        return (0.03, 0.04, 0.03) if is_night else (0.12, 0.18, 0.12)
    else:
        return (0.01, 0.02, 0.01) if is_night else (0.08, 0.12, 0.08)

def draw_mountains():
    glPushMatrix()
    glTranslatef(0, 4500, 0)
    glPushMatrix()
    glTranslatef(-800, 0, -50)
    glColor3f(*get_mountain_color(1, is_night_mode))
    gluCylinder(gluNewQuadric(), 600, 0, 1200, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(300, 200, -50)
    glColor3f(*get_mountain_color(2, is_night_mode))
    gluCylinder(gluNewQuadric(), 800, 0, 1500, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(1200, -100, -50)
    glColor3f(*get_mountain_color(3, is_night_mode))
    gluCylinder(gluNewQuadric(), 700, 0, 1000, 10, 10)
    glPopMatrix()
    glPopMatrix()

def draw_environment():
    glColor3f(*get_env_color(is_night_mode))
    glBegin(GL_QUADS)
    glVertex3f(-2000, -1000, -5)
    glVertex3f(2000, -1000, -5)
    glVertex3f(2000,  6000, -5)
    glVertex3f(-2000,  6000, -5)
    glEnd()

def draw_road():
    hw = ROAD_WIDTH / 2
    for off in road_offsets:
        y0, y1 = off, off + ROAD_SEG_LEN
        glColor3f(*get_road_color(is_night_mode))
        glBegin(GL_QUADS)
        glVertex3f(-hw, y0, 0)
        glVertex3f(hw, y0, 0)
        glVertex3f(hw, y1, 0)
        glVertex3f(-hw, y1, 0)
        glEnd()
        glColor3f(*get_lane_color(is_night_mode))
        y = y0
        while y < y1:
            for lx in [-60, 60]:
                glBegin(GL_QUADS)
                glVertex3f(lx - 4, y,      1)
                glVertex3f(lx + 4, y,      1)
                glVertex3f(lx + 4, y + 40, 1)
                glVertex3f(lx - 4, y + 40, 1)
                glEnd()
            y += 100

    glColor3f(*get_guardrail_color(is_night_mode))
    for rx in [-hw - 10, hw]:
        glBegin(GL_QUADS)
        glVertex3f(rx,      -400,  0)
        glVertex3f(rx + 10, -400,  0)
        glVertex3f(rx + 10, -400, 25)
        glVertex3f(rx,      -400, 25)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(rx, -400,  0)
        glVertex3f(rx,  3000,  0)
        glVertex3f(rx,  3000, 25)
        glVertex3f(rx, -400, 25)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(rx,      -400, 25)
        glVertex3f(rx + 10, -400, 25)
        glVertex3f(rx + 10,  3000, 25)
        glVertex3f(rx,       3000, 25)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(rx + 10, -400,  0)
        glVertex3f(rx + 10,  3000,  0)
        glVertex3f(rx + 10,  3000, 25)
        glVertex3f(rx + 10, -400, 25)
        glEnd()

def draw_hud():
    draw_text(20, 770, f"Score: {score:.1f}")
    draw_text(20, 745, f"Speed: x{speed_mult:.1f}")
    draw_text(20, 720, f"Best: {high_score:.1f}")
    draw_text(20, 695, f"Collision: {collision_count}/{MAx_collision}")
    draw_text(750, 770, "A/D : Move")
    draw_text(750, 750, "P   : Pause")
    draw_text(750, 730, "R   : Restart")
    draw_text(750, 710, "C   : Camera")
    draw_text(750, 690, "1/2 : Change Car")
    draw_text(750, 670, "N   : Day / Night")
    draw_text(750, 650, "Q   : Quit")
    if near_miss_display_timer > 0:
        draw_text(420, 550, "Near Miss!!! +Pts")
    if bonus_display_timer > 0:
        draw_text(420, 500, "Bonus!!! +50 points")
    if womp_womp_display_timer > 0:
        draw_text(400, 450, "Womp Womp... Collision!")
    if game_state == "paused":
        draw_text(450, 420, "PAUSED")
    if game_state == "gameover":
        draw_text(440, 430, "GAME OVER")
        draw_text(420, 400, f"Score: {score:.1f}")
        draw_text(420, 370, "Press R to restart")

def trigger_game_over():
    global game_state
    if game_state != "gameover":
        game_state = "gameover"
        save_high_score()

def update():
    global player_x, speed_mult, elapsed_time, frame_count
    global spawn_timer, SPAWN_INTERVAL, collision_count
    global explosion_progress, bonus_display_timer, near_miss_display_timer, womp_womp_display_timer, score
    if game_state == "exploding":
        explosion_progress += 1
        if explosion_progress > 150: 
            trigger_game_over()
        return
    
    if bonus_display_timer > 0: bonus_display_timer -= 1
    if near_miss_display_timer > 0: near_miss_display_timer -= 1
    if womp_womp_display_timer > 0: womp_womp_display_timer -= 1
    if game_state != "running":
        return
    
    frame_count += 1
    elapsed_time = frame_count / 60
    score += 1 / 60
    speed_mult = min(1 + elapsed_time / 35, MAX_MULT)
    current_speed = base_speed * speed_mult
    SPAWN_INTERVAL = max(80, int(220 / speed_mult))
    target = LANE_POSITIONS[player_lane]
    player_x += (target - player_x) * INTERP_SPEED
    update_road_segments(current_speed)
    survivors = []
    for v in traffic:
        v['y'] -= current_speed * v['speed_mult']
        if aabb_hit(player_x, 0, v['x'], v['y'], v['w'], v['d']):
            collision_count += 1
            if collision_count >= MAx_collision:
                trigger_explosion()
                return
            continue
        elif is_near_miss(player_x, 0, v['x'], v['y'], v['w'], v['d']):
            score += 0.8
            near_miss_display_timer = 120
        if v['y'] > DESPAWN_DIST:
            survivors.append(v)
    traffic[:] = survivors
    spawn_timer += 1
    if spawn_timer >= SPAWN_INTERVAL:
        spawn_vehicle()
        spawn_timer = 0
    if random.random() < 0.003:
        spawn_orb()
    surviving_orbs = []
    for o in orbs:
        o['y'] -= current_speed
        if aabb_hit(player_x, 0, o['x'], o['y'], o['radius']*2, o['radius']*2):
            handle_orb_collision(o)
        else:
            if o['y'] > DESPAWN_DIST:
                surviving_orbs.append(o)
    orbs[:] = surviving_orbs

def reset_game():
    global player_lane, player_x, traffic, road_offsets
    global speed_mult, elapsed_time, frame_count, spawn_timer
    global game_state, collision_count
    global orbs, particles, explosion_progress, near_miss_display_timer, bonus_display_timer, womp_womp_display_timer, score
    explosion_progress = 0
    near_miss_display_timer = 0
    bonus_display_timer = 0
    womp_womp_display_timer = 0
    score = 0.0
    orbs.clear()
    particles.clear()
    player_lane = 1
    player_x = 0
    traffic.clear()
    road_offsets = [(i - 2) * ROAD_SEG_LEN for i in range(NUM_SEGS)]
    speed_mult = 1
    elapsed_time = 0
    frame_count = 0
    spawn_timer = 0
    collision_count = 0
    game_state = "running"

def keyboardListener(key, x, y):
    global player_lane, game_state, camera_mode, player_car_type, collision_count
    if key == b'q':
        glutLeaveMainLoop()
    elif key == b'r':
        reset_game()
    elif key == b'p':
        game_state = "paused" if game_state == "running" else "running"
    elif key == b'c':
        camera_mode = 1 - camera_mode
    elif key == b'1':
        player_car_type = 0
    elif key == b'2':
        player_car_type = 1
    elif key == b'n':
        global is_night_mode
        is_night_mode = not is_night_mode
    elif game_state == "running":
        if key == b'a':
            if player_lane > 0:
                player_lane -= 1
            else:
                collision_count += 1
                if collision_count >= MAx_collision:
                    trigger_explosion()
        if key == b'd':
            if player_lane < 2:
                player_lane += 1
            else:
                collision_count += 1
                if collision_count >= MAx_collision:
                    trigger_explosion()

def idle():
    update()
    glutPostRedisplay()

def showScreen():
    glClearColor(*get_sky_color(is_night_mode))
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, WIN_W, WIN_H)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WIN_W/WIN_H, 1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if camera_mode == 0:
        gluLookAt(player_x, -350, 200,
                  player_x,  200,   0,
                  0, 0, 1)
    else:
        gluLookAt(0, 400, 1200,
                  0, 400, 0,
                  0, 1, 0)
    draw_environment()
    draw_mountains()
    draw_road()
    draw_orbs()
    draw_explosion()
    draw_player()
    for v in traffic:
        draw_npc(v)
    draw_hud()
    glutSwapBuffers()

def main():
    load_high_score()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Highway Rush")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()