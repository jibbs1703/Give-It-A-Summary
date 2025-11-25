#!/bin/sh
ollama serve &
sleep 10
ollama pull llama3.1:7B
tail -f /dev/null