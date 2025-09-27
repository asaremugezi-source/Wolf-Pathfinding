import pygame
import random
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
        
        
        
    def load_chunk(self ,position, reason = lambda board: False):
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
        for index in range(len(self.loaded_chunks)-1, -1,-1):
            chunk = self.loaded_chunks[index]
            if not chunk.reason(board):
                if chunk.position not in self.saved_chunks:
                    chunk.save()
                    self.saved_chunks.append(chunk.position)
                del self.loaded_chunks[index]
                
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
        
class chunk:
    def __init__(self, position, reason = lambda board: False ):
        self.position = position
        self.reason = reason
        
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
                board.load_chunk(position, lambda x: (self.position[0] % 16, self.position[1] % 16) == x)
        
class tile_eval_class():
    def __init__(self, size, tiles = [], values = [], ages = []):
        self.size = size
        while len(tiles) < size:
            tiles.append((0,0))
        for x in [ages, values]:
            while len(x) < size:
                x.append(0)
            
        
        self.values = values
        self.tiles = tiles 
        self.ages = ages
        
    def move_to_front(self, index):
        age = self.ages[index]
        value = self.values[index]
        tile = self.tiles[index]
        while index != 0:
            self.values[index] = self.values[index-1]
            self.ages[index] = self.ages[index-1]
            self.tiles[index] = self.tiles[index-1]
            index -= 1
        
        self.ages[0] = age
        self.tiles[0] = tile
        self.values[index] = value
        
    def value(self, tile):
        for i in range(self.size):
            if self.tiles[i] == tile:
                return self.values[i]
        return None
    
    def change(self, tile, value):
        for index in range(self.size):
            if tuple(tile) == tuple(self.tiles[index]):
                self.values[index] = value
                self.ages[index] = 0
                self.move_to_front(index)
                return True
        return False

            
    def initialise(self, tile, value):
        if self.value(tile) == None:
            
            self.move_to_front(self.size - 1)
            self.tiles[0] = tile
            self.values[0] = value
            self.ages[0] = 1
            return True
        else:
            
            for index in range(self.size):
                if self.tiles[index] == tile:
                    
                    
                    self.move_to_front(index)
                    return False
                
    def get_tile_index(self, tile):
        for i in range(self.size):
            if self.tiles[i] == tile:
                return i

            
    def decay(self, value = 7, threshold = 400):
        for index in range(self.size):
            self.ages[index] += 1
            """
        for a in range(0, value):
            min_value = 1
            for index in range(a ,self.size):
                value = self.values[index]
                if value < min_value:
                    min_value = value
                    min_index = index
            if self.ages[min_index] < threshold:
                self.move_to_front(min_index)"""
                
def find_available_moves(position, board):
        available_moves = []
        for x in range(-1,2):
            for y in range(-1,2):
                if board.fetch_tile((int(position[0] + x), int(position[1]) + y)) == 1 and x*y == 0:
                    available_moves.append(position + pygame.Vector2(x,y))
        return available_moves
                    
class animal(entity):
    def __init__(self, position, board):
        super().__init__(position, board)
        self.tile_eval = tile_eval_class(20)
        self.explore_eval = tile_eval_class(1000)
    def evaluate_move(self, board, previous_position, destination):
        if (pygame.Vector2(self.position) - pygame.Vector2(previous_position)).magnitude_squared() == 0:
            self.tile_eval.change(self.position, 0)
            
        else:
            value = max(self.tile_eval.value(self.position)*.8, self.tile_eval.value(previous_position))
            self.tile_eval.change(previous_position, value)
        self.tile_eval.decay(3)
            
    def find_next_move(self, board, destination):
        tiles = self.evaluate_position(board, destination)
        best_value = 0
        best_position = self.position
        for index in range(len(tiles)):
            value = self.tile_eval.value(tiles[index])
            self.tile_eval.ages[self.tile_eval.get_tile_index(tiles[index])] = 0
            if value > best_value:
                best_value = value
                best_position = tiles[index]
        return best_position
                
    def explore(self, board):
        squares_visted = 0
        tiles = find_available_moves(self.position, board)
        best_value = 0
        for tile in tiles:
            self.explore_eval.initialise(tile, 1)
            value = self.explore_eval.value(tile)
            self.explore_eval.ages[self.explore_eval.get_tile_index(tile)] = 0
            if value > best_value:
                best_value = value
                best_tile = tile
        value = self.explore_eval.value(self.position)/2
        self.explore_eval.change(self.position, value)
        self.move(board ,best_tile)
        self.explore_eval.decay(15, 20)
        
            
    def evaluate_position(self, board, destination):
        tiles = find_available_moves(self.position, board)
        bonus = False
        for tile in tiles:
            tile = pygame.Vector2(tile)
           
            displacement = destination - tile
            if displacement != (0,0):
                value = 1/displacement.magnitude_squared()
            else:
                value = 10
            self.tile_eval.initialise(tile, value)
        return tiles

    def pathfind(self, board, destination):
        previous_position = self.position
        self.move(board,self.find_next_move(board, destination))
        self.evaluate_move(board, previous_position, destination)
        board.unload_unused_chunks()
        
def find_colour(num_list, value, mode = "greyscale"):
    M = max(num_list)
    m = min(num_list)
    scaling_factor = 255/(M-m)
    
    scaled_value = int(scaling_factor*(value-m))
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
    else:
        colour = "white"
    return colour

def display_game(evalution,mode = "traffic light"):
    screen.fill(colour)
    for x in range(-8,8):
        for y in range(-8,8):
            tile = wolf1.position + pygame.Vector2(x,y)
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_TAB]:
                if (evalution.value(tile)) != None:
                    rectangle = pygame.Rect(32*(x+8), 32*(y+8), 32, 32)
                    tile_colour = find_colour(evalution.values, evalution.value(tile), mode)
                    pygame.draw.rect(screen, tile_colour, rectangle)
                    
            if not game_board.fetch_tile(tile):
                rectangle = pygame.Rect(32*(x+8), 32*(y+8), 32, 32)
                pygame.draw.rect(screen, "#413121", rectangle)
            if tile == destination:
                pygame.draw.circle(screen, "red", (32*(x+8.5), 32*(y+8.5)), 10)
    pygame.draw.circle(screen, "grey", (544/2, 544/2), 10)
    pygame.display.flip()
    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
        clock.tick(10)
    else:
        clock.tick(60)
            
    
    
game_board = board(.35)        
wolf1 = animal((0,0), game_board)
screen = pygame.display.set_mode((544,544))
clock = pygame.time.Clock()
running = True
colour = "#085000"
destination = (10,10)
count = 0

while not game_board.fetch_tile(destination):
    destination = (random.randint(-1,1) + destination[0], random.randint(-1,1)+destination[1])
while running:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    previous_position = wolf1.position
    
    if (count // 1000) % 2:
        wolf1.explore(game_board)
        #wolf1.evaluate_position(game_board, destination)
        #wolf1.evaluate_move(game_board, previous_position, destination)
        display_game(wolf1.explore_eval, "greyscale")
    else:
        #wolf1.explore_eval.initialise(wolf1.position, 1)
        #value = wolf1.explore_eval.value(previous_position)/2
        #wolf1.explore_eval.change(previous_position, value)
        wolf1.pathfind(game_board, destination) 
        display_game(wolf1.tile_eval)


    if (pygame.Vector2(wolf1.position) - pygame.Vector2(destination)).magnitude_squared() == 0:
        destination = (random.randint(-100,100), +random.randint(-100,100))
        while not game_board.fetch_tile(destination):
            destination = (random.randint(-1,1) + destination[0], random.randint(-1,1)+destination[1])
    count += 1
    #display_game()
            
            
pygame.quit()

        
