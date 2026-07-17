#!/bin/bash
# Deploy the built app INTO Frappe so it serves at http://siteops.localhost:8000/siteops
# Run from the siteops-web-live folder AFTER `npm run build`.
set -e
BENCH=~/frappe-bench
APP=$BENCH/apps/siteops/siteops

if [ ! -d dist ]; then echo "dist/ not found — run: npm run build"; exit 1; fi
if [ ! -d "$APP" ]; then echo "Frappe app not found at $APP"; exit 1; fi

# 1. copy built assets into the app's public folder (served at /assets/siteops/...)
rm -rf "$APP/public/frontend"
mkdir -p "$APP/public/frontend"
cp -r dist/* "$APP/public/frontend/"

# 2. the page route: /siteops  (www/siteops.html)
mkdir -p "$APP/www"
cp dist/index.html "$APP/www/siteops.html"

# 3. make sure the assets symlink exists (created on app install; recreate if missing)
if [ ! -e "$BENCH/sites/assets/siteops" ]; then
  ln -s "$APP/public" "$BENCH/sites/assets/siteops"
  echo "created assets symlink"
fi

echo ""
echo "Deployed. Now run:"
echo "  cd ~/frappe-bench && bench --site siteops.localhost clear-cache"
echo "  (restart bench start if running)"
echo "Then open: http://siteops.localhost:8000/siteops"
