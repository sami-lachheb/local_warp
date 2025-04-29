"""
Terminal context capture module.

This module provides functionality to capture and manage terminal context
information such as working directory, command history, and system details.
"""

import os
import platform
import socket
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class TerminalContext:
    """
    Class to capture and store terminal context information.
    
    This includes working directory, shell information, system details,
    command history, and errors.
    """
    
    # System and environment information
    hostname: str = field(default_factory=socket.gethostname)
    os_name: str = field(default_factory=lambda: platform.system())
    os_version: str = field(default_factory=lambda: platform.release())
    shell_name: str = field(default="bash")
    shell_version: str = field(default="")
    
    # Dynamic state information
    working_directory: str = field(default_factory=os.getcwd)
    command_history: List[str] = field(default_factory=list)
    last_error: Optional[str] = None
    
    # Maximum number of commands to keep in history
    max_history: int = 10
    
    def update_working_directory(self) -> None:
        """Update the current working directory."""
        self.working_directory = os.getcwd()
    
    def add_command(self, command: str) -> None:
        """
        Add a command to the history.
        
        Args:
            command: The command to add to history
        """
        if command.strip():  # Only add non-empty commands
            self.command_history.append(command.strip())
            # Keep only the most recent commands based on max_history
            if len(self.command_history) > self.max_history:
                self.command_history = self.command_history[-self.max_history:]
    
    def set_last_error(self, error: str) -> None:
        """
        Set the last error message.
        
        Args:
            error: The error message to store
        """
        self.last_error = error
    
    def clear_last_error(self) -> None:
        """Clear the last error message."""
        self.last_error = None
    
    @property
    def previous_command(self) -> Optional[str]:
        """Get the most recent command from history, if available."""
        if self.command_history:
            return self.command_history[-1]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        
        Returns:
            A dictionary representation of the terminal context.
        """
        return {
            "system": {
                "hostname": self.hostname,
                "os": f"{self.os_name} {self.os_version}",
                "shell": f"{self.shell_name} {self.shell_version}",
                "timestamp": datetime.now().isoformat()
            },
            "terminal": {
                "working_directory": self.working_directory,
                "previous_commands": self.command_history,
                "last_error": self.last_error
            }
        }

    def __str__(self) -> str:
        """Return a string representation of the terminal context."""
        return (
            f"TerminalContext:\n"
            f"  Working Directory: {self.working_directory}\n"
            f"  Previous Command: {self.previous_command or 'None'}\n"
            f"  Last Error: {self.last_error or 'None'}\n"
            f"  System: {self.os_name} {self.os_version} ({self.hostname})\n"
            f"  Shell: {self.shell_name} {self.shell_version}"
        )


def get_terminal_context() -> TerminalContext:
    """
    Factory function to create and initialize a TerminalContext instance.
    
    Returns:
        A new TerminalContext instance with current system information.
    """
    # Try to get shell information from environment variables
    shell = os.environ.get("SHELL", "")
    shell_name = os.path.basename(shell) if shell else "unknown"
    
    context = TerminalContext(
        shell_name=shell_name,
        shell_version=""  # We'd need to execute a command to get the version
    )
    
    return context

