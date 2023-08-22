from copy import deepcopy
import logging
from trafilatura.settings import DEFAULT_CONFIG
from page_insights.webpage import Webpage
from trafilatura import fetch_url, extract
# hack needed to mitigate errro: 'signal only works in main thread of the main interpreter' 
# turns off use of `signals`
# https://github.com/adbar/trafilatura/issues/202
my_config = deepcopy(DEFAULT_CONFIG)
my_config['DEFAULT']['EXTRACTION_TIMEOUT'] = '0'

logger = logging.getLogger(__name__)


class WebpageReader:
    """
    The PageReader class is responsible for reading the content of a list of URLs and returning a list of dictionaries
    containing the page content and link for each URL. It uses the SeleniumURLLoader class to load the web pages and
    extract their content.
    """

    @classmethod
    def read(cls, url: str) -> Webpage:
        """extracts the text content of a web page

        :param url: url of the web page
        :return: Webpage object
        """
        try:
            logger.info(f"Reading content for page: {url}")
            downloaded = fetch_url(url)
            text_content = extract(downloaded, include_comments=False, config=my_config)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return None # type: ignore
        else:
            return Webpage(text_content, url)

if __name__ == "__main__":
    page = WebpageReader.read('https://github.com/srush/MiniChain')
    print(page.content)