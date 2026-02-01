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
    ip: str = Field(description="Номер исполнительного производства")
    doc: str = Field(description="Номер исполнительного документа")
    end_reason: str | None = Field(default=None, description="Причина окончания")
    debt: str = Field(description="Сумма задолженности")
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
            ip=case.ip,
            doc=case.doc,
            end_reason=case.end_reason,
            debt=case.debt,
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
