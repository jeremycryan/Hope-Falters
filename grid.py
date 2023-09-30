from image_manager import ImageManager
from pyracy.sprite_tools import Sprite, Animation
import pygame
import constants as c
from word_manager import WordManager
import math, time

class Grid:
    pass

    def __init__(self, path, frame):
        self.victory_tile = None
        self.grabbed_tile = None
        self.grab_position = None
        self.drag_direction = None
        self.grabbed_shape = None
        self.title = ""
        self.width, self.height = self.load_from_file(f"levels/{path}")

        self.won = False
        self.victory_objects = []
        self.since_won = 0
        self.frame = frame
        self.win_shake_occurred = False

        self.title_letters = [GridObject.FONT_DICT[char] for char in self.title]



    def load_from_file(self, path):
        with open(path) as f:
            self.title = f.readline().strip()
            lines = [line.strip() for line in f.readlines()]
        width = len(lines[0])
        height = len(lines)

        self.tiles = [[GridObject(character, self) if character != "." else None for character in line] for line in lines]

        self.calculate_victory_tile()
        return width, height

    def draw_perimeter(self, surface, offset=(0, 0)):
        effective_width = self.width + 1 + c.WALL_INSET_TILES*2
        effective_height = self.height + 1 + c.WALL_INSET_TILES*2
        corners = [
            (c.CENTER_X + offset[0] - c.TILE_SIZE * (effective_width - 1) // 2,
             c.CENTER_Y + offset[1] - c.TILE_SIZE * (effective_height - 1) // 2),
            (c.CENTER_X + offset[0]- c.TILE_SIZE * (effective_width - 1) // 2,
             c.CENTER_Y + offset[1]+ c.TILE_SIZE * (effective_height - 1) // 2),
            (c.CENTER_X + offset[0]+ c.TILE_SIZE * (effective_width - 1) // 2,
             c.CENTER_Y + offset[1]+ c.TILE_SIZE * (effective_height - 1) // 2),
            (c.CENTER_X + offset[0]+ c.TILE_SIZE * (effective_width - 1) // 2,
             c.CENTER_Y + offset[1]- c.TILE_SIZE * (effective_height - 1) // 2),
        ]
        pygame.draw.polygon(surface, c.WHITE, corners, 1)

    def calculate_victory_tile(self):
        for grid_object, x, y in self.all_grid_objects_and_position():
            if grid_object.character == c.VICTORY_CHAR:
                self.victory_tile = x, y
                self.tiles[y][x] = None

    def draw(self, surface, offset=(0, 0)):
        title_width = sum([char.get_width() for char in self.title_letters])

        self.draw_perimeter(surface, offset)

        x = c.CENTER_X - c.TILE_SIZE*(self.width - 1)//2 + offset[0]
        y = c.CENTER_Y - c.TILE_SIZE*(self.height - 1)//2 + offset[1]
        x0=x
        y0=y
        for ty, row in enumerate(self.tiles):
            x = x0
            for tx, tile in enumerate(row):
                if (tx, ty) == self.victory_tile:
                    color = (50, 80, 110)
                else:
                    color = (20, 20, 20)
                if tile is not None and tile.is_wall():
                    wip = c.WALL_INSET_TILES*c.TILE_SIZE
                    pygame.draw.rect(surface, c.WHITE, (x-c.TILE_SIZE//2+wip, y-c.TILE_SIZE//2+wip, c.TILE_SIZE//1-2*wip, c.TILE_SIZE//1 -2*wip), 1)
                else:
                    wip = 0
                    pygame.draw.rect(surface, color, (x-c.TILE_SIZE//2+wip, y-c.TILE_SIZE//2+wip, c.TILE_SIZE//1-2*wip, c.TILE_SIZE//1 -2*wip))
                    wip = 2
                    pygame.draw.rect(surface, c.BLACK, (x-c.TILE_SIZE//2+wip, y-c.TILE_SIZE//2+wip, c.TILE_SIZE//1-2*wip, c.TILE_SIZE//1 -2*wip))
                x += c.TILE_SIZE
            y += c.TILE_SIZE

        y = y0
        for row in self.tiles:
            x = x0
            for grid_object in row:
                if grid_object is not None:
                    grid_object.set_target_position_on_grid(x - offset[0], y - offset[1])
                    grid_object.draw(surface, offset)
                x += c.TILE_SIZE
            y += c.TILE_SIZE

    def all_grid_objects(self):
        for grop in self.all_grid_objects_and_position():
            yield grop[0]

    def all_grid_objects_and_position(self):
        for y, row in enumerate(self.tiles):
            for x, grid_object in enumerate(row):
                if grid_object is None:
                    continue
                yield grid_object, x, y

    def update_hopeness(self):
        for obj in self.all_grid_objects():
            obj.part_of_hope = False
        for obj, x, y in self.all_grid_objects_and_position():
            if obj.character !="H":
                continue
            for direction in [c.UP, c.DOWN, c.LEFT, c.RIGHT]:
                new_position = x, y
                good_tiles = [obj]
                for expected in "OPE":
                    new_position = new_position[0] + direction[0], new_position[1] + direction[1]
                    if not self.in_bounds(*new_position):
                        good_tiles=[]
                        break
                    new_tile = self.tiles[new_position[1]][new_position[0]]
                    if not new_tile:
                        good_tiles=[]
                        break
                    if not new_tile.character==expected:
                        good_tiles=[]
                        break
                    good_tiles.append(new_tile)
                if good_tiles:
                    for obj in good_tiles:
                        obj.part_of_hope=True

    def update(self, dt, events):
        if self.won:
            self.since_won += dt
        if not self.win_shake_occurred and self.won and self.since_won>0.15:
            self.frame.shake(12)
            self.win_shake_occurred = True
        for grid_object in self.all_grid_objects():
            grid_object.update(dt, events)
        mpos = pygame.mouse.get_pos()
        self.update_hovered_statuses(mpos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button!=1:
                    continue
                if self.hovered_object(mpos):
                    self.grab()
            if event.type == pygame.MOUSEBUTTONUP:
                if self.grabbed_tile:
                    self.release()

        self.update_dragging()
        self.check_victory()
        self.update_hopeness()



    def screen_to_tile(self, ppos):
        x0 = c.CENTER_X - c.TILE_SIZE*(self.width)//2
        y0 = c.CENTER_Y - c.TILE_SIZE*(self.height)//2

        xoff = ppos[0] - x0
        yoff = ppos[1] - y0
        return xoff/c.TILE_SIZE, yoff/c.TILE_SIZE

    def hovered_tile(self, mpos):
        tx, ty = self.screen_to_tile(mpos)
        tx = int(tx)
        ty = int(ty)
        return tx, ty

    def hovered_object(self, mpos):
        tx, ty = self.hovered_tile(mpos)
        if tx < 0 or tx > self.width - 1:
            return None
        elif ty < 0 or ty > self.height - 1:
            return None
        return self.tiles[ty][tx]

    def update_hovered_statuses(self, mpos):
        hovered = self.hovered_object(mpos)
        for grid_object, x, y in self.all_grid_objects_and_position():
            if grid_object is None:
                continue
            if self.grabbed_shape and (x, y) in self.grabbed_shape:
                #grid_object.hovered = True
                grid_object.grabbed = True
            elif self.grabbed_tile and (x, y) == self.grabbed_tile:
                grid_object.hovered = True
            elif not self.grabbed_tile and grid_object is hovered:
                grid_object.hovered = True
            else:
                grid_object.hovered = False
                self.grabbed = False

    def check_victory(self):
        if self.won:
            return

        victory_word = "HOPE"
        x = self.victory_tile[0]
        y = self.victory_tile[1]

        while victory_word:
            if not self.in_bounds(x, y):
                return  # Not sure how this would happen
            if self.tiles[y][x] is None:
                return
            if self.tiles[y][x].character != victory_word[-1]:
                return
            victory_word=victory_word[:-1]
            x -= 1

        self.win()
        return

    def win(self):
        self.since_won = 0
        self.won = True
        grabbed_objects = [self.tiles[y][x] for x, y in self.grabbed_shape if self.in_bounds(x, y)]
        grabbed_objects.sort(key=lambda tile: -tile.x)
        self.victory_objects = grabbed_objects[:4]
        self.release()

        print("YAY!")

    def ready_for_next(self):
        return self.won and self.since_won > 2


    def grab(self):
        if self.won:
            return
        mpos = pygame.mouse.get_pos()
        self.regrab(mpos)
        self.grabbed_objects = []
        self.grabbed_shape = None

    def regrab(self, mpos):
        self.grabbed_tile = self.hovered_tile(mpos)
        self.grab_position = mpos

    def release(self):
        self.grabbed_tile = None
        self.grab_position = None
        self.drag_direction = None

        if self.grabbed_shape:
            for pos in self.grabbed_shape:
                if self.in_bounds(*pos):
                    tile = self.tiles[pos[1]][pos[0]]
                    if tile:
                        tile.grabbed = False
            self.grabbed_shape = None

    def in_bounds(self, tx, ty):
        return tx >= 0 and ty >= 0 and tx < self.width and ty < self.height

    def move_tile_contents(self, grabbed_shape, direction):
        if direction == c.UP:
            inc_vec = (0, -1)
        elif direction == c.DOWN:
            inc_vec = (0, 1)
        elif direction == c.LEFT:
            inc_vec = (-1, 0)
        elif direction == c.RIGHT:
            inc_vec = (1, 0)
        else:
            raise

        grabbed_shape = list(grabbed_shape)
        adjusted = []
        for pos in grabbed_shape:
            adjusted.append((pos[0] + inc_vec[0], pos[1] + inc_vec[1]))


        reverse = direction in (c.RIGHT, c.DOWN)
        grabbed_shape.sort(key=lambda x: x[0] + x[1],reverse=reverse)


        for pos in grabbed_shape:
            self.tiles[pos[1] + inc_vec[1]][pos[0] + inc_vec[0]] = self.tiles[pos[1]][pos[0]]
        self.tiles[grabbed_shape[-1][1]][grabbed_shape[-1][0]] = None
        return adjusted



    def update_dragging(self):
        mpos = list(pygame.mouse.get_pos())
        if self.grabbed_tile:

            test_positions = [(mpos[0], self.grab_position[1]), (self.grab_position[0], mpos[1])]


            if self.drag_direction is not None and self.drag_direction == c.HORIZONTAL:
                test_positions.pop(1)
            elif self.drag_direction is not None and self.drag_direction == c.VERTICAL:
                test_positions.pop(0)

            for mpos in test_positions:
                tx, ty = self.hovered_tile(mpos)
                old = self.hovered_tile(self.grab_position)
                if (tx > old[0] + 1):
                    tx = old[0] + 1
                    mpos = self.grab_position[0] + c.TILE_SIZE, mpos[1]
                if (ty > old[1] + 1):
                    ty = old[1] + 1
                    mpos = mpos[0], self.grab_position[1] + c.TILE_SIZE
                if tx < old[0] - 1:
                    tx = old[0] - 1
                    mpos = self.grab_position[0] - c.TILE_SIZE, mpos[1]
                if ty < old[1] - 1:
                    ty = old[1] - 1
                    mpos = mpos[0], self.grab_position[1] - c.TILE_SIZE

                if tx > old[0]:
                    direction = c.RIGHT
                elif tx < old[0]:
                    direction = c.LEFT
                elif ty > old[1]:
                    direction = c.DOWN
                else:
                    direction = c.UP

                grabbed_shape = self.grabbed_shape if self.grabbed_shape else self.calculate_grabbed_objects(direction, old)
                if not grabbed_shape:
                    continue
                obstruction = self.calculate_obstruction(grabbed_shape, direction)
                if not obstruction and self.in_bounds(tx, ty) and abs(tx - old[0]) + abs(ty - old[1]) == 1:
                    self.grabbed_shape = self.move_tile_contents(grabbed_shape, direction)
                    self.regrab(mpos)
                    self.drag_direction = c.VERTICAL if old[0] == tx else c.HORIZONTAL

                    break

    def calculate_obstruction(self, tile_list, direction):
        if direction == c.UP:
            inc_vec = (0, -1)
        elif direction == c.DOWN:
            inc_vec = (0, 1)
        elif direction == c.LEFT:
            inc_vec = (-1, 0)
        elif direction == c.RIGHT:
            inc_vec = (1, 0)
        else:
            raise

        for tile in tile_list:
            new_position = tile[0] + inc_vec[0], tile[1] + inc_vec[1]
            if new_position in tile_list:
                continue
            if not self.in_bounds(*new_position):
                return True
            if self.tiles[new_position[1]][new_position[0]] is not None:
                return True
        return False


    def calculate_grabbed_objects(self, direction, start_tile):
        tx, ty = start_tile
        tiles = []

        if direction == c.UP:
            inc_vec = (0, -1)
        elif direction == c.DOWN:
            inc_vec = (0, 1)
        elif direction == c.LEFT:
            inc_vec = (-1, 0)
        elif direction == c.RIGHT:
            inc_vec = (1, 0)
        else:
            raise

        if self.tiles[ty][tx] is None:
            return None
        tiles.append((tx, ty))
        word = self.tiles[ty][tx].character
        final_tile = tx, ty
        while True:
            test_tile = final_tile[0] + inc_vec[0], final_tile[1] + inc_vec[1]
            if not self.in_bounds(*test_tile):
                break
            grid_object = self.tiles[test_tile[1]][test_tile[0]]
            if grid_object is None:
                break
            final_tile = test_tile
            word += grid_object.character
            tiles.append(final_tile)

        start_tile = tx, ty
        while not WordManager.contains(self.process_word_for_direction(word, direction)):
            test_tile = start_tile[0] - inc_vec[0],start_tile[1] - inc_vec[1]
            if not self.in_bounds(*test_tile):
                break
            grid_object = self.tiles[test_tile[1]][test_tile[0]]
            if grid_object is None:
                break
            start_tile = test_tile
            word = grid_object.character + word
            tiles.append(start_tile)

        if not WordManager.contains(self.process_word_for_direction(word, direction)):
            return None

        return tiles

    def process_word_for_direction(self, word, direction):
        if direction in (c.LEFT, c.UP):
            word = word[::-1]
        return word







class GridObject:
    FONT=None
    FONT_DICT={}
    HOVER_FONT_DICT = {}
    HOPE_FONT_DICT = {}
    MAX_BUZZ = 1.5

    def __init__(self, character, grid):
        self.grid = grid
        if not GridObject.FONT:
            GridObject.FONT=pygame.font.Font("assets/fonts/Rudiment.ttf",40)
        if not GridObject.FONT_DICT:
            GridObject.FONT_DICT = {char: self.FONT.render(char,True,(150, 150, 200)) for char in c.CHARS}
        if not GridObject.HOVER_FONT_DICT:
            GridObject.HOVER_FONT_DICT = {char: self.FONT.render(char, True, c.YELLOW) for char in c.CHARS}
        if not GridObject.HOPE_FONT_DICT:
            GridObject.HOPE_FONT_DICT = {char: self.FONT.render(char, True, c.WHITE) for char in c.CHARS}

        self.character = character
        self.surf = self.FONT_DICT[character].copy()
        self.hover_surf = self.HOVER_FONT_DICT[character].copy()
        self.hope_surf = self.HOPE_FONT_DICT[character].copy()
        self.grabbed = False
        self.hovered = False

        self.x_off = 0  # in grid tiles
        self.y_off = 0
        self.part_of_hope = False

        self.x = None
        self.y = None
        self.target_x = None
        self.target_y = None

        self.age = 0

        self.buzz_amplitude = 0

        self.glows = {}
        for char in "HOPE":
            surf = ImageManager.load(f"assets/images/{char.lower()}_glow.png")
            surf = pygame.transform.scale(surf, (surf.get_width()*0.35, surf.get_height()*0.35))
            self.glows[char] = surf

    def draw(self, surface, offset=(0, 0)):
        if self.character == c.WALL_CHAR:
            return

        if self.x == None:
            self.x = offset[0]
            self.target_x = self.x
        if self.y == None:
            self.y = offset[1]
            self.target_y = self.y


        if self.grid.won and self.grid.since_won > 2 and self in self.grid.victory_objects:
            return

        boff_x = math.sin(time.time()*24+self.x*0.015+self.y*0.01)*self.buzz_amplitude
        boff_y = math.sin(time.time()*20.5+self.x*0.015+self.y*0.01)* self.buzz_amplitude

        x = self.x + boff_x + offset[0]
        y = self.y + boff_y + offset[1]
        x += self.x_off*c.TILE_SIZE
        y += self.y_off*c.TILE_SIZE



        if self.part_of_hope and self.character in self.glows:
            glow_surf = self.glows[self.character]
            weights = (4, 5, 1, 1, 2)
            total_weight = sum(weights)
            glow_intensity = math.sin(self.age) * weights[0] \
                             + math.cos(self.age * 5) * weights[1] \
                             + math.sin(self.age * 22) * weights[2] \
                             + math.sin(self.age * 24) * weights[3] \
                             + math.cos(self.age * 3) * weights[4]
            scaled = 0.75 + glow_intensity * 0.25 / total_weight
            composite = glow_surf.copy()
            dark = composite.copy()
            dark.fill((c.BLACK))
            dark.set_alpha(255 * (1 - scaled))
            composite.blit(dark, (0, 0))
            surface.blit(composite, (x - glow_surf.get_width()//2, y - glow_surf.get_height()//2), special_flags=pygame.BLEND_ADD)

        x -= self.surf.get_width()//2
        y -= self.surf.get_height()//2

        if self.hovered or self.grabbed:
            surface.blit(self.hover_surf, (x, y))
        elif self.part_of_hope:
            surface.blit(self.hope_surf, (x, y))
        else:
            surface.blit(self.surf, (x, y))



    def is_wall(self):
        return self.character==c.WALL_CHAR

    def update(self, dt, events):
        if None in {self.x, self.y, self.target_x, self.target_y}:
            return

        start_shloop = 0.75
        if self.grid.won and self in self.grid.victory_objects and self.grid.since_won>start_shloop:
            vel = (self.grid.since_won - start_shloop) * 2000 + 1500
            self.target_x += vel*dt

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        self.x += dx*dt*15
        self.y += dy*dt*15

        decay = 8
        if self.grabbed and self.buzz_amplitude<self.MAX_BUZZ:
            self.buzz_amplitude=min(self.MAX_BUZZ, self.buzz_amplitude+decay*dt)
        elif not self.grabbed and self.buzz_amplitude > 0:
            self.buzz_amplitude=max(0, self.buzz_amplitude-decay*dt)

        self.age += dt

    def set_target_position_on_grid(self, x, y):
        if not (self.grid.won and self in self.grid.victory_objects and self.grid.since_won>0.5):
            self.target_x = x
            if not self.x:
                self.x = x
            self.target_y = y
            if not self.y:
                self.y = y