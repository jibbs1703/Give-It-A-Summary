#!/bin/sh
MODEL_NAME="granite4:350m"

ollama serve &
sleep 10
ollama pull $MODEL_NAME
tail -f /dev/null
