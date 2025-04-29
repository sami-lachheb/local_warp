"""
Prompt engineering module.

This module provides functionality to create structured prompts for
generating shell commands from natural language requests.
"""

from typing import Dict, Any, List, Optional

from src.terminal.context import TerminalContext


def get_system_message() -> str:
    """
    Get the system message that instructs the model how to respond.
    
    Returns:
        A string containing the system message.
    """
    return """
You are a helpful terminal assistant that translates natural language requests into executable bash commands.

INSTRUCTIONS:
1. Your response should ONLY contain the bash command without any explanations, markdown formatting, or additional text. 
2. The user will confirm or reject your proposed command before execution.
3. Use the current working directory and terminal context provided to generate appropriate commands.
4. Choose the most efficient and correct command for the user's request.
5. Do not include ```bash, ```, or any other markdown formatting in your response.
6. Use appropriate flags and options for user-friendly output (e.g., -h for human-readable output in commands like ls -lh).

EXAMPLES:
Request: "Show me the largest files in this directory"
Response: find . -type f -exec du -h {} \\; | sort -rh | head -n 10

Request: "Create a backup of my config file"
Response: cp ~/.config/myapp/config.yaml ~/.config/myapp/config.yaml.bak

Request: "How much disk space do I have left"
Response: df -h
"""


def format_terminal_history(context: TerminalContext, max_commands: int = 5) -> str:
    """
    Format the terminal command history for inclusion in the prompt.
    
    Args:
        context: The terminal context containing command history.
        max_commands: Maximum number of recent commands to include.
        
    Returns:
        A formatted string with recent command history.
    """
    history = context.command_history[-max_commands:] if context.command_history else []
    
    if not history:
        return "No previous commands in history."
    
    history_text = "Recent commands:\n"
    for i, cmd in enumerate(history, 1):
        history_text += f"{i}. {cmd}\n"
    
    return history_text


def format_error_context(context: TerminalContext) -> str:
    """
    Format the last error message if any.
    
    Args:
        context: The terminal context containing the last error.
        
    Returns:
        A formatted string with the last error message, or empty string if none.
    """
    if context.last_error:
        return f"Last error message: {context.last_error}"
    return ""


def format_system_context(context: TerminalContext) -> str:
    """
    Format the system context information.
    
    Args:
        context: The terminal context containing system information.
        
    Returns:
        A formatted string with system context information.
    """
    return (
        f"OS: {context.os_name} {context.os_version}\n"
        f"Shell: {context.shell_name} {context.shell_version}\n"
        f"Host: {context.hostname}"
    )


def build_prompt(query: str, context: TerminalContext) -> str:
    """
    Build a complete prompt combining user query and terminal context.
    
    Args:
        query: The user's natural language request.
        context: The terminal context information.
        
    Returns:
        A complete prompt string for the language model.
    """
    # Always get fresh directory information
    context.update_working_directory()
    
    # Build each section of the prompt
    system_message = get_system_message()
    working_dir = f"Current working directory: {context.working_directory}"
    history = format_terminal_history(context)
    error = format_error_context(context)
    system_info = format_system_context(context)
    
    # Combine sections into final prompt
    prompt_parts = [
        system_message,
        "TERMINAL CONTEXT:",
        working_dir,
        history
    ]
    
    # Only add error context if there is an error
    if error:
        prompt_parts.append(error)
    
    prompt_parts.extend([
        system_info,
        "",
        "USER REQUEST:",
        query,
        "",
        "COMMAND:"
    ])
    
    return "\n".join(prompt_parts)

