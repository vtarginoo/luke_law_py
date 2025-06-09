from flask import Blueprint
from flask_pydantic import validate

from modules.models.process_dtos import WSRequest
from modules.web_scraping.scrapers.pje_rj_scraper import PjeRjScraper
from modules.web_scraping.scrapers.eproc_rj_scraper import EprocRjScraper
import logging


# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criação de um Blueprint para organizar as rotas
# O prefixo base será /api/v1/scrape
scraping_bp = Blueprint('scraping_api', __name__, url_prefix='/api/v1/scrape')

@scraping_bp.route('/rj/pje', methods=['POST'])
@validate()
def scrape_rj_pje(body:WSRequest):
    """
    Endpoint para realizar o scraping de um processo no PJE-RJ.
    Recebe apenas o número do processo no corpo da requisição.
    """
    num_processo = body.numProcesso

    logger.info(f"Requisição de scraping para PJE-RJ processo: {num_processo}")

    scraper = PjeRjScraper()
    processo_scraped = scraper.scrape_processo(num_processo)
    logger.info(f"Scraping PJE-RJ concluído para {num_processo}")

    # Retorna o objeto Processo raspado, serializado para JSON
    return processo_scraped.model_dump_json(), 200, {'Content-Type': 'application/json'}

@scraping_bp.route('/rj/eproc', methods=['POST'])
@validate()
def scrape_rj_eproc(body:WSRequest):
    """
    Endpoint para realizar o scraping de um processo no Eproc-RJ.
    Recebe apenas o número do processo no corpo da requisição.
    """
    num_processo = body.numProcesso

    logger.info(f"Requisição de scraping para Eproc-RJ processo: {num_processo}")

    scraper = EprocRjScraper()
    processo_scraped = scraper.scrape_processo(num_processo)
    logger.info(f"Scraping Eproc-RJ concluído para {num_processo}")

    # Retorna o objeto Processo raspado, serializado para JSON
    return processo_scraped.model_dump_json(), 200, {'Content-Type': 'application/json'}



