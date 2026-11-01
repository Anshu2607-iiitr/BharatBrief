#!/usr/bin/env bash
# Teen kaam ek server pe: worker (data + summary queue), Telegram bot, website.
# Bot ya worker crash ho to 10 sec baad apne aap dobara shuru (website chalti rahe, bot chupchaap band na ho).

keep_alive() {
  while true; do
    echo "[start] $1 shuru"
    python "$1"
    echo "[start] $1 ruk gaya (exit $?), 10 sec mein dobara"
    sleep 10
  done
}

keep_alive worker.py &
sleep 5                      # worker pehle DB bana le (WAL), phir bot
keep_alive bot.py &

exec python -m streamlit run Home.py --server.port "${PORT:-8501}" --server.address 0.0.0.0 --server.headless true
