#!/data/data/com.termux/files/usr/bin/bash
set -eu

cd "$(dirname "$0")"

pkg install -y python git

if [ ! -d "agency-agents/.git" ]; then
    git clone --depth 1 https://github.com/msitarzewski/agency-agents.git agency-agents
fi

exec python agency_agent.py
