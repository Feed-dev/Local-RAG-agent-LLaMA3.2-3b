import logging
from typing import List, Tuple
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from utils.llm import OllamaLLM, OllamaLLMForJson
from utils.retriever import create_retriever
from utils.tools import create_web_search_tool
from utils.state import GraphState
from utils.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = Config()

def create_agent(retriever, web_search_tool):
    workflow = StateGraph(GraphState)
    
    # Define nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("web_search", web_search)
    workflow.add_node("generate_answer", generate_answer)

    # Define entry
    workflow.set_entry_point("retrieve")
    
    # Define edges and logic
    workflow.add_edge("retrieve", "web_search")
    workflow.add_edge("web_search", "generate_answer")
    workflow.add_edge("generate_answer", END)

    # Initialize the state
    initial_state = GraphState(
        question="",
        context=[],
        current_step="",
        final_answer="",
        retriever=retriever,
        web_search_tool=web_search_tool,
        error=None
    )

    return workflow.compile()

def retrieve(state: GraphState) -> GraphState:
    try:
        logger.info("Starting retrieval process")
        query = state["question"]
        docs = state["retriever"].get_relevant_documents(query)
        state["context"].extend([doc.page_content for doc in docs])
        state["current_step"] = "retrieve"
        logger.info(f"Retrieved {len(docs)} documents")
        return state
    except Exception as e:
        logger.error(f"Error in retrieve function: {str(e)}")
        state["error"] = str(e)
    finally:
        return state

def web_search(state: GraphState) -> GraphState:
    try:
        logger.info("Starting web search process")
        query = state["question"]
        search_results = state["web_search_tool"].run(query)
        state["context"].extend(search_results)
        state["current_step"] = "web_search"
        logger.info(f"Web search completed, added {len(search_results)} results")
        return state
    except Exception as e:
        logger.error(f"Error in web_search function: {str(e)}")
        state["error"] = str(e)
    finally:
        return state


def generate_answer(state: GraphState) -> GraphState:
    try:
        logger.info("Starting answer generation process")
        llm = OllamaLLM(model=config.OLLAMA_MODEL)

        # Convert all context items to strings
        context_strings = []
        for item in state["context"]:
            if isinstance(item, dict):
                # If the item is a dictionary, convert it to a string representation
                context_strings.append(str(item))
            elif isinstance(item, str):
                context_strings.append(item)
            else:
                # For any other type, convert to string
                context_strings.append(str(item))

        prompt = ChatPromptTemplate.from_template(
            "Based on the following context, answer the question: {question}\n\nContext: {context}"
        )

        chain = prompt | llm
        response = chain.invoke({
            "question": state["question"],
            "context": "\n".join(context_strings)
        })

        state["final_answer"] = response
        state["current_step"] = "generate_answer"
        logger.info("Answer generation completed")
        return state
    except Exception as e:
        logger.error(f"Error in generate_answer function: {str(e)}")
        state["error"] = str(e)
    finally:
        return state
