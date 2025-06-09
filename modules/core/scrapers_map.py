# Defina o dicionário de mapeamento
from modules.web_scraping.scrapers.eproc_rj_scraper import EprocRjScraper
from modules.web_scraping.scrapers.pje_rj_scraper import PjeRjScraper

# Dicionário principal para mapear nomes de sistema para classes de scraper
SCRAPER_CLASSES = {
    "eproc_rj": EprocRjScraper,
    "pje_rj": PjeRjScraper,
    # Adicione mais entradas aqui para outros tipos de sistema, se tiver
}

# Novo dicionário para mapear identificadores numéricos para nomes de sistema internos
# Este será usado pela camada de mensagens (controller/service)
SYSTEM_IDENTIFIER_MAP = {
    "1": "eproc_rj",
    "2": "pje_rj"
}

# Opcional: Uma função para obter a classe do scraper (já existe, mantida)
def get_scraper_class(system_type: str):
    """Retorna a classe do scraper para o tipo de sistema especificado."""
    system_type = system_type.lower()
    scraper_class = SCRAPER_CLASSES.get(system_type)
    if not scraper_class:
        raise ValueError(f"Scraper para o sistema '{system_type}' não suportado. Sistemas disponíveis: {list(SCRAPER_CLASSES.keys())}")
    return scraper_class

# Nova função para obter o nome do sistema a partir do identificador numérico
def get_system_name_from_identifier(identifier: str) -> str | None:  # Sinaliza que pode retornar str ou None
    """
    Mapeia um identificador numérico (string) para o nome do sistema de scraping.
    Retorna o nome do sistema ou None se o identificador não for reconhecido.
    """
    system_name = SYSTEM_IDENTIFIER_MAP.get(identifier.strip().lower())

    return system_name
