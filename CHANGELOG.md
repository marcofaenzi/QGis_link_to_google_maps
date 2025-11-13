# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
