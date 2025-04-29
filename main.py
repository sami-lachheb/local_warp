#!/usr/bin/env python3
"""
Terminal AI Assistant

A CLI application that uses the OpenRouter API with Mistral to generate
and execute shell commands from natural language requests.
"""

import os
import signal
import sys
from typing import Optional, NoReturn

# Try to import rich for colored output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from src.terminal.context import get_terminal_context, TerminalContext
from src.terminal.executor import CommandExecutor
from src.llm.openrouter import OpenRouterClient, AuthenticationError
from src.llm.prompt import build_prompt


# Global variables for clean shutdown
running = True
console = Console() if HAS_RICH else None


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""
    
    def handle_sigint(sig, frame):
        global running
        
        # Print a newline to avoid messing up the terminal prompt
        print("\n")
        
        if HAS_RICH:
            console.print("[yellow]Shutting down Terminal AI Assistant...[/yellow]")
        else:
            print("Shutting down Terminal AI Assistant...")
        
        running = False
        sys.exit(0)
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_sigint)


def print_welcome_message() -> None:
    """Display a welcome message when the application starts."""
    if HAS_RICH:
        title = Text("Terminal AI Assistant", style="bold blue")
        content = Text(
            "Ask me anything in natural language, and I'll generate a shell command for you.\n"
            "Type 'exit' or 'quit' to exit the program."
        )
        
        console.print(Panel.fit(
            title + "\n\n" + content,
            border_style="blue",
            padding=(1, 2),
            title="Welcome"
        ))
    else:
        print("\n=== Terminal AI Assistant ===")
        print(
            "Ask me anything in natural language, and I'll generate a shell command for you.\n"
            "Type 'exit' or 'quit' to exit the program.\n"
        )


def get_user_input(prompt: str = "What do you need help with? ") -> str:
    """
    Get input from the user with proper error handling.
    
    Args:
        prompt: The prompt to display to the user.
        
    Returns:
        The user's input, stripped of leading/trailing whitespace.
    """
    try:
        if HAS_RICH:
            # Using rich for a colored prompt
            console.print(f"[bold green]❯[/bold green] {prompt}", end="")
            return input()
        else:
            return input(f"❯ {prompt}")
    except (EOFError, KeyboardInterrupt):
        # Handle Ctrl+D (EOFError) or Ctrl+C (KeyboardInterrupt)
        print("\nExiting...")
        sys.exit(0)


def initialize_components() -> tuple[TerminalContext, OpenRouterClient, CommandExecutor]:
    """
    Initialize all required components.
    
    Returns:
        A tuple containing the initialized terminal context, OpenRouter client,
        and command executor.
        
    Raises:
        AuthenticationError: If the OpenRouter API key is missing or invalid.
    """
    # Initialize terminal context
    context = get_terminal_context()
    
    try:
        # Initialize OpenRouter client
        llm_client = OpenRouterClient()
        
        # Initialize command executor
        executor = CommandExecutor(context, use_colored_output=HAS_RICH)
        
        return context, llm_client, executor
        
    except AuthenticationError as e:
        if HAS_RICH:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            console.print(
                "\n[yellow]Please set your OpenRouter API key in the .env file:[/yellow]\n"
                "1. Create or edit the .env file in the project directory\n"
                "2. Add the line: [green]OPENROUTER_API_KEY=your_api_key_here[/green]\n"
                "3. Get your API key from [blue]https://openrouter.ai/keys[/blue]"
            )
        else:
            print(f"Error: {str(e)}")
            print(
                "\nPlease set your OpenRouter API key in the .env file:\n"
                "1. Create or edit the .env file in the project directory\n"
                "2. Add the line: OPENROUTER_API_KEY=your_api_key_here\n"
                "3. Get your API key from https://openrouter.ai/keys"
            )
        sys.exit(1)


def process_query(
    query: str,
    context: TerminalContext,
    llm_client: OpenRouterClient,
    executor: CommandExecutor
) -> None:
    """
    Process a user query by generating and executing a command.
    
    Args:
        query: The user's natural language query.
        context: The terminal context.
        llm_client: The OpenRouter API client.
        executor: The command executor.
    """
    try:
        # Display processing message
        if HAS_RICH:
            console.print("[cyan]Generating command...[/cyan]")
        else:
            print("Generating command...")
        
        # Build prompt with user query and context
        prompt = build_prompt(query, context)
        
        # Send prompt to LLM
        success, response = llm_client.generate_command(prompt)
        
        if not success:
            if HAS_RICH:
                console.print(f"[bold red]Error generating command:[/bold red] {response}")
            else:
                print(f"Error generating command: {response}")
            return
        
        # Execute the generated command with user confirmation
        result = executor.execute_command(response, require_confirmation=True)
        
        # Display the result
        executor.display_result(result)
        
    except Exception as e:
        if HAS_RICH:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        else:
            print(f"Error: {str(e)}")


def main() -> NoReturn:
    """Main entry point for the Terminal AI Assistant."""
    # Set up signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Display welcome message
    print_welcome_message()
    
    try:
        # Initialize components
        context, llm_client, executor = initialize_components()
        
        # Main loop
        while running:
            # Get user input
            query = get_user_input()
            
            # Check for exit commands
            if query.lower() in ('exit', 'quit', 'bye'):
                if HAS_RICH:
                    console.print("[yellow]Goodbye![/yellow]")
                else:
                    print("Goodbye!")
                break
            
            # Skip empty queries
            if not query.strip():
                continue
                
            # Process the query
            process_query(query, context, llm_client, executor)
            
    except Exception as e:
        if HAS_RICH:
            console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        else:
            print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

