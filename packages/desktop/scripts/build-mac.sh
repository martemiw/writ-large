#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# WritLarge — macOS build & install script
#
# What this does:
#   1. Converts build/icon.svg → build/icon.png → build/icon.icns
#   2. Builds the React renderer (Vite)
#   3. Packages everything as a native .app (electron-builder)
#   4. Installs WritLarge.app to ~/Applications
#
# First run:  chmod +x scripts/build-mac.sh && ./scripts/build-mac.sh
# Subsequent: ./scripts/build-mac.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "  W R I T L A R G E  —  macOS build"
echo "  ──────────────────────────────────"
echo ""

# ── 1. Dependencies ───────────────────────────────────────────────────────────
echo "→ Installing dependencies..."
npm install

# ── 2. Icon ───────────────────────────────────────────────────────────────────
if [ ! -f "build/icon.png" ]; then
  echo "→ Generating icon from SVG..."

  # qlmanage is built into macOS and can render SVG to PNG
  qlmanage -t -s 1024 -o /tmp "build/icon.svg" > /dev/null 2>&1 || true

  if [ -f "/tmp/icon.svg.png" ]; then
    mv /tmp/icon.svg.png build/icon.png
    echo "  icon.png created."
  else
    echo "  ⚠ Could not auto-generate icon — using Electron default."
    echo "    To set a custom icon, place a 1024×1024 PNG at build/icon.png"
    echo "    then re-run this script."
  fi
fi

# Convert PNG → ICNS using macOS built-in tools (sips + iconutil)
if [ -f "build/icon.png" ] && [ ! -f "build/icon.icns" ]; then
  echo "→ Building icon.icns..."
  ICONSET="build/icon.iconset"
  mkdir -p "$ICONSET"
  sips -z 16   16   build/icon.png --out "$ICONSET/icon_16x16.png"       > /dev/null
  sips -z 32   32   build/icon.png --out "$ICONSET/icon_16x16@2x.png"    > /dev/null
  sips -z 32   32   build/icon.png --out "$ICONSET/icon_32x32.png"       > /dev/null
  sips -z 64   64   build/icon.png --out "$ICONSET/icon_32x32@2x.png"    > /dev/null
  sips -z 128  128  build/icon.png --out "$ICONSET/icon_128x128.png"     > /dev/null
  sips -z 256  256  build/icon.png --out "$ICONSET/icon_128x128@2x.png"  > /dev/null
  sips -z 256  256  build/icon.png --out "$ICONSET/icon_256x256.png"     > /dev/null
  sips -z 512  512  build/icon.png --out "$ICONSET/icon_256x256@2x.png"  > /dev/null
  sips -z 512  512  build/icon.png --out "$ICONSET/icon_512x512.png"     > /dev/null
  sips -z 1024 1024 build/icon.png --out "$ICONSET/icon_512x512@2x.png"  > /dev/null
  iconutil -c icns "$ICONSET" -o build/icon.icns
  rm -rf "$ICONSET"
  echo "  icon.icns created."

  # Update package.json to use .icns (better quality on macOS)
  sed -i '' 's|"build/icon.png"|"build/icon.icns"|g' package.json
fi

# ── 3. Renderer build ─────────────────────────────────────────────────────────
echo "→ Building renderer..."
npm run build

# ── 4. Package ────────────────────────────────────────────────────────────────
echo "→ Packaging .app..."
npx electron-builder --mac --dir

# ── 5. Install ────────────────────────────────────────────────────────────────
echo "→ Installing to ~/Applications..."
mkdir -p ~/Applications
APP_SRC="$(find "$PROJECT_DIR/release" -maxdepth 2 -name "WritLarge.app" | head -1)"
APP_DST="$HOME/Applications/WritLarge.app"

[ -d "$APP_DST" ] && rm -rf "$APP_DST"
cp -r "$APP_SRC" "$APP_DST"

echo ""
echo "  ──────────────────────────────────────────────"
echo "  ✓  WritLarge.app installed to ~/Applications"
echo ""
echo "  Pin to Dock:"
echo "    1. Finder → Go → Home → Applications"
echo "    2. Drag WritLarge.app to your Dock"
echo ""
echo "  Launch now:"
echo "    open ~/Applications/WritLarge.app"
echo "  ──────────────────────────────────────────────"
echo ""
