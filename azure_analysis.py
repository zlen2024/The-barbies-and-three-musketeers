import os
import base64
import logging
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

logger = logging.getLogger(__name__)

def generate_forecast_analysis(image_base64, fundamental_data):
    try:
        endpoint = os.getenv("ENDPOINT_URL", "https://barbieai.openai.azure.com/")
        deployment = os.getenv("DEPLOYMENT_NAME", "gpt-5-nano")

        # Initialize Azure OpenAI client with Entra ID authentication
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2025-01-01-preview",
        )

        chat_prompt = [
            {
                "role": "developer",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze the incoming sales trend through fundamental analysis and technical analysis of a provided chart, and then predict sales direction and suggest a sales volume.\n\n# Instructions\n\nYou are tasked with performing an in-depth analysis of the provided information and predicting the incoming sales trend. This involves two parts:\n\n1. **Fundamental Analysis**: Examine the given text-based data to evaluate factors that influence sales trends, such as economic conditions, industry performance, seasonality, or other relevant indicators.\n2. **Technical Analysis**: Analyze the provided image of a chart to assess patterns, trends, and sales volume movements visually. Identify technical indicators such as support, resistance levels, moving averages, or other graphical signals.\n\nFinally, synthesize the insights to determine the likely sales direction (e.g., increase, decrease, stable) and provide a comprehensive report with robust reasoning.\n\n# Steps\n\n1. **Fundamental Analysis**\n   - Examine the provided fundamental data (e.g., external factors, seasonal trends, market indicators).\n   - Identify key drivers that may influence sales trends.\n   - Provide a brief summary of findings. \n\n2. **Technical Analysis**\n   - Analyze the chart image for visually identifiable patterns (e.g., uptrend, downtrend, consolidation).\n   - Identify and comment on key indicators such as:\n     - Support/resistance levels.\n     - Recent sales volume movements.\n     - Chart patterns.\n   - Summarize key visual insights from the chart.\n\n3. **Prediction and Recommendation**\n   - Combine insights from steps 1 and 2 to predict the short-to-midterm sales trend (e.g., upward trend, downward trend, stable).\n   - Provide a clear numerical sales volume prediction based on the analysis.\n   - Offer a detailed, robust explanation justifying your prediction and outlining a complete report.\n\n# Output Format\n\nYour response should be formatted as follows:\n\n```markdown\n### Fundamental Analysis\n[Summary of findings from the provided fundamental data, highlighting key drivers affecting sales trends.]\n\n### Technical Analysis\n[Summary of observations from the chart image, including patterns, key levels, and trends.]\n\n### Prediction and Sales Volume Suggestion\n**Trend Prediction**: [Predicted sales direction: upward, downward, or stable.]\n**Sales Volume Suggestion**: [Predicted Volume] \n**Reasoning**: [Detailed, robust explanation linking fundamental and technical insights to the prediction, forming a complete report.]\n```\n\n# Notes\n\n- Base the prediction on both qualitative (fundamental) and quantitative (technical) factors.\n- If key data is missing or unclear, make reasonable assumptions and state them explicitly.\n- Be comprehensive and thorough in your explanation. Ensure the prediction logically follows from your analysis.\n\nHere is the fundamental data provided by the user:\n" + fundamental_data
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]

        messages = chat_prompt

        completion = client.chat.completions.create(
            model=deployment,
            messages=messages,
            max_completion_tokens=13107,
            stop=None,
            stream=False
        )

        return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Error generating forecast analysis: {str(e)}")
        raise e
