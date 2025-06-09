import logging
import re
import time
from datetime import datetime, timedelta
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, \
    UnexpectedAlertPresentException

from modules.models.process_dtos import ProcessoScrapedDTO
# Importa os modelos Pydantic
from modules.models.process_models import Processo, Movimento
from modules.models.utils.process_mapper import ProcessMapper
from modules.web_scraping.scrapers.base_scrapper import BaseScraper
from modules.web_scraping.selenium_utils import WebDriverFactory  # Importa a fábrica do WebDriver
from modules.models.exception.exceptions import (
    ScraperTechnicalException,
    ProcessNotFoundException, BaseScrapingException

)

logger = logging.getLogger(__name__)

class PjeRjScraper(BaseScraper):
    """
    Classe responsável por realizar o web scraping de processos no sistema PJE do TJRJ.
    """

    def __init__(self):
        self.QUICK_TIMEOUT = 3 # Timeouts curtos
        self.DEFAULT_TIMEOUT = 10  # Aumentei um pouco para estabilidade
        self.PJE_URL = "https://tjrj.pje.jus.br/1g/ConsultaPublica/listView.seam"
        pass

    def _add_cookies_and_local_storage(self, driver: WebDriver):
        """Adiciona cookies e itens ao localStorage para evitar detecção ou popups."""
        try:
            rx_visitor_cookie = {
                'name': 'rxvisitor',
                'value': '1722960632647NRQOMJVLQSK7UM5RBBNRF8S5QGFHD1R7',
                'domain': '.tjrj.pje.jus.br',
                'path': '/',
                'secure': True,
                'httpOnly': False,
                'expiry': int((datetime.now() + timedelta(days=30)).timestamp())
            }
            driver.add_cookie(rx_visitor_cookie)
            driver.execute_script(
                "window.localStorage.setItem('rxvisitor', '1722960632647NRQOMJVLQSK7UM5RBBNRF8S5QGFHD1R7');"
            )
            logger.debug("Cookie 'rxvisitor' e localStorage adicionados.")
        except Exception as e:
            logger.warning(f"Não foi possível adicionar cookies/localStorage: {e}", exc_info=True)


    def _navigate_and_search(self, driver: WebDriver, num_processo: str, wait: WebDriverWait):
        """Navega para a URL do PJE e insere o número do processo."""
        logger.info(f"Navegando para o PJE URL: {self.PJE_URL}")
        driver.get(self.PJE_URL)
        logger.debug(f"Acessada URL: {self.PJE_URL}")

        self._add_cookies_and_local_storage(driver)
        driver.refresh() # Recarrega a página para aplicar os cookies

        search_field_id = "fPP:numProcesso-inputNumeroProcessoDecoration:numProcesso-inputNumeroProcesso"
        try:
            search_field = wait.until(EC.element_to_be_clickable((By.ID, search_field_id)))
            search_field.send_keys(num_processo)
            logger.info("vou apertar o enter")
            search_field.send_keys(Keys.ENTER)
            logger.info("Número do processo inserido e Enter pressionado.")

        except UnexpectedAlertPresentException as e:
            logger.info("Alert Identificado")
            raise ProcessNotFoundException(
                num_processo=num_processo,
                message=f"Processo '{num_processo}' não encontrado no PJE-RJ."
            )

        except (TimeoutException, NoSuchElementException) as e:
            # Se o campo de pesquisa original não for encontrado ou clicável, é um erro técnico.
            raise ScraperTechnicalException(
                f"Campo de pesquisa '{search_field_id}' não encontrado ou não clicável na página do PJE.",
                code="PJE_SEARCH_FIELD_UNAVAILABLE",
                original_exception=e
            )



        #================================================================================

        # Lógica de redirecionamento de login
        time.sleep(2)  # Pequena espera para verificar redirecionamento
        if "login" in driver.current_url.lower():
            logger.info("Redirecionado para a página de login, voltando e reenviando a busca...")
            driver.back()

            try:
                search_field = wait.until(EC.element_to_be_clickable((By.ID, search_field_id)))
                search_field.clear()
                search_field.send_keys(num_processo)
                logger.info("Reenviando número do processo após login e apertando Enter.")
                search_field.send_keys(Keys.ENTER)
                logger.info("Busca reenviada após retorno da página de login.")

            except UnexpectedAlertPresentException as e:  # Captura alerta após reenvio
                logger.info("Alerta identificado após reenvio da busca.")
                raise ProcessNotFoundException(
                    num_processo=num_processo,
                    message=f"Processo '{num_processo}' não encontrado no PJE-RJ."
                )
            except TimeoutException as e:
                raise ScraperTechnicalException(
                    "Campo de pesquisa não ficou clicável após retorno da página de login e reenvio da busca.",
                    code="PJE_SEARCH_FIELD_RETRY_FAILED",
                    original_exception=e
                )

    def _extract_data(self, driver: WebDriver, num_processo: str, wait: WebDriverWait) -> Processo:
        """Extrai os dados do processo da tabela de resultados do PJE."""
        table_body_xpath = "//tbody[@id='fPP:processosTable:tb']"
        first_row_xpath = f"{table_body_xpath}/tr[1]"
        quick_wait = WebDriverWait(driver, self.QUICK_TIMEOUT)

        # --- Extração da última movimentação ---
        ultima_movimentacao_str: str
        try:
            movimentacao_element = wait.until(
                EC.visibility_of_element_located((By.XPATH, f"{first_row_xpath}/td[3]"))
            )
            ultima_movimentacao_str = movimentacao_element.text
            logger.info(f"Última movimentação capturada: '{ultima_movimentacao_str}'")
        except (TimeoutException, NoSuchElementException) as e:
            # Verifica se é um caso de processo não encontrado antes de lançar erro técnico
            raise ProcessNotFoundException(num_processo=num_processo)

        # --- Extração das partes envolvidas ---
        partes_envolvidas: str
        try:
            partes_element = wait.until(
                EC.visibility_of_element_located((By.XPATH, f"{first_row_xpath}/td[2]"))
            )
            texto_completo_td = partes_element.text
            try:
                link_element = partes_element.find_element(By.TAG_NAME, "a")
                texto_link = link_element.text
                partes_envolvidas_raw = texto_completo_td.replace(texto_link, "").strip()
                lines = partes_envolvidas_raw.split('\n')
                partes_envolvidas = "\n".join(lines[1:]).strip() if len(lines) > 1 else partes_envolvidas_raw
                logger.info(f"Partes envolvidas capturadas: '{partes_envolvidas}'")
            except NoSuchElementException:
                partes_envolvidas = texto_completo_td.strip()
                logger.info(f"Partes envolvidas capturadas (sem link): '{partes_envolvidas}'")
            except Exception as e:
                logger.warning(f"Erro ao extrair partes envolvidas, usando texto bruto do TD. Erro: {e}", exc_info=True)
                partes_envolvidas = texto_completo_td.strip() # Fallback
        except (TimeoutException, NoSuchElementException) as e:
            raise ScraperTechnicalException(
                "Não foi possível encontrar o elemento das partes envolvidas.",
                code="PJE_PARTIES_ELEMENT_MISSING",
                original_exception=e
            )

        # --- Processar última movimentação para Movimento ---
        ultimo_movimento: Movimento
        try:
            match = re.search(r'\((\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})\)', ultima_movimentacao_str)
            if match:
                data_hora_str_completa = match.group(1)
                descricao = ultima_movimentacao_str.split('(')[0].strip()
                data_hora_obj = datetime.strptime(data_hora_str_completa, "%d/%m/%Y %H:%M:%S")
            else:
                raise ValueError(f"Formato de data/hora esperado não encontrado na string da movimentação: '{ultima_movimentacao_str}'")

            ultimo_movimento = Movimento(ordem=1, nome=descricao, dataHora=data_hora_obj)
            logger.debug(f"Último movimento criado: {ultimo_movimento}")
        except Exception as e:
            raise ScraperTechnicalException(
                f"Falha ao processar última movimentação: '{ultima_movimentacao_str}'",
                code="PJE_MOVIMENTATION_PARSING_ERROR",
                original_exception=e
            )

        # --- Montar o objeto Processo ---
        processo_scraped = Processo(
            partesEnvolvidas=partes_envolvidas,
            numeroProcesso=num_processo,
            tribunal="TJRJ",
            sistema="Pje",
            grau="1ª Instância",
            movimentos=[ultimo_movimento],
            dataHoraUltimaAtualizacao=ultimo_movimento.dataHora
        )
        logger.info(f"Processo capturado com sucesso para {num_processo}.")
        return processo_scraped

    def scrape_processo(self, num_processo: str) -> ProcessoScrapedDTO:
        """
        Realiza o scraping de um processo no PJE e retorna um objeto Processo.
        Este é o metodo principal que orquestra as etapas e trata as exceções.

        :param num_processo: O número do processo formatado.
        :return: Um objeto Processo com os dados raspados.
        :raises BaseScrapingException: Se ocorrer qualquer erro durante o scraping (técnico ou de negócio).
        """
        driver: Optional[WebDriver] = None
        try:
            logger.info(f"Iniciando scraping do PJE para o processo: {num_processo}")

            driver = WebDriverFactory.create_chrome_driver(headless=True)
            wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)

            # Navega e realiza a busca
            logger.info(f"Navegação e busca iniciada")
            self._navigate_and_search(driver, num_processo, wait)

            # Extrai os dados do processo
            logger.info(f"Captura do Processo")
            processo_entity = self._extract_data(driver, num_processo, wait)

            logger.info(f"Transformação para DTO Iniciada")
            processo_dto: ProcessoScrapedDTO = ProcessMapper.from_entity_to_dto(processo_entity)

            return processo_dto

        except BaseScrapingException: # Captura qualquer uma das nossas exceções base e as relança
            raise
        except (TimeoutException, NoSuchElementException, WebDriverException, ProcessNotFoundException) as e:
            # Captura exceções comuns do Selenium não tratadas em métodos internos
            logger.error(f"Erro técnico de WebDriver/elemento no PJE para processo {num_processo}: {e}", exc_info=True)
            raise ScraperTechnicalException(
                f"Erro técnico durante o scraping do PJE para {num_processo}. Problema com o navegador ou elementos da página.",
                code="PJE_WEBDRIVER_ERROR",
                original_exception=e
            )
        except Exception as e:
            # Captura qualquer outra exceção genérica e inesperada
            logger.critical(f"Erro inesperado e não tratado durante o scraping do PJE para {num_processo}: {e}", exc_info=True)
            raise ScraperTechnicalException(
                f"Erro inesperado no scraping do PJE para {num_processo}.",
                code="PJE_UNEXPECTED_ERROR",
                original_exception=e
            )
        finally:
            if driver:
                driver.quit()
                logger.info("WebDriver do PJE encerrado.")








