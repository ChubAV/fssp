from playwright.async_api import async_playwright
import structlog
from twocaptcha import AsyncTwoCaptcha
from bs4 import BeautifulSoup

from src.config import Settings
from src.schemas import DebItemList, IpNumber, Person, Inn

logger = structlog.get_logger()


def parse_fssp_ip_data(html: str):

    soup = BeautifulSoup(html, "lxml")

    table = soup.select_one(".results-frame table.list")
    if not table:
        return []

    current_region = None
    rows = []
    for tr in table.select("tr"):
        # пропускаем шапку и строки-заголовки региона
        if tr.select("th"):
            continue
        if "region-title" in tr.get("class", []):
            current_region = tr.get_text(strip=True)
            continue

        tds = tr.select("td")
        if len(tds) != 8:
            continue

        rows.append({
            "region": current_region,
            "debtor": " ".join(tds[0].stripped_strings),
            "ip": " ".join(tds[1].stripped_strings),
            "doc": " ".join(tds[2].stripped_strings),
            "end_reason": " ".join(tds[3].stripped_strings),
            # "service": " ".join(tds[4].stripped_strings),
            "debt": " ".join(tds[5].stripped_strings),
            "office": " ".join(tds[6].stripped_strings),
            "bailiff": " ".join(tds[7].stripped_strings),
        })

    return rows

async def request_to_rucaptcha(api_key, file_capthca="captcha.png"):
    """ Распознает капчу и возвращает результат через API RuCaptcha
    Args:
        api_key: API ключ для RuCaptcha
        file_capthca: Путь к файлу с капчей
    Returns:
        dict: Результат распознавания капчи {'captchaId': '81352489150', 'code': '20114'}
    """
    logger.debug('Пытаемся распознать капчу через API RuCaptcha', file_capthca=file_capthca)
    result = {'captchaId': None, 'code': None}
    solver = AsyncTwoCaptcha(api_key)
    try:
        result = await solver.normal(str(file_capthca), numeric=1)
        logger.debug('Результат распознавания капчи', result=result)
    except Exception as e:
        logger.error('Ошибка распознания капчи', error=e)

    return result

async def solve_captcha(api_key, file_capthca="captcha.png"):
    result = await request_to_rucaptcha(api_key, file_capthca)
    return result['code']

async def get_browser_data(url: str, settings: Settings):
    """ Получает данные по ИП через браузер
    Args:
        url: URL ссылка с параметрами для поиска
        settings настройки проекта
    Returns:
        dict: Данные по ИП
    """
    temp_path = settings.TEMP_PATH
    api_key = settings.RUCAPTCH_API_KEY
    logger.debug('Получаем данные по ИП из ФССП', url=url)

    
    async with async_playwright() as playwright:
        logger.debug('Запускаем браузер')
        browser = await playwright.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        logger.debug('Переходим на страницу ФССП', url=url)
        await page.goto(
        url,
        timeout=60000,
        wait_until="domcontentloaded",
        )
        
        logger.debug('Ждем загрузки капчи', selector="img#capchaVisualImage")
        await page.wait_for_selector("img#capchaVisualImage", timeout=60000)
        
        logger.debug('Выключаем таймеры')
        await page.evaluate("for (let i = 1; i < 99999; i++) clearInterval(i)")
        
        logger.debug('Получаем элемент капчи в браузере', selector="img#capchaVisualImage")
        img = await page.wait_for_selector("img#capchaVisualImage", timeout=60000)
        
        logger.debug('Сохраняем капчу в файл', path="captcha.png")
        await img.screenshot(path=temp_path / "captcha.png")
        
        captcha_code = await solve_captcha(api_key, file_capthca=temp_path / "captcha.png")
        
        logger.debug('Заполняем капчу в браузере', captcha_code=captcha_code)
        await page.locator("#captcha-popup-code").click()
        await page.locator("#captcha-popup-code").fill(str(captcha_code))
        await page.get_by_role("button", name="Отправить").click()
        
        
        results_ip = await page.wait_for_selector(".results", timeout=5000)  # 5 секунд
        logger.debug('Скриншотим результаты поиска в файл', path=temp_path / "fullpage.png")
        await results_ip.screenshot(path=temp_path / "fullpage.png")
        html = await results_ip.inner_html()
        logger.debug('Парсим результаты поиска')
        data = parse_fssp_ip_data(html)
        
        
        logger.debug('Закрываем браузер')
        await page.close()
        await context.close()
        await browser.close()

    return data

async def get_fssp_data_by_ip(ip_number: IpNumber, settings: Settings):
    """ Получает данные по ИП из ФССП
    Args:
        ip_number: Номер ИП
        settings настройки проекта
    Returns:
        dict: Данные по ИП
    """
    url_fssp_ip = settings.URL_FSSP_IP.format(ip_number=ip_number.ip)
    data = await get_browser_data(url_fssp_ip, settings)
    return DebItemList(root=data)

async def get_fssp_data_by_person(person: Person, settings: Settings):
    """ Получает данные по человеку из ФССП
    Args:
        person: данные о человеке
        settings настройки проекта
    Returns:
        dict: Данные по ИП
    """
    url_fssp_person = settings.URL_FSSP_PERSON.format(last_name=person.last_name, first_name=person.first_name, patronymic=person.patronymic, birthday=person.birthday, region_id=-1)
    data = await get_browser_data(url_fssp_person, settings)
    return DebItemList(root=data)

async def get_fssp_data_by_inn(inn: Inn, settings: Settings):
    """ Получает данные по ИНН из ФССП
    Args:
        inn: ИНН
        settings настройки проекта
    Returns:
        dict: Данные по ИНН
    """
    url_fssp_inn = settings.URL_FSSP_INN.format(inn=inn.inn)
    data = await get_browser_data(url_fssp_inn, settings)
    return DebItemList(root=data)