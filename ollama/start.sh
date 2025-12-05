#!/bin/sh
ollama serve &
sleep 10
ollama pull llama3.1:8B
tail -f /dev/null