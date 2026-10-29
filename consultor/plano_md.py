"""Exporta o plano de ação em Markdown (para download ou para o README do portfólio)."""
from .servico import Plano

_ICONE = {"atende": "✅", "parcial": "🟡", "ausente": "🔴"}


def plano_markdown(base: dict, plano: Plano, nome: str = "") -> str:
    r, tid = plano.resultado, plano.trilha_id
    trilha = base["trilhas"][tid]
    item = r.item(tid)
    L = [f"# Plano de carreira{' de ' + nome if nome else ''}", ""]
    L += ["## Top 3 de compatibilidade", ""]
    for pos, i in enumerate(r.top3, start=1):
        L.append(f"{pos}. **{i.nome}**: {round(i.compatibilidade)}%")
    L += ["", f"Confiança do resultado: **{r.confianca}**.", ""]
    for a in r.alertas:
        L.append(f"> ⚠️ {a}")
    if r.alertas:
        L.append("")
    L += [f"## Trilha escolhida: {trilha['nome']}", "", trilha["descricao"], "",
          f"Compatibilidade: **{round(item.compatibilidade)}%**", "", "### Por que esta trilha?", ""]
    for m in item.motivos:
        L.append(f"- {m.texto} ({m.rotulo}): +{m.pontos} pts")
    for g in item.regras:
        sinal = "+" if g["delta"] > 0 else ""
        L.append(f"- Regra {g['id']} ({sinal}{g['delta']} pts): {g['justificativa']}")
    if item.atencao:
        L += ["", "### Pontos de atenção", ""]
        L += [f"- {a.texto} ({a.rotulo}): {a.pontos} pts" for a in item.atencao]
    gp = plano.gaps
    L += ["", "## Análise de lacunas (nível Júnior)", "",
          f"Prontidão: **{round(gp.prontidao)}%** ({gp.classificacao})", "",
          "| Competência | Atual | Exigido | Prioridade | Situação |", "|---|---|---|---|---|"]
    esc = base["escalas"]["nivel"]["rotulos"]
    for i in gp.itens:
        L.append(f"| {i.nome} | {esc[str(i.atual)]} | {esc[str(i.exigido)]} | {i.prioridade} | {_ICONE[i.status]} {i.status} |")
    rm = plano.roadmap
    L += ["", "## Roadmap de estudos", ""]
    if rm.mensagem:
        L += [rm.mensagem, ""]
    else:
        L += [f"Estimativa: **{rm.horas_total} h** (~{rm.semanas_total} semanas a {rm.horas_semana} h/semana).", ""]
    for f in rm.fases:
        L += [f"### Fase {f.numero}: {f.titulo} (~{f.horas} h, {f.semanas} semana(s))", ""]
        for it in f.itens:
            L.append(f"- **{it.nome}** ({esc[str(it.de)]} → {esc[str(it.para)]}, ~{it.horas} h)")
            L += [f"  - {t}" for t in it.topicos]
        L.append("")
    L += ["## Certificações e cursos sugeridos", ""]
    L += [f"- **{c['nome']}** ({c['tipo']}): {c['quando']}" for c in rm.certificacoes]
    L += ["", "## Projetos para o portfólio no GitHub", ""]
    for p in rm.projetos:
        L += [f"### {p['nome']} ({p['nivel']})", "", p["descricao"], "",
              f"- Quando: {p['quando']}", f"- Tecnologias: {', '.join(p['tecnologias'])}",
              "- Entregáveis: " + "; ".join(p["entregaveis"]), ""]
    if rm.complementares:
        L += ["## Para ir além do nível Júnior", "", ", ".join(rm.complementares), ""]
    L += ["---", *[f"*{a}*" for a in base.get("avisos", [])]]
    return "\n".join(L) + "\n"
