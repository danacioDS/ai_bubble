#!/bin/sh
API_URL="${VITE_API_URL:-http://localhost:8000}"

cat > /usr/share/nginx/html/config.js <<EOF
window.__APP_CONFIG__ = {
  apiUrl: "${API_URL}"
};
EOF

nginx -g "daemon off;"
