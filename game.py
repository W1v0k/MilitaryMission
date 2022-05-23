import pygame, os, random, csv
from pygame import mixer

mixer.init()
pygame.init()

screen_width = 800
screen_height = int(screen_width * 0.8)

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Military Mission') # name of the game

#FRAMERATE

clock = pygame.time.Clock()
FPS = 60

#define game vars
GRAVITY = 0.75
SCROLL_THRESH = 200 # threshhold, when the player gets close, we need to scroll
LEFTCLICK = 1
RIGHTCLICK = 3
ROWS = 16
COLS = 150
TILE_SIZE = screen_height // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0

level = 1
start_game = False
start_intro = False

#Player action variables
left_move = False
right_move = False
shoot = False
grenade = False
grenade_thrown = False

#LOAD MUSIC + SOUNDS
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)# how much should it loop(-1 represents infinity), delay, duration of fade

jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.5)

shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.5)

grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.5)

#LOAD IMAGES
#button image
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
#background

#load background
pine1_img = pygame.image.load('img/background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/background/sky_cloud.png').convert_alpha()

#store tiles in a list

img_list = []
for x in range(TILE_TYPES): #because we have a lot of different types, we don't want to upload them individually, so we will use an iteration
    img = pygame.image.load(f'img/tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

#bullet
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()

#grenade
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()

#pickUp boxes
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()

#dictionary
item_boxes = {
    'Health'    : health_box_img,
    'Ammo'      : ammo_box_img,
    'Grenade'   : grenade_box_img
}

BG = (144,201,120)
RED = (255, 0, 0)
PINK = (235, 65, 54)
WHITE = (255,255,255)
GREEN = (29,33,13)
LIME = (0,255,0)
BLACK = (0,0,0)

#define font
#font = pygame.font.SysFont('Futura', 30)
game_font = pygame.font.Font('font/BlackOpsOne-Regular.ttf', 30)

def draw_text(text, font, text_color, x, y):
    img = font.render(text, True, text_color)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width() # the shortest image
    for x in range(5):
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.25,0))
        screen.blit(mountain_img,((x * width) - bg_scroll * 0.5, screen_height - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - bg_scroll * 0.75, screen_height - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - bg_scroll * 1, screen_height - pine2_img.get_height()))

#function to reset the level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    deco_group.empty()
    water_group.empty()
    exit_group.empty()

    #create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    return data

#PLAYER

class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type,xPlayer, yPlayer, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenade = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1 # 1-is looking to the right
        self.jump = False # stationary state
        self.in_air = True
        self.vel_y = False # y velocity
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0 # IDLE 
        self.update_time = pygame.time.get_ticks()
        
        #ai specific vars
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20) # 150 - how far the enemies can see
        self.idling = False
        self.idling_counter = 0

        #load all iamges for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            #reset temporary list of images
            temp_list = []
            #count number of files in the folder
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                imgPlayer = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                imgPlayer = pygame.transform.scale(imgPlayer, (int(imgPlayer.get_width() * scale), int(imgPlayer.get_height() * scale)))
                temp_list.append(imgPlayer)
            self.animation_list.append(temp_list) #List of lists
            
        self.image = self.animation_list[self.action][self.frame_index]

        self.rect = self.image.get_rect()
        self.rect.center = (xPlayer, yPlayer)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        #update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        screen_scroll = 0
        dx = 0
        dy = 0

        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1 # moving left
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1 # moving right
        if self.jump == True and self.in_air == False:
            self.vel_y = -11
            self.jump = False
            self.in_air = True
        #we need gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y
        
        #check for collision
        for tile in world.obstacle_list: # tile = (image, image_rect)
            #check collision in x axis
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #if the ai has hit a wall, then make it turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            #check collision in y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if below the ground, i.e. jumping (i.e. = id est in latin = that is)
                if self.vel_y < 0: # it's moving up
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top # the bottom of a tile and his head
                #check if above the ground, i.e. falling
                elif self.vel_y >= 0: #it's moving down
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom # the top of a tile and his feet
        
        #check for collision with water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0
        
        #check for collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        #check if fallen off the map
        if self.rect.bottom > screen_height:
            self.health = 0

        #check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > screen_width:
                dx = 0

        #update rectangle pos
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on player pos
        if self.char_type == 'player': # so enemies can't scroll the bg
            if (self.rect.right > screen_width - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - screen_width)\
                 or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
        return screen_scroll, level_complete    


    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.75 * self.direction * self.rect.size[0]), self.rect.centery, self.direction)
            bullet_group.add(bullet)
            #reduce ammo
            self.ammo -= 1
            shot_fx.play()

    def AI(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1: #we don't want them idling forever, it's a possibility that the counter doesn't get fully to 0 and it gets reseted
                self.update_action(0)#0: idle
                self.idling = True
                self.idling_counter = 75
            #check if the AI is near the player
            if self.vision.colliderect(player.rect):
                #stop running and face the player
                self.update_action(0)#0: idle
                #shoot
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1: #facing Right
                        AI_moving_right = True
                    else:
                        AI_moving_right = False
                    AI_moving_left = not AI_moving_right
                    self.move(AI_moving_left,AI_moving_right)
                    self.update_action(1) #1: run
                    self.move_counter += 1
                    #update AI vision as the enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1 #we want it to patrol, not to spawn in that place again
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        #scroll
        self.rect.x += screen_scroll

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        #update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]

        #check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #reset the animation after it finished
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        #check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            #update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        #HACK :pygame.draw.rect(screen, RED, self.rect,3)
enemy_group = pygame.sprite.Group()

class World():
    def __init__(self):
        self.obstacle_list =[] # for collision with dirt, the ground

    def process_data(self, data):
        self.level_length = len(data[0]) # we choose a row and count the overall tiles
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        water = Water(img, x*TILE_SIZE, y*TILE_SIZE) #decorations, rocks, grass, pick-up boxes
                        water_group.add(water) # water
                    elif tile >= 11 and tile <= 14:
                        deco = Decors(img, x*TILE_SIZE, y*TILE_SIZE) #decorations, rocks, grass, pick-up boxes
                        deco_group.add(deco)
                    elif tile == 15: # create player
                        player = Soldier('player', x* TILE_SIZE, y* TILE_SIZE,1.65,5,20,5)
                        health_bar = HealthBar(150, 13, player.health, player.health)
                    elif tile == 16: # create enemy
                        enemy = Soldier('enemy', x* TILE_SIZE, y*TILE_SIZE,1.65,2,20,0)                     
                        enemy_group.add(enemy)
                    elif tile == 17: #create ammo box
                        item_box = ItemBox('Ammo', x* TILE_SIZE, y* TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18: #create grenade box
                        item_box = ItemBox('Grenade', x* TILE_SIZE, y* TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19: #create ammo box
                        item_box = ItemBox('Health', x* TILE_SIZE, y* TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20: #create exit
                        exit = Exit(img, x*TILE_SIZE, y*TILE_SIZE) #decorations, rocks, grass, pick-up boxes
                        exit_group.add(exit)
        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0]  += screen_scroll# the x coord
            screen.blit(tile[0], tile[1]) # the tile and the rect               

class Decors(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
        
    def update(self):
        self.rect.x += screen_scroll

deco_group = pygame.sprite.Group()

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll
water_group = pygame.sprite.Group()

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll
exit_group = pygame.sprite.Group()

class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + int(TILE_SIZE - self.image.get_height())) # // - floor division for getting an int
    
    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #check if the player has picked up the box
        if pygame.sprite.collide_rect(self, player):
            #check what kind of box it was
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenade += 3
            #delete the item box
            self.kill() # delete that instance

item_box_group = pygame.sprite.Group()

class HealthBar():
    def __init__(self, x, y , health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health
    
    def draw(self, health):
        #update with new health
        self.health = health

        #calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154,24)) # border
        pygame.draw.rect(screen, RED, (self.x, self.y, 150,20))
        pygame.draw.rect(screen, LIME, (self.x,self.y, 150 * ratio, 20))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        #check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > screen_width:
            self.kill()

        #check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        #check collision with characters
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()
#create sprite groups
bullet_group = pygame.sprite.Group()

class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()    
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y
        
        #check for collision with level
        for tile in world.obstacle_list:
            #check collision with walls
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            #check collision in y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                # check if below the ground, i.e. thrown up; moving up
                if self.vel_y < 0: 
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above the ground, i.e. falling
                elif self.vel_y >= 0: 
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom # the top of a tile and his feet   
        
        #update grenade pos
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        #countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 1)
            explosion_group.add(explosion)
            #do damage to anyone nearby
            dmg_taken_player = False
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2  and\
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2 and\
                    dmg_taken_player == False :
                player.health = 0 # the player is very close to the explosion so he dies
                dmg_taken_player = True
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 3 and\
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 3 and\
                    dmg_taken_player == False:
                player.health -= 50
                dmg_taken_player = True
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 4 and\
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 4 and\
                    dmg_taken_player == False:
                player.health -= 25 # the futher away the player is, ge takes less damage
                dmg_taken_player = True
            dmg_taken_player = False

            for enemy in enemy_group:
                dmg_taken_enemy = False
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2  and\
                abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2 and\
                    dmg_taken_enemy == False :
                    enemy.health = 0 
                    dmg_taken_enemy = True
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 3 and\
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 3 and\
                        dmg_taken_enemy == False:
                    enemy.health -= 50
                    dmg_taken_enemy = True
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 4 and\
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 4 and\
                        dmg_taken_enemy == False:
                    enemy.health -= 25 # the futher away the player is, ge takes less damage
                    dmg_taken_enemy = True
                dmg_taken_enemy = False


grenade_group = pygame.sprite.Group()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1,6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0    

    def update(self):
        #scroll
        self.rect.x += screen_scroll

        EXPLOSION_SPEED = 4
        #update explosion animation
        self.counter += 1

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            #if the animation is complete then delete the explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

explosion_group = pygame.sprite.Group()

class Button():
    def __init__(self,x,y,image,scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width* scale), int(height* scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False
    
    def draw(self, surface):
        action = False

        #get mouse pos
        pos = pygame.mouse.get_pos()

        #check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
        
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        #draw button
        surface.blit(self.image, (self.rect.x, self.rect.y))

        return action
#create buttons
start_button = Button(screen_width // 2 - 130, screen_height // 2 - 150, start_img, 1)
exit_button = Button(screen_width // 2 - 110, screen_height // 2 + 50, exit_img, 1)
restart_button = Button(screen_width // 2 - 100, screen_height // 2 - 50, restart_img, 2)

class ScreenFade():
    def __init__(self, direction, color, speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False # so it doesn't go forever
        self.fade_counter += self.speed
        if self.direction == 1: #whole screen fade
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter,0, screen_width//2,screen_height))
            pygame.draw.rect(screen, self.color, (screen_width // 2 + self.fade_counter,0,screen_width,screen_height))
            pygame.draw.rect(screen, self.color,(0,0-self.fade_counter,screen_width,screen_height//2))
            pygame.draw.rect(screen,self.color,(0,screen_height//2 + self.fade_counter, screen_width,screen_height))
        if self.direction == 2: #vertical screen fade down
            pygame.draw.rect(screen, self.color, (0, 0, screen_width, 0 + self.fade_counter))
        if self.fade_counter >= screen_width:
            fade_complete = True
        
        return fade_complete
#create screen fades
death_fade = ScreenFade(2, PINK, 4)
intro_fade = ScreenFade(1, BLACK, 4)

#create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile: #open a file as a csvfile and read from it with the help of a reader
    reader = csv.reader(csvfile, delimiter=',')
    for x,row in enumerate(reader):
        for y,tile in enumerate(row):
            world_data[x][y] = int(tile) # int because as we read from the csvfile we get back strings, not integers

world = World()
player, health_bar = world.process_data(world_data)

runGame = True
while runGame:
    clock.tick(FPS)

    if start_game == False:
        #draw menu
        screen.fill(BG)
        #add buttons
        if start_button.draw(screen): #if clicked
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            runGame = False
    else:
        #update background
        draw_bg()
        
        #draw world map
        world.draw()

        #show health
        draw_text('HEALTH: ', game_font, RED, 10, 5)
        health_bar.draw(player.health)

        #show ammo
        draw_text('AMMO: ', game_font, WHITE, 10, 30)
        for x in range(player.ammo):
            screen.blit(bullet_img, (120 + (x * 10), 45))
        #show grenades
        draw_text('GRENADES: ', game_font, GREEN, 10, 55)
        for x in range(player.grenade):
            screen.blit(grenade_img, (200 + (x * 15), 65))
        

        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.AI()
            enemy.update()
            enemy.draw()

        #update and draw groups
        bullet_group.update()
        bullet_group.draw(screen)

        grenade_group.update()
        grenade_group.draw(screen)

        explosion_group.update()
        explosion_group.draw(screen)

        item_box_group.update()
        item_box_group.draw(screen)

        deco_group.update()
        deco_group.draw(screen)

        water_group.update()
        water_group.draw(screen)

        exit_group.update()
        exit_group.draw(screen)

        #show intro
        if start_intro == True:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0
        
        #update player actions        
        if player.alive:
            #shoot bullet
            if shoot:
                player.shoot()

            #throw grenades
            elif grenade and grenade_thrown == False and player.grenade > 0:
                grenade = Grenade(player.rect.centerx + (player.rect.size[0] * 0.5 * player.direction), \
                                player.rect.top,player.direction) # \ used for going down a line on the same line of code
                grenade_group.add(grenade)
                player.grenade -= 1
                grenade_thrown = True
                
            #update player actions
            if player.in_air:
                player.update_action(2)#2:jump     
            elif left_move or right_move:
                player.update_action(1) #1: run
            else:
                player.update_action(0) #0: idle
            
            screen_scroll, level_complete = player.move(left_move, right_move)
            bg_scroll -= screen_scroll
            #check if player has completed the level
            if level_complete:
                start_intro = True
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x,row in enumerate(reader):
                            for y,tile in enumerate(row):
                                world_data[x][y] = int(tile) 
                    world = World()
                    player, health_bar = world.process_data(world_data)
        else: # the player is DEAD
            screen_scroll = 0
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0 # total ammount of how much the player scrolled
                    world_data = reset_level()
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x,row in enumerate(reader):
                            for y,tile in enumerate(row):
                                world_data[x][y] = int(tile) 
                    world = World()
                    player, health_bar = world.process_data(world_data)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runGame = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                left_move = True
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                right_move = True
            if event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP and player.alive:
                player.jump = True
                jump_fx.play()
            if event.key == pygame.K_ESCAPE:
                runGame = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFTCLICK:
            shoot = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == LEFTCLICK:
            shoot = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == RIGHTCLICK:
            grenade = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == RIGHTCLICK:
            grenade = False
            grenade_thrown = False
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                left_move = False
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                right_move = False 

    pygame.display.update()
pygame.quit()