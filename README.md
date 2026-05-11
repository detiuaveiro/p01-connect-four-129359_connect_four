# <img src="frontend/favicon.svg" alt="logo" width="128" height="128" align="middle"> SI2 - Connect Four

Connect Four is a classic two-player connection board game in which the players choose a color and then take turns dropping colored discs into a seven-column, six-row vertically suspended grid. The pieces fall straight down, occupying the lowest available space within the column. The objective of the game is to be the first to form a horizontal, vertical, or diagonal line of four of one's own discs.

In this project, we focus on developing autonomous agents that can play Connect Four against each other or against a human player. The game state is managed by a central server that communicates with the agents and a frontend viewer via WebSockets. Each agent receives the current board state and must decide the best column to drop their disc.

## Game Rules

The game is played on a grid with $R=6$ rows and $C=7$ columns. Two players, Player 1 and Player 2, take turns dropping their pieces.
- **State**: The world state is represented by a 2D grid of size $6 \times 7$, where 0 represents an empty cell, 1 represents a disc from Player 1, and 2 represents a disc from Player 2.
- **Actions**: A player can choose a column index $c \in \{0, 1, \dots, 6\}$ that is not yet full (i.e., the top row of that column is 0).
- **Gravity**: When a player chooses a column, the piece falls to the lowest available row $r$ in that column.
- **Win Condition**: A player wins if they have 4 of their discs in a row (horizontal, vertical, or diagonal).
- **Draw**: The game ends in a draw if the board is full and no player has won.

## Setup

The "simulation" is launched using Docker Compose, which starts the backend server and the frontend viewer.

1.  **Start the environment**:
    ```bash
    docker compose up
    ```
    The frontend viewer will be available at `http://localhost:8080`.

2.  **Run Agents**:
    Create a virtual environment and install the dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    Execute the agents locally:
    ```bash
    python agents/dummy_agent.py
    ```
    or
    ```bash
    python agents/manual_agent.py
    ```
    or run the submitted autonomous agent:
    ```bash
    python agents/my_agent.py
    ```

For an automated match, open two terminals after the backend is running and start:
```bash
python agents/my_agent.py
python agents/dummy_agent.py
```

The server assigns Player 1 and Player 2 in connection order. The frontend at
`http://localhost:8080` shows the board, whose turn it is, connection status,
and the running score.

## Project Structure

- `backend/`: contains the server-side Python code (`server.py`) and its `Dockerfile`. The server manages the game state, scores, and communication.
- `frontend/`: contains the viewer (HTML, JS, CSS) to monitor the game state.
- `agents/`: contains the Connect Four agents:
    - `base_agent.py`: the abstract base class for agents.
    - `dummy_agent.py`: a simple automated agent that makes random moves.
    - `manual_agent.py`: an agent that allows manual player interaction via the terminal.
    - `my_agent.py`: the submitted autonomous agent using Minimax with alpha-beta pruning.
- `compose.yml`: Docker Compose configuration to run the backend and frontend.

## Solution Architecture

The project follows the required client-server structure:

- The backend WebSocket server owns the official board state, validates moves,
  applies gravity, checks wins/draws, tracks scores, and broadcasts the current
  state.
- Agents connect as WebSocket clients. On every state update, an agent only
  acts when `current_turn` matches its assigned `player_id`.
- The frontend connects as a viewer client and renders the live board and score.
- `MyAgent` stores the latest board received from the server, evaluates legal
  columns, and sends a selected column back as a move.

## Submitted Agent

`agents/my_agent.py` implements a depth-limited Minimax search with alpha-beta
pruning. The heuristic rewards:

- Center-column control, because central discs participate in more possible
  four-in-a-row lines.
- Completed four-disc lines.
- Three-in-a-row and two-in-a-row patterns with open spaces.
- Defensive blocking when the opponent has three discs and one empty cell in a
  four-cell window.

The agent now uses its assigned `player_id`, so it works correctly as either
Player 1 or Player 2. It also uses the same board orientation as the server:
row `0` is the top of the board and row `5` is the bottom, so a column is legal
when the top cell is empty and simulated pieces fall to the lowest empty row.

Search depth is set to `5`, which gives a stronger strategy than a random
agent while keeping moves responsive for live matches.

## Evaluation

The implemented agent should consistently outperform `dummy_agent.py` because
it searches future positions instead of selecting random legal moves. In logic
checks, it prioritizes central columns, takes immediate wins when available,
and blocks many direct opponent threats.

Expected strengths:

- Strong tactical play in short and medium-range positions.
- Much better move quality than random play.
- Works from both player positions.

Known limitations:

- Depth `5` is not a solved-game strategy; deeper forced wins can still be
  missed.
- The heuristic is handcrafted, so it may prefer locally good patterns over a
  long-term forced plan.
- Increasing depth improves strength but also increases move time.

## Contributions and Fixes

The repository includes the following project-specific additions beyond the
base simulation:

- A custom autonomous Connect Four agent in `agents/my_agent.py`.
- Score logging in the backend to `/tmp/scores.csv` after wins and draws.
- Automatic round restart and alternating first player between rounds.
- Frontend support for agent display names.
- Backend support for receiving and broadcasting agent display names.
- Fixes in the agent simulation logic so column validity, gravity, and player
  identity match the server.

## Development

To develop a new agent, you should inherit from the `BaseC4Agent` class and implement the `deliberate` method.

```python
from agents.base_agent import BaseC4Agent
import random

class MyAgent(BaseC4Agent):
    async def deliberate(self, valid_actions):
        # Your logic here
        return random.choice(valid_actions)
```

For more details on the API, please refer to the [documentation](https://mariolpantunes.github.io/si2-connect-four/).

## Authors

* **Mário Antunes** - [mariolpantunes](https://github.com/mariolpantunes)
* **Nihal Fateen** - [NihalFateen](https://github.com/Nihalfateen)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
