"""
Input Sanitizer Tool

Sanitizes user inputs to prevent prompt injection and other security issues.
"""

import re
from typing import Dict, Any, List, Optional
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata


class InputSanitizerTool(BaseTool):
    """
    Sanitizes user inputs to prevent security vulnerabilities

    Features:
    - Prompt injection detection and prevention
    - HTML/Script tag removal
    - SQL injection pattern detection
    - Command injection pattern detection
    - Configurable sanitization rules
    """

    # Dangerous patterns that could indicate attacks
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"ignore\s+all\s+previous",
        r"disregard\s+previous",
        r"forget\s+previous",
        r"you\s+are\s+now",
        r"new\s+instructions",
        r"system\s*:\s*",
        r"<\s*system\s*>",
        r"\[SYSTEM\]",
        r"execute\s+the\s+following",
    ]

    SQL_INJECTION_PATTERNS = [
        r"('\s*OR\s*'1'\s*=\s*'1)",
        r"(;\s*DROP\s+TABLE)",
        r"(;\s*DELETE\s+FROM)",
        r"(UNION\s+SELECT)",
        r"(--\s*$)",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",  # Shell metacharacters
        r"\$\{.*\}",   # Variable substitution
        r"\$\(.*\)",   # Command substitution
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_length = self.config.get("max_length", 10000)
        self.allow_html = self.config.get("allow_html", False)
        self.strict_mode = self.config.get("strict_mode", False)

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="input_sanitizer",
            description="Sanitizes user inputs to prevent security vulnerabilities",
            version="1.0.0",
            tags=["security", "validation", "sanitization"],
            is_safe=True,
            input_schema={
                "text": "string - Text to sanitize",
                "check_prompt_injection": "boolean - Check for prompt injection patterns",
                "check_sql_injection": "boolean - Check for SQL injection patterns",
                "check_command_injection": "boolean - Check for command injection patterns",
                "remove_html": "boolean - Remove HTML tags",
            }
        )

    def execute(
        self,
        text: str,
        check_prompt_injection: bool = True,
        check_sql_injection: bool = True,
        check_command_injection: bool = True,
        remove_html: bool = True,
    ) -> ToolResult:
        """
        Sanitize input text

        Args:
            text: Text to sanitize
            check_prompt_injection: Check for prompt injection attempts
            check_sql_injection: Check for SQL injection patterns
            check_command_injection: Check for command injection patterns
            remove_html: Remove HTML tags

        Returns:
            ToolResult with sanitized text and security warnings
        """
        return self._wrap_execution(
            self._sanitize,
            text=text,
            check_prompt_injection=check_prompt_injection,
            check_sql_injection=check_sql_injection,
            check_command_injection=check_command_injection,
            remove_html=remove_html,
        )

    def _sanitize(
        self,
        text: str,
        check_prompt_injection: bool,
        check_sql_injection: bool,
        check_command_injection: bool,
        remove_html: bool,
    ) -> ToolResult:
        """Internal sanitization logic"""

        if not text:
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data="",
                metadata={"warnings": []}
            )

        warnings = []
        original_text = text
        sanitized_text = text

        # Check length
        if len(text) > self.max_length:
            warnings.append(f"Input exceeds max length ({self.max_length}). Truncating.")
            sanitized_text = sanitized_text[:self.max_length]

        # Check for prompt injection
        if check_prompt_injection:
            for pattern in self.PROMPT_INJECTION_PATTERNS:
                if re.search(pattern, sanitized_text, re.IGNORECASE):
                    warnings.append(f"Potential prompt injection detected: pattern '{pattern}'")
                    if self.strict_mode:
                        return ToolResult(
                            status=ToolStatus.FAILURE,
                            error="Prompt injection detected in strict mode",
                            metadata={"warnings": warnings, "pattern": pattern}
                        )
                    # In non-strict mode, sanitize by removing the pattern
                    sanitized_text = re.sub(pattern, "[REMOVED]", sanitized_text, flags=re.IGNORECASE)

        # Check for SQL injection
        if check_sql_injection:
            for pattern in self.SQL_INJECTION_PATTERNS:
                if re.search(pattern, sanitized_text, re.IGNORECASE):
                    warnings.append(f"Potential SQL injection detected: pattern '{pattern}'")
                    if self.strict_mode:
                        return ToolResult(
                            status=ToolStatus.FAILURE,
                            error="SQL injection detected in strict mode",
                            metadata={"warnings": warnings, "pattern": pattern}
                        )
                    sanitized_text = re.sub(pattern, "[REMOVED]", sanitized_text, flags=re.IGNORECASE)

        # Check for command injection
        if check_command_injection:
            for pattern in self.COMMAND_INJECTION_PATTERNS:
                if re.search(pattern, sanitized_text):
                    warnings.append(f"Potential command injection detected: pattern '{pattern}'")
                    if self.strict_mode:
                        return ToolResult(
                            status=ToolStatus.FAILURE,
                            error="Command injection detected in strict mode",
                            metadata={"warnings": warnings, "pattern": pattern}
                        )
                    sanitized_text = re.sub(pattern, "", sanitized_text)

        # Remove HTML tags if requested
        if remove_html and not self.allow_html:
            # First, remove dangerous tags completely (including their content)
            dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed', 'noscript']
            for tag in dangerous_tags:
                pattern = rf'<{tag}[^>]*>.*?</{tag}>'
                if re.search(pattern, sanitized_text, re.IGNORECASE | re.DOTALL):
                    warnings.append(f"Dangerous <{tag}> tag detected and removed completely")
                    sanitized_text = re.sub(pattern, '', sanitized_text, flags=re.IGNORECASE | re.DOTALL)

            # Then remove remaining HTML tags (but keep their content)
            html_pattern = r"<[^>]+>"
            if re.search(html_pattern, sanitized_text):
                warnings.append("HTML tags detected and removed")
                sanitized_text = re.sub(html_pattern, "", sanitized_text)

        # Remove potentially dangerous Unicode characters
        sanitized_text = self._remove_dangerous_unicode(sanitized_text)

        # Normalize whitespace
        sanitized_text = " ".join(sanitized_text.split())

        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=sanitized_text,
            metadata={
                "warnings": warnings,
                "original_length": len(original_text),
                "sanitized_length": len(sanitized_text),
                "was_modified": original_text != sanitized_text,
            }
        )

    def _remove_dangerous_unicode(self, text: str) -> str:
        """Remove potentially dangerous Unicode characters"""
        # Remove zero-width characters that could hide malicious content
        dangerous_chars = [
            "\u200B",  # Zero-width space
            "\u200C",  # Zero-width non-joiner
            "\u200D",  # Zero-width joiner
            "\uFEFF",  # Zero-width no-break space
        ]
        for char in dangerous_chars:
            text = text.replace(char, "")
        return text
