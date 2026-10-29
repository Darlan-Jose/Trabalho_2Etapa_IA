"""Geração do roadmap personalizado: ordem de estudo, certificações e projetos de portfólio."""
import math
from dataclasses import dataclass, field

from .gaps import AnaliseGap, nivel_atual


@dataclass
class ItemEstudo:
    competencia: str
    nome: str
    de: int
    para: int
    horas: int
    prioridade: int
    topicos: list = field(default_factory=list)


@dataclass
class Fase:
    numero: int
    titulo: str
    itens: list
    horas: int
    semanas: int


@dataclass
class Roadmap:
    trilha_id: str
    horas_semana: int
    fases: list = field(default_factory=list)
    horas_total: int = 0
    semanas_total: int = 0
    certificacoes: list = field(default_factory=list)
    projetos: list = field(default_factory=list)
    complementares: list = field(default_factory=list)
    mensagem: str = ""


_FASE_POR_PRIORIDADE = {3: 1, 2: 2, 1: 3}
_TITULOS_PADRAO = {3: "Fundamentos essenciais", 2: "Consolidação", 1: "Complementos"}


def _validar_horas(base, horas_semana):
    p = base["parametros_usuario"]["horas_semana"]
    h = p["padrao"] if horas_semana is None else horas_semana
    if isinstance(h, bool) or not isinstance(h, (int, float)) or not p["min"] <= h <= p["max"]:
        raise ValueError(f"horas_semana deve estar entre {p['min']} e {p['max']}.")
    return int(h)


def _ordenar(base, cids, pend):
    """Ordena por prioridade/lacuna respeitando pré-requisitos (ordenação topológica estável)."""
    restantes = sorted(cids, key=lambda c: (-pend[c].prioridade, -pend[c].lacuna, pend[c].nome))
    saida = []
    while restantes:
        for c in restantes:
            pres = base["competencias"][c].get("pre_requisitos", [])
            if all(p not in restantes for p in pres):
                saida.append(c)
                restantes.remove(c)
                break
        else:  # ciclo (não deve ocorrer em bases válidas)
            saida.extend(restantes)
            break
    return saida


def _quando(req: dict, base, respostas, alvo: dict, fase_de: dict) -> str:
    """Diz quando um projeto/certificação se torna viável dado o roadmap."""
    maior_fase, depois = 0, []
    for cid, nivel in req.items():
        if nivel_atual(base, respostas, cid) >= nivel:
            continue
        if cid in alvo and alvo[cid] >= nivel:
            maior_fase = max(maior_fase, fase_de[cid])
        else:
            depois.append(base["competencias"][cid]["nome"])
    if depois:
        return "Depois do roadmap (exige nível acima do Júnior em: " + ", ".join(depois) + ")"
    if maior_fase == 0:
        return "Pode começar agora"
    return f"Após a Fase {maior_fase}"


def gerar_roadmap(base: dict, trilha_id: str, gaps: AnaliseGap, respostas: dict,
                  horas_semana=None) -> Roadmap:
    h = _validar_horas(base, horas_semana)
    trilha = base["trilhas"][trilha_id]
    pend = {i.competencia: i for i in gaps.pendentes}
    titulos = {int(k): v for k, v in base.get("fases_roadmap", {}).items()} or _TITULOS_PADRAO

    # Fase inicial por prioridade; pré-requisitos nunca ficam em fase posterior à de quem depende deles
    fase_bruta = {c: _FASE_POR_PRIORIDADE[i.prioridade] for c, i in pend.items()}
    mudou = True
    while mudou:
        mudou = False
        for c in pend:
            for pre in base["competencias"][c].get("pre_requisitos", []):
                if pre in pend and fase_bruta[pre] > fase_bruta[c]:
                    fase_bruta[pre] = fase_bruta[c]
                    mudou = True

    fases, fase_de, alvo = [], {}, {}
    grupos = sorted(set(fase_bruta.values()))
    for numero, g in enumerate(grupos, start=1):
        cids = _ordenar(base, [c for c, f in fase_bruta.items() if f == g], pend)
        itens = []
        for c in cids:
            gp = pend[c]
            cat = base["competencias"][c]
            horas = sum(cat["horas_por_nivel"][gp.atual:gp.exigido])
            topicos = [cat["estudar"][str(n)] for n in range(gp.atual + 1, gp.exigido + 1)]
            itens.append(ItemEstudo(c, cat["nome"], gp.atual, gp.exigido, horas, gp.prioridade, topicos))
            fase_de[c] = numero
            alvo[c] = gp.exigido
        prioridade_fase = {v: k for k, v in _FASE_POR_PRIORIDADE.items()}[g]
        horas_fase = sum(i.horas for i in itens)
        fases.append(Fase(numero, titulos.get(prioridade_fase, f"Fase {numero}"), itens,
                          horas_fase, math.ceil(horas_fase / h)))

    horas_total = sum(f.horas for f in fases)
    rm = Roadmap(
        trilha_id=trilha_id, horas_semana=h, fases=fases, horas_total=horas_total,
        semanas_total=math.ceil(horas_total / h) if horas_total else 0,
        complementares=list(trilha.get("tecnologias_complementares", [])),
    )

    for ce in trilha.get("certificacoes", []):
        rm.certificacoes.append({**ce, "quando": _quando(ce["requer"], base, respostas, alvo, fase_de)})
    for pr in trilha.get("projetos", []):
        rm.projetos.append({**pr, "quando": _quando(pr["requer"], base, respostas, alvo, fase_de)})

    if not pend:
        rm.mensagem = ("Você já atende às competências mínimas de nível Júnior nesta trilha. "
                       "Foque em projetos de portfólio, certificações e em se candidatar a vagas.")
    return rm
