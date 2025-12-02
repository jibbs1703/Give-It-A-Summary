"""Give It A Summary - Prompt Templates Module."""

from string import Template

summarize_prompt = Template("""
        Summarize the following text in a $style style, with a maximum of $max_words words:
        $content
    """)
