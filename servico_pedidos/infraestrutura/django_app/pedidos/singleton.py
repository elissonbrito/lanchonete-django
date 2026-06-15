class ConfiguracaoLanchonete:
    """Configurações globais da lanchonete — existe uma única instância."""

    _instancia: "ConfiguracaoLanchonete | None" = None

    def __new__(cls) -> "ConfiguracaoLanchonete":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.nome = "Lanchonete Django"
            cls._instancia.taxa_entrega = 5.00
            cls._instancia.tempo_preparo_padrao_minutos = 20
        return cls._instancia

    def __str__(self) -> str:
        return f"{self.nome} | Taxa de entrega: R${self.taxa_entrega:.2f}"

    def __repr__(self) -> str:
        return (
            f"ConfiguracaoLanchonete("
            f"nome={self.nome!r}, "
            f"taxa_entrega=R${self.taxa_entrega:.2f}, "
            f"tempo_preparo={self.tempo_preparo_padrao_minutos}min)"
        )
