from bs4 import BeautifulSoup
import structlog
import re
from src.domain.errors import ParsingError, CaptchaLimitExceeded


logger = structlog.get_logger()


class FsspHtmlParser:
    """Парсер HTML страницы результатов ФССП."""

    def _parse_debtor_info(self, td_element) -> dict:
        """
        Парсит детальную информацию о должнике из первой ячейки таблицы.
        
        Args:
            td_element: BeautifulSoup элемент <td>
            
        Returns:
            dict с полями: debtor, debtor_type и дополнительными полями в зависимости от типа
        """
        # Получаем все текстовые строки, разделенные <br>
        lines = []
        for content in td_element.children:
            if content.name == "br":
                continue
            text = content.strip() if isinstance(content, str) else content.get_text(strip=True)
            if text:
                lines.append(text)
        
        # Полная строка должника (как раньше)
        debtor_full = " ".join(lines)
        
        result = {"debtor": debtor_full}
        
        if not lines:
            return result
        
        # Определяем тип должника и парсим соответствующие поля
        # Проверяем, есть ли ИНН (только цифры, 10 или 12 символов)
        inn_pattern = re.compile(r"^\d{10}(\d{2})?$")
        birthday_pattern = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
        
        has_inn = any(inn_pattern.match(line.strip()) for line in lines)
        has_birthday = any(birthday_pattern.match(line.strip()) for line in lines)
        
        if has_inn:
            # Юридическое лицо
            result["debtor_type"] = "legal"
            result["debtor_name"] = lines[0] if len(lines) > 0 else None
            
            # Ищем адрес (вторая строка, если она не ИНН)
            if len(lines) > 1 and not inn_pattern.match(lines[1].strip()):
                result["debtor_address"] = lines[1]
            
            # Ищем ИНН в последних строках
            for line in reversed(lines):
                if inn_pattern.match(line.strip()):
                    result["debtor_inn"] = line.strip()
                    break
        
        elif has_birthday:
            # Физическое лицо
            result["debtor_type"] = "physical"
            
            # Первая строка - ФИО
            if len(lines) > 0:
                fio_parts = lines[0].split()
                if len(fio_parts) >= 1:
                    result["debtor_last_name"] = fio_parts[0]
                if len(fio_parts) >= 2:
                    result["debtor_first_name"] = fio_parts[1]
                if len(fio_parts) >= 3:
                    result["debtor_patronymic"] = fio_parts[2]
            
            # Ищем дату рождения
            for i, line in enumerate(lines):
                if birthday_pattern.match(line.strip()):
                    result["debtor_birthday"] = line.strip()
                    # Следующая строка после даты рождения - место рождения
                    if i + 1 < len(lines):
                        result["debtor_birthplace"] = lines[i + 1]
                    break
        
        return result

    def _parse_doc_info(self, td_element) -> dict:
        """
        Парсит детальную информацию о документе из третьей ячейки таблицы.
        
        Args:
            td_element: BeautifulSoup элемент <td>
            
        Returns:
            dict с полями: doc, doc_basis, doc_issuer, creditor_inn
        """
        # Получаем все текстовые строки, разделенные <br>
        lines = []
        for content in td_element.children:
            if content.name == "br":
                continue
            text = content.strip() if isinstance(content, str) else content.get_text(strip=True)
            if text:
                lines.append(text)
        
        # Полная строка документа (как раньше)
        doc_full = " ".join(lines)
        
        result = {"doc": doc_full}
        
        if not lines:
            return result
        
        # Основание для возбуждения ИП - первая строка
        if len(lines) > 0:
            result["doc_basis"] = lines[0]
        
        # Паттерн для поиска ИНН (10 или 12 цифр)
        inn_pattern = re.compile(r"^\d{10}(\d{2})?$")
        
        # Ищем ИНН взыскателя и орган-эмитент
        # ИНН обычно последняя или предпоследняя строка (перед "Постановление...")
        creditor_inn = None
        doc_issuer = None
        
        # Фильтруем строки, исключая "Постановление о взыскании исполнительского сбора"
        filtered_lines = [
            line for line in lines 
            if not line.startswith("Постановление о взыскании")
        ]
        
        # Ищем ИНН (строка из цифр)
        for i, line in enumerate(filtered_lines):
            if inn_pattern.match(line.strip()):
                creditor_inn = line.strip()
                # Орган-эмитент обычно перед ИНН
                if i > 0:
                    # Берем предыдущую непустую строку, которая не является основанием
                    for j in range(i - 1, 0, -1):
                        if filtered_lines[j] and filtered_lines[j] != result.get("doc_basis"):
                            doc_issuer = filtered_lines[j]
                            break
                break
        
        if creditor_inn:
            result["creditor_inn"] = creditor_inn
        
        if doc_issuer:
            result["doc_issuer"] = doc_issuer
        
        return result

    def _parse_debt_info(self, td_element) -> dict:
        """
        Парсит детальную информацию о долге из пятой ячейки таблицы.
        
        Args:
            td_element: BeautifulSoup элемент <td>
            
        Returns:
            dict с полями: debt, debt_type, debt_amount, debt_remaining, debt_bailiff_fee
        """
        # Получаем все текстовые строки, разделенные <br>
        lines = []
        for content in td_element.children:
            if content.name == "br":
                continue
            text = content.strip() if isinstance(content, str) else content.get_text(strip=True)
            if text:
                lines.append(text)
        
        # Полная строка долга (как раньше)
        debt_full = " ".join(lines)
        
        result = {"debt": debt_full}
        
        if not lines:
            return result
        
        # Тип задолженности - первая строка
        if len(lines) > 0:
            result["debt_type"] = lines[0]
        
        # Парсим остальные поля
        for line in lines:
            # Сумма долга
            if line.startswith("Сумма долга:"):
                # Извлекаем число из строки "Сумма долга: 194054.92 руб."
                # Может быть пустой, например "Сумма долга: руб." или просто "Сумма долга:"
                debt_match = re.search(r"Сумма долга:\s*([\d\s.,-]+)\s*руб", line)
                if debt_match:
                    amount = debt_match.group(1).strip()
                    # Проверяем, что это не пустая строка
                    if amount:
                        result["debt_amount"] = amount
            
            # Остаток долга по исполнительному документу
            elif "Остаток долга по исполнительному документу:" in line:
                debt_match = re.search(r"Остаток долга по исполнительному документу:\s*([\d\s.,-]+)\s*руб", line)
                if debt_match:
                    remaining = debt_match.group(1).strip()
                    if remaining:
                        result["debt_remaining"] = remaining
            
            # Исполнительский сбор
            elif line.startswith("Исполнительский сбор:"):
                debt_match = re.search(r"Исполнительский сбор:\s*([\d\s.,-]+)\s*руб", line)
                if debt_match:
                    fee = debt_match.group(1).strip()
                    if fee:
                        result["debt_bailiff_fee"] = fee
        
        return result

    def parse_cases(self, html: str) -> list[dict]:
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as exc:  # noqa: BLE001
            raise ParsingError("Не удалось распарсить HTML") from exc

        # Проверка на ошибку превышения лимита попыток капчи
        error_div = soup.select_one(".results .empty")
        if error_div:
            error_text = error_div.get_text(strip=True)
            if "Количество неверных попыток ввода кода превышено" in error_text:
                logger.warning("Обнаружено сообщение о превышении лимита попыток капчи")
                raise CaptchaLimitExceeded(
                    "Превышено количество неверных попыток ввода капчи. "
                    "Попробуйте позже или используйте другой способ получения данных."
                )

        table = soup.select_one(".results-frame table.list")
        if not table:
            logger.warning("Таблица результатов не найдена")
            return []

        current_region: str | None = None
        rows: list[dict] = []
        for tr in table.select("tr"):
            if tr.select("th"):
                continue
            if "region-title" in tr.get("class", []):
                current_region = tr.get_text(strip=True)
                continue

            tds = tr.select("td")
            if len(tds) != 8:
                continue

            # Парсим детальную информацию о должнике
            debtor_info = self._parse_debtor_info(tds[0])
            
            # Парсим детальную информацию о документе
            doc_info = self._parse_doc_info(tds[2])
            
            # Парсим детальную информацию о долге
            debt_info = self._parse_debt_info(tds[5])
            
            rows.append(
                {
                    "region": current_region,
                    **debtor_info,  # Добавляем распарсенную информацию о должнике
                    "ip": " ".join(tds[1].stripped_strings),
                    **doc_info,  # Добавляем распарсенную информацию о документе
                    "end_reason": " ".join(tds[3].stripped_strings),
                    **debt_info,  # Добавляем распарсенную информацию о долге
                    "office": " ".join(tds[6].stripped_strings),
                    "bailiff": " ".join(tds[7].stripped_strings),
                }
            )

        return rows
