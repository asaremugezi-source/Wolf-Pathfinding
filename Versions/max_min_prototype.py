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
        
class tile_eval():
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
            for x in [self.ages, self.values, self.tiles]:
                x[index] = x[index-1]
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
        for a in range(0, value):
            min_value = 1
            for index in range(a ,self.size):
                value = self.values[index]
                if value < min_value:
                    min_value = value
                    min_index = index
            if self.ages[min_index] < threshold:
                self.move_to_front(min_index)
                
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
        self.tile_eval = tile_eval(20)
        self.best_tiles = []
        self.worst_tiles = []
        self.best_tile = [self.position , 1,False]
        self.worst_tile = [None ,0 ,False]

    def evaluate_tile(self, board, tile, destination):
        if self.position == self.best_tile[0]:
            max_value = self.best_tile[1]
        else:
            max_value = 2
        try:
            x = 1/distance_squared(tile, destination)
        except:
            ZeroDivisionError
            return 2
        if x < max_value:
            return x
        return 0
    
    def find_best_move(self, board, destination):
        tiles = find_available_moves(self.position, board)
        best_value = 0
        best = self.best_tile[0]
        for tile in tiles:
            if tile != self.worst_tile[0] and tile != self.worst_tile[0]:
                value = self.evaluate_tile(board, tile, destination)
                if value >= best_value:
                    best_value = value
                    best = tile
        return best
    
    def update_evaluation(self, board, previous_position, destination):
        previous_value = self.evaluate_tile(board, previous_position, destination)
        current_value = self.evaluate_tile(board, self.position, destination)
        
        if self.best_tile[1] > current_value:
            self.worst_tile[0] = self.best_tile[0]
            self.worst_tile[2] = True
            if self.best_tiles != []:
                self.best_tile[0] = self.best_tiles[-1][0]
                del self.best_tiles[-1]
                
        """
        if self.worst_tile[1] < current_value:
            if self.worst_tiles != []:
                self.worst_tile[0] = self.worst_tiles[-1][0]
                del self.worst_tiles[-1]
            
        if previous_position == self.best_tile and self.position != self.best_tile:
            self.best_tile[1] = current_value
"""
        #get rid of best_tile
        if current_value > previous_value:
            self.worst_tile[2] = False
            if not self.best_tile[2]:
                self.best_tiles.append(self.best_tile)
                self.best_tile = [previous_position, self.evaluate_tile(board,self.position, destination),True]
                
        else:
            self.best_tile[2] = False
            if not self.worst_tile[2]:
                self.worst_tiles.append(self.worst_tile)
                self.worst_tile = [previous_position, self.evaluate_tile(board,previous_position, destination),True]
       
        
       
        
        

    def pathfind(self, board, destinaiton):
        previous_position = self.position
        best_move = self.find_best_move(board, destination)
        self.move(board, best_move)
        self.update_evaluation(board, previous_position, destination)
        

        
        
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

def display_game(mode = "traffic light"):
    screen.fill(colour)
    for x in range(-8,8):
        for y in range(-8,8):
            tile = wolf1.position + pygame.Vector2(x,y)
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_TAB]:
                if tile == wolf1.best_tile[0]:
                    rectangle = pygame.Rect(32*(x+8), 32*(y+8), 32, 32)
                    tile_colour = "green"
                    pygame.draw.rect(screen, tile_colour, rectangle)
                if tile == wolf1.worst_tile[0]:
                    rectangle = pygame.Rect(32*(x+8), 32*(y+8), 32, 32)
                    tile_colour = "red"

                    pygame.draw.rect(screen, tile_colour, rectangle)
                    
            if not game_board.fetch_tile(tile):
                rectangle = pygame.Rect(32*(x+8), 32*(y+8), 32, 32)
                pygame.draw.rect(screen, "#413121", rectangle)
            if tile == destination:
                pygame.draw.circle(screen, "red", (32*(x+8.5), 32*(y+8.5)), 10)
    pygame.draw.circle(screen, "grey", (544/2, 544/2), 10)
    pygame.display.flip()
    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
        clock.tick(15)
    else:
        clock.tick(240)
        pass
            
    
    
game_board = board(0.1)        
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
    display_game()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    previous_position = wolf1.position
    wolf1.pathfind(game_board, destination)
        
    if (pygame.Vector2(wolf1.position) - pygame.Vector2(destination)).magnitude_squared() == 0:
        destination = (random.randint(-100,100), +random.randint(-100,100))
        while not game_board.fetch_tile(destination):
            destination = (random.randint(-1,1) + destination[0], random.randint(-1,1)+destination[1])
    count += 1
    #display_game()
            
            
pygame.quit()

        
