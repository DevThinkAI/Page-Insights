import logging
import re
import os
import time
from page_insights.llm_adapter import LlmAdapter
from page_insights.prompts_manager import PromptsManager

logger = logging.getLogger(__name__)



class Summarizer(object):
    def __init__(
        self, prompts_manager: PromptsManager, llm_adapter: LlmAdapter
    ):
        self.prompts_manager = prompts_manager
        self.llm_adapter = llm_adapter
        self.LLM_API_SECONDS_BETWEEN_REQUESTS = float(os.getenv("LLM_API_SECONDS_BETWEEN_REQUESTS", 10.0))
        logger.info(f"using llm api seconds between requests: {self.LLM_API_SECONDS_BETWEEN_REQUESTS}")

    def get_all_summaries(
        self,
        links: list[str],
        temprature_input,
        prompt_name,
        summary_words_max_range
    ) -> tuple[str, str]:
        # get the prompt from the PromtsManager
        prompt_txt = self.prompts_manager.get_prompt(prompt_name)
        # for each link, get the llm response
        llm_responses = []
        debug_resp = []
        prompt_replacements = self._populate_prompt_replacements(summary_words_max_range)

        for index, link in enumerate(links):
            try:
                llm_resp, debug = self.llm_adapter.get_llm_response(
                    link, temprature_input, prompt_txt, prompt_replacements
                )
                logger.info(f"llm_resp: {llm_resp}")
                llm_responses.append(llm_resp)
                debug_resp.append(debug)
                # sleep for 30 seconds to avoid rate limiting
                # openai.error.RateLimitError: Rate limit reached for 10KTPM-200RPM in organization org-5Zo... on
                #     tokens per min. Limit: 10000 / min. Please try again in 6ms. Contact us through our help center at help.openai.com if you continue to have issues.
                if index+1 < len(links):  # if not the last link
                    logger.info(f"sleeping for {self.LLM_API_SECONDS_BETWEEN_REQUESTS} seconds to avoid rate limiting")
                    time.sleep(self.LLM_API_SECONDS_BETWEEN_REQUESTS)
            except Exception as e:
                llm_responses.append(f"ERROR[{link}]: {str(e)}")
                logger.error(
                    f"An error occurred in the llm response for link: {link}:  Error: {str(e)}"
                )
                continue
        # return sumaries as a concatenated string
        return "\n\n".join(llm_responses), "\n\n".join(debug_resp)

    def get_summary_for_url(
        self, url: str, temp: float, prompt_name: str, summary_words_max_range
    ) -> tuple[str, str]:
        prompt_txt = self.prompts_manager.get_prompt(prompt_name)
        prompt_replacements = self._populate_prompt_replacements(summary_words_max_range)
        return self.llm_adapter.get_llm_response(url, temp, prompt_txt, prompt_replacements)
    

    def _populate_prompt_replacements(self, summary_words_max_range) -> dict[str, str]:
        # throw exception if summary_words_max_range does not match pattern: '\d+\s*,\s*\d+'
        if not re.search(r"\d+\s*,\s*\d+", summary_words_max_range):
            raise ValueError(f"summary_words_max_range does not match pattern: digit, digit'")
        min, max = self._get_min_max_range(summary_words_max_range)
        prompt_replacements = PromptsManager.PROMPT_PLACEHOLDERS
        prompt_replacements[PromptsManager.MIN_RESP_WORD_COUNT_FIELD] = min
        prompt_replacements[PromptsManager.MAX_RESP_WORD_COUNT_FIELD] = max
        return prompt_replacements

    def _get_min_max_range(self, summary_words_max_range: str) -> list[str]:
        return [x.strip() for x in summary_words_max_range.split(",")]
