# Site Ops — deploy inside Frappe (/siteops) + installable PWA

## Deploy to Frappe (serves at siteops.localhost:8000/siteops)
    cd siteops-web-live
    npm install
    npm run build
    bash deploy_to_frappe.sh
    cd ~/frappe-bench && bench --site siteops.localhost clear-cache
    # restart bench start, then open http://siteops.localhost:8000/siteops

## Install as an app (PWA)
On desktop Chrome/Edge at /siteops: click the install icon in the address bar
("Install Site Ops Console"). It opens full-screen like a native app.
On Android: Chrome menu -> "Add to Home screen" / "Install app".
NOTE: phones require HTTPS for install (localhost is exempt on the PC).
For phone install, deploy the site with HTTPS (production) first.

## Dev mode still works
    npm run dev   ->  http://localhost:5173 (proxied to Frappe)
