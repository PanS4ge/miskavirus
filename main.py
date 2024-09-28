import pygame
import win32api
import win32con
import win32gui
import os
import time
import random
import math
import ctypes
from PIL import Image
from shapely.geometry import box
from shapely.ops import unary_union
import requests
import tempfile

# Pobierz rozmiar ekranu
screen_width = win32api.GetSystemMetrics(0)
screen_height = win32api.GetSystemMetrics(1)

# Ustaw rozmiar okna na rozmiar ekranu
width = screen_width
height = screen_height

SQUARE = 128

segments = []

pygame.init()
window_screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
hwnd = pygame.display.get_wm_info()["window"]

# Ustawienie okna jako "zawsze na wierzchu"
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, width, height, 0)

# Ustawienie przezroczystości okna
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(
                       hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(255, 0, 128), 0, win32con.LWA_COLORKEY)

alltime = 0

# TUTAJ POBIERANIE PLICZKÓW, JESZCZE SERWER MUSZE POSTAWIĆ
def download(file):
    with open(os.path.join(tempfile.gettempdir(), file), "wb") as filew:
        r = requests.get("https://assets.pansage.xyz/download/jasper/" + file)
        filew.write(r.content)
        filew.close()

download("miska.png")
download("egzorcyzm.png")
download("pabianice.mp3")
download("tata.mp3")

# Klasa reprezentująca ruchomy obrazek
class MovingImage:
    def __init__(self, image_path, start_pos = None, speed = None):
        self.image = pygame.image.load(image_path).convert_alpha()
        if(start_pos == None):
            self.x, self.y = (random.randint(0, screen_width), random.randint(0, screen_height))
        else:
            self.x, self.y = start_pos
        if(speed == None):
            self.dx, self.dy = (random.randint(15, 30), random.randint(15, 30))
        else:
            self.dx, self.dy = speed
        self.width, self.height = (255, 255)
    
    def update_position(self):
        global alltime
        # Aktualizuj pozycję obiektu
        self.x += self.dx
        self.y += self.dy

        # Sprawdź kolizje z krawędziami ekranu i odbij się
        if self.x <= -1 * self.width or self.x >= screen_width:
            self.dx = -self.dx
        if self.y <= -1 * self.height or self.y >= screen_height:
            self.dy = -self.dy

        # Nowy segment jako prostokąt
        new_segment = box(self.x + 8, self.y + 64, self.x + 8 + SQUARE, self.y + 150 + SQUARE)

        # Aktualizuj listę segmentów, usuwając te, które są całkowicie pokryte
        global segments
        updated_segments = []
        for segment in segments:
            # Sprawdź różnicę (czyli część segmentu, która nie jest pokryta)
            difference = segment.difference(new_segment)
            if not difference.is_empty:
                updated_segments.append(difference)

        updated_segments.append(new_segment)
        alltime = alltime + 1

        segments = updated_segments
        if segments:
            total_area = unary_union(segments).area
        else:
            total_area = 0
        screen_area = screen_width * screen_height
        occupied_percentage = (total_area / screen_area) * 100

        if(len(updated_segments) >= 1000):
            updated_segments.pop(0)

    def draw(self, surface : pygame.Surface):
        surface.blit(self.image, (self.x, self.y))

# Tworzenie listy obiektów MovingImage
images = [
    MovingImage(os.path.join(tempfile.gettempdir(), "miska.png"))
]

done = False
started = time.time()

EGZORCYZM = os.path.join(tempfile.gettempdir(), "egzorcyzm_prepped.png")

i = Image.open(EGZORCYZM.replace("_prepped", ""))
i = i.resize((screen_width, screen_height))
i.save(EGZORCYZM)

wlaczonoostateczne = False
kiedyostateczne = time.time() + 2700     

pygame.mixer.init()
pygame.mixer.music.load(os.path.join(tempfile.gettempdir(), "pabianice.mp3"))
pygame.mixer.music.set_volume(2)
pygame.mixer.music.play(loops=10**5)
while not done:   
    for event in pygame.event.get():    
        if event.type == pygame.QUIT:   
            done = True               
        if event.type == pygame.KEYDOWN:    
            if event.key == pygame.K_ESCAPE:  
                done = True
        if event.type == pygame.KEYDOWN:    
            if event.key == pygame.K_SPACE:
                alltime = 100000000000000000

    # Wypełnij okno kolorem przezroczystości
    window_screen.fill((255, 0, 128))  

    image = pygame.image.load(EGZORCYZM).convert_alpha()

    for loc in segments:
        xmin, ymin, xmax, ymax = loc.bounds
        window_screen.blit(image, (xmin, ymin), (xmin, ymin, SQUARE, SQUARE))

    # Aktualizuj pozycje i narysuj wszystkie obrazy
    for img in images:
        img.update_position()
        img.draw(window_screen)

    if(started != -1):
        if(time.time() - started >= 10):
            images.append(MovingImage(os.path.join(tempfile.gettempdir(), "miska.png")))
            started = time.time()

        pygame.font.init()
        font = pygame.font.SysFont('Comic Sans MS', 120)
        m = math.floor(10 - (time.time() - started))
        o = math.floor(time.time() - started)
        s = o if o != 0 else 1
        text_surface = font.render(str(m), False, (255, math.floor(255 / s), math.floor(255 / s)))
        window_screen.blit(text_surface, (0,0))

    if(alltime >= 10**3):
        started = -1
        for i in range(len(images)):
            try:
                t = images[i]
                t.dx = 0
                t.dy = 30
            except:
                pass
        if(t.dy <= 0):
            images.pop(i)
        if(not wlaczonoostateczne):
            for c in range(1, screen_height):
                window_screen.blit(image, (0, 0), (0, 0, screen_width, c))
                pygame.display.update()
                time.sleep(0.01)
        else:
            window_screen.blit(image, (0, 0), (0, 0, screen_width, screen_height))
        if(not wlaczonoostateczne):
            pygame.mixer.music.load(os.path.join(tempfile.gettempdir(), "tata.mp3"))
            pygame.mixer.music.set_volume(8)
            pygame.mixer.music.play(loops=1)
            wlaczonoostateczne = True
            kiedyostateczne = time.time()
        if(time.time() - kiedyostateczne >= 7):
            SPI_SETDESKWALLPAPER = 20 
            ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, EGZORCYZM, 0)
            done = True

    pygame.display.update()

    # Dodaj opóźnienie, aby ruch był widoczny
    time.sleep(0.01)
