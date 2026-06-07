# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.2.x   | :white_check_mark: |
| < 2.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in WCT, please report it responsibly:

1. **Do not** open a public issue
2. Contact the author directly via Telegram: @diver5
3. Provide a clear description and steps to reproduce
4. Allow reasonable time for a fix before public disclosure

## Security Features

- All data stored locally in `%LOCALAPPDATA%`
- No cloud telemetry or external API calls
- Optional updater only checks GitHub Releases
- Firewall rules prefixed with `WCT_` to avoid conflicts
- Quarantine prevents accidental deletion
- System processes whitelisted by default

## Known Limitations

- Admin rights required for Windows Firewall rule creation
- `netsh` is used for firewall integration
- WMI queries used for USB detection
