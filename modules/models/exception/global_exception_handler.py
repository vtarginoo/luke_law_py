import logging
from flask import Blueprint, jsonify
from pydantic import ValidationError # Importar ValidationError para tratar erros de Pydantic

# Importe suas exceções customizadas
from modules.models.exception.exceptions import ( # Ajuste o caminho conforme sua estrutura
    BaseScrapingException,
    ScraperTechnicalException,
    ScraperBusinessException,
    ProcessNotFoundException
)

# Importe o seu modelo de ResponseError (assumindo que está em modules.web_scraping.models)
from modules.models.exception.response_error import ResponseError
from modules.models.exception.validations_exceptions import InputValidationException

# Configurar o logger
logger = logging.getLogger(__name__)

# Criar um Blueprint para os handlers de exceção
exception_scrape_bp = Blueprint('exception_handlers', __name__)

# --- Handlers para suas exceções customizadas ---



# --- Handler para erros de validação de entrada customizados ---
@exception_scrape_bp.app_errorhandler(InputValidationException)
def handle_input_validation_exception(e: InputValidationException):
    """
    Handler para exceções de validação de entrada da API (InputValidationException e suas subclasses).
    Retorna uma resposta 400 Bad Request com detalhes dos erros de validação.
    """
    logger.warning(f"Input Validation Error (Code: {e.code}, Message: {e.message})", exc_info=True)

    response_error = ResponseError(
        message=e.message,
        code=e.code,
        details=e.details
    )
    return jsonify(response_error.model_dump()), 400 # 400 Bad Request é o mais apropriado aqui



@exception_scrape_bp.app_errorhandler(BaseScrapingException)
def handle_base_scraping_exception(e: BaseScrapingException):
    """
    Handler genérico para todas as exceções de scraping customizadas (BaseScrapingException e suas subclasses).
    Extrai o código, mensagem e detalhes da exceção para formatar a resposta JSON.
    """
    status_code = 500  # Default para erros internos do scraper

    # Ajusta o status code baseado no tipo de exceção de negócio
    if isinstance(e, ProcessNotFoundException):
        status_code = 404 # Not Found
    elif isinstance(e, ScraperBusinessException):
        status_code = 422 # Unprocessable Entity (erros de lógica de negócio)
    elif isinstance(e, ScraperTechnicalException):
        status_code = 500 # Internal Server Error (erros técnicos)


    logger.error(f"Scraping Exception (Code: {e.code}, Message: {e.message})", exc_info=True)

    response_error = ResponseError(
        message=e.message,
        code=e.code,
        details=e.details
    )
    return jsonify(response_error.model_dump()), status_code


# --- Handler para erros de validação do Pydantic ---
@exception_scrape_bp.errorhandler(ValidationError)
def handle_pydantic_validation_error(e: ValidationError):
    """
    Handler para erros de validação de modelos Pydantic (ex: nos dados de entrada da API).
    Retorna uma resposta 400 Bad Request com detalhes dos erros de validação.
    """
    logger.warning(f"Pydantic Validation Error: {e.errors()}", exc_info=True)

    # Constrói uma mensagem mais amigável
    error_details = []
    for error in e.errors():
        field = ".".join(map(str, error.get("loc", ["unknown_field"])))
        error_details.append(f"Campo '{field}': {error.get('msg')}")

    response_error = ResponseError(
        message="Dados de entrada inválidos.",
        code="VALIDATION_ERROR",
        details={"validation_errors": e.errors(), "summary": error_details}
    )
    return jsonify(response_error.model_dump()), 400 # Bad Request


# --- Handler genérico para outras exceções ---
@exception_scrape_bp.app_errorhandler(Exception)
def handle_generic_exception(e: Exception):
    """
    Handler genérico para qualquer outra exceção não capturada.
    Retorna um erro 500 Internal Server Error.
    """
    logger.critical(f"Unhandled internal server error: {e}", exc_info=True)

    response_error = ResponseError(
        message="Um erro interno inesperado ocorreu.",
        code="INTERNAL_SERVER_ERROR",
        details= "null"

    )
    return jsonify(response_error.model_dump()), 500
