# viva-nfsim

Process-bigraph wrapper for [BioNetGen](https://bionetgen.org/)/[NFSim](https://github.com/RuleWorld/nfsim) rule-based simulations.

Wraps NFSim network-free stochastic simulation as composable process-bigraph Processes. Includes a flagella assembly model demonstrating hierarchical complexation of ~30 proteins through 7 sequential reactions (237 rules), with standalone and composed workflow configurations.

**[View Interactive Demo Report](https://vivarium-collective.github.io/viva-nfsim/)** — flagella assembly with standalone complexation, composed steady production, and fast production (3x rate) configurations, including Plotly time series and bigraph architecture diagrams.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Requires `bionetgen` (installed automatically).

## Quick Start

```python
from process_bigraph import Composite, allocate_core
from process_bigraph.emitter import RAMEmitter
from pbg_nfsim import NFSimProcess, make_complexation_document

core = allocate_core()
core.register_link('nfsim', NFSimProcess)
core.register_link('ram-emitter', RAMEmitter)

doc = make_complexation_document(n_steps=100, interval=50.0)
sim = Composite({'state': doc}, core=core)
sim.run(500.0)

print(sim.state['species'])
```

### Composed Workflow (Production + Complexation)

```python
from pbg_nfsim import MonomerProduction, make_production_document

core.register_link('monomer-production', MonomerProduction)

doc = make_production_document(
    complexation_interval=50.0,
    production_rate_scale=1.0,
)
sim = Composite({'state': doc}, core=core)
sim.run(2000.0)
```

## API Reference

### Processes

| Process | Type | Description |
|---------|------|-------------|
| `NFSimProcess` | Process | Wraps BioNetGen/NFSim, returns delta changes in observables |
| `MonomerProduction` | Process | Produces monomers at constant rates |

### NFSimProcess

**Config:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `model_file` | string | (required) | Path to BNGL model file |
| `n_steps` | integer | 100 | NFSim output time points per interval |

**Ports:**

| Port | Direction | Schema | Description |
|------|-----------|--------|-------------|
| `observables` | input/output | `map[float]` | Observable molecule counts |

### MonomerProduction

**Config:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `production_rates` | map[float] | {} | Monomer name -> rate (molecules/s) |

**Ports:**

| Port | Direction | Schema | Description |
|------|-----------|--------|-------------|
| `monomers` | output | `map[float]` | Monomer production deltas |

### Composite Factories

| Function | Description |
|----------|-------------|
| `make_complexation_document()` | Standalone NFSim complexation |
| `make_production_document()` | Production + complexation composed |

## Architecture

```
Composed Workflow:
  production (MonomerProduction, interval=1s)
      └─ outputs.monomers ──> [species]
  complexation (NFSimProcess, interval=50s)
      ├─ inputs.observables <── [species]
      └─ outputs.observables ──> [species]
  emitter (RAMEmitter)
      └─ inputs.species <── [species]
```

The NFSimProcess uses a **bridge pattern**: each step reads current state, updates seed species in the BNGL template via regex substitution, runs NFSim in a temporary directory, and returns delta changes. "Seedable" observables (simple molecules) carry over between steps; growing intermediates with counter states do not.

## Demo Report

To regenerate locally:

```bash
python demo/demo_report.py
```

The report includes interactive Plotly charts showing three configurations:
1. Standalone assembly (fixed monomer pool)
2. Composed steady production + complexation
3. Composed fast production (3x rate)

## Tests

```bash
pytest tests/ -v
```
