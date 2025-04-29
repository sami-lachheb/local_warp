"""
Terminal command execution module.

This module provides functionality to safely execute shell commands
with proper error handling and user confirmation.
"""

import shlex
import subprocess
from dataclasses import dataclass
from typing import Tuple, Optional, List, Dict, Any

from src.terminal.context import TerminalContext

try:
    # Optional import for colored output
    from rich.console import Console
    from rich.syntax import Syntax
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


@dataclass
class CommandResult:
    """
    Class to store the result of a command execution.
    
    Attributes:
        success: Whether the command executed successfully
        command: The command that was executed
        stdout: Standard output from the command
        stderr: Standard error from the command
        return_code: The return code of the command
    """
    success: bool
    command: str
    stdout: str
    stderr: str
    return_code: int


class CommandExecutor:
    """
    Class to safely execute shell commands with user confirmation.
    
    This class handles command execution, confirmation prompts,
    and terminal context updates.
    """
    
    def __init__(self, context: TerminalContext, use_colored_output: bool = True):
        """
        Initialize the command executor.
        
        Args:
            context: The terminal context to update with command results.
            use_colored_output: Whether to use colored output via Rich (if available).
        """
        self.context = context
        self.use_colored_output = use_colored_output and HAS_RICH
        
        if self.use_colored_output:
            self.console = Console()
    
    def display_command(self, command: str) -> None:
        """
        Display the command to be executed with optional syntax highlighting.
        
        Args:
            command: The command to display.
        """
        print("\nProposed command:")
        
        if self.use_colored_output:
            # Display the command with syntax highlighting if Rich is available
            syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
            self.console.print(syntax)
        else:
            # Simple display without Rich
            print(f"  $ {command}")
        
        print()  # Add a blank line for readability
    
    def ask_confirmation(self, command: str) -> bool:
        """
        Ask the user for confirmation before executing a command.
        
        Args:
            command: The command to be executed.
            
        Returns:
            True if the user confirms, False otherwise.
        """
        self.display_command(command)
        
        while True:
            response = input("Execute this command? [y/n]: ").strip().lower()
            
            if response in ('y', 'yes'):
                return True
            elif response in ('n', 'no'):
                return False
            else:
                print("Please enter 'y' or 'n'.")
    
    def execute_command(
        self, 
        command: str, 
        timeout: Optional[int] = 60,
        require_confirmation: bool = True
    ) -> CommandResult:
        """
        Execute a shell command safely.
        
        Args:
            command: The command to execute.
            timeout: Timeout in seconds for command execution, None for no timeout.
            require_confirmation: Whether to require user confirmation before execution.
            
        Returns:
            CommandResult object containing the result of the execution.
        """
        # Add command to history regardless of execution
        self.context.add_command(command)
        
        # Check if confirmation is required and ask for it
        if require_confirmation and not self.ask_confirmation(command):
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr="Command execution cancelled by user.",
                return_code=-1
            )
        
        try:
            # Execute the command using subprocess
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                executable='/bin/bash'  # Explicitly use bash
            )
            
            # Wait for the process to complete, with optional timeout
            stdout, stderr = process.communicate(timeout=timeout)
            return_code = process.returncode
            
            # Update terminal context based on result
            if return_code != 0:
                self.context.set_last_error(stderr.strip())
            else:
                self.context.clear_last_error()
            
            return CommandResult(
                success=return_code == 0,
                command=command,
                stdout=stdout.strip(),
                stderr=stderr.strip(),
                return_code=return_code
            )
            
        except subprocess.TimeoutExpired:
            # Handle command timeout
            try:
                process.kill()
            except Exception:
                pass
                
            error_msg = f"Command timed out after {timeout} seconds."
            self.context.set_last_error(error_msg)
            
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr=error_msg,
                return_code=-1
            )
            
        except Exception as e:
            # Handle any other exceptions
            error_msg = f"Error executing command: {str(e)}"
            self.context.set_last_error(error_msg)
            
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr=error_msg,
                return_code=-1
            )
    
    def display_result(self, result: CommandResult) -> None:
        """
        Display the result of command execution.
        
        Args:
            result: The CommandResult object containing execution results.
        """
        if not result.success:
            # Command failed or was cancelled
            print("\nCommand failed or was cancelled.")
            
            if result.stderr:
                print("\nError output:")
                if self.use_colored_output:
                    self.console.print(f"[bold red]{result.stderr}[/bold red]")
                else:
                    print(result.stderr)
        else:
            # Command succeeded
            if result.stdout:
                print("\nOutput:")
                if self.use_colored_output:
                    # Use syntax highlighting for output that looks like it might be code
                    # This is a simple heuristic and could be improved
                    if any(char in result.stdout for char in ';{}()[]/\\'):
                        syntax = Syntax(result.stdout, "bash", theme="monokai", line_numbers=False)
                        self.console.print(syntax)
                    else:
                        print(result.stdout)
                else:
                    print(result.stdout)
            else:
                print("\nCommand executed successfully with no output.")
        
        print()  # Add a blank line for readability

