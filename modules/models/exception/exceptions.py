
class BaseScrapingException(Exception):
    """Exceção base para todos os erros de scraping."""
    def __init__(self, message: str, code: str = "SCRAPING_ERROR", original_exception: Exception = None):
        super().__init__(message)
        self.message = message # Armazena a mensagem
        self.code = code
        self.original_exception = original_exception
        self.details = None

class ScraperTechnicalException(BaseScrapingException):
    """Exceção para erros técnicos durante o scraping (Selenium, parsing, rede, etc.)."""
    pass

class ScraperBusinessException(BaseScrapingException):
    """Exceção para erros de lógica de negócio durante o scraping (ex: processo não encontrado, CAPTCHA falhou)."""
    pass

class ProcessNotFoundException(ScraperBusinessException):
    """Exceção quando um processo não é encontrado no sistema alvo."""
    def __init__(self, num_processo: str, message: str = None):
        super().__init__(
            message=message or f"Processo '{num_processo}' não encontrado no sistema.",
            code="PROCESS_NOT_FOUND"
        )

class CaptchaResolutionFailedException(ScraperBusinessException):
    """Exceção quando a resolução do CAPTCHA falha após múltiplas tentativas."""
    def __init__(self, message: str = "Falha ao resolver o CAPTCHA."):
        super().__init__(
            message=message,
            code="CAPTCHA_RESOLUTION_FAILED"
        )


