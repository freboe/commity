"""glm OpenAI-compatible client."""

from commity.llm.openai import OpenAIClient


class GLMClient(OpenAIClient):
    """Client for the glm API."""

    default_base_url = "https://open.bigmodel.cn/api/paas/v4"
    default_model = "glm-4.7"
