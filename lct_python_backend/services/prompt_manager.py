"""
Prompt Manager Service
Week 9: Prompts Configuration System

Manages loading, rendering, versioning, and hot-reloading of prompt templates
from prompts.json configuration file.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil
from string import Template
import hashlib


class PromptManager:
    """
    Centralized manager for LLM prompts

    Features:
    - Load prompts from prompts.json
    - Render templates with variable substitution
    - Save prompt changes with versioning
    - Hot-reload on file changes
    - History tracking
    """

    def __init__(self, prompts_file: str = "prompts.json", history_dir: str = "prompts_history"):
        self.prompts_file = Path(prompts_file)
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)

        self._prompts_cache = None
        self._file_mtime = None

        # Load prompts on initialization
        self.reload()

    def reload(self) -> None:
        """Reload prompts from file (hot-reload support)"""
        if not self.prompts_file.exists():
            raise FileNotFoundError(f"Prompts file not found: {self.prompts_file}")

        with open(self.prompts_file, 'r') as f:
            self._prompts_cache = json.load(f)

        self._file_mtime = self.prompts_file.stat().st_mtime

    def _check_reload(self) -> None:
        """Check if file has changed and reload if needed"""
        if self.prompts_file.exists():
            current_mtime = self.prompts_file.stat().st_mtime
            if current_mtime != self._file_mtime:
                self.reload()

    def get_prompts_config(self) -> Dict[str, Any]:
        """
        Get complete prompts configuration

        Returns:
            Full prompts.json content
        """
        self._check_reload()
        return self._prompts_cache.copy()

    def get_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """
        Get a specific prompt configuration

        Args:
            prompt_name: Name of the prompt (e.g., "initial_clustering")

        Returns:
            Prompt configuration dict

        Raises:
            KeyError: If prompt not found
        """
        self._check_reload()

        if prompt_name not in self._prompts_cache.get("prompts", {}):
            raise KeyError(f"Prompt not found: {prompt_name}")

        return self._prompts_cache["prompts"][prompt_name].copy()

    def render_prompt(self, prompt_name: str, variables: Dict[str, Any]) -> str:
        """
        Render a prompt template with variable substitution

        Args:
            prompt_name: Name of the prompt
            variables: Dictionary of variables to substitute

        Returns:
            Rendered prompt string

        Example:
            >>> pm = PromptManager()
            >>> rendered = pm.render_prompt("initial_clustering", {
            ...     "utterance_count": 50,
            ...     "participant_count": 3,
            ...     "participants": "Alice, Bob, Carol",
            ...     "transcript": "..."
            ... })
        """
        prompt_config = self.get_prompt(prompt_name)
        template_str = prompt_config.get("template", "")

        # Use string.Template for safe variable substitution
        # Supports $variable and ${variable} syntax
        template = Template(template_str)

        try:
            rendered = template.substitute(variables)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(
                f"Missing required variable '{missing_var}' for prompt '{prompt_name}'"
            )

        return rendered

    def get_prompt_metadata(self, prompt_name: str) -> Dict[str, Any]:
        """
        Get prompt metadata (model, temperature, etc.) without template

        Args:
            prompt_name: Name of the prompt

        Returns:
            Metadata dict with model, temperature, max_tokens, etc.
        """
        prompt_config = self.get_prompt(prompt_name)

        return {
            "description": prompt_config.get("description", ""),
            "model": prompt_config.get("model", self._prompts_cache.get("defaults", {}).get("default_model", "gpt-4")),
            "temperature": prompt_config.get("temperature", self._prompts_cache.get("defaults", {}).get("default_temperature", 0.5)),
            "max_tokens": prompt_config.get("max_tokens", self._prompts_cache.get("defaults", {}).get("default_max_tokens", 2000)),
            "output_format": prompt_config.get("output_format", "json"),
            "constraints": prompt_config.get("constraints", {}),
            "few_shot_examples": prompt_config.get("few_shot_examples", [])
        }

    def list_prompts(self) -> List[str]:
        """
        List all available prompt names

        Returns:
            List of prompt names
        """
        self._check_reload()
        return list(self._prompts_cache.get("prompts", {}).keys())

    def save_prompt(
        self,
        prompt_name: str,
        prompt_config: Dict[str, Any],
        user_id: str = "system",
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        Save or update a prompt configuration with versioning

        Args:
            prompt_name: Name of the prompt
            prompt_config: New prompt configuration
            user_id: User making the change
            comment: Comment describing the change

        Returns:
            Dict with success status and version info
        """
        self._check_reload()

        # Create version backup before modifying
        if prompt_name in self._prompts_cache.get("prompts", {}):
            old_version = self._prompts_cache["prompts"][prompt_name].copy()
            self._save_version(prompt_name, old_version, user_id, comment, "update")
        else:
            self._save_version(prompt_name, {}, user_id, comment, "create")

        # Update prompts cache
        if "prompts" not in self._prompts_cache:
            self._prompts_cache["prompts"] = {}

        self._prompts_cache["prompts"][prompt_name] = prompt_config
        self._prompts_cache["last_updated"] = datetime.now().isoformat()

        # Save to file
        self._save_to_file()

        return {
            "success": True,
            "prompt_name": prompt_name,
            "version_saved": True,
            "timestamp": datetime.now().isoformat()
        }

    def delete_prompt(self, prompt_name: str, user_id: str = "system", comment: str = "") -> Dict[str, Any]:
        """
        Delete a prompt with versioning backup

        Args:
            prompt_name: Name of the prompt to delete
            user_id: User making the change
            comment: Comment describing the deletion

        Returns:
            Dict with success status
        """
        self._check_reload()

        if prompt_name not in self._prompts_cache.get("prompts", {}):
            raise KeyError(f"Prompt not found: {prompt_name}")

        # Save version before deletion
        old_version = self._prompts_cache["prompts"][prompt_name].copy()
        self._save_version(prompt_name, old_version, user_id, comment, "delete")

        # Delete from cache
        del self._prompts_cache["prompts"][prompt_name]
        self._prompts_cache["last_updated"] = datetime.now().isoformat()

        # Save to file
        self._save_to_file()

        return {
            "success": True,
            "prompt_name": prompt_name,
            "deleted": True,
            "timestamp": datetime.now().isoformat()
        }

    def get_prompt_history(self, prompt_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get version history for a prompt

        Args:
            prompt_name: Name of the prompt
            limit: Maximum number of versions to return

        Returns:
            List of version records, newest first
        """
        history_files = list(self.history_dir.glob(f"{prompt_name}_*.json"))
        history_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        history = []
        for version_file in history_files[:limit]:
            try:
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                    history.append(version_data)
            except Exception as e:
                print(f"[WARNING] Failed to load version file {version_file}: {e}")
                continue

        return history

    def restore_version(
        self,
        prompt_name: str,
        version_timestamp: str,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Restore a prompt to a previous version

        Args:
            prompt_name: Name of the prompt
            version_timestamp: Timestamp of the version to restore
            user_id: User performing the restore

        Returns:
            Dict with success status
        """
        # Find version file
        version_file = self.history_dir / f"{prompt_name}_{version_timestamp}.json"

        if not version_file.exists():
            raise FileNotFoundError(f"Version not found: {version_timestamp}")

        # Load version
        with open(version_file, 'r') as f:
            version_data = json.load(f)

        # Restore the prompt config from the version
        old_config = version_data.get("prompt_config", {})

        # Save current version before restoring
        current_config = self.get_prompt(prompt_name)
        self._save_version(
            prompt_name,
            current_config,
            user_id,
            f"Pre-restore backup before reverting to {version_timestamp}",
            "pre_restore"
        )

        # Restore
        return self.save_prompt(
            prompt_name,
            old_config,
            user_id,
            f"Restored from version {version_timestamp}"
        )

    def validate_prompt(self, prompt_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a prompt configuration

        Args:
            prompt_config: Prompt configuration to validate

        Returns:
            Dict with valid: bool and errors: List[str]
        """
        errors = []

        # Required fields
        if "template" not in prompt_config:
            errors.append("Missing required field: template")

        if "description" not in prompt_config:
            errors.append("Missing required field: description")

        # Optional but recommended fields
        if "model" not in prompt_config:
            # Will use default, but warn
            pass

        # Validate model if specified
        if "model" in prompt_config:
            valid_models = ["gpt-4", "gpt-3.5-turbo", "claude-sonnet-4"]
            if prompt_config["model"] not in valid_models:
                errors.append(f"Unknown model: {prompt_config['model']}. Valid: {valid_models}")

        # Validate temperature
        if "temperature" in prompt_config:
            temp = prompt_config["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append("Temperature must be a number between 0 and 2")

        # Validate max_tokens
        if "max_tokens" in prompt_config:
            tokens = prompt_config["max_tokens"]
            if not isinstance(tokens, int) or tokens < 1:
                errors.append("max_tokens must be a positive integer")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _save_to_file(self) -> None:
        """Save prompts cache to JSON file"""
        with open(self.prompts_file, 'w') as f:
            json.dump(self._prompts_cache, f, indent=2)

        # Update mtime
        self._file_mtime = self.prompts_file.stat().st_mtime

    def _save_version(
        self,
        prompt_name: str,
        prompt_config: Dict[str, Any],
        user_id: str,
        comment: str,
        change_type: str
    ) -> None:
        """Save a version to history"""
        timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")

        version_data = {
            "prompt_name": prompt_name,
            "timestamp": timestamp,
            "user_id": user_id,
            "comment": comment,
            "change_type": change_type,
            "prompt_config": prompt_config,
            "config_hash": self._hash_config(prompt_config)
        }

        version_file = self.history_dir / f"{prompt_name}_{timestamp}.json"

        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)

    def _hash_config(self, config: Dict[str, Any]) -> str:
        """Generate hash of config for deduplication"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]


# Global singleton instance
_prompt_manager_instance: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """
    Get global PromptManager singleton

    Returns:
        PromptManager instance
    """
    global _prompt_manager_instance

    if _prompt_manager_instance is None:
        # Find prompts.json relative to this file
        current_dir = Path(__file__).parent.parent
        prompts_file = current_dir / "prompts.json"
        history_dir = current_dir / "prompts_history"

        _prompt_manager_instance = PromptManager(
            prompts_file=str(prompts_file),
            history_dir=str(history_dir)
        )

    return _prompt_manager_instance
