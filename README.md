
# Local RAG agent with LLaMA3.2-3b
## We'll combine ideas from paper RAG papers into a RAG agent:
- Routing: Adaptive RAG (paper). Route questions to different retrieval approaches
- Fallback: Corrective RAG (paper). Fallback to web search if docs are not relevant to query
- Self-correction: Self-RAG (paper). Fix answers w/ hallucinations or don’t address question
