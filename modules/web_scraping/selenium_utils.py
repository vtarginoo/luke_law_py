import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional


class WebDriverFactory:
    """
    Fábrica para criar e configurar instâncias do WebDriver do Chrome.
    """

    @staticmethod
    def create_chrome_driver(headless: bool = True, driver_path: Optional[str] = None) -> webdriver.Chrome:
        """
        Cria e configura uma instância do ChromeDriver.

        :param headless: Se True, executa o navegador em modo headless (sem UI). Padrão é True.
        :param driver_path: Caminho explícito para o chromedriver. Se None, usa webdriver_manager.
        :return: Uma instância do WebDriver do Chrome.
        :raises RuntimeError: Se não for possível configurar o serviço do ChromeDriver.
        """
        options = Options()

        # Configurações de headless
        if headless:
            options.add_argument("--headless=new") # Modo mais recente e recomendado para headless
            print("INFO: Executando Chrome em modo headless.")
        else:
            print("INFO: Executando Chrome com UI visível (não headless).")

        # Argumentos essenciais para ambientes de servidor/Docker e para evitar detecção
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu") # Bom para compatibilidade, especialmente em VMs
        options.add_argument("--remote-debugging-port=9222") # Útil para depuração remota

        # Estratégias para evitar a detecção do bot
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Configurações de interface
        options.add_argument("window-size=1600,800")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")

        service: ChromeService

        # Lógica para definir o caminho do chromedriver: Docker vs. Local
        if os.getenv("DOCKER_ENV", "false").lower() == "true":
            print("INFO: Detectado ambiente Docker.")
            if driver_path:
                # Se um caminho explícito for fornecido, use-o (ideal para Dockerfile que instala chromedriver)
                service = ChromeService(executable_path=driver_path)
                print(f"INFO: Usando chromedriver no caminho especificado: {driver_path}")
            else:
                # Em Docker, é altamente recomendado que o chromedriver esteja no PATH
                # ou que você forneça um `driver_path` via variável de ambiente ou config.
                # Se webdriver_manager for usado sem um driver_path, ele tentará baixar.
                try:
                    service = ChromeService(ChromeDriverManager().install())
                    print("INFO: Usando webdriver_manager para Docker (certifique-se de que o container tem as dependências para baixar).")
                except Exception as e:
                    print(f"ERRO: Não foi possível instalar o chromedriver via webdriver_manager no Docker: {e}")
                    print("Por favor, certifique-se de que o chromedriver está no PATH do container ou forneça um 'driver_path'.")
                    raise RuntimeError(f"Falha ao iniciar ChromeDriver em Docker: {e}")
        else:
            print("INFO: Detectado ambiente local.")
            if driver_path:
                service = ChromeService(executable_path=driver_path)
                print(f"INFO: Usando chromedriver no caminho especificado: {driver_path}")
            else:
                # Em ambiente local, webdriver_manager é a opção mais conveniente
                service = ChromeService(ChromeDriverManager().install())
                print("INFO: Usando chromedriver gerenciado automaticamente por webdriver_manager.")

        try:
            driver = webdriver.Chrome(service=service, options=options)
            print("INFO: WebDriver Chrome iniciado com sucesso.")
            return driver
        except Exception as e:
            print(f"ERRO: Falha ao iniciar WebDriver Chrome: {e}")
            raise RuntimeError(f"Não foi possível iniciar o WebDriver Chrome: {e}")



