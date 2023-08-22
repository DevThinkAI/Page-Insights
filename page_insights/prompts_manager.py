"""
This class managed access to prompt files.  Each file contains one prompt
The name of the file is the used as the name identiier for the prompt
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class PromptsManager:
    
    PROMPTS_FOLDER = "prompts"
    PROMPTS_FILE_EXT = "txt"
    MIN_RESP_WORD_COUNT_FIELD = "min_llm_resp_word_count"
    MAX_RESP_WORD_COUNT_FIELD = "max_llm_resp_word_count"
    WEB_PAGE_CONTENT_FIELD = "web_page_content"

    PROMPT_PLACEHOLDERS: dict[str, str] = {MIN_RESP_WORD_COUNT_FIELD: "", MAX_RESP_WORD_COUNT_FIELD: "", 
                                           WEB_PAGE_CONTENT_FIELD: ""}

    def __init__(self, assets_dir: Path):
        self._prompts: dict[str, str] = {}
        self._prompts_storage_path: Path = assets_dir.joinpath(self.PROMPTS_FOLDER)
        self._prompts_storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Prompt storage path: {self._prompts_storage_path}")
        self._init()

    def add_prompt(self, promt_name: str, prompt_text, persist: bool = True) -> None:
        for placeholder in self.PROMPT_PLACEHOLDERS.keys():
            if placeholder not in prompt_text:
                raise ValueError(f"The prompt must contain the placeholder {{{{{placeholder}}}}}")
        self._prompts[promt_name] = prompt_text
        if persist:
            self._save_prompt(promt_name, prompt_text)

    def update_prompt(self, promt_name, prompt_text, persist: bool = True) -> None:
        self._prompts[promt_name] = prompt_text
        if persist:
            self._save_prompt(promt_name, prompt_text)
    def get_prompt_names(self) -> list[str]:
        # return list of prompt names
        return list(self._prompts.keys())
    
    def get_prompt(self, prompt_name) -> str:
        logger.info(f"Getting prompt: {prompt_name}")
        return self._prompts[prompt_name]
    

    def _init(self):
        # create the prompt folder if it doesn't exist
        if not os.path.exists(self._prompts_storage_path):
            logger.info(f"Creating prompts folder: {self._prompts_storage_path}")
            os.mkdir(self._prompts_storage_path)
        
        self._load_prompts()

    def _load_prompts(self) -> None:
        # For each file in the prompts folder, load content of the file into 
        # a prompt str in self._prompts
        for prompt_file in self._prompts_storage_path.glob(f"*.{self.PROMPTS_FILE_EXT}"):
            with open(prompt_file, "r") as f:
                # use the file base name as the prompt name
                self._prompts[prompt_file.stem] = f.read().strip()
        logger.info(f"Loaded {len(self._prompts)} prompts")
        
        

    def _save_prompt(self, promt_name, prompt_text) -> None:
        with open(self._prompts_storage_path.joinpath(f"{promt_name}.{self.PROMPTS_FILE_EXT}"), "w") as f:
            f.write(prompt_text)
