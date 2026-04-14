import re

async def format_text(raw_text):
    # Common punctuation to escape in Markdown inline contexts
    return re.sub(r'([\\`*_{}\[\]()#+\-.!=])', r'\\\1', raw_text)

