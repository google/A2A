docker build -f samples/python/agents/langgraph/Dockerfile -t langgraph-agent .
docker run --rm -e GOOGLE_API_KEY=your_api_key langgraph-agent
