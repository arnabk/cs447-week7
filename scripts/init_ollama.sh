#!/bin/sh

# Ollama initialization script
# This script downloads and sets up the required models

set -e

echo "🤖 Initializing Ollama models..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
until curl -f http://$OLLAMA_HOST/api/tags >/dev/null 2>&1; do
  echo "Ollama is unavailable - sleeping"
  sleep 5
done

echo "✅ Ollama is ready"

# Check if models are already downloaded
echo "🔍 Checking existing models..."
EXISTING_MODELS=$(curl -s http://$OLLAMA_HOST/api/tags | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g' || echo "")

# Function to download model if not exists
download_model() {
    local model_name=$1
    local model_description=$2
    
    if echo "$EXISTING_MODELS" | grep -q "$model_name"; then
        echo "✅ Model $model_name already exists"
    else
        echo "📥 Downloading $model_name ($model_description)..."
        curl -X POST http://$OLLAMA_HOST/api/pull -d "{\"name\": \"$model_name\"}"
        echo "✅ Downloaded $model_name"
    fi
}

# Download required models
download_model "llama3.1" "Theme extraction model (4.7GB)"
download_model "nomic-embed-text" "Embedding model (274MB)"

# Verify models are working
echo "🔍 Verifying models..."

# Test llama3.1
echo "🧪 Testing llama3.1..."
TEST_RESPONSE=$(curl -s -X POST http://$OLLAMA_HOST/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Hello",
    "stream": false
  }' | grep -o '"response":"[^"]*"' | sed 's/"response":"//g' | sed 's/"//g' 2>/dev/null || echo "")

if [ -n "$TEST_RESPONSE" ]; then
    echo "✅ llama3.1 is working"
else
    echo "❌ llama3.1 test failed"
    exit 1
fi

# Test nomic-embed-text
echo "🧪 Testing nomic-embed-text..."
EMBEDDING_RESPONSE=$(curl -s -X POST http://$OLLAMA_HOST/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "prompt": "test"
  }' | grep -o '"embedding":\[[^]]*\]' | grep -o ',' | wc -l 2>/dev/null || echo "0")

if [ "$EMBEDDING_RESPONSE" -gt 700 ]; then
    echo "✅ nomic-embed-text is working ($EMBEDDING_RESPONSE dimensions)"
else
    echo "❌ nomic-embed-text test failed (got $EMBEDDING_RESPONSE dimensions)"
    exit 1
fi

# Show model information
echo "📊 Model information:"
curl -s http://$OLLAMA_HOST/api/tags | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g'

echo "🎉 Ollama initialization complete!"
echo "📋 Available models:"
curl -s http://$OLLAMA_HOST/api/tags | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g'
