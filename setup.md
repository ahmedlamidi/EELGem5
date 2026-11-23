# gem5 Setup Guide

Follow this guide to prepare a development environment for the EEL matrix multiplication experiments. Run host commands in your computer's terminal and simulator commands inside the professor-provided container unless stated otherwise.

## Phase 1 — Environment Setup

1. **Clone the project repository** — Clone `eel_project` from GitHub and use it for shared benchmark code, configurations, scripts, and documentation.
2. **Check your computer's architecture** — Identify whether your host uses ARM64 or x86_64 so you can select the appropriate Docker environment. On macOS or Linux, run `uname -m`. The host architecture and simulated target ISA are separate settings; this project uses an ARM simulation target.
3. **Verify Docker installation** — Install Docker for your operating system if needed, then run `docker --version` to check that the command is available.
4. **Verify the Docker engine** — Start Docker Desktop or your Docker service, then run `docker info` to confirm the engine is reachable.
5. **Prepare the Ubuntu environment** — Use the Ubuntu environment defined by the professor's Docker setup. A separate manually created container is only needed if the provided instructions require one.
6. **Check development dependencies** — Use the provided Dockerfile to install GCC, SCons, Python, and other required tools. Follow the professor's dependency instructions if anything is missing.
7. **Obtain the professor's setup files** — Locate the supplied `gem5_setup` directory containing the Dockerfiles, Makefile, scripts, and demos. Keep the full gem5 installation outside this repository.
8. **Build the Docker image** — From the host terminal in `gem5_setup`, run `make build` using the provided Makefile.
9. **Start the container** — From the same directory, run `make run`. Use `make shell` to enter the container when needed.
10. **Compile ARM gem5** — From the host terminal in `gem5_setup`, run `make gem5-build ISA=ARM TYPE=opt JOBS=4`. Adjust the job count and Docker memory allocation to suit your machine. If compilation runs out of memory, increase available memory or reduce parallel build jobs.
11. **Verify the executable** — Inside the container, locate the generated ARM `gem5.opt` executable and run it with `--help`, using its actual path. Confirm that it starts successfully before proceeding.

These commands depend on the professor-provided Makefile. Check its instructions if your version uses different targets or paths.

## Phase 2 — Benchmark and Experiment Setup

12. **Inspect matrix multiplication code**
    - Verify that both IJK and KIJ loop orders are available.
    - Confirm matrix sizes are configurable for 16×16, 32×32, and 64×64.
    - Check that both implementations produce the same correct result.
13. **Verify ARM simulation configuration**
    - Inspect the professor's gem5 scripts and test compatibility with the compiled ARM simulator.
    - Confirm that the benchmark executable targets the ARM ISA expected by the simulation.
14. **Run one baseline simulation**
    - Run a small matrix multiplication benchmark with the ARM configuration.
    - Confirm correct output, successful simulation completion, and a generated statistics file.
    - Record the command and configuration used so the baseline can be reproduced.
15. **Configure CPU widths**
    - Set up 2-wide, 4-wide, and 8-wide out-of-order CPU configurations.
    - Inspect the supported CPU parameters and record which pipeline widths are changed.
    - Keep other CPU, cache, memory, and clock settings consistent across width comparisons.
16. **Organize the GitHub repository**
    - Add benchmark code under `benchmarks/`, configuration scripts under `configs/`, and experiment scripts under `scripts/`.
    - Use `results/`, `analysis/`, and `docs/` for statistics, comparisons, and documentation.
    - Exclude the full gem5 source tree, compiled binaries, and Docker environment from version control.
17. **Verify statistics collection**
    - Identify available execution time, IPC, CPI, and stall metrics in the baseline statistics.
    - Record the exact statistic names, units, and CPU scope for the installed gem5 version.
    - If CPI must be derived, document the calculation as simulated CPU cycles divided by committed instructions.
    - Confirm that experiment scripts preserve each run's configuration and statistics separately.

Once these checks are complete, run the 18 planned experiments: two loop orders × three matrix sizes × three CPU widths.
