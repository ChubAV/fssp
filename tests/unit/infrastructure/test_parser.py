"""Unit-тесты для FsspHtmlParser."""

import pytest

from src.infrastructure.parser import FsspHtmlParser
from src.domain.errors import CaptchaLimitExceeded, ParsingError


@pytest.fixture
def parser():
    """Создать парсер."""
    return FsspHtmlParser()


def test_parse_cases_success(parser, sample_html_result):
    """Тест успешного парсинга результатов."""
    # Act
    cases = parser.parse_cases(sample_html_result)

    # Assert
    assert len(cases) == 1
    assert cases[0]["debtor"] == "Иванов Иван Иванович"
    assert cases[0]["ip"] == "1234567/12/34/56"
    assert cases[0]["region"] == "Московская область"
    assert cases[0]["debt"] == "100000.00"


def test_parse_cases_empty_table(parser):
    """Тест парсинга пустой таблицы."""
    # Arrange
    html = '<div class="results"><div>Нет результатов</div></div>'

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert cases == []


def test_parse_cases_captcha_limit_exceeded(parser):
    """Тест обработки превышения лимита капчи."""
    # Arrange
    html = '''
    <div class="results">
        <div class="empty">Количество неверных попыток ввода кода превышено</div>
    </div>
    '''

    # Act & Assert
    with pytest.raises(CaptchaLimitExceeded, match="Превышено количество"):
        parser.parse_cases(html)


def test_parse_cases_multiple_rows(parser):
    """Тест парсинга нескольких строк."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Москва</tr>
            <tr>
                <td>Должник 1</td>
                <td>111/11/11/11</td>
                <td>DOC1</td>
                <td></td>
                <td></td>
                <td>1000</td>
                <td>ОСП 1</td>
                <td>Пристав 1</td>
            </tr>
            <tr>
                <td>Должник 2</td>
                <td>222/22/22/22</td>
                <td>DOC2</td>
                <td></td>
                <td></td>
                <td>2000</td>
                <td>ОСП 2</td>
                <td>Пристав 2</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 2
    assert cases[0]["debtor"] == "Должник 1"
    assert cases[1]["debtor"] == "Должник 2"
    assert all(case["region"] == "Москва" for case in cases)


def test_parse_physical_person_debtor(parser):
    """Тест парсинга должника - физического лица."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Республика Адыгея</tr>
            <tr>
                <td class="first">
                    ИСАЕВ МИСТО НАДРОВИЧ
                    <br>
                    30.06.1995
                    <br>
                    С. КРАСНОГВАРДЕЙСКОЕ КРАСНОГВАРДЕЙСКИЙ РАЙОН РЕСПУБЛИКА АДЫГЕЯ
                </td>
                <td>12345/20/01001-ИП</td>
                <td>Судебный приказ от 01.01.2020</td>
                <td></td>
                <td></td>
                <td>50000.00</td>
                <td>ОСП Красногвардейского района</td>
                <td>Иванов И.И.</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем базовое поле
    assert case["debtor"] == "ИСАЕВ МИСТО НАДРОВИЧ 30.06.1995 С. КРАСНОГВАРДЕЙСКОЕ КРАСНОГВАРДЕЙСКИЙ РАЙОН РЕСПУБЛИКА АДЫГЕЯ"
    
    # Проверяем тип должника
    assert case["debtor_type"] == "physical"
    
    # Проверяем ФИО
    assert case["debtor_last_name"] == "ИСАЕВ"
    assert case["debtor_first_name"] == "МИСТО"
    assert case["debtor_patronymic"] == "НАДРОВИЧ"
    
    # Проверяем дату и место рождения
    assert case["debtor_birthday"] == "30.06.1995"
    assert case["debtor_birthplace"] == "С. КРАСНОГВАРДЕЙСКОЕ КРАСНОГВАРДЕЙСКИЙ РАЙОН РЕСПУБЛИКА АДЫГЕЯ"
    
    # Проверяем, что поля для юр. лиц пустые
    assert case.get("debtor_name") is None
    assert case.get("debtor_address") is None
    assert case.get("debtor_inn") is None


def test_parse_legal_entity_debtor(parser):
    """Тест парсинга должника - юридического лица."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Краснодарский край</tr>
            <tr>
                <td class="first">
                    ООО"НАВИГАТОР ПЛЮС"
                    <br>
                    354200,23, СОЧИ Г, ЛАЗАРЕВА УЛ,40
                    <br>
                    <br>
                    2318027030
                </td>
                <td>13365/16/23050-ИП</td>
                <td>Акт органа от 10.03.2016</td>
                <td></td>
                <td></td>
                <td>10064.28</td>
                <td>Лазаревское РОСП г. Сочи</td>
                <td>ЛЕВЧЕНКО Ю. А.</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем базовое поле
    assert 'ООО"НАВИГАТОР ПЛЮС"' in case["debtor"]
    assert "2318027030" in case["debtor"]
    
    # Проверяем тип должника
    assert case["debtor_type"] == "legal"
    
    # Проверяем наименование организации
    assert case["debtor_name"] == 'ООО"НАВИГАТОР ПЛЮС"'
    
    # Проверяем юридический адрес
    assert case["debtor_address"] == "354200,23, СОЧИ Г, ЛАЗАРЕВА УЛ,40"
    
    # Проверяем ИНН
    assert case["debtor_inn"] == "2318027030"
    
    # Проверяем, что поля для физ. лиц пустые
    assert case.get("debtor_last_name") is None
    assert case.get("debtor_first_name") is None
    assert case.get("debtor_patronymic") is None
    assert case.get("debtor_birthday") is None
    assert case.get("debtor_birthplace") is None


def test_parse_mixed_debtors(parser):
    """Тест парсинга смешанного списка должников (физ. и юр. лица)."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Москва</tr>
            <tr>
                <td class="first">
                    ПЕТРОВ ПЕТР ПЕТРОВИЧ
                    <br>
                    15.03.1985
                    <br>
                    Г. МОСКВА
                </td>
                <td>11111/21/77001-ИП</td>
                <td>Судебный приказ</td>
                <td></td>
                <td></td>
                <td>25000.00</td>
                <td>ОСП Москва</td>
                <td>Сидоров А.А.</td>
            </tr>
            <tr>
                <td class="first">
                    ООО "РОГА И КОПЫТА"
                    <br>
                    123456, МОСКВА, УЛ. ЛЕНИНА, 1
                    <br>
                    <br>
                    7701234567
                </td>
                <td>22222/21/77002-ИП</td>
                <td>Акт налогового органа</td>
                <td></td>
                <td></td>
                <td>100000.00</td>
                <td>ОСП Москва</td>
                <td>Иванова Б.Б.</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 2
    
    # Первый должник - физическое лицо
    assert cases[0]["debtor_type"] == "physical"
    assert cases[0]["debtor_last_name"] == "ПЕТРОВ"
    assert cases[0]["debtor_birthday"] == "15.03.1985"
    
    # Второй должник - юридическое лицо
    assert cases[1]["debtor_type"] == "legal"
    assert cases[1]["debtor_name"] == 'ООО "РОГА И КОПЫТА"'
    assert cases[1]["debtor_inn"] == "7701234567"


def test_parse_doc_info_with_court(parser):
    """Тест парсинга документа с судебным решением."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Краснодарский край</tr>
            <tr>
                <td>Должник</td>
                <td>12345/25/23001-ИП</td>
                <td>
                    Исполнительный лист от 04.06.2025 № 23RS0047#2-3147/2025#2
                    <br>
                    <br>
                    СОВЕТСКИЙ РАЙОННЫЙ СУД Г.КРАСНОДАРА
                    <br>
                    7707083893
                </td>
                <td></td>
                <td></td>
                <td>50000.00</td>
                <td>ОСП</td>
                <td>Пристав</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем полный документ (обратная совместимость)
    assert "Исполнительный лист от 04.06.2025 № 23RS0047#2-3147/2025#2" in case["doc"]
    assert "СОВЕТСКИЙ РАЙОННЫЙ СУД Г.КРАСНОДАРА" in case["doc"]
    assert "7707083893" in case["doc"]
    
    # Проверяем распарсенные поля
    assert case["doc_basis"] == "Исполнительный лист от 04.06.2025 № 23RS0047#2-3147/2025#2"
    assert case["doc_issuer"] == "СОВЕТСКИЙ РАЙОННЫЙ СУД Г.КРАСНОДАРА"
    assert case["creditor_inn"] == "7707083893"


def test_parse_doc_info_with_tax_authority(parser):
    """Тест парсинга документа с актом налогового органа."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Краснодарский край</tr>
            <tr>
                <td>Должник</td>
                <td>12345/25/23001-ИП</td>
                <td>
                    Акт органа, осуществляющего контрольные функции от 16.09.2025 № 1131
                    <br>
                    <br>
                    ИНСПЕКЦИЯ ФЕДЕРАЛЬНОЙ НАЛОГОВОЙ СЛУЖБЫ ПО Г. НОВОРОССИЙСКУ КРАСНОДАРСКОГО КРАЯ
                    <br>
                    2315020237
                    <br>
                    Постановление о взыскании исполнительского сбора
                </td>
                <td></td>
                <td></td>
                <td>10000.00</td>
                <td>ОСП</td>
                <td>Пристав</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем распарсенные поля
    assert case["doc_basis"] == "Акт органа, осуществляющего контрольные функции от 16.09.2025 № 1131"
    assert case["doc_issuer"] == "ИНСПЕКЦИЯ ФЕДЕРАЛЬНОЙ НАЛОГОВОЙ СЛУЖБЫ ПО Г. НОВОРОССИЙСКУ КРАСНОДАРСКОГО КРАЯ"
    assert case["creditor_inn"] == "2315020237"
    
    # Проверяем, что постановление игнорируется в парсинге, но остается в полном тексте
    assert "Постановление о взыскании исполнительского сбора" in case["doc"]


def test_parse_doc_info_multiple_cases(parser):
    """Тест парсинга документов в нескольких делах."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Москва</tr>
            <tr>
                <td>Должник 1</td>
                <td>11111/25/77001-ИП</td>
                <td>
                    Исполнительный лист от 01.01.2025 № 001
                    <br>
                    <br>
                    ТВЕРСКОЙ РАЙОННЫЙ СУД Г.МОСКВЫ
                    <br>
                    7701234567
                </td>
                <td></td>
                <td></td>
                <td>25000.00</td>
                <td>ОСП 1</td>
                <td>Пристав 1</td>
            </tr>
            <tr>
                <td>Должник 2</td>
                <td>22222/25/77002-ИП</td>
                <td>
                    Акт налогового органа от 15.02.2025 № 456
                    <br>
                    <br>
                    ИФНС № 1 ПО Г.МОСКВЕ
                    <br>
                    7702345678
                    <br>
                    Постановление о взыскании исполнительского сбора
                </td>
                <td></td>
                <td></td>
                <td>100000.00</td>
                <td>ОСП 2</td>
                <td>Пристав 2</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 2
    
    # Первое дело - суд
    assert cases[0]["doc_basis"] == "Исполнительный лист от 01.01.2025 № 001"
    assert cases[0]["doc_issuer"] == "ТВЕРСКОЙ РАЙОННЫЙ СУД Г.МОСКВЫ"
    assert cases[0]["creditor_inn"] == "7701234567"
    
    # Второе дело - налоговая
    assert cases[1]["doc_basis"] == "Акт налогового органа от 15.02.2025 № 456"
    assert cases[1]["doc_issuer"] == "ИФНС № 1 ПО Г.МОСКВЕ"
    assert cases[1]["creditor_inn"] == "7702345678"


def test_parse_debt_info_with_tax(parser):
    """Тест парсинга информации о долге (налоги)."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Регион</tr>
            <tr>
                <td>Должник</td>
                <td>12345/25/01-ИП</td>
                <td>Документ</td>
                <td></td>
                <td></td>
                <td>
                    Взыскание налогов и сборов, включая пени (кроме таможенных)
                    <br>
                    <br>
                    Сумма долга: 194054.92 руб.
                    <br>
                    <br>
                    Остаток долга по исполнительному документу: 177735.51 руб.
                    <br>
                    <br>
                    Исполнительский сбор: 15419.41 руб.
                </td>
                <td>ОСП</td>
                <td>Пристав</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем полную строку (обратная совместимость)
    assert "Взыскание налогов и сборов" in case["debt"]
    assert "194054.92" in case["debt"]
    
    # Проверяем распарсенные поля
    assert case["debt_type"] == "Взыскание налогов и сборов, включая пени (кроме таможенных)"
    assert case["debt_amount"] == "194054.92"
    assert case["debt_remaining"] == "177735.51"
    assert case["debt_bailiff_fee"] == "15419.41"


def test_parse_debt_info_with_mortgage(parser):
    """Тест парсинга информации о долге (ипотека)."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Регион</tr>
            <tr>
                <td>Должник</td>
                <td>67890/25/02-ИП</td>
                <td>Документ</td>
                <td></td>
                <td></td>
                <td>
                    Задолженность по кредитным платежам (ипотека)
                    <br>
                    <br>
                    Сумма долга: 5534057.60 руб.
                    <br>
                    <br>
                    Остаток долга по исполнительному документу: 5172014.52 руб.
                    <br>
                    <br>
                    Исполнительский сбор: 362043.08 руб.
                </td>
                <td>ОСП</td>
                <td>Пристав</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем распарсенные поля
    assert case["debt_type"] == "Задолженность по кредитным платежам (ипотека)"
    assert case["debt_amount"] == "5534057.60"
    assert case["debt_remaining"] == "5172014.52"
    assert case["debt_bailiff_fee"] == "362043.08"


def test_parse_debt_info_multiple_cases(parser):
    """Тест парсинга долгов в нескольких делах."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Регион</tr>
            <tr>
                <td>Должник 1</td>
                <td>11111/25/01-ИП</td>
                <td>Документ 1</td>
                <td></td>
                <td></td>
                <td>
                    Взыскание налогов и сборов, включая пени (кроме таможенных)
                    <br>
                    <br>
                    Сумма долга: 10000.50 руб.
                    <br>
                    <br>
                    Остаток долга по исполнительному документу: 8000.25 руб.
                    <br>
                    <br>
                    Исполнительский сбор: 2000.25 руб.
                </td>
                <td>ОСП 1</td>
                <td>Пристав 1</td>
            </tr>
            <tr>
                <td>Должник 2</td>
                <td>22222/25/02-ИП</td>
                <td>Документ 2</td>
                <td></td>
                <td></td>
                <td>
                    Задолженность по кредитным платежам (ипотека)
                    <br>
                    <br>
                    Сумма долга: 500000.00 руб.
                    <br>
                    <br>
                    Остаток долга по исполнительному документу: 450000.00 руб.
                    <br>
                    <br>
                    Исполнительский сбор: 50000.00 руб.
                </td>
                <td>ОСП 2</td>
                <td>Пристав 2</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 2
    
    # Первое дело - налоги
    assert cases[0]["debt_type"] == "Взыскание налогов и сборов, включая пени (кроме таможенных)"
    assert cases[0]["debt_amount"] == "10000.50"
    assert cases[0]["debt_remaining"] == "8000.25"
    assert cases[0]["debt_bailiff_fee"] == "2000.25"
    
    # Второе дело - ипотека
    assert cases[1]["debt_type"] == "Задолженность по кредитным платежам (ипотека)"
    assert cases[1]["debt_amount"] == "500000.00"
    assert cases[1]["debt_remaining"] == "450000.00"
    assert cases[1]["debt_bailiff_fee"] == "50000.00"


def test_parse_debt_info_empty_amount(parser):
    """Тест парсинга долга с пустой суммой."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Регион</tr>
            <tr>
                <td>Должник</td>
                <td>12345/25/01-ИП</td>
                <td>Документ</td>
                <td></td>
                <td></td>
                <td>
                    Взыскание задолженности
                    <br>
                    <br>
                    Сумма долга:
                </td>
                <td>ОСП</td>
                <td>Пристав</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем, что тип задолженности есть
    assert case["debt_type"] == "Взыскание задолженности"
    
    # Проверяем, что сумма отсутствует (None)
    assert case.get("debt_amount") is None
    assert case.get("debt_remaining") is None
    assert case.get("debt_bailiff_fee") is None


def test_parse_debt_info_partial_data(parser):
    """Тест парсинга долга с частичными данными."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Регион</tr>
            <tr>
                <td>Должник</td>
                <td>12345/25/01-ИП</td>
                <td>Документ</td>
                <td></td>
                <td></td>
                <td>
                    Возмещение ущерба
                    <br>
                    <br>
                    Сумма долга: 100000.00 руб.
                    <br>
                    <br>
                    Остаток долга по исполнительному документу:
                </td>
                <td>ОСП</td>
                <td>Пристав</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем, что тип и сумма есть
    assert case["debt_type"] == "Возмещение ущерба"
    assert case["debt_amount"] == "100000.00"
    
    # Проверяем, что остаток и сбор отсутствуют
    assert case.get("debt_remaining") is None
    assert case.get("debt_bailiff_fee") is None


def test_parse_foreign_name_with_multiple_patronymic_parts(parser):
    """Тест парсинга иностранного имени с несколькими частями в отчестве."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Краснодарский край</tr>
            <tr>
                <td class="first">
                    АБУ ШАНАБ ТАРИК ЗИАД МУСТАФА 16.05.1992 ИОРДАНИЯ, Г. АЛЬ
                </td>
                <td>12345/20/23001-ИП</td>
                <td>Судебный приказ от 01.01.2020</td>
                <td></td>
                <td></td>
                <td>50000.00</td>
                <td>ОСП Краснодара</td>
                <td>Иванов И.И.</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем тип должника
    assert case["debtor_type"] == "physical"
    
    # Проверяем ФИО - отчество должно содержать все части
    assert case["debtor_last_name"] == "АБУ"
    assert case["debtor_first_name"] == "ШАНАБ"
    assert case["debtor_patronymic"] == "ТАРИК ЗИАД МУСТАФА"
    
    # Проверяем дату и место рождения
    assert case["debtor_birthday"] == "16.05.1992"
    assert case["debtor_birthplace"] == "ИОРДАНИЯ, Г. АЛЬ"


def test_parse_debt_info_only_type(parser):
    """Тест парсинга долга только с типом задолженности."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Регион</tr>
            <tr>
                <td>Должник</td>
                <td>12345/25/01-ИП</td>
                <td>Документ</td>
                <td></td>
                <td></td>
                <td>
                    Административный штраф
                </td>
                <td>ОСП</td>
                <td>Пристав</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 1
    case = cases[0]
    
    # Проверяем, что только тип задолженности есть
    assert case["debt_type"] == "Административный штраф"
    assert case["debt"] == "Административный штраф"
    
    # Проверяем, что все суммы отсутствуют
    assert case.get("debt_amount") is None
    assert case.get("debt_remaining") is None
    assert case.get("debt_bailiff_fee") is None
