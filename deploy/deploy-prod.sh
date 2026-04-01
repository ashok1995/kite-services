#!/bin/bash
# =============================================================================
# Deploy Kite Services to Production (GCP VM)
# Single prod deploy script. Uses gcloud; image from ghcr.io (CI builds on main).
# Config: deploy/.deploy.env (GCP_*, VM_HOST, GITHUB_TOKEN, optional KITE_*).
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "${SCRIPT_DIR}/.deploy.env" ] && . "${SCRIPT_DIR}/.deploy.env"

GCP_INSTANCE="${GCP_INSTANCE:?Set GCP_INSTANCE in deploy/.deploy.env}"
GCP_ZONE="${GCP_ZONE:?Set GCP_ZONE}"
GCP_PROJECT="${GCP_PROJECT:?Set GCP_PROJECT}"
VM_HOST="${VM_HOST:?Set VM_HOST}"
GITHUB_TOKEN="${GITHUB_TOKEN:?Set GITHUB_TOKEN (read:packages for ghcr.io)}"
KITE_API_KEY="${KITE_API_KEY:-}"
KITE_API_SECRET="${KITE_API_SECRET:-}"
PROJECT_DIR="${PROJECT_DIR:-/opt/kite-services}"
SERVICE_PORT="${SERVICE_PORT:-8179}"
GITHUB_REPO="${GITHUB_REPO:-ashok1995/kite-services}"

if ! command -v gcloud >/dev/null 2>&1; then
  for p in /opt/homebrew/share/google-cloud-sdk/bin "$HOME/google-cloud-sdk/bin"; do
    [ -x "${p}/gcloud" ] && export PATH="${p}:${PATH}" && break
  done
fi
[ -x "$(command -v gcloud 2>/dev/null)" ] || { echo "❌ gcloud not found. Install Google Cloud SDK."; exit 1; }

run_ssh() {
  if [ $# -eq 1 ] && [ ! -t 0 ]; then
    gcloud compute ssh "${GCP_INSTANCE}" --zone "${GCP_ZONE}" --project "${GCP_PROJECT}" -- bash -s
  else
    gcloud compute ssh "${GCP_INSTANCE}" --zone "${GCP_ZONE}" --project "${GCP_PROJECT}" -- "$@"
  fi
}
run_scp() {
  gcloud compute scp "$1" "${GCP_INSTANCE}:$2" --zone "${GCP_ZONE}" --project "${GCP_PROJECT}"
}

echo "============================================"
echo "  Kite Services — Production Deploy"
echo "============================================"
echo "  VM:     ${GCP_INSTANCE}"
echo "  Host:   http://${VM_HOST}:${SERVICE_PORT}"
echo "============================================"
echo ""

echo "📦 [1/4] Repo on VM (main)..."
run_ssh << EOF
  sudo mkdir -p ${PROJECT_DIR}
  sudo chown -R \$(whoami):\$(whoami) ${PROJECT_DIR} 2>/dev/null || true
  if ! command -v git >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo apt-get install -y -qq git
  fi
  cd ${PROJECT_DIR}
  if [ -d .git ]; then
    git remote set-url origin https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git 2>/dev/null || true
    git fetch origin main
    git checkout -B main FETCH_HEAD
    git reset --hard FETCH_HEAD
  else
    rm -rf ${PROJECT_DIR}/*
    GIT_TERMINAL_PROMPT=0 git clone --branch main --depth 1 https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git ${PROJECT_DIR}
  fi
  mkdir -p envs logs kite-credentials
  echo "   Commit: \$(git log -1 --oneline 2>/dev/null || echo '?')"
EOF

if [ -n "${KITE_API_KEY}" ] && [ -n "${KITE_API_SECRET}" ]; then
  echo ""
  echo "🔑 [2/4] Writing Kite credentials on VM..."
  KITE_JSON=$(printf '{"api_key":"%s","api_secret":"%s","access_token":""}' "${KITE_API_KEY}" "${KITE_API_SECRET}")
  TMP_TOKEN=$(mktemp)
  echo -n "$KITE_JSON" > "$TMP_TOKEN"
  run_ssh "mkdir -p ${PROJECT_DIR}/kite-credentials"
  run_scp "$TMP_TOKEN" "/tmp/kite_token.json"
  run_ssh "cp /tmp/kite_token.json ${PROJECT_DIR}/kite-credentials/kite_token.json && rm -f /tmp/kite_token.json"
  rm -f "$TMP_TOKEN"
  echo "   Done. Get token via GET /api/auth/login-url then PUT /api/auth/token"
else
  echo ""
  echo "⏭️  [2/4] Skipping credentials (set KITE_API_KEY + KITE_API_SECRET in .deploy.env to write)"
fi

echo ""
echo "🔐 [3/4] Docker login and pull..."
run_ssh << EOF
  cd ${PROJECT_DIR}
  echo "${GITHUB_TOKEN}" | sudo docker login ghcr.io -u ${GITHUB_REPO%%/*} --password-stdin 2>/dev/null || true
  sudo docker-compose -f docker-compose.prod.yml pull
  sudo docker-compose -f docker-compose.prod.yml stop kite-services
  sudo docker-compose -f docker-compose.prod.yml rm -f kite-services
  sudo docker-compose -f docker-compose.prod.yml up -d kite-services
  echo "   kite-services restarted"
EOF

echo ""
echo "✅ [4/4] Verify..."
sleep 12
if curl -sf "http://${VM_HOST}:${SERVICE_PORT}/health" >/dev/null 2>&1; then
  echo "✅ Prod OK: http://${VM_HOST}:${SERVICE_PORT}/health"
else
  echo "⚠️  Health check failed; check VM logs"
  exit 1
fi
echo ""
echo "  SSH:  gcloud compute ssh ${GCP_INSTANCE} --zone ${GCP_ZONE} --project ${GCP_PROJECT}"
echo "  Logs: ... -- 'sudo docker-compose -f ${PROJECT_DIR}/docker-compose.prod.yml logs -f'"
echo ""
