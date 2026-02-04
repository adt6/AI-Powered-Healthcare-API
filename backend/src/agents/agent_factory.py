"""
Agent Factory for creating configured clinical AI assistants.
This combines all components to create a working AI assistant.
"""

import os
from datetime import datetime
from pathlib import Path

from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from . import agent_config


def load_and_format_instructions() -> str:
    """
    Load instructions from file or use fallback.
    This tells the AI how to behave as a clinical assistant.
    """
    if agent_config.INSTRUCTIONS_FILE_PATH.exists():
        with open(agent_config.INSTRUCTIONS_FILE_PATH, "r") as f:
            instructions = f.read()
    else:
        instructions = agent_config.FALLBACK_INSTRUCTIONS

    # Replace placeholders with current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    instructions = instructions.replace("{{CURRENT_DATE}}", current_date)

    return instructions


def get_llm(model_type=None):
    """
    Create and configure the LLM (Language Model) based on model_type or DEFAULT_LLM_TYPE.
    This is the "brain" of the AI assistant.

    Args:
        model_type (str, optional): The type of model to use. If None, uses DEFAULT_LLM_TYPE.
    """
    # Use provided model_type or fall back to DEFAULT_LLM_TYPE
    selected_model_type = model_type or agent_config.DEFAULT_LLM_TYPE

    # Choose model based on selected model type
    if selected_model_type == agent_config.OPENAI_LLM_TYPE:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")

        return ChatOpenAI(
            model=agent_config.MODEL_ID_OPENAI,  # gpt-4o-mini
            temperature=0.1,
            api_key=api_key,
        )

    elif selected_model_type == agent_config.SONNET_LLM_TYPE:
        # TODO: Add Anthropic Claude Sonnet support
        raise NotImplementedError(
            "Anthropic Claude Sonnet not implemented yet. Please use OPENAI_LLM_TYPE for now."
        )

    elif selected_model_type == agent_config.LLAMA_GROQ_LLM_TYPE:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Please set GROQ_API_KEY environment variable. Current value: {}".format(
                    "(empty)" if api_key == "" else "(not set)"
                )
            )

        # Ensure api_key is a string and not empty
        api_key = str(api_key).strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY is empty. Please set a valid API key.")

        llm = ChatGroq(
            model=agent_config.MODEL_ID_LLAMA_GROQ,  # llama-3.3-70b-versatile
            temperature=0.1,
            api_key=api_key,
        )
        return llm

    elif selected_model_type == agent_config.MIXTRAL_LLM_TYPE:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Please set GROQ_API_KEY environment variable. Current value: {}".format(
                    "(empty)" if api_key == "" else "(not set)"
                )
            )

        # Ensure api_key is a string and not empty
        api_key = str(api_key).strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY is empty. Please set a valid API key.")

        return ChatGroq(
            model=agent_config.MODEL_ID_MIXTRAL_GROQ,  # mixtral-8x7b-32768
            temperature=0.1,
            api_key=api_key,  # ChatGroq uses api_key parameter
        )

    elif selected_model_type == agent_config.HAIKU_LLM_TYPE:
        # TODO: Add Anthropic Claude Haiku support
        raise NotImplementedError(
            "Anthropic Claude Haiku not implemented yet. Please use MIXTRAL_LLM_TYPE for now."
        )

    elif selected_model_type == agent_config.GEMINI_LLM_TYPE:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Please set GEMINI_API_KEY environment variable.")

        # Import ChatGoogleGenerativeAI for Gemini support
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "Please install langchain-google-genai: pip install langchain-google-genai"
            )

        llm = ChatGoogleGenerativeAI(
            model=agent_config.MODEL_ID_GEMINI,  # gemini-2.5-flash
            temperature=0.1,
            google_api_key=api_key,
        )
        return llm

    else:
        raise ValueError(
            f"Unknown LLM type: {selected_model_type}. Please check agent_config.py"
        )


def create_assistant(model_type=None):
    """
    Main factory method - creates a fully configured AI assistant.
    This combines all components: instructions, LLM, tools, and prompts.

    Args:
        model_type (str, optional): The type of model to use. If None, uses DEFAULT_LLM_TYPE.
    """
    # Step 1: Load instructions (how the AI should behave)
    instructions = load_and_format_instructions()

    # Step 2: Create LLM (the AI brain)
    selected_model_type = model_type or agent_config.DEFAULT_LLM_TYPE
    llm = get_llm(model_type)

    # Step 3: Get tools (functions to call your API)
    from .tools import (
        get_patient_conditions,
        get_patient_encounters,
        get_patient_info,
        get_patient_observation_by_type,
        get_patient_observations,
        get_patient_summary,
        search_patients,
    )

    tools = [
        get_patient_info,
        search_patients,
        get_patient_conditions,
        get_patient_encounters,
        get_patient_observations,
        get_patient_observation_by_type,
        get_patient_summary,
    ]

    # Step 4: Prepare clinical instructions as system prompt
    # Instructions are loaded from clinical_instructions.md file
    # The file already contains all necessary instructions, so we use it directly
    system_prompt = instructions.strip()

    # Step 5: Create conversation memory (using MemorySaver for LangGraph)
    memory = MemorySaver()

    # Step 6: Create the agent using LangChain v1.0 API
    # create_agent returns a compiled graph that handles the conversation flow
    # It automatically binds tools to the LLM
    agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=memory,  # Use MemorySaver for conversation history
        debug=False,  # Enable debug mode to see tool calls
    )

    return agent_graph
