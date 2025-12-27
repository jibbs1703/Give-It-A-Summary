"""Give It A Summary - Prompt Templates Module."""

from string import Template

SUMMARIZE_PROMPT = Template("""
        Summarize the following text in a $style style, with a maximum of $max_words words:
        $content
    """)
