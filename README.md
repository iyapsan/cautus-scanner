# Cautus Scanner

Low-latency, deterministic stock scanner for momentum trading.

## Features

- **5 Pillar System**: Price, Momentum, Volume, Catalyst, Float
- **IBKR Integration**: Real-time market data via Interactive Brokers
- **Provider Abstraction**: Swap data sources without touching pillar logic
- **Performance**: <500ms scan cycles via pre-computed caching

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest tests/unit_tests/ -v
```

## Configuration

Copy `scanner.yaml.example` to `scanner.yaml` and configure:

```yaml
providers:
  market_data:
    type: ibkr
    host: 127.0.0.1
    port: 7497
```

## Architecture

See `docs/` for detailed documentation.
