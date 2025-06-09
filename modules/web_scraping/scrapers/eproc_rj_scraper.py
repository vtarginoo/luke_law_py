import logging
from datetime import datetime
from typing import Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, \
    UnexpectedAlertPresentException

from modules.models.process_dtos import ProcessoScrapedDTO
from modules.models.process_models import Processo, Movimento
from modules.models.utils.process_mapper import ProcessMapper
from modules.web_scraping.scrapers.base_scrapper import BaseScraper
from modules.web_scraping.scrapers.captcha_resolver import CaptchaResolvers
from modules.web_scraping.selenium_utils import WebDriverFactory
from modules.models.exception.exceptions import (
    ScraperTechnicalException,
    ScraperBusinessException,
    ProcessNotFoundException,
    CaptchaResolutionFailedException
)
# Assumindo que Processo e Movimento estão definidos em process_models.py

logger = logging.getLogger(__name__)

class EprocRjScraper(BaseScraper):
    """
    Scraper para processos no Eproc-RJ (TJRJ).
    Versão simplificada para focar na navegação e preenchimento.
    """
    def __init__(self):
        self.DEFAULT_TIMEOUT = 10 # Aumentei um pouco para estabilidade
        self.EPROC_URL = "https://eproc1g-cp.tjrj.jus.br/eproc/externo_controlador.php?acao=processo_consulta_publica"
        self.MAX_CAPTCHA_ATTEMPTS = 5

    def captcha_resolution_iteration(self, driver: WebDriver, wait: WebDriverWait, search_field_id: str) -> bool:
        """
        Tenta resolver o CAPTCHA e submeter a busca.
        Retorna True se resolvido e submetido com sucesso, False caso contrário.
        """
        for attempt in range(1, self.MAX_CAPTCHA_ATTEMPTS + 1):
            logger.info(f"Tentativa de resolução de CAPTCHA {attempt}/{self.MAX_CAPTCHA_ATTEMPTS}...")

            captcha_response_text = CaptchaResolvers.gemini_captcha_text_resolver(
                driver,
                captcha_img_locator=(By.XPATH, "//div[@id='divInfraCaptcha']//img"),
                captcha_input_locator=(By.ID, "txtInfraCaptcha"),
                timeout=self.DEFAULT_TIMEOUT
            )

            if captcha_response_text:
                logger.info("CAPTCHA resolvido pela API. Tentando submeter e verificar...")
                try:
                    search_field_after_captcha = wait.until(EC.element_to_be_clickable((By.ID, search_field_id)))
                    search_field_after_captcha.send_keys(Keys.ENTER)

                    # Esperar 2 segundos para ver se o CAPTCHA desaparece
                    WebDriverWait(driver, 2).until(EC.invisibility_of_element_located((By.ID, "divInfraCaptcha")))
                    logger.debug("CAPTCHA desapareceu. Resolução bem-sucedida.")
                    return True # CAPTCHA resolvido e submetido com sucesso

                except UnexpectedAlertPresentException as e:
                    logger.info("Alert Identificado | Erro Ao Resolver Captcha")
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
                    continue


                except TimeoutException:
                    logger.warning("CAPTCHA não desapareceu após submissão. Resposta da API pode não ter sido aceita.", exc_info=True)
            else:
                logger.info("API do CAPTCHA não conseguiu resolver a imagem.")

        logger.info(f"Falha ao resolver o CAPTCHA após {self.MAX_CAPTCHA_ATTEMPTS} tentativas.")
        return False # Todas as tentativas falharam

    def _scrape_acesso(self, driver: WebDriver, num_processo: str):
        """
        Navega até a página do Eproc, insere o número do processo e tenta resolver o CAPTCHA.
        Lança exceções se o campo de busca não for encontrado ou se o CAPTCHA falhar.
        """
        logger.info("Acessando a página de consulta pública do Eproc-RJ...")
        driver.get(self.EPROC_URL)

        wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)
        search_field_id = "txtNumProcesso"

        try:
            search_field = wait.until(EC.element_to_be_clickable((By.ID, search_field_id)))
            search_field.send_keys(num_processo)
            logger.debug(f"Número do processo '{num_processo}' inserido no Eproc.")
        except TimeoutException as e:
            raise ProcessNotFoundException(
                f"Campo de pesquisa '{search_field_id}' não encontrado ou não clicável na página do Eproc.")

        # Verifica e tenta resolver CAPTCHA
        try:
            # Espera para detectar o elemento do CAPTCHA
            wait.until(EC.presence_of_element_located((By.ID, "divInfraCaptcha")))
            logger.info("CAPTCHA detectado. Iniciando a resolução...")

            captcha_resolved = self.captcha_resolution_iteration(driver, wait, search_field_id)

            if not captcha_resolved:
                raise CaptchaResolutionFailedException(
                    message=f"Não foi possível solucionar o CAPTCHA para o processo {num_processo} após {self.MAX_CAPTCHA_ATTEMPTS} tentativas."
                )
            logger.info("CAPTCHA resolvido com sucesso.")

        except TimeoutException:
            logger.info("CAPTCHA element not detected within the timeout. Assuming no CAPTCHA is present.")
            pass

    def _scrape_dados(self, driver: WebDriver, num_processo: str) -> Processo:
        """
        Extrai os dados do processo da página do Eproc-RJ após acesso bem-sucedido.
        Lança exceções se elementos de dados não forem encontrados ou se houver erros de parsing.
        """
        logger.info("Iniciando extração de dados do processo Eproc...")
        wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)

        try:
            # Tribunal e Sistema são fixos para este scraper
            tribunal = "TJRJ"
            sistema = "Eproc"

            # --- 1. Extrair Dados da Capa do Processo ---
            # Verifica se o processo foi encontrado ou se há mensagem de erro
            if "Nenhum registro encontrado." in driver.page_source or "Processo não encontrado" in driver.page_source:
                 raise ProcessNotFoundException(num_processo=num_processo,
                                                message=f"Processo '{num_processo}' não encontrado no Eproc-RJ.")

            numero_processo_confirmado = wait.until(EC.presence_of_element_located((By.ID, "txtNumProcesso"))).text.strip()
            logger.debug(f"Número do Processo na página: {numero_processo_confirmado}")

            data_autuacao_str = wait.until(EC.presence_of_element_located((By.ID, "txtAutuacao"))).text.strip()
            try:
                data_autuacao = datetime.strptime(data_autuacao_str, "%d/%m/%Y %H:%M:%S")
            except ValueError as e:
                 raise ScraperTechnicalException(
                    f"Erro ao parsear data de autuação '{data_autuacao_str}' para processo {num_processo}.",
                    code="EPROC_AUTUACAO_DATE_PARSE_ERROR",
                    original_exception=e
                )
            logger.debug(f"Data de Autuação: {data_autuacao}")

            situacao = wait.until(EC.presence_of_element_located((By.ID, "txtSituacao"))).text.strip()
            orgao_julgador = wait.until(EC.presence_of_element_located((By.ID, "txtOrgaoJulgador"))).text.strip()
            juiz = wait.until(EC.presence_of_element_located((By.ID, "txtMagistrado"))).text.strip()
            grau = wait.until(EC.presence_of_element_located((By.ID, "txtClasse"))).text.strip()

            # --- 2. Extrair Partes Envolvidas ---
            partes_envolvidas_text = ""
            try:
                partes_table = wait.until(EC.presence_of_element_located((By.XPATH, "//fieldset[@id='fldPartes']/table")))
                partes_tds = partes_table.find_elements(By.TAG_NAME, "td")
                for td in partes_tds:
                    if td.text.strip():
                        partes_envolvidas_text += td.text.strip() + "; "
                partes_envolvidas = partes_envolvidas_text.strip().replace(";;", ";")
                logger.debug(f"Partes Envolvidas: {partes_envolvidas}")
            except TimeoutException:
                logger.warning("Tabela de Partes e Representantes não encontrada.")
                partes_envolvidas = "Não informado"

            # --- 3. Extrair Movimentos ---
            movimentos: List[Movimento] = []
            ultima_atualizacao: datetime = data_autuacao

            try:
                movimentos_table = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//table[contains(@class, 'infraTable') and .//th[text()='Data/Hora'] and .//th[text()='Descrição']]")
                    )
                )
                logger.debug("Tabela de Movimentos encontrada.")

                movimento_elements = movimentos_table.find_elements(By.XPATH, "./tbody/tr[./td]")
                logger.debug(f"Encontrados {len(movimento_elements)} elementos de movimento.")

                for i, elem in enumerate(movimento_elements):
                    try:
                        cols = elem.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 3:
                            data_hora_str = cols[1].text.strip()
                            nome_movimento = cols[2].text.strip()

                            try:
                                data_hora = datetime.strptime(data_hora_str, "%d/%m/%Y %H:%M:%S")
                            except ValueError:
                                # Tenta formato alternativo sem segundos se o primeiro falhar
                                try:
                                    data_hora = datetime.strptime(data_hora_str, "%d/%m/%Y %H:%M")
                                except ValueError as e:
                                    logger.warning(f"Não foi possível parsear a data e hora '{data_hora_str}' do movimento. Usando a hora atual.", exc_info=True)
                                    data_hora = datetime.now() # Fallback seguro

                            mov = Movimento(ordem=i + 1, nome=nome_movimento, dataHora=data_hora)
                            movimentos.append(mov)

                            if data_hora > ultima_atualizacao:
                                ultima_atualizacao = data_hora
                        else:
                            logger.warning(f"Linha de movimento com número de colunas inesperado: {len(cols)}")
                    except NoSuchElementException as e:
                        logger.warning(f"Pulando um movimento devido a elemento ausente: {e}", exc_info=True)

            except TimeoutException:
                logger.warning("Tabela de movimentos não encontrada. Lista de movimentos estará vazia.")
            except Exception as e:
                logger.error(f"Ocorreu um erro ao tentar encontrar elementos de movimento: {e}", exc_info=True)

            # --- 4. Construir e Retornar o Objeto Processo ---
            processo = Processo(
                partesEnvolvidas=partes_envolvidas,
                numeroProcesso=num_processo,
                tribunal=tribunal,
                sistema=sistema,
                grau=grau,
                movimentos=movimentos,
                dataHoraUltimaAtualizacao=ultima_atualizacao
            )
            logger.info("Dados do processo extraídos com sucesso.")
            return processo
        except (TimeoutException, NoSuchElementException) as e:
            # Captura erros comuns de Selenium na extração de dados e os relança como técnicos
            raise ScraperTechnicalException(
                f"Erro ao extrair dados do processo {num_processo}: Elemento não encontrado ou tempo limite excedido.",
                code="EPROC_DATA_EXTRACTION_FAILURE",
                original_exception=e
            )



    # Metodo Principal da classe
    def scrape_processo(self, num_processo: str) -> ProcessoScrapedDTO:
        """
        Realiza o scraping de um processo no Eproc-RJ.
        Executa a navegação, busca e extração de dados do processo.
        """
        driver: Optional[WebDriver] = None
        try:
            logger.info(f"Iniciando scraping do Eproc-RJ para o processo: {num_processo}")

            driver = WebDriverFactory.create_chrome_driver(headless=True)

            # 1. Chamar o metodo auxiliar para acesso inicial ao processo
            self._scrape_acesso(driver, num_processo)

            logger.info(f"Acesso inicial para o processo {num_processo} bem-sucedido. Iniciando extração de dados.")
            # _scrape_dados retorna a entidade Processo
            processo_entity: Processo = self._scrape_dados(driver, num_processo)

            # >>> PONTO DA CONVERSÃO: Entidade para DTO <<<
            processo_dto: ProcessoScrapedDTO = ProcessMapper.from_entity_to_dto(processo_entity)
            logger.info(f"Entidade Processo convertida para ProcessoScrapedDTO para {num_processo}.")

            logger.info(f"Objeto ProcessoScrapedDTO Extraído e Convertido com Sucesso para {num_processo}!")
            # O debug agora mostra o DTO que será retornado
            logger.debug(processo_dto.model_dump_json(indent=2, exclude_none=True))

            return processo_dto

            # Captura as exceções customizadas e as relança para o handler global
        except (ScraperTechnicalException, ScraperBusinessException, CaptchaResolutionFailedException,
                ProcessNotFoundException):
            raise
            # Captura exceções gerais do WebDriver no nível mais alto se não forem tratadas antes
        except WebDriverException as e:
            logger.error(f"Erro de WebDriver (Eproc) para processo {num_processo}: {e}", exc_info=True)
            raise ScraperTechnicalException(
                f"Erro no WebDriver durante scraping do Eproc-RJ para {num_processo}.",
                code="EPROC_WEBDRIVER_ERROR",
                original_exception=e
            )
        except Exception as e:
            # Captura qualquer exceção genérica não esperada
            logger.critical(f"Erro inesperado e não tratado durante o scraping do Eproc-RJ para {num_processo}: {e}",
                            exc_info=True)
            raise ScraperTechnicalException(
                f"Erro inesperado no scraping do Eproc-RJ para {num_processo}.",
                code="EPROC_UNEXPECTED_ERROR",
                original_exception=e
            )
        finally:
            if driver:
                driver.quit()
                logger.info("WebDriver do Eproc encerrado.")
