
class InputValidationException(Exception):
    """
    Exceção base para erros de validação de entrada da API.
    Não herda de BaseScrapingException, pois são domínios de erro diferentes.
    """
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {} # Garante que 'details' é sempre um dicionário


# No mesmo módulo de exceções, ou onde a InputValidationException foi definida
class InvalidProcessNumberException(InputValidationException):
    """
    Exceção levantada quando o número do processo fornecido não está em um formato válido.
    """
    def __init__(self, num_processo: str):
        super().__init__(
            message=(f"O número do processo '{num_processo}' não está em um formato válido. "
                     "Esperado 'xxxxxxx-xx.xxxx.x.xx.xxxx' ou 'xxxxxxxxxxxxxxxxxxxx'."),
            code="INVALID_PROCESS_NUMBER",
            details={"received_process_number": num_processo}
        )