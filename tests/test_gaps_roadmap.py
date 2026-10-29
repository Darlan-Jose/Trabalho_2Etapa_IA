"""Fase 3 - skill gaps, roadmap e plano em Markdown."""
import math
import unittest

from perfis import BASE, PERSONAS, perfil
from consultor.gaps import analisar_gaps
from consultor.plano_md import plano_markdown
from consultor.roadmap import gerar_roadmap
from consultor.servico import gerar_plano

TODAS_SK = {p["id"]: 3 for p in BASE["perguntas"] if p["grupo"] == "conhecimento"}
NENHUMA_SK = {p["id"]: 0 for p in BASE["perguntas"] if p["grupo"] == "conhecimento"}


class TestGaps(unittest.TestCase):
    def test_iniciante_tem_todas_as_lacunas(self):
        g = analisar_gaps(BASE, "DEVOPS", perfil(**NENHUMA_SK))
        self.assertEqual(g.prontidao, 0)
        self.assertEqual(g.classificacao, "Iniciante")
        self.assertTrue(all(i.status == "ausente" for i in g.itens))
        self.assertEqual(len(g.pendentes), len(BASE["trilhas"]["DEVOPS"]["junior"]))

    def test_avancado_nao_tem_lacunas(self):
        g = analisar_gaps(BASE, "BACK", perfil(**TODAS_SK))
        self.assertEqual(g.prontidao, 100)
        self.assertEqual(g.classificacao, "Já atende ao nível Júnior")
        self.assertFalse(g.pendentes)

    def test_lacuna_parcial(self):
        g = analisar_gaps(BASE, "BACK", perfil(sk_python=1, sk_sql=2, sk_apis=2, sk_git=2, sk_testes=1, sk_linux=1, sk_docker=1))
        py = next(i for i in g.itens if i.competencia == "python")
        self.assertEqual((py.atual, py.exigido, py.lacuna, py.status), (1, 2, 1, "parcial"))
        self.assertEqual([c.competencia for c in g.criticos], ["python"])
        self.assertTrue(0 < g.prontidao < 100)

    def test_itens_ordenados_por_prioridade(self):
        g = analisar_gaps(BASE, "BACK", perfil(**NENHUMA_SK))
        prios = [i.prioridade for i in g.itens]
        self.assertEqual(prios, sorted(prios, reverse=True))

    def test_nivel_acima_do_exigido_nao_gera_lacuna(self):
        g = analisar_gaps(BASE, "PM", perfil(sk_agil=3, sk_design=3, sk_sql=3, sk_estatistica=3))
        self.assertEqual(g.prontidao, 100)


class TestRoadmap(unittest.TestCase):
    def _rm(self, tid, horas=10, **kw):
        resp = perfil(**kw)
        g = analisar_gaps(BASE, tid, resp)
        return gerar_roadmap(BASE, tid, g, resp, horas)

    def test_horas_e_semanas(self):
        rm = self._rm("DEVOPS", horas=10, **NENHUMA_SK)
        self.assertEqual(rm.horas_total, sum(f.horas for f in rm.fases))
        self.assertEqual(rm.semanas_total, math.ceil(rm.horas_total / 10))
        rm20 = self._rm("DEVOPS", horas=20, **NENHUMA_SK)
        self.assertEqual(rm20.horas_total, rm.horas_total)
        self.assertLess(rm20.semanas_total, rm.semanas_total)

    def test_prerequisitos_vem_antes(self):
        rm = self._rm("DE", **NENHUMA_SK)
        ordem = [i.competencia for f in rm.fases for i in f.itens]
        self.assertLess(ordem.index("sql"), ordem.index("etl"))
        self.assertLess(ordem.index("python"), ordem.index("etl"))
        rm = self._rm("DEVOPS", **NENHUMA_SK)
        ordem = [i.competencia for f in rm.fases for i in f.itens]
        self.assertLess(ordem.index("linux"), ordem.index("docker"))

    def test_fases_ordenadas_por_prioridade(self):
        rm = self._rm("BACK", **NENHUMA_SK)
        self.assertEqual([f.numero for f in rm.fases], list(range(1, len(rm.fases) + 1)))
        self.assertTrue(all(i.prioridade == 3 for i in rm.fases[0].itens))

    def test_topicos_cobrem_so_os_niveis_que_faltam(self):
        rm = self._rm("BACK", sk_python=1, sk_sql=2, sk_apis=2, sk_git=2, sk_testes=1, sk_linux=1, sk_docker=1)
        item = rm.fases[0].itens[0]
        self.assertEqual((item.competencia, item.de, item.para), ("python", 1, 2))
        self.assertEqual(len(item.topicos), 1)
        self.assertEqual(item.horas, BASE["competencias"]["python"]["horas_por_nivel"][1])

    def test_projetos_e_certificacoes_tem_quando(self):
        rm = self._rm("FRONT", sk_html_css=2)
        quando = {p["nome"]: p["quando"] for p in rm.projetos}
        self.assertEqual(quando["Landing page responsiva e acessível"], "Pode começar agora")
        self.assertTrue(any(q.startswith("Após a Fase") for q in quando.values()))
        self.assertEqual(len(rm.certificacoes), 3)
        self.assertEqual(len(rm.projetos), 3)

    def test_sem_lacunas_gera_mensagem(self):
        rm = self._rm("QA", **TODAS_SK)
        self.assertFalse(rm.fases)
        self.assertEqual(rm.horas_total, 0)
        self.assertTrue(rm.mensagem)
        self.assertTrue(all(p["quando"] == "Pode começar agora" for p in rm.projetos))

    def test_horas_por_semana_invalidas(self):
        for h in (0, 1, 41, "dez", True):
            with self.subTest(h=h), self.assertRaises(ValueError):
                self._rm("QA", horas=h)

    def test_toda_trilha_gera_roadmap_para_iniciante(self):
        for tid in BASE["trilhas"]:
            with self.subTest(trilha=tid):
                rm = self._rm(tid, **NENHUMA_SK)
                self.assertTrue(rm.fases)
                self.assertGreater(rm.horas_total, 0)


class TestPlano(unittest.TestCase):
    def test_plano_padrao_usa_a_primeira_do_ranking(self):
        resp, esperada, _ = PERSONAS["DevOps"]
        p = gerar_plano(BASE, resp)
        self.assertEqual(p.trilha_id, esperada)

    def test_plano_para_trilha_alternativa(self):
        resp, _, _ = PERSONAS["DevOps"]
        p = gerar_plano(BASE, resp, trilha_id="CLOUD", horas_semana=15)
        self.assertEqual(p.trilha_id, "CLOUD")
        self.assertEqual(p.roadmap.horas_semana, 15)

    def test_trilha_inexistente(self):
        with self.assertRaises(ValueError):
            gerar_plano(BASE, perfil(), trilha_id="XYZ")

    def test_markdown(self):
        resp, _, _ = PERSONAS["Back-end"]
        p = gerar_plano(BASE, resp)
        md = plano_markdown(BASE, p, nome="Maria")
        for trecho in ("# Plano de carreira de Maria", "Top 3 de compatibilidade", "Análise de lacunas",
                       "Roadmap de estudos", "Projetos para o portfólio"):
            self.assertIn(trecho, md)


if __name__ == "__main__":
    unittest.main()
