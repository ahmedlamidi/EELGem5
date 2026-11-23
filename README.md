
# EEL Project — gem5 Matrix Multiplication

## Project Overview

This project investigates whether software optimization can reduce the need for wider CPU hardware.

Using the **gem5 simulator**, we compare two matrix multiplication loop orders (**IJK and KIJ**) across different CPU issue widths and matrix sizes.

### Experiment Configurations

- **Loop orders:** IJK, KIJ
- **Matrix sizes:** 16×16, 32×32, 64×64
- **CPU widths:** 2-wide, 4-wide, 8-wide
- **Total experiments:** 18

**Performance metrics:** Execution time, IPC, CPI, speedup, cache miss rates, and stall statistics.

## Repository Structure

```text
eel_project/
│
├── benchmarks/     # IJK and KIJ matrix multiplication code
├── configs/        # gem5 CPU configuration scripts
├── scripts/        # Scripts to run all 18 experiments
├── results/        # Collected simulation statistics
├── analysis/       # Graphs, tables, and comparisons
├── docs/           # Project documentation
│
├── README.md       # Project overview and setup instructions
└── .gitignore      # Files excluded from version control
```

## Prerequisites

Before starting, make sure you have:

- **Git** — For cloning and managing the project repository.
- **Docker Desktop** — Installed and running.
- **Professor-provided `gem5_setup` folder** — Contains the Dockerfiles, Makefile, scripts, and example benchmarks.
- **Make** — Required to execute the setup commands.

The professor's Docker configuration handles the Linux environment and gem5 dependencies.

## gem5 Setup

See the [setup guide](docs/setup.md) for the full environment, benchmark, and experiment setup instructions (steps 1–17).

The [development log](docs/dev-log.md) records setup validation, encountered errors and fixes, preliminary results, and remaining work.

### 1. Clone the Project Repository

Clone this repository to your local machine.

### 2. Open the Professor's Setup Folder

Open Terminal and navigate to the provided `gem5_setup` directory.

```bash
cd /path/to/gem5_setup
```

### 3. Build the Docker Environment

```bash
make build
```

This builds the development Docker image for your machine's architecture.

### 4. Start the Container

```bash
make run
```

### 5. Enter the Container

```bash
make shell
```

### 6. Build gem5

From your Mac or host terminal, inside the `gem5_setup` directory:

```bash
make gem5-build ISA=ARM TYPE=opt JOBS=4
```

For an x86 target, use `ISA=X86` instead. Use the same target ISA and gem5 configuration across experiments to ensure consistent comparisons.

**Note:** These commands use the professor-provided Makefile. The gem5 source code, compiled binaries, and Docker environment are kept separate from the team repository.

## Running Experiments

Run from the `eel_project` folder on your computer (not inside the container). Recompile only when `mm_bench.c` changes:

```bash
docker exec gem5-dev bash -c 'gcc -O2 -fno-tree-vectorize -static -I/opt/gem5/include -o /workspace/programs/mm_bench_arm /workspace/eel_project/benchmarks/mm_bench.c /opt/gem5/util/m5/build/arm64/out/libm5.a -lm'
```

(`libm5.a` is built once with `docker exec gem5-dev bash -c 'cd /opt/gem5/util/m5 && scons arm64.CROSS_COMPILE= build/arm64/out/m5'`.)

Run all 18 experiments, then extract the results:

```bash
for w in 2 4 8; do for n in 16 32 64; do for k in ijk kij; do
  name="${k}_n${n}_w${w}"
  docker exec gem5-dev bash -c "mkdir -p /workspace/runs/$name && /opt/gem5/build/ARM/gem5.opt -d /workspace/runs/$name /workspace/eel_project/configs/01-simple.py --width $w --size $n --kernel $k > /workspace/runs/$name/program_output.log 2>&1"
done; done; done
cd ../runs
python3 ../eel_project/scripts/extract_stats.py *_n*_w*/ --csv all_runs.csv
grep "Max error" *_n*_w*/program_output.log   # all should be 0.00e+00
```

Extraction is not automatic. `scripts/extract_stats.py` writes a `summary.txt` into each run folder and, with `--csv`, one combined table.

**Reading `stats.txt` by hand:** use only the first block (the kernel; the second block also includes verification). Don't use `simInsts`, which isn't reset; use `commitStats0.numInsts`. Compare times with `simTicks`, since `simSeconds` is rounded.

## Team Workflow

1. Clone this repository.
2. Obtain the professor-provided `gem5_setup` folder.
3. Set up the gem5 environment using Docker.
4. Create a separate Git branch for your work.
5. Commit and push changes.
6. Open a pull request to merge changes into `main`.

## Project Status

**Current phase:** Measurement setup complete; next is setup step 15, then the 18 runs.
