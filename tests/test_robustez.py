"""Fase 5 - robustez, casos limite e desacoplamento da base de conhecimento."""
import copy
import json
import pathlib
import tempfile
import unittest

from perfis import BASE, DADOS_E_WEB, PERSONAS, perfil
from consultor import gaps, motor, roadmap, servico
from consultor.base import BaseInvalida, CAMINHO_PADRAO, carregar_base, validar_base
from consultor.motor import calcular

DADOS = {"DS", "DE"}
WEB = {"FRONT", "BACK"}


class TestPerfilAmbiguo(unittest.TestCase):
    """Alguém que gosta tanto de dados quanto de desenvolvimento web."""

    def setUp(self):
        self.r = calcular(BASE, DADOS_E_WEB)

    def test_top3_mistura_dados_e_web(self):
        ids = {i.trilha_id for i in self.r.top3}
        self.assertTrue(ids & DADOS, ids)
        self.assertTrue(ids & WEB, ids)

    def test_empate_parcial_detectado(self):
        self.assertTrue(self.r.hibrido)
        a, b, diff = self.r.empates[0]
        self.assertLess(diff, BASE["limiares"]["empate_pp"])
        self.assertTrue(any("Perfil híbrido" in al for al in self.r.alertas))

    def test_confianca_nao_e_alta(self):
        self.assertNotEqual(self.r.confianca, "alta")

    def test_justificativa_das_trilhas_empatadas(self):
        for tid in self.r.empates[0][:2]:
            item = self.r.item(tid)
            self.assertTrue(item.motivos or item.regras, f"{tid} sem justificativa")

    def test_plano_continua_gerando_para_qualquer_das_empatadas(self):
        for tid in self.r.empates[0][:2]:
            p = servico.gerar_plano(BASE, DADOS_E_WEB, trilha_id=tid)
            self.assertEqual(p.trilha_id, tid)
            self.assertTrue(p.roadmap.fases)

    def test_dica_de_desempate_para_par_confundivel(self):
        # DS × DE é um par catalogado: dados + matemática alta + pipelines próximos
        resp = perfil(af_dados=5, af_matematica=4, af_ia=4, af_logica=4, af_infra=4, sk_python=2, sk_sql=2)
        r = calcular(BASE, resp)
        ids = [i.trilha_id for i in r.top3]
        if "DS" in ids and "DE" in ids:
            comp = {i.trilha_id: i.compatibilidade for i in r.ranking}
            if abs(comp["DS"] - comp["DE"]) <= BASE["limiares"]["proximo_pp"]:
                self.assertTrue(any("Ciência de Dados" in d and "Engenharia de Dados" in d for d in r.dicas))

    def test_desempate_fullstack(self):
        r = calcular(BASE, perfil(af_web=5, af_design=5, af_logica=5, ob_usuario=4, sk_javascript=2, sk_html_css=2, sk_python=2))
        self.assertEqual({i.trilha_id for i in r.top3[:2]}, {"FRONT", "BACK"})
        ids_regras = {g["id"] for i in r.top3[:2] for g in i.regras}
        self.assertIn("BON09", ids_regras)


class TestRespostasExtremas(unittest.TestCase):
    def test_tudo_neutro(self):
        r = calcular(BASE, perfil(padrao_likert=3))
        self.assertEqual(r.confianca, "baixa")
        self.assertTrue(any("quase todas iguais" in a for a in r.alertas))
        self.assertTrue(any("Nenhuma trilha atingiu" in a for a in r.alertas))

    def test_tudo_maximo(self):
        r = calcular(BASE, perfil(padrao_likert=5))
        self.assertTrue(any("quase todas iguais" in a for a in r.alertas))
        self.assertTrue(all(0 <= i.compatibilidade <= 100 for i in r.ranking))

    def test_tudo_minimo(self):
        r = calcular(BASE, perfil(padrao_likert=1))
        self.assertTrue(any("quase todas iguais" in a for a in r.alertas))
        self.assertTrue(all(0 <= i.compatibilidade <= 100 for i in r.ranking))
        self.assertLess(r.top3[0].compatibilidade, BASE["limiares"]["compatibilidade_minima"])

    def test_empate_total_usa_ordem_estavel_do_json(self):
        r = calcular(BASE, perfil(padrao_likert=3))
        topo = r.ranking[0].compatibilidade
        empatadas = [i.trilha_id for i in r.ranking if i.compatibilidade == topo]
        ordem_json = [t for t in BASE["trilhas"] if t in empatadas]
        self.assertEqual(empatadas, ordem_json)

    def test_sem_respostas(self):
        r = calcular(BASE, {})
        self.assertTrue(any("sem resposta" in a for a in r.alertas))
        self.assertEqual(len(r.ranking), 10)

    def test_respostas_invalidas(self):
        casos = [{"af_mobile": 0}, {"af_mobile": 6}, {"af_mobile": "alto"}, {"af_mobile": True},
                 {"sk_python": 4}, {"sk_python": -1}, {"nao_existe": 3}]
        for caso in casos:
            with self.subTest(caso=caso), self.assertRaises(ValueError):
                calcular(BASE, caso)

    def test_nenhum_resultado_depende_de_ordem_das_chaves(self):
        resp = PERSONAS["Mobile"][0]
        invertido = dict(reversed(list(resp.items())))
        a = [(i.trilha_id, i.compatibilidade) for i in calcular(BASE, resp).ranking]
        b = [(i.trilha_id, i.compatibilidade) for i in calcular(BASE, invertido).ranking]
        self.assertEqual(a, b)


class TestDesacoplamento(unittest.TestCase):
    """As regras vivem no JSON: alterar o arquivo muda o comportamento sem tocar no Python."""

    def _salvar(self, base, tmp):
        caminho = pathlib.Path(tmp) / "base.json"
        caminho.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
        return caminho

    def test_codigo_nao_tem_trilhas_nem_pesos_embutidos(self):
        for modulo in (motor, gaps, roadmap, servico):
            fonte = pathlib.Path(modulo.__file__).read_text(encoding="utf-8")
            for tid in BASE["trilhas"]:
                self.assertNotIn(f'"{tid}"', fonte, f"{modulo.__name__} cita a trilha {tid}")
            for qid in list(BASE["pesos"])[:10]:
                self.assertNotIn(qid, fonte, f"{modulo.__name__} cita a pergunta {qid}")

    def test_alterar_peso_no_json_muda_o_ranking(self):
        resp = PERSONAS["Front-end"][0]
        original = calcular(BASE, resp).item("FRONT").compatibilidade
        alterada = copy.deepcopy(BASE)
        alterada["pesos"]["af_design"]["FRONT"] = 1
        with tempfile.TemporaryDirectory() as tmp:
            nova = carregar_base(self._salvar(alterada, tmp))
        self.assertNotEqual(calcular(nova, resp).item("FRONT").compatibilidade, original)

    def test_remover_regra_no_json_remove_o_efeito(self):
        resp = perfil(af_matematica=1, af_dados=3)
        self.assertIn("PEN01", [g["id"] for g in calcular(BASE, resp).item("DS").regras])
        alterada = copy.deepcopy(BASE)
        alterada["regras_logicas"] = [r for r in alterada["regras_logicas"] if r["id"] != "PEN01"]
        with tempfile.TemporaryDirectory() as tmp:
            nova = carregar_base(self._salvar(alterada, tmp))
        self.assertNotIn("PEN01", [g["id"] for g in calcular(nova, resp).item("DS").regras])

    def test_nova_trilha_apenas_no_json(self):
        alterada = copy.deepcopy(BASE)
        alterada["trilhas"]["EXTRA"] = copy.deepcopy(alterada["trilhas"]["QA"])
        alterada["trilhas"]["EXTRA"]["nome"] = "Trilha Extra"
        alterada["pesos"]["af_testes"]["EXTRA"] = 10
        with tempfile.TemporaryDirectory() as tmp:
            nova = carregar_base(self._salvar(alterada, tmp))
        r = calcular(nova, perfil(af_testes=5))
        self.assertEqual(len(r.ranking), 11)
        self.assertIn("EXTRA", [i.trilha_id for i in r.ranking])

    def test_base_padrao_e_valida(self):
        self.assertEqual(carregar_base(CAMINHO_PADRAO)["versao"], BASE["versao"])
        self.assertEqual(len(BASE["trilhas"]), 10)


class TestValidacaoDaBase(unittest.TestCase):
    def _invalida(self, mutacao):
        b = copy.deepcopy(BASE)
        mutacao(b)
        with self.assertRaises(BaseInvalida):
            validar_base(b)

    def test_peso_para_trilha_inexistente(self):
        self._invalida(lambda b: b["pesos"]["af_mobile"].update({"XXX": 5}))

    def test_peso_para_pergunta_inexistente(self):
        self._invalida(lambda b: b["pesos"].update({"af_fantasma": {"QA": 5}}))

    def test_peso_negativo(self):
        self._invalida(lambda b: b["pesos"]["af_mobile"].update({"MOBILE": -1}))

    def test_operador_invalido(self):
        self._invalida(lambda b: b["regras_logicas"][0]["condicoes"][0].update({"op": "~"}))

    def test_competencia_inexistente_no_junior(self):
        self._invalida(lambda b: b["trilhas"]["QA"]["junior"].append({"competencia": "cobol", "nivel": 1, "prioridade": 1}))

    def test_composicao_nao_soma_um(self):
        self._invalida(lambda b: b["composicao"].update({"afinidade": 0.5}))

    def test_chave_ausente(self):
        b = copy.deepcopy(BASE)
        del b["pesos"]
        with self.assertRaises(BaseInvalida):
            validar_base(b)

    def test_arquivo_inexistente_e_json_quebrado(self):
        with self.assertRaises(BaseInvalida):
            carregar_base("/caminho/que/nao/existe.json")
        with tempfile.TemporaryDirectory() as tmp:
            quebrado = pathlib.Path(tmp) / "x.json"
            quebrado.write_text("{ isto nao e json", encoding="utf-8")
            with self.assertRaises(BaseInvalida):
                carregar_base(quebrado)


if __name__ == "__main__":
    unittest.main()
