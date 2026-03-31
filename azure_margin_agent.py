import os
import logging
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

logger = logging.getLogger(__name__)

def generate_agentic_rationale(prompt, image_base64):
    """
    Sends the user prompt and base64 chart image to the Azure OpenAI gpt-5-nano model.
    """
    try:
        endpoint = os.getenv("ENDPOINT_URL", "https://barbieai.openai.azure.com/")
        deployment = os.getenv("DEPLOYMENT_NAME", "gpt-5-nano")

        # In local dev or if identity is not fully set up, we fallback to API key if token fails
        # but the request specifically uses Entra ID authentication.
        try:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider,
                api_version="2025-01-01-preview",
            )
        except Exception as auth_e:
            logger.warning(f"Entra ID auth failed, falling back to API key if available: {auth_e}")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            if not api_key:
                return {"error": "Azure OpenAI authentication failed and no fallback API key found."}

            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version="2025-01-01-preview",
            )

        # Prepare messages
        messages = [
            {
                "role": "developer",
                "content": "You are the AI Pricing Strategist, a senior financial consultant specializing in dynamic pricing and inventory optimization. Your role is to analyze data from a Margin Simulator chart and the user's question, and provide concise, data-driven rationales (\"Smart Why\") to guide a Sales Manager's decision-making process. Answer the user's specific question based on the visual data in the chart."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]

        completion = client.chat.completions.create(
            model=deployment,
            messages=messages,
            max_completion_tokens=1000,
            stop=None,
            stream=False
        )

        return {"success": True, "rationale": completion.choices[0].message.content}

    except Exception as e:
        logger.error(f"Error generating agentic rationale: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
