"""Manage the aspects of the Research"""

import json
import string
import random
import logging
import re
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ResearchManager(object):
    RESEARCH_FOLDER = "research"
    RESEARCH_FILE_EXT = "md"
    RESEARCH_DIGEST_FILE_NAME = "research_digest.json"

    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self.perist_folder_path = assets_dir.joinpath(self.RESEARCH_FOLDER)
        self.perist_folder_path.mkdir(parents=True, exist_ok=True)
        self.digest_file_path = self.perist_folder_path.joinpath(
            self.RESEARCH_DIGEST_FILE_NAME
        )
        self.saved_research: list[dict[str, Any]] = []
        if not self.digest_file_path.exists():
            self.digest_file_path.touch()
            self.digest_file_path.write_text("[]")
        self._load_saved_research_metadata()

    def persist_research(self, research_text: str, research_name: str, research_links: list[str], 
                         add_title_header: bool = True) -> str:
        if add_title_header:
            research_text = f"# {research_name}\n{research_text}"
        # ensure research_name is safe for a file name
        research_name = re.sub(r"[^a-zA-Z0-9-_\.]", "_", research_name)
        research_name = research_name.strip('.')
        research_name = re.sub(r"_+", "_", research_name)
        logger.info(f"Persisting research: {research_name}")
        return self._persist_digest_record(research_text, research_name, research_links)
    
    def delete_research(self, research_id: str, permanent_delete: bool = False):
        action = "deleted" if permanent_delete else "archived"
        # find the record in self.saved_research which matches the research_id
        for i, research in enumerate(self.saved_research):
            if research["id"] == research_id:
                if permanent_delete:
                    logger.info(f"Deleting research record: {research_id}")
                    del self.saved_research[i]
                else:
                    self.saved_research[i]['archived'] = True
                self.digest_file_path.write_text(json.dumps(self.saved_research, indent=4))
                break
        if permanent_delete:
            self._delete_research_file(research_id)
        logger.info(f"Research {research_id} {action}")

    def _delete_research_file(self, research_id: str):
        logger.info(f"Deleting research file: {research_id}")
        research_filepath = self.perist_folder_path.joinpath(f"{research_id}.{self.RESEARCH_FILE_EXT}")
        if research_filepath.exists():
            research_filepath.unlink()

    def get_research_ids(self, include_archived: bool = False) -> list[str]:
        if include_archived:
            return [research["id"] for research in self.saved_research]
        else:
            return [research["id"] for research in self.saved_research if not research["archived"]]

    def get_research_details(self, research_id: str, include_archived: bool = False) -> tuple[dict[str, Any], str]:
        logger.info(f"Getting research details for id: {research_id}")
        research_metadata = None
        for research in self.saved_research:
            if research["id"] == research_id:
                logger.info(f"Found research with id: {research_id}: {research}")
                research_metadata = research
                if not include_archived and research["archived"]:
                    research_metadata = None
                break
        if not research_metadata:
            return {}, ""
        # read the file content of the research
        file_path = self.perist_folder_path.joinpath(research_metadata["file_name"])
        if not file_path.exists():
            logger.error(f"Research file does not exist: {file_path}")
            return research_metadata, ""
        research_content = file_path.read_text()
        return research_metadata, research_content

    def _persist_digest_record(
        self, research_text: str, research_name: str, research_links: list[str]
    ) -> str:
        research_id = self._generate_research_id(research_name)

        research_filepath = self.perist_folder_path.joinpath(f"{research_id}.{self.RESEARCH_FILE_EXT}")
        research_filepath.write_text(research_text)

        self.saved_research.append(
            self._generate_research_record(research_id, research_name, research_filepath, research_links)
        )
        # save the digest
        self.digest_file_path.write_text(json.dumps(self.saved_research, indent=4))
        return research_id
        

    def _load_saved_research_metadata(self) -> None:
        if self.digest_file_path.exists():
            with open(self.digest_file_path, "r") as file:
                self.saved_research = json.load(file)
                logger.info(
                    f"Loaded metadata for {len(self.saved_research)} research"
                )

    def _generate_research_id(self, research_name: str) -> str:
        return f"{research_name}-{self._generate_random_string(4)}"
    

    def _generate_research_record(
        self, research_id: str, research_name: str, file_path: Path, research_links: list[str]
    ) -> dict[str, Any]:
        return {
            "id": research_id,
            "created_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %z"),
            "name": research_name,
            "file_name": str(file_path.name),
            "links": research_links,
            "archived": False
        }
    
    def _generate_random_string(self, length: int) -> str:
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string
