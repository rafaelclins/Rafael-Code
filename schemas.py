from pydantic import BaseModel, Field
from typing import List, Optional


class AlinhadorOutput(BaseModel):
    objetivo_principal: str = Field(default="", description="O objetivo limpo do usuario")
    restricoes_e_limites: List[str] = Field(default_factory=list, description="Lista de restricoes de custo e ferramentas")
    regras_de_negocio: List[str] = Field(default_factory=list, description="Leis e regras de conformidade")


class PlanoPasso(BaseModel):
    passo: int = Field(description="Numero sequencial do passo")
    tarefa: str = Field(description="O que fazer")
    criterio_sucesso: str = Field(description="Como saber se deu certo")


class PlanejadorOutput(BaseModel):
    plano_de_acao: List[PlanoPasso] = Field(default_factory=list)


class DadoColetado(BaseModel):
    fonte: str = Field(default="", description="Nome do servico/site")
    fato_tecnico: str = Field(default="", description="Informacao precisa encontrada")
    custo_ou_metrica: str = Field(default="", description="Valores se houver")


class PesquisadorOutput(BaseModel):
    dados_coletados: List[DadoColetado] = Field(default_factory=list)


class ExecutorOutput(BaseModel):
    rascunho_da_solucao: str = Field(default="", description="Codigo gerado")


class ConsolidadorOutput(BaseModel):
    documento_final_formatado: str = Field(default="", description="Documento em Markdown")
    arquivos: List["ArquivoAlteracao"] = Field(default_factory=list, description="Arquivos a criar/modificar/excluir")


class ArquivoAlteracao(BaseModel):
    caminho: str = Field(default="", description="Caminho relativo do arquivo dentro do repositorio")
    acao: str = Field(default="criar", description="criar, modificar ou excluir")
    conteudo: str = Field(default="", description="Conteudo completo do arquivo")


class AvaliadorOutput(BaseModel):
    status: str = Field(default="APROVADO", description="APROVADO ou REPROVADO")
    motivo_da_reprovacao: Optional[str] = Field(default=None, description="Motivo se REPROVADO. None se APROVADO.")


class GuardiaoOutput(BaseModel):
    status_seguranca: str = Field(default="SEGURO", description="SEGURO ou BLOQUEADO")
    resposta_final_higienizada: str = Field(default="", description="Texto em Markdown limpo")
    politica_violada: Optional[str] = Field(default=None, description="Politica violada se BLOQUEADO. None se SEGURO.")
