"""Fachada que une motor, análise de gaps e roadmap em um único plano."""
from dataclasses import dataclass

from .gaps import AnaliseGap, analisar_gaps
from .motor import Resultado, calcular
from .roadmap import Roadmap, gerar_roadmap


@dataclass
class Plano:
    resultado: Resultado
    trilha_id: str
    gaps: AnaliseGap
    roadmap: Roadmap


def gerar_plano(base: dict, respostas: dict, trilha_id: str | None = None,
                horas_semana: int | None = None) -> Plano:
    """Calcula o ranking e gera gaps + roadmap para `trilha_id` (padrão: a 1ª do ranking)."""
    resultado = calcular(base, respostas)
    trilha_id = trilha_id or resultado.ranking[0].trilha_id
    if trilha_id not in base["trilhas"]:
        raise ValueError(f"Trilha inexistente: {trilha_id}")
    gaps = analisar_gaps(base, trilha_id, resultado.respostas)
    roadmap = gerar_roadmap(base, trilha_id, gaps, resultado.respostas, horas_semana)
    return Plano(resultado, trilha_id, gaps, roadmap)
