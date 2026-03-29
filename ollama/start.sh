#!/bin/sh
MODEL_1="qwen3:0.6b"
MODEL_2="granite4:350m"

ollama serve &
sleep 10
ollama pull $MODEL_1
ollama pull $MODEL_2
sleep 10
tail -f /dev/null
