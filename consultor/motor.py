"""Motor de inferência com pontuação ponderada e regras lógicas.
"""
from dataclasses import dataclass, field
from statistics import pstdev

import operator

_OPS = {
    "<": operator.lt, "<=": operator.le, ">": operator.gt,
    ">=": operator.ge, "==": operator.eq, "!=": operator.ne,
}


@dataclass
class Contribuicao:
    pergunta_id: str
    texto: str
    resposta: int
    rotulo: str
    pontos: float  


@dataclass
class ItemRanking:
    trilha_id: str
    nome: str
    compatibilidade: float
    afinidade: float          
    conhecimento: float       
    ajuste_regras: float      
    regras: list = field(default_factory=list)    
    motivos: list = field(default_factory=list)   
    atencao: list = field(default_factory=list)   


@dataclass
class Resultado:
    ranking: list
    respostas: dict
    alertas: list = field(default_factory=list)
    empates: list = field(default_factory=list)   ]
    dicas: list = field(default_factory=list)
    confianca: str = "baixa"

    @property
    def top3(self) -> list:
        return self.ranking[:3]

    @property
    def hibrido(self) -> bool:
        return bool(self.empates)

    def item(self, trilha_id: str) -> ItemRanking:
        return next(i for i in self.ranking if i.trilha_id == trilha_id)


# ----------------------------------------------------------------- respostas
def normalizar_respostas(base: dict, respostas: dict):
    """Valida e completa as respostas. Retorna (respostas_completas, ids_sem_resposta)."""
    ids = {p["id"] for p in base["perguntas"]}
    desconhecidas = set(respostas) - ids
    if desconhecidas:
        raise ValueError(f"Perguntas desconhecidas: {', '.join(sorted(desconhecidas))}")
    completas, faltando = {}, []
    for p in base["perguntas"]:
        esc = base["escalas"][p["tipo"]]
        v = respostas.get(p["id"])
        if v is None:
            completas[p["id"]] = esc["padrao"]
            faltando.append(p["id"])
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not esc["min"] <= v <= esc["max"]:
            raise ValueError(
                f"Resposta inválida para {p['id']}: {v!r} (esperado {esc['min']}..{esc['max']})"
            )
        completas[p["id"]] = int(v)
    return completas, faltando


def _norm(valor, esc) -> float:
    return (valor - esc["min"]) / (esc["max"] - esc["min"])


def _rotulo(base, pergunta, valor) -> str:
    return base["escalas"][pergunta["tipo"]]["rotulos"].get(str(valor), str(valor))


# ------------------------------------------------------------------- regras
def _regra_dispara(regra: dict, respostas: dict) -> bool:
    return all(_OPS[c["op"]](respostas[c["pergunta"]], c["valor"]) for c in regra["condicoes"])


# -------------------------------------------------------------------- motor
def calcular(base: dict, respostas: dict) -> Resultado:
    """Calcula o ranking completo de compatibilidade das trilhas."""
    resp, faltando = normalizar_respostas(base, respostas)
    perguntas = {p["id"]: p for p in base["perguntas"]}
    comp = base["composicao"]
    lim = base["limiares"]

    regras_disparadas = [r for r in base["regras_logicas"] if _regra_dispara(r, resp)]

    itens = []
    for tid, trilha in base["trilhas"].items():
        score_grupo = {g: 0.0 for g in comp}
        contribs: list[Contribuicao] = []
        perdas: list[Contribuicao] = []

        for grupo, peso_grupo in comp.items():
            qs = [p for p in base["perguntas"] if p["grupo"] == grupo and base["pesos"].get(p["id"], {}).get(tid, 0) > 0]
            soma_pesos = sum(base["pesos"][p["id"]][tid] for p in qs)
            if soma_pesos == 0:
                continue
            for p in qs:
                w = base["pesos"][p["id"]][tid]
                esc = base["escalas"][p["tipo"]]
                v = _norm(resp[p["id"]], esc)
                score_grupo[grupo] += w * v / soma_pesos
                ganho = 100 * peso_grupo * w * v / soma_pesos
                perda = 100 * peso_grupo * w * (1 - v) / soma_pesos
                ref = (p["id"], p["texto"], resp[p["id"]], _rotulo(base, p, resp[p["id"]]))
                if v >= 0.5:
                    contribs.append(Contribuicao(*ref, round(ganho, 1)))
                elif grupo == "afinidade" and v < 0.5:
                    perdas.append(Contribuicao(*ref, round(-perda, 1)))

        base_pct = 100 * sum(comp[g] * score_grupo[g] for g in comp)

        ajuste = 0.0
        regras_trilha = []
        for r in regras_disparadas:
            if tid in r["efeitos"]:
                delta = r["efeitos"][tid]
                ajuste += delta
                regras_trilha.append({
                    "id": r["id"], "tipo": r["tipo"], "descricao": r["descricao"],
                    "delta": delta, "justificativa": r["justificativa"],
                })

        final = max(0.0, min(100.0, base_pct + ajuste))
        contribs.sort(key=lambda c: -c.pontos)
        perdas.sort(key=lambda c: c.pontos)
        itens.append(ItemRanking(
            trilha_id=tid, nome=trilha["nome"], compatibilidade=round(final, 1),
            afinidade=round(100 * score_grupo.get("afinidade", 0), 1),
            conhecimento=round(100 * score_grupo.get("conhecimento", 0), 1),
            ajuste_regras=ajuste, regras=regras_trilha,
            motivos=contribs[:4], atencao=perdas[:3],
        ))

    ordem = list(base["trilhas"])
    itens.sort(key=lambda i: (-i.compatibilidade, -i.afinidade, ordem.index(i.trilha_id)))

    res = Resultado(ranking=itens, respostas=resp)
    _analisar(base, res, faltando, lim)
    return res


def _analisar(base, res: Resultado, faltando, lim) -> None:
    """Preenche alertas, empates parciais, dicas de desempate e nível de confiança."""
    top = res.ranking
    if faltando:
        res.alertas.append(
            f"{len(faltando)} pergunta(s) sem resposta foram tratadas como neutras; "
            "o resultado pode ser menos preciso."
        )

    likert = [p for p in base["perguntas"] if p["grupo"] == "afinidade"]
    valores = [_norm(res.respostas[p["id"]], base["escalas"][p["tipo"]]) for p in likert]
    if pstdev(valores) < lim["uniformidade_desvio"]:
        res.alertas.append(
            "Suas respostas de afinidade são quase todas iguais, o que dificulta distinguir as trilhas. "
            "Tente diferenciar mais o que você realmente gosta do que não gosta."
        )

    margem = top[0].compatibilidade - top[1].compatibilidade
    if top[0].compatibilidade < lim["compatibilidade_minima"]:
        res.alertas.append(
            f"Nenhuma trilha atingiu {lim['compatibilidade_minima']}% de compatibilidade: "
            "o perfil está indefinido ou muito diversificado. Considere explorar mais de uma área."
        )

    # Empates parciais entre as 3 primeiras
    for i in range(len(top[:3])):
        for j in range(i + 1, len(top[:3])):
            diff = round(top[i].compatibilidade - top[j].compatibilidade, 1)
            if diff < lim["empate_pp"]:
                res.empates.append((top[i].trilha_id, top[j].trilha_id, diff))
    if res.empates:
        a, b, d = res.empates[0]
        res.alertas.append(
            f"Perfil híbrido: {top_nome(base, a)} e {top_nome(base, b)} estão em empate parcial "
            f"(diferença de {d} ponto(s) percentual(is)). Vale explorar as duas antes de decidir."
        )

    # Dicas de desempate para pares confundíveis próximos
    ids_top = [i.trilha_id for i in top[:3]]
    comp = {i.trilha_id: i.compatibilidade for i in top}
    for par in base.get("pares_confundiveis", []):
        a, b = par["trilhas"]
        if a in ids_top and b in ids_top and abs(comp[a] - comp[b]) <= lim["proximo_pp"]:
            res.dicas.append(
                f"{top_nome(base, a)} × {top_nome(base, b)}: {par['dica']}"
            )

    if margem >= lim["confianca_alta_margem"] and top[0].compatibilidade >= lim["confianca_alta_minimo"]:
        res.confianca = "alta"
    elif margem >= lim["confianca_media_margem"] and top[0].compatibilidade >= lim["confianca_media_minimo"]:
        res.confianca = "média"
    else:
        res.confianca = "baixa"


def top_nome(base: dict, trilha_id: str) -> str:
    return base["trilhas"][trilha_id]["nome"]
