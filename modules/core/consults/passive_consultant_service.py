import logging

from modules.core.process_consultant import ProcessConsultant
from modules.core.scrapers_map import get_system_name_from_identifier
from modules.models.exception.exceptions import ProcessNotFoundException, ScraperTechnicalException, \
    ScraperBusinessException
from modules.models.process_dtos import ProcessoScrapedDTO

logger = logging.getLogger(__name__)

class PassiveConsultantService:
    def __init__(self):
        self.process_consultant = ProcessConsultant()
        logger.info("PassiveConsultantService inicializado.")

    def process_passive_consultation(self, adv_wpp: str, system_identifier: str, num_processo: str) -> ProcessoScrapedDTO:
        """
        Orquestra a consulta passiva de um processo.
        Recebe o identificador do sistema (numérico), o número do processo e o WhatsApp do advogado.
        Retorna o ProcessoScrapedDTO ou levanta uma exceção.
        """
        logger.info(f"Iniciando processamento passivo para {adv_wpp}: sistema_id='{system_identifier}', processo='{num_processo}'")

        try:
            # 1. Obter o nome do sistema a partir do identificador numérico
            system_type = get_system_name_from_identifier(system_identifier)
            logger.debug(f"Identificador '{system_identifier}' mapeado para tipo de sistema: '{system_type}'")

            # 2. Chamar o ProcessConsultant para obter os detalhes do processo
            process_data_dto = self.process_consultant.get_process_details(num_processo, system_type)
            logger.info(f"Dados do processo '{num_processo}' ({system_type}) obtidos com sucesso.")

            return process_data_dto

        except ValueError as e:
            logger.warning(f"Erro de validação na consulta passiva para {adv_wpp}: {e}")
            raise # Re-lança para o controller lidar
        except (ProcessNotFoundException, ScraperTechnicalException, ScraperBusinessException) as e:
            logger.error(f"Erro específico de scraping/negócio na consulta passiva para {adv_wpp}, processo {num_processo}: {e}", exc_info=True)
            raise # Re-lança para o controller lidar
        except Exception as e:
            logger.critical(f"Erro inesperado na consulta passiva para {adv_wpp}, processo {num_processo}: {e}", exc_info=True)
            raise # Re-lança para o controller lidar


