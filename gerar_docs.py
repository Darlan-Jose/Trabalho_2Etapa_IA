"""Gera docs/matriz_pesos.md (Fase 1) a partir do JSON da base de conhecimento.

Uso: python gerar_docs.py
"""
from consultor.base import carregar_base

b = carregar_base()
ids = list(b["trilhas"])
curto = {t: b["trilhas"][t].get("nome_curto", t) for t in ids}
L = [
    "# Matriz de pesos e regras (gerada do JSON)",
    "",
    "Fonte: `base_conhecimento/regras_carreiras.json`. Não edite este arquivo: edite o JSON e rode `python gerar_docs.py`.",
    "",
    "## Como a compatibilidade é calculada",
    "",
    "1. Cada resposta é normalizada para 0–1 (`(resposta − mín) / (máx − mín)`).",
    "2. Para cada trilha e cada grupo: `score_grupo = Σ(peso × resposta) / Σ(pesos)`.",
    "3. Os grupos são combinados pela `composicao` "
    + ", ".join(f"{g} {int(v*100)}%" for g, v in b["composicao"].items()) + ".",
    "4. Regras lógicas somam (bônus) ou subtraem (penalidade) pontos percentuais quando **todas** as condições são verdadeiras.",
    "5. O resultado é limitado a 0–100% e ordenado (Top 3 em destaque).",
    "",
    "## Matriz pergunta × trilha (pesos 0–10)",
    "",
    "| Pergunta | Grupo | " + " | ".join(curto[t] for t in ids) + " |",
    "|---|---|" + "---|" * len(ids),
]
for p in b["perguntas"]:
    w = b["pesos"].get(p["id"], {})
    L.append(f"| `{p['id']}` | {p['grupo']} | " + " | ".join(str(w.get(t, "")) for t in ids) + " |")
L += ["", "## Regras lógicas (bônus, penalidades e desambiguação)", "",
      "| Regra | Tipo | Condições (E) | Efeitos (pontos %) |", "|---|---|---|---|"]
for r in b["regras_logicas"]:
    cond = " **e** ".join(f"`{c['pergunta']} {c['op']} {c['valor']}`" for c in r["condicoes"])
    ef = ", ".join(f"{curto[t]} {'+' if v > 0 else ''}{v}" for t, v in r["efeitos"].items())
    L.append(f"| {r['id']} | {r['tipo']} | {cond} | {ef} |")
L += ["", "## Requisitos de nível Júnior por trilha", "",
      "Níveis: " + ", ".join(f"{k} = {v}" for k, v in b["escalas"]["nivel"]["rotulos"].items()), ""]
for t in ids:
    L += [f"**{b['trilhas'][t]['nome']}**: " + "; ".join(
        f"{b['competencias'][j['competencia']]['nome']} ≥ {j['nivel']} (prioridade {j['prioridade']})"
        for j in b["trilhas"][t]["junior"]), ""]
open("docs/matriz_pesos.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("docs/matriz_pesos.md gerado")
