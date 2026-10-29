"""Fase 2 - motor de pontuação: personas, conflitos e propriedades do cálculo."""
import random
import unittest

from perfis import BASE, PERSONAS, perfil
from consultor.motor import calcular


class TestPersonas(unittest.TestCase):
    def test_primeira_colocada_e_top3(self):
        for nome, (resp, esperada, no_top3) in PERSONAS.items():
            with self.subTest(persona=nome):
                r = calcular(BASE, resp)
                ids = [i.trilha_id for i in r.top3]
                self.assertEqual(ids[0], esperada, f"{nome}: {[(i.trilha_id, i.compatibilidade) for i in r.top3]}")
                for t in no_top3:
                    self.assertIn(t, ids, f"{nome}: {t} deveria estar no Top 3")

    def test_todas_as_trilhas_alcancaveis(self):
        self.assertEqual({v[1] for v in PERSONAS.values()}, set(BASE["trilhas"]))

    def test_top3_tem_percentuais_validos_e_ordenados(self):
        for nome, (resp, _, _) in PERSONAS.items():
            with self.subTest(persona=nome):
                r = calcular(BASE, resp)
                pcts = [i.compatibilidade for i in r.top3]
                self.assertEqual(pcts, sorted(pcts, reverse=True))
                self.assertTrue(all(0 <= p <= 100 for p in pcts))


class TestCalculo(unittest.TestCase):
    def test_penalidade_de_perfil_conflitante(self):
        # gosta de dados e IA, mas tem afinidade mínima com matemática
        r = calcular(BASE, perfil(af_dados=5, af_ia=5, af_matematica=1, af_logica=4, sk_python=2))
        ds, de = r.item("DS"), r.item("DE")
        self.assertLess(ds.compatibilidade, de.compatibilidade)
        self.assertIn("PEN01", [g["id"] for g in ds.regras])
        self.assertLess(ds.ajuste_regras, 0)

    def test_regra_com_duas_condicoes_exige_ambas(self):
        # PEN05 só dispara se gestão E pessoas forem baixas
        so_gestao = calcular(BASE, perfil(af_gestao=1, perf_pessoas=5))
        ambas = calcular(BASE, perfil(af_gestao=1, perf_pessoas=1))
        self.assertNotIn("PEN05", [g["id"] for g in so_gestao.item("PM").regras])
        self.assertIn("PEN05", [g["id"] for g in ambas.item("PM").regras])

    def test_monotonicidade_da_afinidade(self):
        anteriores = None
        for v in range(1, 6):
            c = calcular(BASE, perfil(af_seguranca=v)).item("SEC").compatibilidade
            if anteriores is not None:
                self.assertGreaterEqual(c, anteriores)
            anteriores = c

    def test_conhecimento_aumenta_compatibilidade(self):
        sem = calcular(BASE, perfil(af_mobile=4)).item("MOBILE").compatibilidade
        com = calcular(BASE, perfil(af_mobile=4, sk_mobile=3)).item("MOBILE").compatibilidade
        self.assertGreater(com, sem)

    def test_limites_e_determinismo_em_perfis_aleatorios(self):
        rng = random.Random(42)
        for _ in range(200):
            resp = {p["id"]: (rng.randint(1, 5) if p["tipo"] != "nivel" else rng.randint(0, 3))
                    for p in BASE["perguntas"]}
            r1, r2 = calcular(BASE, resp), calcular(BASE, resp)
            self.assertEqual([(i.trilha_id, i.compatibilidade) for i in r1.ranking],
                             [(i.trilha_id, i.compatibilidade) for i in r2.ranking])
            pcts = [i.compatibilidade for i in r1.ranking]
            self.assertTrue(all(0 <= p <= 100 for p in pcts))
            self.assertEqual(pcts, sorted(pcts, reverse=True))
            self.assertEqual(len(r1.ranking), 10)

    def test_justificativa_coerente_com_a_pontuacao(self):
        for nome, (resp, esperada, _) in PERSONAS.items():
            with self.subTest(persona=nome):
                item = calcular(BASE, resp).item(esperada)
                self.assertTrue(item.motivos, "a trilha vencedora precisa de motivos")
                # os motivos listados só incluem respostas altas (>= metade da escala)
                for m in item.motivos:
                    self.assertGreater(m.pontos, 0)


if __name__ == "__main__":
    unittest.main()
