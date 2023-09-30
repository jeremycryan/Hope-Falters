from pyracy.sprite_tools import Sprite, Animation
import pygame
import constants as c
from word_manager import WordManager

class Grid:
    pass

    def __init__(self, path):
        self.width, self.height = self.load_from_file(path)
        self.grabbed_tile = None
        self.grab_position = None
        self.drag_direction = None
        self.grabbed_shape = None

    def load_from_file(self, path):
        with open(path) as f:
            lines = [line.strip() for line in f.readlines()]
        width = len(lines[0])
        height = len(lines)

        self.tiles = [[GridObject(character, self) if character != "." else None for character in line] for line in lines]

        return width, height

    def draw(self, surface, offset=(0, 0)):
        x = c.CENTER_X - c.TILE_SIZE*(self.width - 1)//2
        y = c.CENTER_Y - c.TILE_SIZE*(self.height - 1)//2
        x0=x
        for row in self.tiles:
            x = x0
            for grid_object in row:
                pygame.draw.rect(surface, (50, 50, 50), (x-c.TILE_SIZE//4, y-c.TILE_SIZE//4, c.TILE_SIZE//2, c.TILE_SIZE//2))
                if grid_object is not None:
                    grid_object.draw(surface, (x, y))
                x += c.TILE_SIZE
            y += c.TILE_SIZE

    def all_grid_objects(self):
        for row in self.tiles:
            for grid_object in row:
                if grid_object is None:
                    continue
                yield grid_object

    def update(self, dt, events):
        for grid_object in self.all_grid_objects():
            grid_object.update(dt, events)
        mpos = pygame.mouse.get_pos()
        self.update_hovered_statuses(mpos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.hovered_object(mpos):
                    self.grab()
            if event.type == pygame.MOUSEBUTTONUP:
                if self.grabbed_tile:
                    self.release()

        self.update_dragging()



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
        for grid_object in self.all_grid_objects():
            if grid_object is hovered:
                grid_object.hovered = True
            else:
                grid_object.hovered = False

    def grab(self):
        mpos = pygame.mouse.get_pos()
        self.regrab(mpos)
        self.grabbed_objects = []
        self.grabbed_shape = None
        print("Grab!")

    def regrab(self, mpos):
        self.grabbed_tile = self.hovered_tile(mpos)
        self.grab_position = mpos

    def release(self):
        self.grabbed_tile = None
        self.grab_position = None
        self.drag_direction = None
        print("Release!")

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

    def __init__(self, character, grid):
        self.grid = grid
        if not GridObject.FONT:
            GridObject.FONT=pygame.font.SysFont("sans",24)
        if not GridObject.FONT_DICT:
            GridObject.FONT_DICT = {char: self.FONT.render(char,True,c.WHITE) for char in c.CHARS}
        if not GridObject.HOVER_FONT_DICT:
            GridObject.HOVER_FONT_DICT = {char: self.FONT.render(char, True, c.YELLOW) for char in c.CHARS}

        self.character = character
        self.surf = self.FONT_DICT[character].copy()
        self.hover_surf = self.HOVER_FONT_DICT[character].copy()
        self.highlighted = False
        self.hovered = False

        self.x_off = 0  # in grid tiles
        self.y_off = 0

    def draw(self, surface, offset=(0, 0)):
        x = offset[0] - self.surf.get_width()//2
        y = offset[1] - self.surf.get_height()//2
        if not self.hovered:
            surface.blit(self.surf, (x, y))
        else:
            surface.blit(self.hover_surf, (x, y))

    def update(self, dt, events):
        pass