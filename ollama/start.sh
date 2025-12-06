#!/bin/sh
MODEL_NAME="llama3.1:8B"  # Specify the model name here

ollama serve &
sleep 10
ollama pull $MODEL_NAME
tail -f /dev/null
