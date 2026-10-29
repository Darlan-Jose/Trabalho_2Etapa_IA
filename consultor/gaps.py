"""Análise de lacunas de competências (skill gap) para o nível Júnior."""
from dataclasses import dataclass, field


@dataclass
class ItemGap:
    competencia: str
    nome: str
    atual: int
    exigido: int
    prioridade: int
    lacuna: int
    status: str  


@dataclass
class AnaliseGap:
    trilha_id: str
    itens: list = field(default_factory=list)
    prontidao: float = 0.0          # 0-100
    classificacao: str = ""
    criticos: list = field(default_factory=list)   

    @property
    def pendentes(self) -> list:
        return [i for i in self.itens if i.lacuna > 0]


def nivel_atual(base: dict, respostas: dict, competencia: str) -> int:
    esc = base["escalas"]["nivel"]
    return int(respostas.get(f"sk_{competencia}", esc["padrao"]))


def classificar(base: dict, prontidao: float) -> str:
    lim = base["limiares"]
    if prontidao >= lim["prontidao_junior"]:
        return "Já atende ao nível Júnior"
    if prontidao >= lim["prontidao_quase"]:
        return "Quase Júnior"
    if prontidao >= lim["prontidao_desenvolvimento"]:
        return "Em desenvolvimento"
    return "Iniciante"


def analisar_gaps(base: dict, trilha_id: str, respostas: dict) -> AnaliseGap:
    """Compara o nível atual de cada competência com o mínimo exigido para Júnior."""
    itens = []
    for req in base["trilhas"][trilha_id]["junior"]:
        cid = req["competencia"]
        atual = nivel_atual(base, respostas, cid)
        exigido = req["nivel"]
        lacuna = max(0, exigido - atual)
        if lacuna == 0:
            status = "atende"
        elif atual > 0:
            status = "parcial"
        else:
            status = "ausente"
        itens.append(ItemGap(
            competencia=cid, nome=base["competencias"][cid]["nome"],
            atual=atual, exigido=exigido, prioridade=req["prioridade"],
            lacuna=lacuna, status=status,
        ))

    itens.sort(key=lambda i: (-i.prioridade, -i.lacuna, i.nome))
    total = sum(i.prioridade * i.exigido for i in itens)
    obtido = sum(i.prioridade * min(i.atual, i.exigido) for i in itens)
    prontidao = round(100 * obtido / total, 1) if total else 100.0
    return AnaliseGap(
        trilha_id=trilha_id, itens=itens, prontidao=prontidao,
        classificacao=classificar(base, prontidao),
        criticos=[i for i in itens if i.prioridade == 3 and i.lacuna > 0],
    )
