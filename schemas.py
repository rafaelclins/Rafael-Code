from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List


class AlinhadorOutput(BaseModel):
    objetivo_principal: str = Field(description="O objetivo limpo do usuario")
    restricoes_e_limites: List[str] = Field(description="Lista de restricoes de custo e ferramentas")
    regras_de_negocio: List[str] = Field(description="Leis e regras de conformidade")

    @field_validator("objetivo_principal")
    @classmethod
    def nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("objetivo_principal nao pode ser vazio")
        return v.strip()


class PlanoPasso(BaseModel):
    passo: int = Field(description="Numero sequencial do passo")
    tarefa: str = Field(description="O que fazer")
    criterio_sucesso: str = Field(description="Como saber se deu certo")


class PlanejadorOutput(BaseModel):
    plano_de_acao: List[PlanoPasso]

    @field_validator("plano_de_acao")
    @classmethod
    def pelo_menos_um_passo(cls, v: List[PlanoPasso]) -> List[PlanoPasso]:
        if not v:
            raise ValueError("plano_de_acao deve conter pelo menos 1 passo")
        return v


class DadoColetado(BaseModel):
    fonte: str = Field(description="Nome do servico/site")
    fato_tecnico: str = Field(description="Informacao precisa encontrada")
    custo_ou_metrica: str = Field(description="Valores se houver")


class PesquisadorOutput(BaseModel):
    dados_coletados: List[DadoColetado]

    @field_validator("dados_coletados")
    @classmethod
    def pelo_menos_um_dado(cls, v: List[DadoColetado]) -> List[DadoColetado]:
        if not v:
            raise ValueError("dados_coletados deve conter pelo menos 1 item")
        return v


class ExecutorOutput(BaseModel):
    rascunho_da_solucao: str = Field(description="Texto tecnico completo ou codigo")

    @field_validator("rascunho_da_solucao")
    @classmethod
    def minimo_conteudo(cls, v: str) -> str:
        if len(v.strip()) < 50:
            raise ValueError("rascunho_da_solucao deve ter no minimo 50 caracteres")
        return v.strip()


class ConsolidadorOutput(BaseModel):
    documento_final_formatado: str = Field(description="Texto polido em Markdown")

    @field_validator("documento_final_formatado")
    @classmethod
    def minimo_conteudo(cls, v: str) -> str:
        if len(v.strip()) < 50:
            raise ValueError("documento_final_formatado deve ter no minimo 50 caracteres")
        return v.strip()


class AvaliadorOutput(BaseModel):
    status: str = Field(description="APROVADO ou REPROVADO")
    motivo_da_reprovacao: str = Field(description="Motivo detalhado se REPROVADO. Vazio se APROVADO.")

    @field_validator("status")
    @classmethod
    def validar_status_estrito(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in ("APROVADO", "REPROVADO"):
            raise ValueError("O status deve ser estritamente 'APROVADO' ou 'REPROVADO'")
        return v_upper

    @model_validator(mode="after")
    def validar_motivo_obrigatorio(self):
        if self.status == "REPROVADO" and len(self.motivo_da_reprovacao.strip()) < 10:
            raise ValueError("Para status 'REPROVADO', um motivo detalhado de pelo menos 10 caracteres e obrigatorio.")
        if self.status == "APROVADO":
            self.motivo_da_reprovacao = ""
        return self


class GuardiaoOutput(BaseModel):
    status_seguranca: str = Field(description="SEGURO ou BLOQUEADO")
    resposta_final_higienizada: str = Field(description="Texto em Markdown limpo ou mensagem de erro")
    politica_violada: str = Field(description="Nome da diretriz violada se BLOQUEADO. Vazio se SEGURO.")

    @field_validator("status_seguranca")
    @classmethod
    def validar_seguranca_estrito(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in ("SEGURO", "BLOQUEADO"):
            raise ValueError("O status de seguranca deve ser 'SEGURO' ou 'BLOQUEADO'")
        return v_upper

    @model_validator(mode="after")
    def validar_campos_seguranca(self):
        if self.status_seguranca == "SEGURO":
            self.politica_violada = ""
        if self.status_seguranca == "BLOQUEADO" and not self.politica_violada.strip():
            raise ValueError("Se BLOQUEADO, politica_violada nao pode ser vazia")
        return self
