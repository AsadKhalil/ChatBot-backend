import os
from app.src import constants

def get_prompt_params() -> dict:
    """
    Get prompt parameters from environment variables with defaults.
    
    Returns:
        dict: Dictionary containing prompt parameters
    """
    return {
        "persona": "helpful assistant",
        "glossary": "",
        "tone": "professional",
        "response_length": "concise",
        "content": "",
    }

def get_project_extra_info(project_name: str) -> str:
    """
    Get extra information based on the project name.
    
    Args:
        project_name: The name of the project
        
    Returns:
        str: Extra information for the prompt
    """
    if project_name == "naw":
        return f"""
        Here are the two books that you have access to:

        Outlines:

        FTFOC - Innovate to Dominate:
        {constants.OUTLINE_FTFOC_Innovate_to_Dominate}

        Mergers and Acquisitions:
        {constants.OUTLINE_Mergers_and_Acquisitions}
        """
    return ""

def get_model_config(use_openai: bool = True) -> str:
    """
    Get the default model name based on whether using OpenAI or Ollama.
    
    Args:
        use_openai: Whether to use OpenAI models
        
    Returns:
        str: Default model name
    """
    return "gpt-3.5-turbo" if use_openai else "gemma3:1b"

def get_prompt_template(persona: str, glossary: str, tone: str, response_length: str, content: str, extra_info: str = "") -> str:
    """
    Generate a prompt template with the given parameters.
    
    Args:
        persona: The persona to use for the response
        glossary: The glossary to use for the response
        tone: The tone to use for the response
        response_length: The desired length of the response
        content: Additional instructions for the response
        extra_info: Any extra information to include in the prompt
        
    Returns:
        str: The formatted prompt template
    """
    return f"""
    You are a {persona} and your job is to answer the user's questions.\
    Your job is to cater to the distributors sector.\
    You can only answer questions related to the data that you retrieve from semantic search.
    Keep the length of the response {response_length}
    the tone of the response should be {tone}
    Here is the glossary for {glossary}
    Here are some extra instructions:
    {content}

    Provide a reference for every claim that you make\
    If you cannot answer the question, just say "Sorry. I don't know."\
    If the user provides specific instructions about response format, follow them.

    {extra_info}
    """ 