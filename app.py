"""Interface Streamlit (wizard) do Consultor Avançado de Carreiras.

Execute com:  streamlit run app.py
"""
import streamlit as st

from consultor.base import BaseInvalida, carregar_base
from consultor.motor import calcular
from consultor.plano_md import plano_markdown
from consultor.servico import gerar_plano

try:  # gráfico de radar é opcional
    import plotly.graph_objects as go
except ImportError:  # pragma: no cover
    go = None

ICONE = {"atende": "✅ Atende", "parcial": "🟡 Parcial", "ausente": "🔴 Ausente"}


@st.cache_resource
def _base():
    return carregar_base()


# ------------------------------------------------------------------ estado
def _iniciar(base):
    ss = st.session_state
    ss.setdefault("etapa", 1)
    ss.setdefault("resp", {})
    ss.setdefault("nome", "")
    ss.setdefault("horas", base["parametros_usuario"]["horas_semana"]["padrao"])


def _salvar(base, etapa):
    """Copia os valores dos widgets da etapa para o estado persistente."""
    ss = st.session_state
    for p in base["perguntas"]:
        if p["etapa"] == etapa and f"w_{p['id']}" in ss:
            ss.resp[p["id"]] = ss[f"w_{p['id']}"]
    if etapa == 1 and "w_nome" in ss:
        ss.nome = ss.w_nome
    if etapa == 3 and "w_horas" in ss:
        ss.horas = ss.w_horas


def _navegar(base, etapa, delta):
    _salvar(base, etapa)
    st.session_state.etapa = etapa + delta


def _reiniciar():
    for k in list(st.session_state.keys()):
        del st.session_state[k]


# ------------------------------------------------------------------ widgets
def _campo(base, p, coluna=None):
    esc = base["escalas"][p["tipo"]]
    rotulos = {int(k): v for k, v in esc["rotulos"].items()}
    valor = st.session_state.resp.get(p["id"], esc["padrao"])
    alvo = coluna or st
    alvo.select_slider(
        p["texto"], options=list(range(esc["min"], esc["max"] + 1)), value=valor,
        format_func=lambda v, r=rotulos: r[v], key=f"w_{p['id']}",
    )


def _barra_navegacao(base, etapa, ultimo):
    esq, _, dir_ = st.columns([1, 2, 1])
    if etapa > 1:
        esq.button("← Voltar", on_click=_navegar, args=(base, etapa, -1))
    dir_.button("Ver resultado →" if etapa == ultimo else "Avançar →", type="primary",
                on_click=_navegar, args=(base, etapa, +1))


def _passo(base, etapa):
    ultimo = max(int(k) for k in base["etapas"])
    st.progress((etapa - 1) / ultimo, text=f"Passo {etapa} de {ultimo}: {base['etapas'][str(etapa)]}")
    st.subheader(f"Passo {etapa}: {base['etapas'][str(etapa)]}")

    if etapa == 1:
        st.text_input("Como podemos te chamar? (opcional)", value=st.session_state.nome, key="w_nome")
        st.caption("Indique o quanto você concorda com cada frase.")
    if etapa == 2:
        st.caption("Afinidade: de 1 (nenhuma) a 5 (muita). Conhecimento: de 'nunca estudei' a 'avançado'.")

    secoes = []
    for p in base["perguntas"]:
        if p["etapa"] == etapa and p["secao"] not in secoes:
            secoes.append(p["secao"])
    for secao in secoes:
        qs = [p for p in base["perguntas"] if p["etapa"] == etapa and p["secao"] == secao]
        if etapa == 2:
            st.markdown(f"#### {secao}")
        if qs[0]["grupo"] == "conhecimento":
            cols = st.columns(2)
            for n, p in enumerate(qs):
                _campo(base, p, cols[n % 2])
        else:
            for p in qs:
                _campo(base, p)

    if etapa == ultimo:
        h = base["parametros_usuario"]["horas_semana"]
        st.markdown("#### Disponibilidade")
        st.slider("Quantas horas por semana você pode dedicar aos estudos?",
                  h["min"], h["max"], st.session_state.horas, key="w_horas")
    _barra_navegacao(base, etapa, ultimo)


# ---------------------------------------------------------------- resultado
def _curto(base, tid):
    return base["trilhas"][tid].get("nome_curto", base["trilhas"][tid]["nome"])


def _graficos(base, resultado):
    nomes = [_curto(base, i.trilha_id) for i in resultado.ranking]
    valores = [i.compatibilidade for i in resultado.ranking]
    if go is not None:
        fig = go.Figure(go.Scatterpolar(r=valores + valores[:1], theta=nomes + nomes[:1], fill="toself",
                                        name="Compatibilidade (%)"))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), showlegend=False,
                          margin=dict(l=40, r=40, t=30, b=30), height=420)
        st.plotly_chart(fig, use_container_width=True)
    st.bar_chart({"Compatibilidade (%)": dict(zip(nomes, valores))})
    st.dataframe(
        [{"Trilha": i.nome, "Compatibilidade (%)": round(i.compatibilidade), "Afinidade (%)": round(i.afinidade),
          "Conhecimento (%)": round(i.conhecimento), "Ajuste das regras (pts)": i.ajuste_regras}
         for i in resultado.ranking],
        hide_index=True, use_container_width=True,
    )


def _justificativa(base, resultado, tid):
    item = resultado.item(tid)
    st.markdown(f"**Por que {item.nome}?** Compatibilidade de **{round(item.compatibilidade)}%** "
                f"(afinidade {round(item.afinidade)}%, conhecimento {round(item.conhecimento)}%, "
                f"regras {'+' if item.ajuste_regras > 0 else ''}{item.ajuste_regras:g} pts).")
    if item.motivos:
        st.markdown("**O que mais pesou a favor**")
        for m in item.motivos:
            st.markdown(f"- {m.texto} — *{m.rotulo}* (+{m.pontos} pts)")
    if item.regras:
        st.markdown("**Regras lógicas aplicadas**")
        for g in item.regras:
            icone = "🟢" if g["delta"] > 0 else "🔴"
            st.markdown(f"- {icone} **{g['id']}** ({'+' if g['delta'] > 0 else ''}{g['delta']} pts): {g['justificativa']}")
    if item.atencao:
        st.markdown("**Pontos de atenção** (respostas baixas em fatores importantes)")
        for a in item.atencao:
            st.markdown(f"- {a.texto} — *{a.rotulo}* ({a.pontos} pts)")


def _lacunas(base, plano):
    g = plano.gaps
    c1, c2 = st.columns(2)
    c1.metric("Prontidão para Júnior", f"{round(g.prontidao)}%")
    c2.metric("Situação", g.classificacao)
    st.progress(min(g.prontidao, 100) / 100)
    rot = base["escalas"]["nivel"]["rotulos"]
    st.dataframe(
        [{"Competência": i.nome, "Seu nível": rot[str(i.atual)], "Exigido para Júnior": rot[str(i.exigido)],
          "Prioridade": "★" * i.prioridade, "Situação": ICONE[i.status]} for i in g.itens],
        hide_index=True, use_container_width=True,
    )
    if g.criticos:
        st.warning("Lacunas críticas (prioridade máxima): " + ", ".join(i.nome for i in g.criticos))
    else:
        st.success("Nenhuma lacuna crítica.")


def _plano(base, plano):
    rm = plano.roadmap
    rot = base["escalas"]["nivel"]["rotulos"]
    if rm.mensagem:
        st.success(rm.mensagem)
    else:
        a, b, c = st.columns(3)
        a.metric("Horas estimadas", f"{rm.horas_total} h")
        b.metric("Duração estimada", f"{rm.semanas_total} semanas")
        c.metric("Ritmo", f"{rm.horas_semana} h/semana")
    st.markdown("### 1. O que estudar, em ordem")
    for f in rm.fases:
        with st.expander(f"Fase {f.numero}: {f.titulo} (~{f.horas} h, {f.semanas} semana(s))", expanded=f.numero == 1):
            for it in f.itens:
                st.markdown(f"**{it.nome}** — {rot[str(it.de)]} → {rot[str(it.para)]} (~{it.horas} h)")
                for t in it.topicos:
                    st.markdown(f"- {t}")
    st.markdown("### 2. Certificações e cursos")
    st.dataframe([{"Certificação/curso": c["nome"], "Tipo": c["tipo"], "Quando": c["quando"]}
                  for c in rm.certificacoes], hide_index=True, use_container_width=True)
    st.markdown("### 3. Projetos para o portfólio no GitHub")
    for p in rm.projetos:
        with st.expander(f"{p['nome']} ({p['nivel']}) — {p['quando']}"):
            st.write(p["descricao"])
            st.markdown("**Tecnologias:** " + ", ".join(p["tecnologias"]))
            st.markdown("**O que publicar no repositório:**")
            for e in p["entregaveis"]:
                st.markdown(f"- [ ] {e}")
    if rm.complementares:
        st.markdown("### 4. Para ir além do nível Júnior")
        st.write(", ".join(rm.complementares))
    for a in base.get("avisos", []):
        st.caption(a)


def _resultado(base):
    ss = st.session_state
    nome = ss.nome.strip()
    try:
        previa = calcular(base, ss.resp)
    except ValueError as e:
        st.error(f"Não foi possível calcular: {e}")
        st.button("← Voltar", on_click=_navegar, args=(base, 4, -1))
        return

    st.header(f"Resultado{' de ' + nome if nome else ''}")
    top = previa.top3
    cols = st.columns(3)
    for pos, (col, i) in enumerate(zip(cols, top), start=1):
        col.metric(f"{pos}º lugar", f"{round(i.compatibilidade)}%", i.nome, delta_color="off")
        col.progress(i.compatibilidade / 100)
    st.caption(f"Confiança do resultado: **{previa.confianca}**")
    for a in previa.alertas:
        st.warning(a)
    for d in previa.dicas:
        st.info(d)

    opcoes = [i.trilha_id for i in top]
    escolhida = st.selectbox("Trilha para detalhar (gaps e plano de ação)", opcoes,
                             format_func=lambda t: base["trilhas"][t]["nome"])
    plano = gerar_plano(base, ss.resp, trilha_id=escolhida, horas_semana=ss.horas)
    st.caption(base["trilhas"][escolhida]["perfil_ideal"])

    t1, t2, t3, t4 = st.tabs(["📊 Compatibilidade", "🔎 Justificativa", "🧩 Lacunas (gaps)", "🗺️ Plano de ação"])
    with t1:
        _graficos(base, previa)
    with t2:
        _justificativa(base, previa, escolhida)
        for i in top:
            if i.trilha_id != escolhida:
                with st.expander(f"Por que {i.nome}?"):
                    _justificativa(base, previa, i.trilha_id)
    with t3:
        _lacunas(base, plano)
    with t4:
        _plano(base, plano)

    st.divider()
    st.download_button("⬇️ Baixar plano (.md)", data=plano_markdown(base, plano, nome),
                       file_name="plano_de_carreira.md", mime="text/markdown")
    esq, dir_ = st.columns(2)
    esq.button("← Ajustar respostas", on_click=_navegar, args=(base, 4, -1))
    dir_.button("Refazer do zero", on_click=_reiniciar)


# --------------------------------------------------------------------- main
def main():
    st.set_page_config(page_title="Consultor Avançado de Carreiras em TI", page_icon="🧭", layout="wide")
    st.title("🧭 Consultor Avançado de Carreiras e Desenvolvimento Profissional")
    try:
        base = _base()
    except BaseInvalida as e:
        st.error(f"Falha ao carregar a base de conhecimento: {e}")
        st.stop()
        return
    _iniciar(base)
    etapa = st.session_state.etapa
    ultimo = max(int(k) for k in base["etapas"])
    if etapa <= ultimo:
        _passo(base, etapa)
    else:
        _resultado(base)


main()
