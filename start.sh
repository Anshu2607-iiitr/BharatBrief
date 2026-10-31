#!/usr/bin/env bash
python worker.py &
python bot.py &
exec python -m streamlit run Home.py --server.port "${PORT:-8501}" --server.address 0.0.0.0 --server.headless true
