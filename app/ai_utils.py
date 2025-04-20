import os
import logging
from typing import Optional, Dict, Any
import cohere
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

api_key = os.getenv("COHERE_API_KEY")
if not api_key:
    raise ValueError("COHERE_API_KEY not found in environment variables.")

client = cohere.Client(api_key)

def summarize_text(text: str, length: str = 'medium', format: str = 'paragraph', extractiveness: str = 'low') -> str:
    """
    Summarizes the input text using Cohere's model.
    
    Args:
        text: The text to summarize
        length: The length of the summary ('short', 'medium', or 'long')
        format: The format of the summary ('paragraph' or 'bullets')
        extractiveness: The extractiveness of the summary ('low' or 'high')
        
    Returns:
        A string containing the summarized text
    """
    if not text or len(text.strip()) == 0:
        logger.error("Empty text provided for summarization.")
        return "No text provided for summarization."

    try:
        logger.info(f"Summarizing text of length {len(text)} characters")
        response = client.summarize(
            text=text,
            length=length,
            format=format,
            extractiveness=extractiveness,
            model='summarize-xlarge'
        )
        logger.info("Successfully generated summary")
        return response.summary
    except cohere.CohereAPIError as e:
        error_msg = f"Cohere API error: {e}"
        logger.error(error_msg)
        return f"Failed to summarize the text due to API error: {str(e)}"
    except Exception as e:
        error_msg = f"Summarization failed: {e}"
        logger.error(error_msg)
        return f"Failed to summarize the text due to an error: {str(e)}"
