import json
import logging
import os
import re
import openai
from page_insights.webpage_reader import WebpageReader

logger = logging.getLogger(__name__)

class LlmAdapter(object):
    
    def __init__(self, openai_api_key: str, resp_max_tokens: int = 1024):
        openai.api_key = openai_api_key
        self.resp_max_tokens = resp_max_tokens
        self.OPENAI_LLM = os.getenv("OPENAI_LLM", None)
        if not self.OPENAI_LLM:
            raise Exception("OPENAI_LLM not set in environment")
        logger.info(f"using llm model: {self.OPENAI_LLM}")


    def get_llm_response(self, url: str, temprature: float, system_prompt: str, 
                         prompt_replacements: dict[str, str]) -> tuple[str, str]:
        webpage = WebpageReader.read(url)
        prompt_replacements["web_page_content"] = webpage.content

        system_prompt = self._make_prompt_string_replacements(system_prompt, prompt_replacements)
        response = openai.ChatCompletion.create(
            model=self.OPENAI_LLM,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Link: {url}"},
            ],
            temperature=temprature,
            stream=False,
            max_tokens=self.resp_max_tokens,
        )
        debug = json.dumps(response, indent=4)
        query_reponse = response.choices[0]  # type: ignore

        return query_reponse["message"]["content"], debug


    def _make_prompt_string_replacements(self, templated_prompt: str, replacement_values: dict[str, str]) -> str:
        for key, value in replacement_values.items():
            templated_prompt = templated_prompt.replace(f"{{{{{key}}}}}", value)
        # assert there is no more replacemnt pattern ({{\w}}) substrings in tempalted_prompt
        if re.search('{{[a-zA-Z0-9-_\\s]+}}', templated_prompt):
            raise ValueError(f"Found more replacement patterns in templated_prompt: {templated_prompt}")

        return templated_prompt
