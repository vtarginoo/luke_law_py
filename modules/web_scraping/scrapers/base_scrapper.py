from abc import ABC, abstractmethod
from typing import Optional
from modules.models.process_dtos import ProcessoScrapedDTO

class BaseScraper(ABC):
    """
    Classe abstrata base para todos os scrapers de processo.
    Define o contrato que todas as implementações de scraper devem seguir.
    """

    @abstractmethod
    def scrape_processo(self, num_processo: str) -> ProcessoScrapedDTO:
        """
        Método abstrato para realizar o scraping de um processo.
        Todas as subclasses devem implementar este método.

        :param num_processo: O número do processo a ser raspado.
        :return: Um objeto ProcessoScrapedDTO contendo os dados raspados, ou None se não encontrado.
        """
        pass