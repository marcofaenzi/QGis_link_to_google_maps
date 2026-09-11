# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2026-09-11
### Added
- Google Earth Web action: open the clicked location in Google Earth in the browser (thanks to [@Txito-alpha](https://github.com/Txito-alpha)).

## [1.0.4] - 2026-09-11
### Added
- Spanish translation (`es`): `LinkToGoogleMaps_es.ts` / `.qm` and update of translation build script.

### Fixed
- Use fully scoped Qt / QGIS enums for Qt6 / QGIS 4 plugin checker compliance (ToolButtonStyle, ToolButtonPopupMode, InsertPolicy, StandardButton, DialogCode, IconType).
- Replace bare `except Exception: pass` with specific handlers / `QgsMessageLog` (Bandit B110).

## [1.0.3] - 2026-04-27
### Added
- Catalan translation (`ca`): `LinkToGoogleMaps_ca.ts` / `.qm` and update of translation build script.

## [1.0.2] - 2026-04-27
### Security
- Hardened Nominatim request validation before `urlopen`: explicit allowlist for HTTPS and trusted host only, with targeted Bandit suppression (`B310`) on the guarded call.

## [1.0.1] - 2025-03-05
### Added
- Qt6 / QGIS 4 compatibility: use `qgis.PyQt` shim for `QDesktopServices` and `QUrl` (no direct PyQt5 import).
- `qgisMaximumVersion=4.99` in metadata for QGIS 4 Ready Plugins list.

### Changed
- Version 1.0.1 for QGIS 3.x and QGIS 4.x.

## [0.2.5] - 2025-03-05
### Changed
- Version bump 0.2.5.

## [0.2.4] - 2025-03-05
### Security
- Audit URL scheme for Nominatim requests: only HTTPS is allowed before calling `urlopen` (Bandit compliance).

## [0.2] - 2025-01-01
### Added
- Added Street View support: new dropdown option to open the nearest Street View location in the browser.
- Dynamic toolbar button: icon and tooltip change based on selected action (copy, open in browser, or Street View).
- Multiple action modes in dropdown menu with corresponding icons.
- Updated to use non-deprecated `QgsCoordinateReferenceSystem.fromEpsgId(4326)` for better compatibility.

### Changed
- Improved user interface with a more flexible button system.
- Enhanced metadata for official QGIS plugin repository submission.

### Fixed
- Fixed deprecated constructor warning for `QgsCoordinateReferenceSystem`.

## [0.1] - 2025-01-01
### Added
- Initial release: basic functionality to copy Google Maps link to clipboard from clicked map position.
- Automatic WGS84 reprojection from any project CRS.
- Toolbar button with click-to-copy action.

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A
