import logging

from modules.core.scrapers_map import SCRAPER_CLASSES, SYSTEM_IDENTIFIER_MAP, get_system_name_from_identifier

from modules.models.process_dtos import ProcessoScrapedDTO

logger = logging.getLogger(__name__)

class ProcessConsultant:
    def __init__(self):
        # Referencia o dicionário de classes importado
        self.scraper_classes = SCRAPER_CLASSES
        self._scraper_instances = {}  # Cache para instâncias de scraper

    def _get_scraper_instance(self, system_input: str): # Renomeei para system_input para clareza
        """
        Retorna uma instância do scraper para o tipo de sistema especificado.
        Aceita tanto o identificador numérico (ex: "1") quanto o nome do sistema (ex: "eproc_rj").
        Cria a instância se ela ainda não existir no cache.
        """
        system_input = system_input.strip().lower()

        # 1. Tenta resolver o input como um identificador numérico
        system_name = get_system_name_from_identifier(system_input)
        logger.info(f"System_name = {system_name}")

        # Se encontrou um mapeamento numérico, usa o nome do sistema correspondente
        if system_name is None:
            final_system_type = system_name
            logger.info(f"System_name é None")
        # Se não encontrou um mapeamento numérico, assume que o input já é o nome do sistema
        elif system_name in self.scraper_classes:
            final_system_type = system_name
            logger.info(f"System_name {system_name} foi achado nas scrapper classes")
        else:
            logger.warning(f"Não foi possível converter o tipo do sistema - parou tudo")
            # Se não é nem numérico válido nem nome de sistema direto, lança erro
            raise ValueError(
                f"Entrada de sistema '{system_input}' inválida. "
                f"Por favor, use um dos identificadores numéricos: {', '.join([f'{k} ({v})' for k,v in SYSTEM_IDENTIFIER_MAP.items()])} "
                f"ou um nome de sistema direto: {list(self.scraper_classes.keys())}."
            )

        # Agora, com o final_system_type definido, o restante da lógica é a mesma
        scraper_class = self.scraper_classes.get(final_system_type)

        if not scraper_class:
            # Isso só deveria acontecer se houver um erro de configuração em SCRAPER_CLASSES
            raise ValueError(
                f"Erro interno: Scraper para o sistema '{final_system_type}' mapeado mas não encontrado."
            )

        if final_system_type not in self._scraper_instances:
            print(f"Core: Criando nova instância do scraper para '{final_system_type}'.")
            self._scraper_instances[final_system_type] = scraper_class()

        return self._scraper_instances[final_system_type]

    def get_process_details(self, process_number: str, system_type: str) -> ProcessoScrapedDTO:
        """
        Consulta os detalhes de um processo usando o scraper apropriado
        com base no `system_type`.
        """
        if not process_number:
            raise ValueError("O número do processo não pode ser vazio.")
        if not system_type:
            raise ValueError("O tipo de sistema (eproc_rj, pje_rj, etc.) é obrigatório.")

        try:
            scraper_instance = self._get_scraper_instance(system_type)

            print(f"Core: Solicitando dados do processo {process_number} do sistema {system_type} ao scraping.")
            process_data = scraper_instance.scrape_processo(process_number)
            print(f"Core: Dados do processo {process_number} obtidos com sucesso do sistema {system_type}.")
            return process_data
        except Exception as e:
            print(f"Erro ao consultar processo {process_number} via scraper de {system_type}: {e}")
            raise  # Re-lança a exceção para que a camada superior possa tratá-la

