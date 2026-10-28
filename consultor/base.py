"""Carregamento e validação da base de conhecimento externa (JSON).
"""
import json
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "base_conhecimento" / "regras_carreiras.json"
OPERADORES = {"<", "<=", ">", ">=", "==", "!="}
CHAVES_OBRIGATORIAS = (
    "escalas", "composicao", "limiares", "trilhas", "perguntas", "pesos",
    "regras_logicas", "competencias",
)


class BaseInvalida(ValueError):
    """A base de conhecimento está mal formada ou inconsistente."""


def carregar_base(caminho=None) -> dict:
    """Lê o JSON, valida a consistência interna e devolve o dicionário."""
    caminho = Path(caminho) if caminho else CAMINHO_PADRAO
    try:
        with open(caminho, encoding="utf-8") as f:
            base = json.load(f)
    except FileNotFoundError as e:
        raise BaseInvalida(f"Arquivo de base não encontrado: {caminho}") from e
    except json.JSONDecodeError as e:
        raise BaseInvalida(f"JSON inválido em {caminho}: {e}") from e
    validar_base(base)
    return base


def validar_base(base: dict) -> None:
    """Verifica referências cruzadas. Levanta BaseInvalida listando todos os problemas."""
    erros: list[str] = []
    faltando = [k for k in CHAVES_OBRIGATORIAS if k not in base]
    if faltando:
        raise BaseInvalida(f"Chaves ausentes na base: {', '.join(faltando)}")

    trilhas = set(base["trilhas"])
    perguntas = {p["id"]: p for p in base["perguntas"]}
    competencias = set(base["competencias"])
    escalas = base["escalas"]

    if len(perguntas) != len(base["perguntas"]):
        erros.append("Há ids de perguntas duplicados.")
    for p in base["perguntas"]:
        if p["tipo"] not in escalas:
            erros.append(f"Pergunta {p['id']}: tipo '{p['tipo']}' sem escala definida.")
        if p["grupo"] not in base["composicao"]:
            erros.append(f"Pergunta {p['id']}: grupo '{p['grupo']}' fora de 'composicao'.")
        if p["grupo"] == "conhecimento" and p.get("competencia") not in competencias:
            erros.append(f"Pergunta {p['id']}: competência '{p.get('competencia')}' inexistente.")

    if abs(sum(base["composicao"].values()) - 1.0) > 1e-9:
        erros.append("Os valores de 'composicao' devem somar 1.")

    for qid, pesos in base["pesos"].items():
        if qid not in perguntas:
            erros.append(f"Pesos para pergunta inexistente: {qid}")
        for t, w in pesos.items():
            if t not in trilhas:
                erros.append(f"Pesos de {qid}: trilha inexistente '{t}'.")
            if not isinstance(w, (int, float)) or w < 0:
                erros.append(f"Pesos de {qid}/{t}: valor inválido {w!r}.")

    for t in trilhas:
        tem_peso = any(t in pesos for pesos in base["pesos"].values())
        if not tem_peso:
            erros.append(f"Trilha {t} não recebe peso de nenhuma pergunta.")

    for r in base["regras_logicas"]:
        for c in r["condicoes"]:
            if c["pergunta"] not in perguntas:
                erros.append(f"Regra {r['id']}: pergunta inexistente '{c['pergunta']}'.")
            if c["op"] not in OPERADORES:
                erros.append(f"Regra {r['id']}: operador inválido '{c['op']}'.")
        for t in r["efeitos"]:
            if t not in trilhas:
                erros.append(f"Regra {r['id']}: trilha inexistente '{t}'.")

    for cid, c in base["competencias"].items():
        for pre in c.get("pre_requisitos", []):
            if pre not in competencias:
                erros.append(f"Competência {cid}: pré-requisito inexistente '{pre}'.")
        if len(c["horas_por_nivel"]) != escalas["nivel"]["max"] - escalas["nivel"]["min"]:
            erros.append(f"Competência {cid}: 'horas_por_nivel' deve ter um valor por nível.")

    def checar_req(rotulo, req):
        for comp, nivel in req.items():
            if comp not in competencias:
                erros.append(f"{rotulo}: competência inexistente '{comp}'.")
            elif not escalas["nivel"]["min"] <= nivel <= escalas["nivel"]["max"]:
                erros.append(f"{rotulo}: nível inválido {nivel} para '{comp}'.")

    for tid, t in base["trilhas"].items():
        checar_req(f"Trilha {tid} (júnior)", {j["competencia"]: j["nivel"] for j in t["junior"]})
        for pr in t.get("projetos", []):
            checar_req(f"Projeto '{pr['nome']}'", pr["requer"])
        for ce in t.get("certificacoes", []):
            checar_req(f"Certificação '{ce['nome']}'", ce["requer"])

    for par in base.get("pares_confundiveis", []):
        for t in par["trilhas"]:
            if t not in trilhas:
                erros.append(f"Par confundível com trilha inexistente '{t}'.")

    if erros:
        raise BaseInvalida("Base de conhecimento inconsistente:\n- " + "\n- ".join(erros))
