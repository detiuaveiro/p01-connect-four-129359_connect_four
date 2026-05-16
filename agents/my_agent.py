from agents.base_agent import BaseC4Agent
import random
import math
import asyncio
import logging

ROW_COUNT = 6
COLUMN_COUNT = 7
WINDOW_LENGTH = 4


def evaluate_window(window, piece, opponent_piece):
    """Evaluate a 4-cell window for Connect Four patterns"""
    score = 0

    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(0) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(0) == 2:
        score += 2

    if window.count(opponent_piece) == 3 and window.count(0) == 1:
        score -= 4

    return score


def score_position(board, piece, opponent_piece):
    """Comprehensive board position evaluation"""
    score = 0

    # Center column preference
    center_array = [int(board[r][COLUMN_COUNT // 2]) for r in range(ROW_COUNT)]
    center_count = center_array.count(piece)
    score += center_count * 3

    # Horizontal evaluation
    for r in range(ROW_COUNT):
        row_array = [int(i) for i in board[r]]
        for c in range(COLUMN_COUNT - 3):
            window = row_array[c : c + WINDOW_LENGTH]
            score += evaluate_window(window, piece, opponent_piece)

    # Vertical evaluation
    for c in range(COLUMN_COUNT):
        col_array = [int(board[r][c]) for r in range(ROW_COUNT)]
        for r in range(ROW_COUNT - 3):
            window = col_array[r : r + WINDOW_LENGTH]
            score += evaluate_window(window, piece, opponent_piece)

    # Positive diagonal (/)
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r + i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece, opponent_piece)

    # Negative diagonal (\)
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r + 3 - i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece, opponent_piece)

    return score


def is_valid_location(board, col):
    """Check if column has space"""
    return board[0][col] == 0


def get_next_open_row(board, col):
    """Find next available row in column"""
    for r in range(ROW_COUNT - 1, -1, -1):
        if board[r][col] == 0:
            return r


def drop_piece(board, row, col, piece):
    """Place piece on board"""
    board[row][col] = piece


def copy_board(board):
    """Create a lightweight copy of the 6x7 board."""
    return [row[:] for row in board]


def winning_move(board, piece):
    """Check if piece has won the game"""
    # Horizontal
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT):
            if all(board[r][c + i] == piece for i in range(4)):
                return True
    # Vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return True
    # Diagonal /
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True
    # Diagonal \
    for c in range(COLUMN_COUNT - 3):
        for r in range(3, ROW_COUNT):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True
    return False


def minimax(board, depth, alpha, beta, maximizing_player, ai_piece, opponent_piece):
    """
    Minimax algorithm with Alpha-Beta pruning

    Args:
        board: Current game state
        depth: Remaining search depth
        alpha: Best score for maximizer
        beta: Best score for minimizer
        maximizing_player: True if AI's turn

    Returns:
        (column, score) tuple
    """
    valid_locations = [c for c in range(COLUMN_COUNT) if is_valid_location(board, c)]
    is_terminal = (
        winning_move(board, opponent_piece)
        or winning_move(board, ai_piece)
        or len(valid_locations) == 0
    )

    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, ai_piece):
                return (None, 100000000)
            elif winning_move(board, opponent_piece):
                return (None, -100000000)
            else:
                return (None, 0)
        else:
            return (None, score_position(board, ai_piece, opponent_piece))

    if maximizing_player:
        value = -math.inf
        column = random.choice(valid_locations)

        for col in valid_locations:
            row = get_next_open_row(board, col)
            temp_board = copy_board(board)
            drop_piece(temp_board, row, col, ai_piece)

            new_score = minimax(
                temp_board, depth - 1, alpha, beta, False, ai_piece, opponent_piece
            )[1]

            if new_score > value:
                value = new_score
                column = col

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return column, value

    else:
        value = math.inf
        column = random.choice(valid_locations)

        for col in valid_locations:
            row = get_next_open_row(board, col)
            temp_board = copy_board(board)
            drop_piece(temp_board, row, col, opponent_piece)

            new_score = minimax(
                temp_board, depth - 1, alpha, beta, True, ai_piece, opponent_piece
            )[1]

            if new_score < value:
                value = new_score
                column = col

            beta = min(beta, value)
            if alpha >= beta:
                break

        return column, value


class MyAgent(BaseC4Agent):
    """
    Nihoo's Minimax-based Connect Four agent with Alpha-Beta pruning.

    This agent uses game tree search to find optimal moves in Connect Four.
    """

    def __init__(self, server_uri=None):
        super().__init__(server_uri)
        self.current_board = None
        self.agent_name = "Nihoo Minimax Agent"

    async def run(self):
        """Override run to capture board state and send agent name"""
        import json
        from websockets.asyncio.client import connect

        try:
            async with connect(self.server_uri) as websocket:
                # Send agent identification
                await websocket.send(
                    json.dumps({"client": "agent", "agent_name": self.agent_name})
                )

                async for message in websocket:
                    if isinstance(message, bytes):
                        message = message.decode("utf-8")
                    data = json.loads(message)

                    if data.get("type") == "setup":
                        self.player_id = data.get("player_id")
                        logging.info(
                            f"{self.agent_name} connected as Player {self.player_id}."
                        )

                    elif data.get("type") == "state":
                        self.current_board = data.get("board")

                        current_turn = data.get("current_turn")
                        valid_actions = data.get("valid_actions")

                        if current_turn == self.player_id and isinstance(
                            valid_actions, list
                        ):
                            action = await self.deliberate(valid_actions)

                            if action is not None:
                                await websocket.send(
                                    json.dumps({"action": "move", "column": action})
                                )

                    elif data.get("type") == "game_over":
                        logging.info(f"Round Over: {data.get('message')}")
                        logging.info("Waiting for next round to start...")

        except Exception as e:
            logging.error(f"Connection lost: {e}")

    async def deliberate(self, valid_actions):
        """
        Use Minimax with Alpha-Beta pruning to select the best move.

        Args:
            valid_actions: List of valid column indices

        Returns:
            int: The chosen column index
        """
        if self.current_board is None:
            return random.choice(valid_actions)

        board = [[int(cell) for cell in row] for row in self.current_board]
        ai_piece = int(self.player_id or 2)
        opponent_piece = 3 - ai_piece

        # Run Minimax search with depth 5
        col, score = minimax(
            board, 5, -math.inf, math.inf, True, ai_piece, opponent_piece
        )

        # Log the decision (helps with debugging)
        logging.info(f"{self.agent_name} chose column {col} (evaluation: {score:.2f})")

        if col not in valid_actions:
            return random.choice(valid_actions)

        return col


if __name__ == "__main__":
    agent = MyAgent()
    asyncio.run(agent.run())
