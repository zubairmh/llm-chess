import io
import outlines
import chess
import chess.svg
import pygame
import time
import uuid
from wand.image import Image

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((512, 600))  # Increased height to fit extra data
pygame.display.set_caption("Hermes 3 LLaMA 3.1 vs DeepSeek-R1-Qwen-7B Chess")

# Initialize pygame font
pygame.font.init()
font = pygame.font.Font(None, 32)  # Default font with size 32 for better visibility

# Initialize pygame for sound
pygame.mixer.init()
move_sound = pygame.mixer.Sound("move-self.mp3")
check_sound = pygame.mixer.Sound("capture.mp3")
notify_sound = pygame.mixer.Sound("notify.mp3")
# Generate a unique game ID
gid = str(uuid.uuid4()) # "6e54fc19-3748-4649-b398-22b404e07d9f" #
print("Game ID:", gid)

# Initialize AI clients
llama_client = outlines.models.openai(
    "hermes-3-llama-3.1-8b", base_url="http://172.16.166.139:1234/v1", api_key="dopeness"
)
deepseek_client = outlines.models.openai(
    "deepseek-r1-distill-qwen-7b",
    base_url="http://172.16.166.139:1234/v1",
    api_key="dopeness",
)

def display_message(text, duration=3):
    """Displays a message on a black screen for a given duration."""
    screen.fill((0, 0, 0))  # Black background
    message_surface = font.render(text, True, (255, 255, 255))  # White text
    text_rect = message_surface.get_rect(center=(256, 300))  # Center text
    screen.blit(message_surface, text_rect)
    pygame.display.flip()
    time.sleep(duration)

def get_best_move(board: chess.Board, model):
    """Get the best move from the model given the current board state."""
    legal_moves = [move.uci() for move in board.legal_moves]

    # Optional State of last 5 moves
    last_moves = [
        board.move_stack[-i].uci() for i in range(1, min(6, len(board.move_stack) + 1))
    ]
    check_moves = [
        move.uci() for move in board.legal_moves if board.gives_check(move)
    ]
    captures = [
        move.uci() for move in board.legal_moves if board.is_capture(move)
    ]

    generator = outlines.generate.choice(model, legal_moves)
    best_move = generator(
        f"""GAME ID: {gid} 
        What is the best possible move in this board? 
        You play as {'WHITE' if board.turn == chess.WHITE else 'BLACK'}: lowercase characters represent black pieces and uppercase are white
        Board State:
        {board.__str__()}, 
        Possible Piece Captures: {captures}
        Possible Check Moves: {check_moves}
        Last 5 Moves: {last_moves}"""
    )
    return best_move

def render_board(board, move):
    """Renders the chess board using pygame and overlays extra data."""
    board_svg = chess.svg.board(board=board, size=512, lastmove=chess.Move.from_uci(move))
    with Image(blob=board_svg.encode('utf-8'), format="svg") as img:
        img.format = "png"
        png_data = img.make_blob()

    # Load PNG into Pygame
    image = pygame.image.load(io.BytesIO(png_data))
    screen.fill((255, 255, 255))  # Clear the screen
    screen.blit(image, (0, 0))  # Draw the chessboard

    # Display additional game information
    turn_text = f"Turn: {'White' if board.turn == chess.WHITE else 'Black'}"
    move_text = f"Move Number: {board.fullmove_number}"
    last_move_text = f"Last Move: {move if move else 'None'}"

    # Render text
    turn_surface = font.render(turn_text, True, (0, 0, 0))
    move_surface = font.render(move_text, True, (0, 0, 0))
    last_move_surface = font.render(last_move_text, True, (0, 0, 0))

    # Draw text below the board
    screen.blit(turn_surface, (10, 520))
    screen.blit(move_surface, (10, 545))
    screen.blit(last_move_surface, (10, 570))

    pygame.display.flip()

# Initialize the chess board
board = chess.Board()

def get_game_result():
    """Returns a formatted string for the game result."""
    outcome = board.outcome()
    if outcome is None:
        return "Game Over! No result detected."

    if outcome.winner is None:
        return f"Game Over! Result: {outcome.termination.name} (Draw)"
    winner = "White" if outcome.winner else "Black"
    return f"Game Over! {winner} wins by {outcome.termination.name}"

def play_game():
    """Plays a game where LLaMA 3.2 (White) competes against DeepSeek-R1 (Black)."""

    # Display Game ID before starting
    display_message(f"Game ID: {gid}", duration=3)

    running = True
    while running and not board.is_game_over():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
        
        legal_moves = [move.uci() for move in board.legal_moves]
        
        # Choose model based on turn
        model = llama_client if board.turn == chess.WHITE else deepseek_client
        move = get_best_move(board, model)
        
        # Ensure move is valid
        if move in legal_moves:
            board.push_uci(move)
            
            # Play check sound if the move puts the opponent in check
            if board.is_check():
                check_sound.play()
            else:
                move_sound.play()

        else:
            print("Invalid move generated. Terminating game.")
            break
        
        # Render the board in pygame
        render_board(board, move)
    notify_sound.play()
    time.sleep(5)
    # Display the game result for 10 seconds
    game_result = get_game_result()
    print(game_result)
    display_message(game_result, duration=10)

play_game()
pygame.quit()
