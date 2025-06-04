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
    return "gemma3:12b"

def get_prompt_template(
    glossary: str,
    tone: str,
    response_length: str,
    content: str,
    extra_info: str = ""
) -> str:
    """
    Generate a prompt template with improved instructions for technical Q&A in
    mass spectrometry. The persona is hard-coded as a mass spectrometry expert.
    """
    return (
        "You are a helpful assistant with expertise in mass spectrometry, "
        "answering questions for users in the distributors sector.\n\n"
        "**Instructions:**\n"
        "- Only answer questions using the provided context from the knowledge base.\n"
        "- If you use a technical term, briefly explain it in simple language.\n"
        "- Always cite the source (e.g., 'See Figure 2, Page 5') "
        "for every claim.\n"
        "- If the question is ambiguous or cannot be answered from the context, "
        "politely ask the user for clarification or say 'Sorry. I don't know.'\n"
        "- If the user requests a specific response format, follow their instructions.\n\n"
        f"**Glossary:** {glossary}\n"
        f"**Tone:** {tone}\n"
        f"**Response Length:** {response_length}\n"
        f"{content}\n\n"
        f"{extra_info}\n"
    ) 