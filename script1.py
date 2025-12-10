# from playwright.sync_api import Playwright, sync_playwright
from twocaptcha import TwoCaptcha
# from time import sleep


def request_to_rucaptcha(api_key, file_capthca="captcha.png"):
    result = False
    # logger.info(f'Пытаемся распознать капчу')
    solver = TwoCaptcha(api_key)
    # print(dir(solver))
    try:
        #   logger.info(f'Запрос на RuCaptcha')
        result = solver.normal(file_capthca, numeric=1)

    except Exception as e:
        #  logger.error(f'Ошибка распознания капчи - {str(e)}')
        print(e)

    return result


# def run(playwright: Playwright) -> None:
#     print("RUN")
#     browser = playwright.chromium.launch(
#         headless=True, args=["--disable-blink-features=AutomationControlled"]
#     )
#     context = browser.new_context()
#     page = context.new_page()
#     page.goto(
#         "https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=3&is%5Bip_number%5D=342956%2F24%2F23060-%D0%98%D0%9F",
#         timeout=60000,
#         wait_until="domcontentloaded",
#     )
#     img = page.wait_for_selector("img#capchaVisualImage", timeout=60000)
#     page.evaluate("for (let i = 1; i < 99999; i++) clearInterval(i)")
#     # sleep(15)
#     # print("Выключаем таймеры")
#     # page.add_init_script("for (let i = 1; i < 99999; i++) window.clearInterval(i);")
#     # page.add_init_script("console.log('TEST')")
#     # sleep(10)
#     img: ElementHandle | None = page.wait_for_selector(
#         "img#capchaVisualImage", timeout=60000
#     )
#     img.screenshot(path="captcha.png")
#     result = request_to_rucaptcha("")
#     print(result)
#     page.locator("#captcha-popup-code").click()
#     # sleep(10)
#     page.locator("#captcha-popup-code").fill(str(result["code"]))
#     sleep(5)
#     page.get_by_role("button", name="Отправить").click()
#     sleep(5)
#     page.screenshot(path="fullpage.png", full_page=True)

#     page.close()

#     # ---------------------
#     context.close()
#     browser.close()


# with sync_playwright() as playwright:
#     print("Старт браузер")
#     run(playwright)
