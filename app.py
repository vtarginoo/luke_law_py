from dotenv import load_dotenv
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

load_dotenv()

from modules.message.message_controller import message_bp
from modules.models.exception.global_exception_handler import exception_scrape_bp
from modules.web_scraping.scraping_controller import scraping_bp
import logging



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



app = Flask(__name__)


### Configuração do Swagger UI ###
SWAGGER_URL = '/swagger'  # URL para acessar a UI do Swagger
API_URL = '/static/swagger.json'  # URL do seu arquivo de especificação OpenAPI

# Crie o Blueprint do Swagger UI
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "API de Web Scraping Jurídico"
    }
)

# Blueprint do Swagger UI
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Blueprint de exception
app.register_blueprint(exception_scrape_bp)

# Blueprint de scraping
app.register_blueprint(scraping_bp)

# Blueprint de message
app.register_blueprint(message_bp)

@app.route('/')
def home():
    logger.info("Acessando a rota inicial.")
    return "Bem-vindo à API de Web Scraping de Processos!"

if __name__ == '__main__':
    logger.info("Iniciando servidor Flask em modo de desenvolvimento.")
    app.run(debug=True, host='0.0.0.0', port=5000)
