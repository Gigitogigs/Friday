"""
Ollama Client for Friday.

Provides a simple interface to communicate with the local Ollama instance.
All LLM interactions go through this client.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Generator
from pathlib import Path


@dataclass
class Message:
    """Represents a chat message."""
    role: str  # "system", "user", or "assistant"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResponse:
    """Response from the Ollama API."""
    content: str
    model: str
    done: bool
    total_duration: Optional[int] = None
    eval_count: Optional[int] = None
    
    @property
    def tokens_per_second(self) -> Optional[float]:
        """Calculate tokens per second if data is available."""
        if self.eval_count and self.total_duration:
            # Duration is in nanoseconds
            seconds = self.total_duration / 1_000_000_000
            return self.eval_count / seconds if seconds > 0 else None
        return None


class OllamaClient:
    """
    Client for interacting with local Ollama instance.
    
    This client uses the Ollama CLI/API to communicate with locally running models.
    It supports both synchronous and streaming responses.
    """
    
    def __init__(
        self,
        model: str = "deepseek-r1:1.5b",
        host: str = "http://localhost:11434",
        timeout: int = 120
    ):
        """
        Initialize the Ollama client.
        
        Args:
            model: Name of the model to use
            host: Ollama API host URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.host = host
        self.timeout = timeout
        self._conversation_history: List[Message] = []
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available and running.
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models.
        
        Returns:
            List of model names
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )
            if result.returncode != 0:
                return []
            
            models = []
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            return models
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []
    
    def model_exists(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model_name: Model to check (defaults to self.model)
            
        Returns:
            True if model exists, False otherwise
        """
        model = model_name or self.model
        models = self.list_models()
        
        # Check exact match or prefix match (e.g., "deepseek-r1:1.5b" matches "deepseek-r1:1.5b")
        for m in models:
            if m == model or m.startswith(model.split(":")[0]):
                return True
        return False
    
    def _filter_reasoning(self, text: str) -> str:
        """
        Filter out reasoning/thinking process from DeepSeek R1 responses.
        
        DeepSeek R1 models output their reasoning in a specific format.
        This method extracts only the final answer.
        
        Args:
            text: Raw model output
            
        Returns:
            Filtered text with only the final answer
        """
        # DeepSeek R1 typically wraps reasoning in specific patterns
        # Common patterns: "Thinking...", "...done thinking.", or between <think> tags
        
        # Remove "Thinking..." prefix and "...done thinking." suffix
        lines = text.split('\n')
        filtered_lines = []
        skip_thinking = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Skip lines that indicate thinking process
            if 'thinking...' in line_lower or 'okay, so' in line_lower:
                skip_thinking = True
                continue
            
            if '...done thinking.' in line_lower or 'done thinking' in line_lower:
                skip_thinking = False
                continue
            
            # Skip empty lines during thinking
            if skip_thinking:
                continue
            
            # Keep non-thinking lines
            if line.strip():
                filtered_lines.append(line)
        
        result = '\n'.join(filtered_lines).strip()
        
        # If filtering removed everything, return original
        if not result:
            return text
        
        return result
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> ChatResponse:
        """
        Send a chat request to Ollama.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            ChatResponse with the model's reply
        """
        # Build the prompt
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")
        
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        
        prompt = "\n".join(prompt_parts)
        prompt += "\nAssistant:"
        
        try:
            # Use ollama run command with UTF-8 encoding
            result = subprocess.run(
                [
                    "ollama", "run", self.model,
                    prompt
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of crashing
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                return ChatResponse(
                    content=f"Error: {result.stderr or 'Unknown error'}",
                    model=self.model,
                    done=True
                )
            
            # Check if stdout is None
            if result.stdout is None:
                return ChatResponse(
                    content="Error: No response from model",
                    model=self.model,
                    done=True
                )
            
            # Filter out reasoning/thinking process
            filtered_content = self._filter_reasoning(result.stdout.strip())
            
            return ChatResponse(
                content=filtered_content,
                model=self.model,
                done=True
            )
            
        except subprocess.TimeoutExpired:
            return ChatResponse(
                content="Error: Request timed out",
                model=self.model,
                done=True
            )
        except FileNotFoundError:
            return ChatResponse(
                content="Error: Ollama not found. Please install Ollama.",
                model=self.model,
                done=True
            )
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a response for a single prompt.
        
        This is a simpler interface for one-off requests.
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            
        Returns:
            The model's response text
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, system_prompt=system_prompt, temperature=temperature)
        return response.content
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self._conversation_history.clear()
    
    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self._conversation_history.append(Message(role=role, content=content))
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the conversation history as a list of dicts."""
        return [msg.to_dict() for msg in self._conversation_history]
    
    def switch_model(self, model: str) -> bool:
        """
        Switch to a different model.
        
        Args:
            model: Name of the model to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        if self.model_exists(model):
            self.model = model
            return True
        return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        try:
            result = subprocess.run(
                ["ollama", "show", self.model],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )
            
            if result.returncode != 0:
                return {"name": self.model, "error": result.stderr}
            
            return {
                "name": self.model,
                "info": result.stdout.strip()
            }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"name": self.model, "error": "Could not get model info"}
    
    def pull_model(self, model: str) -> bool:
        """
        Pull a model from Ollama registry.
        
        This is a blocking operation that may take a while.
        
        Args:
            model: Model name to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=600  # 10 minutes for large models
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
