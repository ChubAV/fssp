"""DTO (Data Transfer Objects) для API поиска."""

from pydantic import BaseModel, Field

from src.domain.models import DebtorCase, DebtorCaseList


class SearchByIpRequest(BaseModel):
    """Запрос на поиск по номеру ИП."""

    ip_number: str = Field(
        description="Номер исполнительного производства",
        examples=["1234567/12/34/56", "1234567/12/34/56-ИП"],
    )


class SearchByPersonRequest(BaseModel):
    """Запрос на поиск по данным физического лица."""

    last_name: str = Field(description="Фамилия", examples=["Иванов"])
    first_name: str = Field(description="Имя", examples=["Иван"])
    patronymic: str | None = Field(default=None, description="Отчество", examples=["Иванович"])
    birthday: str = Field(
        description="Дата рождения в формате DD.MM.YYYY",
        examples=["16.05.1992"],
    )


class SearchByInnRequest(BaseModel):
    """Запрос на поиск по ИНН."""

    inn: str = Field(
        description="ИНН физического или юридического лица (10 или 12 цифр)",
        examples=["1234567890", "123456789012"],
    )


class DebtorCaseResponse(BaseModel):
    """Ответ с данными об исполнительном производстве."""

    region: str | None = Field(default=None, description="Регион")
    debtor: str = Field(description="ФИО или наименование должника")
    debtor_type: str | None = Field(default=None, description="Тип должника: physical или legal")
    
    # Поля для физических лиц
    debtor_last_name: str | None = Field(default=None, description="Фамилия (для физ. лиц)")
    debtor_first_name: str | None = Field(default=None, description="Имя (для физ. лиц)")
    debtor_patronymic: str | None = Field(default=None, description="Отчество (для физ. лиц)")
    debtor_birthday: str | None = Field(default=None, description="Дата рождения (для физ. лиц)")
    debtor_birthplace: str | None = Field(default=None, description="Место рождения (для физ. лиц)")
    
    # Поля для юридических лиц
    debtor_name: str | None = Field(default=None, description="Наименование организации (для юр. лиц)")
    debtor_address: str | None = Field(default=None, description="Юридический адрес (для юр. лиц)")
    debtor_inn: str | None = Field(default=None, description="ИНН (для юр. лиц)")
    
    ip: str = Field(description="Номер исполнительного производства")
    doc: str = Field(description="Номер исполнительного документа")
    
    # Поля для документа (основание для возбуждения ИП)
    doc_basis: str | None = Field(default=None, description="Основание для возбуждения ИП")
    doc_issuer: str | None = Field(default=None, description="Орган, выдавший документ")
    creditor_inn: str | None = Field(default=None, description="ИНН взыскателя")
    
    end_reason: str | None = Field(default=None, description="Причина окончания")
    debt: str = Field(description="Сумма задолженности (полная строка)")
    
    # Поля для информации о долге
    debt_type: str | None = Field(default=None, description="Тип задолженности")
    debt_amount: str | None = Field(default=None, description="Сумма долга")
    debt_remaining: str | None = Field(default=None, description="Остаток долга по ИД")
    debt_bailiff_fee: str | None = Field(default=None, description="Исполнительский сбор")
    
    office: str = Field(description="Отдел судебных приставов")
    bailiff: str = Field(description="ФИО пристава-исполнителя")

    @classmethod
    def from_domain(cls, case: DebtorCase) -> "DebtorCaseResponse":
        """
        Создать DTO из доменной модели.

        Args:
            case: Доменная модель дела

        Returns:
            DTO для API
        """
        return cls(
            region=case.region,
            debtor=case.debtor,
            debtor_type=case.debtor_type,
            debtor_last_name=case.debtor_last_name,
            debtor_first_name=case.debtor_first_name,
            debtor_patronymic=case.debtor_patronymic,
            debtor_birthday=case.debtor_birthday,
            debtor_birthplace=case.debtor_birthplace,
            debtor_name=case.debtor_name,
            debtor_address=case.debtor_address,
            debtor_inn=case.debtor_inn,
            ip=case.ip,
            doc=case.doc,
            doc_basis=case.doc_basis,
            doc_issuer=case.doc_issuer,
            creditor_inn=case.creditor_inn,
            end_reason=case.end_reason,
            debt=case.debt,
            debt_type=case.debt_type,
            debt_amount=case.debt_amount,
            debt_remaining=case.debt_remaining,
            debt_bailiff_fee=case.debt_bailiff_fee,
            office=case.office,
            bailiff=case.bailiff,
        )


class DebtorCaseListResponse(BaseModel):
    """Ответ со списком исполнительных производств."""

    items: list[DebtorCaseResponse] = Field(description="Список найденных дел")
    total: int = Field(description="Общее количество найденных дел")

    @classmethod
    def from_domain(cls, cases: DebtorCaseList) -> "DebtorCaseListResponse":
        """
        Создать DTO из доменной модели.

        Args:
            cases: Доменная модель списка дел

        Returns:
            DTO для API
        """
        return cls(
            items=[DebtorCaseResponse.from_domain(case) for case in cases.items],
            total=len(cases.items),
        )
