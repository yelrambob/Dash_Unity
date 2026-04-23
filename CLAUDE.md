# CTDash / CTDash_Unity — Project Notes for Claude

## Platform
- **OS: Linux** — all paths, shell commands, and tooling should assume Linux.
- Do not suggest Windows-only tools or paths.

## Repository layout
- `CTDash/` — Python simulation (design reference and balance sandbox)
- `CTDash_Unity/` — Unity 2022.3 LTS port (the actual game)

## Active branch
- Development branch: `claude/add-progress-tracking-xaMtJ`

## Unity project
- Version: Unity 2022.3.20f1 LTS
- Template: 2D (built-in renderer, no URP for now)
- Entry point: `SimulationController.cs` — attach to a single `GameManager` GameObject

## Simulation architecture
- All game logic is pure C# (no MonoBehaviour dependencies except `SimulationController`)
- `GameConfig.cs` is the single source of truth for all tunable values
- Tick rate: `TIME_SCALE = 210` game-seconds per real second
- Simulation namespace: `CTDash`
