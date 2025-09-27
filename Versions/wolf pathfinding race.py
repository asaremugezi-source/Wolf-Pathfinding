import pygame
import random
import os
#squares: (position, value)
epsilon = 10**-8
class board:
    def __init__(self, obstacle_chance = .05):
        self.obstacle_chance = obstacle_chance
        self.saved_chunks = []
        self.loaded_chunks = []
        self.entities = []

    def fetch_tile(self, position):
        in_chunk = self.load_chunk(position)
        x = int(position[0]%16)
        y = int(position[1]%16)
        return in_chunk.tiles[x][y]
        
        
        
    def load_chunk(self ,position, reason = lambda chunk: False):
        chunk_position = (position[0] // 16, position[1]//16)
        for index in range(len(self.loaded_chunks)):
            if self.loaded_chunks[index].position == chunk_position:
                self.loaded_chunks[index].reason = reason
                return(self.loaded_chunks[index])
        x = chunk(chunk_position, reason)
        if chunk_position in self.saved_chunks:
            x.load()
        else:
            x.generate(self.obstacle_chance)
        self.loaded_chunks.append(x)
        return(x)
    
    def unload_unused_chunks(self):
        unloaded = False
        for index in range(len(self.loaded_chunks)-1, -1,-1):
            chunk = self.loaded_chunks[index]
            if not chunk.reason(chunk):
                if chunk.position not in self.saved_chunks:
                    chunk.save()
                    self.saved_chunks.append(chunk.position)
                del self.loaded_chunks[index]
            chunk.entities = []
                
    def force_unload(self, chunk_position, delete = False):
        for index in range(len(self.loaded_chunks)):
            if chunk.position == chunk_position:
                x = self.loaded_chunks[index]
                del self.loaded_chunks[index]
                if not delete:
                    x.save()
                    return
                else:
                    for index in range(len(self.generated_chunks)):
                        if self.generated_chunks[index] == chunk_position:
                            del self.generated_chunks[index]
                            
    def add_entity_to_chunk(self, entity, position):
        chunk = self.load_chunk(position, lambda chunk: chunk.entities != [])
        chunk.entities.append(entity)
        
        
class chunk:
    def __init__(self, position, reason = lambda board: False ):
        self.position = position
        self.reason = reason
        self.entities = []
        
    def generate(self, obstacle_chance):
        self.tiles = [[1 for x in range(16)] for y in range(16)]
        for x in range(16):
            for y in range(16):
                r = random.uniform(0,1)
                if r < obstacle_chance:
                    self.tiles[x][y] = 0
                    
    def save(self):
        title = (int(self.position[0]),int(self.position[1]))
        title = str(title)
        file = open(title + ".txt", "w")
        for x in range(16):
            for y in range(16):
                file.write(str(self.tiles[x][y]))
            file.write("\n")
        file.close()

    def load(self):
        title = (int(self.position[0]),int(self.position[1]))
        title = str(title)
        self.tiles = [[1 for x in range(16)] for y in range(16)]
        file = open(title + ".txt", "r")
        for x in range(16):
            line = file.readline()
            for y in range(16):
                self.tiles[x][y] = int(line[y])
        file.close()
        
class entity:
    def __init__(self, position, board):
        self.position = position
        board.entities.append(self)
        self.board_index = len(board.entities) - 1
        
    def move(self, board, destination):
        self.position = destination
        for x in range(-1,2):
            for y in range(-1,2):
                position = (self.position[0] + 16*x, self.position[1] + 16*y)
                board.add_entity_to_chunk(self, position)
                
class tile_eval():
    def __init__(self, size, tiles = [], values = [], distances = []):
        self.size = size
        self.values = values
        self.tiles = tiles
        self.distances = distances
        self.max_value = 0
        self.max_changed = False
        
    def move_to_front(self, index):
        value = self.values[index]
        tile = self.tiles[index]
        distance = self.distances[index]
        while index != 0:
            for x in [self.values, self.tiles]:
                x[index] = x[index-1]
            index -= 1
        self.tiles[0] = tile
        self.values[index] = value
        self.distances[index] = distance
        
    def truncate(self):
        index = len(self.tiles) - 1
        while index > self.size:
            for x in [self.values, self.tiles, self.distances]:
                del x[index]
            index -= 1
            
    def value(self, tile):
        for i in range(len(self.tiles)):
            if self.tiles[i] == tile:
                return self.values[i]
    
    def change(self, tile, value):
        if value > self.max_value:
            self.max_value = value
        for index in range(len(self.tiles)):
            if tuple(tile) == tuple(self.tiles[index]):
                self.max_changed =  self.values[index] == self.max_value
                self.values[index] = value
                self.distances[index] += 1
                self.move_to_front(index)
                return True
        return False

    def initialise(self, tile, value):
        global M_changed
        global current_wolf
        if self.value(tile) == None:
            M_changed[current_wolf] = True
            
            if value > self.max_value:
                
                self.max_changed = True
                self.max_value = value
            self.tiles.append(tile)
            self.values.append(value)
            self.distances.append(0)
            return True
                
    def get_tile_index(self, tile):
        for i in range(len(self.tiles)):
            if self.tiles[i] == tile:
                return i
    def forget(self):
        self.values = []
        self.tiles = []
        self.distances = []
        self.size = 0

                
def distance_squared(tile1, tile2):
    return (tile1[0] - tile2[0])**2 + (tile1[1]-tile2[1]) **2

def find_available_moves(position, board):
    available_moves = []
    for i in range(4):
        direction = [(-1)**(i//2)*((k+i)%2) for k in range(2)]
        tile = (position[0] + direction[0], position[1] + direction[1])
        if board.fetch_tile(tile):
            available_moves.append(tile)
    return available_moves

class animal(entity):
    def __init__(self, position, board):
        super().__init__(position, board)
        self.tile_eval = tile_eval(0, [self.position], [0], [0])
        
    def evaluate_moves(self, board, destination):
        moves = find_available_moves(self.position, board)
        for move in moves + [self.position]:
            value = 1/(distance_squared(move, destination)+1)
            self.tile_eval.initialise(move, value)
        return moves

    def choose_direction(self, board, moves):
        current_value = self.tile_eval.value(self.position)
        in_local_max = True
        max_value = 0
        second_best = 0
        total = 0
        for move in moves:
            move_value = self.tile_eval.value(move)
            total += move_value
            if in_local_max and move_value > current_value:
                in_local_max = False
                max_value = move_value
                best_move = move
                
            elif move_value >= max_value:
                second_best = max_value
                max_value = move_value
                try:
                    index = self.tile_eval.get_tile_index(best_move)
                    distance = 1+self.tile_eval.distances[index]
                except UnboundLocalError:
                    distance = 0
                best_move = move
                
            elif move_value > second_best:
                index = self.tile_eval.get_tile_index(move)
                distance = 1+self.tile_eval.distances[index]
                second_best = move_value
                
        if not self.tile_eval.max_changed or in_local_max:
            
            self_index = self.tile_eval.get_tile_index(self.position)
            if self.tile_eval.distances[self_index] == 0:
                self.tile_eval.size += 1
            
            try:
                index = self.tile_eval.get_tile_index(self.position)
                y = total/(4)
            except ZeroDivisionError:
                y = 0
            self.tile_eval.change(self.position, y)
        return best_move

    def pathfind(self, board, destination):
        global count
        previous_max = self.tile_eval.max_value
        moves = self.evaluate_moves(board, destination)
        direction = self.choose_direction(board, moves)
        self.move(board, direction)
        self.tile_eval.truncate()
        board.unload_unused_chunks()
        if self.tile_eval.max_changed:
            temp_count = 0
        if self.tile_eval.max_value > previous_max:
            if self.tile_eval.size > 1000:
                print(self.tile_eval.size, self)
            self.tile_eval.forget()
class animal2(animal):
    def choose_direction(self, board, moves):
        current_value = self.tile_eval.value(self.position)
        in_local_max = True
        max_value = 0
        second_best = 0
        distance = 1
        for move in moves:
            move_value = self.tile_eval.value(move)
            
            if in_local_max and move_value > current_value:
                in_local_max = False
                max_value = move_value
                best_move = move
                
            elif move_value >= max_value:
                second_best = max_value
                max_value = move_value
                try:
                    index = self.tile_eval.get_tile_index(best_move)
                    distance = 1+self.tile_eval.distances[index]
                except UnboundLocalError:
                    distance = 0
                best_move = move
                
            elif move_value > second_best:
                index = self.tile_eval.get_tile_index(move)
                distance = 1+self.tile_eval.distances[index]
                second_best = move_value
                
        if in_local_max:
            
            self_index = self.tile_eval.get_tile_index(self.position)
            if self.tile_eval.distances[self_index] == 0:
                self.tile_eval.size += 1
            
            
            try:
                index = self.tile_eval.get_tile_index(self.position)
                self.tile_eval.distances[index] = distance
                x = (1/second_best) + 2*distance - 1
                y = 1/x
                
            except ZeroDivisionError:
                y = 0
            self.tile_eval.change(self.position, y)
        return best_move
    
def normalise_list(num_list):
    global M
    global M_changed
    if M_changed[animal]:
        M[animal] = max(num_list)
        M_changed[animal] = False
    try:
        scaling_factor = 1/(M[animal])
    except ZeroDivisionError:
        return num_list
    return [(num_list[i])*scaling_factor for i in range(len(num_list))]

def find_colour(normed_list, index, mode = "greyscale"):
    scaled_value = int(255*normed_list[index])
    d1 = scaled_value // 16
    d2 = scaled_value % 16
    translation = '0123456789ABCDEF'
    colour = '#'
    if mode == "greyscale":
        for i in range(3):
            colour += translation[d1] + translation[d2]
    elif mode == "traffic light":
        backwards_value = 255-int(scaled_value)
        a1 = backwards_value // 16
        a2 = backwards_value % 16
        colour += translation[a1] + translation[a2]
        colour += translation[d1] + translation[d2]
        colour += "00"
    elif mode == "rainbow":
        R = 0
        G = 0
        B = 0
        fifth = 255//5
        if scaled_value < fifth:
            R = scaled_value*5
        elif scaled_value < 2*fifth:
            G = scaled_value*5-255
            R = 255-G
        elif scaled_value < 3*fifth:
            B = scaled_value*5-255*2
            G = 255-B
        elif scaled_value <4*fifth:
            B = 255
            R = scaled_value*5-255*3
        else:
            R = 255
            G = scaled_value*5-255*4
            B = 255
        try:
            colour += translation[R//16]
            colour += translation[R%16]
            colour += translation[G//16]
            colour += translation[G%16]
            colour += translation[B//16]
            colour += translation[B%16]
        except:
            raise IndexError("Error, Values out of range ", R, G, B)
    else:
        colour = "white"
    return colour

def display_game(animal, mode = "traffic light"):
    global count
    global colour
    global dest_count
    screen.fill(colour)
    next_mode = "traffic light"
    for x in range(-8,9):
        for y in range(-8,9):
            tile = animal.position + pygame.Vector2(x,y)
            if keys[pygame.K_TAB]:
                index = animal.tile_eval.get_tile_index(tile)
                if index != None:
                    normed_list = normalise_list(animal.tile_eval.values)
                    
                    if animal.tile_eval.distances[index] > 15:
                        next_mode = "rainbow"
                    tile_colour = find_colour(normed_list, index, mode)
                    rectangle = pygame.Rect(32*(x+8), 32*(y+8), 32, 32)

                    pygame.draw.rect(screen, tile_colour, rectangle)
                pass
                    
            if not game_board.fetch_tile(tile):
                rectangle = pygame.Rect(32*(x+8), 32*(y+8), 32, 32)
                pygame.draw.rect(screen, "#002A00", rectangle)
            if tile == destination:
                pygame.draw.circle(screen, "red", (32*(x+8.5), 32*(y+8.5)), 10)
            if tile == wolf1.position:
                pygame.draw.circle(screen, "white", (32*(x+8.5), 32*(y+8.5)), 10)
            if tile == wolf2.position:
                pygame.draw.circle(screen, "black", (32*(x+8.5), 32*(y+8.5)), 10)
    pygame.display.flip()
    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
        clock.tick(30)
    else:
        pass
    return next_mode
            
    
    
game_board = board(.25)        
wolf1 = animal((0,1), game_board)
wolf2 = animal2((0,1), game_board)
screen = pygame.display.set_mode((544,544))
clock = pygame.time.Clock()
running = True
colour = "#603500"
destination = (7*16+1,-4*16+1)
count = 0
temp_count = count
start = False
next_mode = ""
M = {wolf1:0, wolf2:0}
dest_count = 0
save_chunks = False
animal = wolf1
current_wolf = wolf1
scores = [0,0]
M_changed = {wolf1:0, wolf2:0}
First = True
Display = True
Q_pressed_last_time = False

while not game_board.fetch_tile(destination):
    destination = (random.randint(-1,1) + destination[0], random.randint(-1,1)+destination[1])
while running:
    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]:
        start = True
        
    if Display:
        next_mode = display_game(animal, next_mode)
        
    if keys[pygame.K_q] and not Q_pressed_last_time:
        Q_pressed_last_time = True
        Display = not Display
    Q_pressed_last_time = keys[pygame.K_q]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    if keys[pygame.K_F1]:
        animal = wolf1
    if keys[pygame.K_F2]:
        animal = wolf2
        
    if start:
        if wolf1.position != destination:
            wolf1.pathfind(game_board, destination)
        elif First:
            print(1, count, end = " ")
            First = False
            scores[0] += 1
        current_wolf = wolf2
        if wolf2.position != destination:
            wolf2.pathfind(game_board, destination)
            
        elif First:
            print(2, count, end = " ")
            First = False
            scores[1] += 1
        current_wolf = wolf1
    
    if (wolf1.position == destination and wolf2.position == destination) or keys[pygame.K_RETURN] or temp_count > 10000:
        destination = (random.randint(-1000,1000), random.randint(-1000,1000))
        dest_count += 1
        print (count)
        First = True
        count = 0
        temp_count = count
        wolf1.tile_eval.forget()
        wolf1.tile_eval.max_value = 0
        wolf2.tile_eval.forget()
        wolf2.tile_eval.max_value = 0
        
        while not game_board.fetch_tile(destination):
            destination = (random.randint(-1,1) + destination[0], random.randint(-1,1)+destination[1])
    count += 1
    if dest_count > int(1/game_board.obstacle_chance):
        print(game_board.obstacle_chance, scores)
        scores = [0,0]
        for chunk_ in game_board.saved_chunks:
            name = str((int(chunk_[0]),  int (chunk_[1])))
            os.remove(name + ".txt")
        wolf1.position = wolf2.position
        game_board.saved_chunks = []
        game_board.obstacle_chance += 1/16
        dest_count = 0
        
    if game_board.obstacle_chance >= .5:
        break
    
    if keys[pygame.K_ESCAPE]:
        for chunk in game_board.loaded_chunks:
            print(chunk.position)
            game_board.force_unload(chunk)
            save_chunks = True
        break
    #display_game()
    if keys[pygame.K_BACKSPACE]:
        start = False
print(scores)
pygame.quit()
if not save_chunks:
    for chunk in game_board.saved_chunks:
        name = str((int(chunk[0]),  int (chunk[1])))
        os.remove(name + ".txt")

        
