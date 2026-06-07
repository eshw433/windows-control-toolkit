# Contributing to Windows Control Toolkit

Thank you for your interest in WCT! This project is a personal final project, but suggestions and improvements are welcome.

## How to Contribute

1. **Fork the repository**
2. **Create a branch** (`git checkout -b feature/my-feature`)
3. **Make changes** following the style guide below
4. **Run tests** (`pytest tests/`)
5. **Commit** with clear messages
6. **Open a Pull Request** using the provided template

## Style Guide

- **Python**: PEP 8, type hints where possible
- **Qt**: Use `QThread` for background work, never block UI
- **i18n**: Add keys to all 3 languages (EN, RU, AZ)
- **Database**: Use repositories in `db/repositories.py`, raw SQL only in migrations
- **UI**: Follow existing QSS patterns, test with all 6 themes

## Development Setup

```bash
pip install -r requirements.txt
python -m wct.main          # Run app
pytest tests/               # Run tests
python -m PyInstaller --onefile --windowed --name WCT src/wct/main.py  # Build
```

## Questions?

Open an issue or contact: @diver5 on Telegram
