import logging
import os

import base64
import types

from dotenv import load_dotenv

from google import genai
from google.genai import types
from selenium.common import NoSuchElementException, TimeoutException

from selenium.webdriver.remote.webdriver import WebDriver

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from modules.models.exception.exceptions import  ScraperTechnicalException

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()


logger = logging.getLogger(__name__)

class CaptchaResolvers:

    @staticmethod
    def gemini_captcha_text_resolver(
            driver: WebDriver,
            captcha_img_locator: tuple,
            captcha_input_locator: tuple,
            timeout: int = 15,
            model_name: str = "gemini-1.5-flash"
    ) -> bool: # Retorna True para sucesso, False para falha na resolução
        """
        Resolve um CAPTCHA de texto usando a API Gemini.

        Args:
            driver (WebDriver): Instância do WebDriver do Selenium.
            captcha_img_locator (tuple): Tupla (By.STRATEGY, locator) para localizar a imagem do CAPTCHA.
                                         Assume que a imagem tem o src em base64.
            captcha_input_locator (tuple): Tupla (By.STRATEGY, locator) para localizar o campo de input do CAPTCHA.
            timeout (int): Tempo máximo de espera para o CAPTCHA aparecer e ser resolvido.
            model_name (str): Nome do modelo Gemini a ser usado.

        Returns:
            bool: Retorna True se o CAPTCHA foi resolvido e preenchido com sucesso, False caso contrário.

        Raises:
            ScraperTechnicalException: Se ocorrer um erro técnico crítico que impeça a tentativa de resolução
                                       (ex: API Key ausente, falha na decodificação Base64).
        """
        logger.info(f"Tentando resolver CAPTCHA com Gemini usando modelo: {model_name}")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # ERRO CRÍTICO: Não é possível continuar sem a API Key. Lança exceção.
            raise ScraperTechnicalException(
                "GEMINI_API_KEY não configurada nas variáveis de ambiente. A resolução de CAPTCHA não pode prosseguir.",
                code="API_KEY_MISSING"
            )

        try:
            client = genai.Client(api_key=api_key)

            wait = WebDriverWait(driver, timeout)
            # 2. Esperar e localizar a imagem do CAPTCHA
            captcha_img_element = wait.until(
                EC.presence_of_element_located(captcha_img_locator)
            )

            # 3. Obter a string Base64 do atributo 'src'
            captcha_img_src = captcha_img_element.get_attribute("src")
            if not captcha_img_src or not captcha_img_src.startswith("data:image"):
                logger.warning("O atributo 'src' da imagem do CAPTCHA não é uma string Base64 válida. Falha na tentativa de resolução.")
                return False # Falha não crítica, permite nova tentativa

            # 4. Extrair o conteúdo Base64 e o tipo MIME
            mime_type_part = captcha_img_src.split(';')[0].split(':')[1]
            base64_data = captcha_img_src.split(',')[1]

            logger.info(f"Tipo MIME da imagem do CAPTCHA: {mime_type_part}")

            # 5. Decodificar a string Base64 para bytes
            try:
                image_bytes = base64.b64decode(base64_data)
            except Exception as e:
                # ERRO CRÍTICO: Falha na decodificação Base64, impede a consulta ao Gemini. Lança exceção.
                raise ScraperTechnicalException(
                    "Erro ao decodificar Base64 da imagem do CAPTCHA.",
                    code="CAPTCHA_BASE64_DECODE_ERROR",
                    original_exception=e
                )


            # 6. Criar o objeto Part a partir dos bytes da imagem
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type_part
            )

            # 7. Enviar a imagem e o prompt para o modelo Gemini
            logger.info("Enviando imagem do CAPTCHA para a API Gemini...")
            response = client.models.generate_content(
                model=model_name,
                contents=[image_part, "Resolve the Captcha. Provide only the text, do not add any extra explanation or punctuation."]
            )

            # 8. Obter o texto resolvido
            resolved_text = response.text.strip()
            if not resolved_text:
                logger.warning("A API Gemini não retornou texto para o CAPTCHA. Falha na tentativa de resolução.")
                return False # Falha na resolução pela API, permite nova tentativa

            logger.info(f"CAPTCHA resolvido: {resolved_text}")

            # 9. Preencher o campo de input
            captcha_input_element = driver.find_element(*captcha_input_locator)
            captcha_input_element.send_keys(resolved_text)

            return True # Sucesso na resolução e preenchimento

        except (TimeoutException, NoSuchElementException) as e:
            # Problema ao encontrar elementos do Selenium. Não é um erro "fatal" para a tentativa,
            # apenas indica que não foi possível tentar resolver o CAPTCHA nesta rodada.
            logger.warning(f"Elemento da imagem ou input do CAPTCHA não encontrado dentro do tempo limite: {e}", exc_info=True)
            return False
        except Exception as e:
            # Qualquer outra exceção inesperada durante o processo de resolução.
            # Loga como erro, mas retorna False para permitir novas tentativas se for um erro intermitente.
            logger.error(f"Ocorreu um erro inesperado durante a resolução do CAPTCHA com a API Gemini: {e}", exc_info=True)
            return False



