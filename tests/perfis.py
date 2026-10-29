"""Perfis de teste (personas e casos limite) compartilhados pelos testes."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from consultor.base import carregar_base  # noqa: E402

BASE = carregar_base()


def perfil(padrao_likert=2, **kw):
    """Respostas completas: Likert = `padrao_likert`, conhecimentos = 0, com sobrescritas."""
    d = {p["id"]: (padrao_likert if p["tipo"] != "nivel" else 0) for p in BASE["perguntas"]}
    desconhecidas = set(kw) - set(d)
    assert not desconhecidas, desconhecidas
    d.update(kw)
    return d


# nome -> (respostas, trilha esperada em 1º, trilhas que devem estar no Top 3)
PERSONAS = {
    "DevOps": (perfil(af_infra=5, af_automacao=5, af_nuvem=4, perf_pressao=4, af_logica=3, ob_escala=4, ob_processos=4,
                      sk_linux=2, sk_docker=1, sk_git=2, sk_python=1), "DEVOPS", ["CLOUD"]),
    "Cloud": (perfil(af_infra=4, af_nuvem=5, perf_abstracao=5, af_automacao=3, af_logica=3, ob_escala=4, ob_especialista=4,
                     sk_cloud=1, sk_redes=2, sk_linux=2), "CLOUD", ["DEVOPS"]),
    "Back-end": (perfil(af_logica=5, af_web=4, af_dados=3, perf_foco=4, ob_escala=4, af_matematica=3,
                        sk_python=2, sk_sql=2, sk_apis=2, sk_git=2), "BACK", []),
    "Front-end": (perfil(af_design=5, af_web=5, af_logica=3, ob_usuario=5, perf_pessoas=4, perf_detalhe=3,
                         sk_html_css=2, sk_javascript=2, sk_design=1), "FRONT", []),
    "Cientista de Dados": (perfil(af_matematica=5, af_dados=5, af_ia=5, af_logica=4, ob_inovacao=4, perf_foco=4, ob_especialista=4,
                                  sk_python=2, sk_estatistica=2, sk_ml=1), "DS", ["DE"]),
    "Engenheiro de Dados": (perfil(af_dados=5, af_infra=4, af_matematica=3, af_logica=4, af_automacao=4, ob_escala=5,
                                   sk_sql=2, sk_python=2, sk_etl=1), "DE", []),
    "Segurança": (perfil(af_seguranca=5, af_infra=4, perf_detalhe=5, perf_pressao=4, ob_especialista=5, af_logica=3,
                         sk_redes=2, sk_linux=2, sk_seguranca=1), "SEC", []),
    "Mobile": (perfil(af_mobile=5, af_design=4, ob_usuario=5, af_logica=4, perf_pessoas=3, sk_mobile=2), "MOBILE", []),
    "QA": (perfil(af_testes=5, perf_detalhe=5, af_automacao=4, ob_processos=5, af_logica=3, sk_testes=2, sk_python=1), "QA", []),
    "Produto": (perfil(af_gestao=5, perf_pessoas=5, ob_lideranca=5, perf_abstracao=4, ob_usuario=4, af_design=3, sk_agil=2), "PM", []),
}

DADOS_E_WEB = perfil(af_dados=5, af_web=5, af_logica=4, af_matematica=4, af_design=4, af_ia=4, af_infra=3,
                     perf_foco=3, sk_python=2, sk_sql=1, sk_javascript=2)
