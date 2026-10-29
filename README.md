# 🧭 Consultor Avançado de Carreiras e Desenvolvimento Profissional

Evolução do consultor de carreiras em TI. Em vez de uma recomendação única, o sistema:

1. coleta respostas **graduais** (escalas de 1 a 5 e níveis de 0 a 3);
2. calcula um **Top 3 com compatibilidade (%)** entre as 10 trilhas;
3. identifica **lacunas de competências** (skill gap) para o nível Júnior;
4. gera um **plano de ação**: o que estudar primeiro, certificações e projetos de portfólio no GitHub.

Trilhas: Back-end, Front-end/UX, Ciência de Dados, Engenharia de Dados, Cibersegurança, DevOps/SRE, Cloud Architecture, Mobile, QA e Product Management.

## Instalação e execução

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Testes:

```bash
python -m unittest discover -s tests -v
```

## Arquitetura

```
.
├── app.py                                # Interface Streamlit em etapas (wizard)
├── gerar_docs.py                         # Gera docs/matriz_pesos.md a partir do JSON
├── requirements.txt
├── base_conhecimento/
│   └── regras_carreiras.json             # TODO o conhecimento: perguntas, pesos, regras, trilhas, planos
├── consultor/
│   ├── base.py                           # Carrega e VALIDA o JSON
│   ├── motor.py                          # Pontuação ponderada, regras lógicas, ranking, justificativas
│   ├── gaps.py                           # Skill gap analysis
│   ├── roadmap.py                        # Ordem de estudo, certificações e projetos
│   ├── servico.py                        # gerar_plano(): une motor + gaps + roadmap
│   └── plano_md.py                       # Exporta o plano em Markdown
├── docs/matriz_pesos.md                  # Fase 1: matriz pergunta × trilha e regras
└── tests/                                # Fases 2 a 5
```

## O arquivo `regras_carreiras.json`

| Chave | O que define |
|---|---|
| `escalas` | Escalas de resposta (`likert`, `concordancia`, `nivel`): mínimo, máximo, valor neutro e rótulos |
| `composicao` | Peso de cada grupo no resultado (padrão: 85% afinidade, 15% conhecimento atual) |
| `limiares` | Margens de empate, de confiança, de prontidão etc. |
| `etapas` | Títulos dos passos do wizard |
| `perguntas` | Texto, etapa, seção, grupo (`afinidade`/`conhecimento`) e tipo de escala |
| `pesos` | `pergunta → trilha → peso (0 a 10)`: quanto cada resposta importa para cada trilha |
| `regras_logicas` | Bônus, penalidades e desambiguações com condições combinadas (E) e justificativa |
| `pares_confundiveis` | Dicas de desempate para trilhas parecidas (ex.: Ciência × Engenharia de Dados) |
| `trilhas` | Nome, descrição, requisitos de nível **Júnior**, projetos, certificações e tecnologias complementares |
| `competencias` | Horas por nível, pré-requisitos e o que estudar em cada nível |

Exemplo de regra lógica:

```json
{
  "id": "PEN01", "tipo": "penalidade",
  "condicoes": [{"pergunta": "af_matematica", "op": "<=", "valor": 2}],
  "efeitos": {"DS": -15},
  "justificativa": "Ciência de Dados depende de base estatística; ..."
}
```

Para alterar o comportamento, edite o JSON e rode os testes. `carregar_base()` valida referências cruzadas (trilhas, perguntas, competências, operadores) e acusa o erro com mensagem clara. Depois de mexer nos pesos, rode `python gerar_docs.py` para atualizar a matriz documentada.

## Como o cálculo funciona

1. Cada resposta é normalizada para 0–1.
2. Para cada trilha e grupo: `score = Σ(peso × resposta) / Σ(pesos)`.
3. `compatibilidade = 100 × (0,85 × afinidade + 0,15 × conhecimento)`.
4. Regras lógicas somam (bônus) ou subtraem (penalidade) pontos quando **todas** as condições são verdadeiras, e o resultado é limitado a 0–100%.
5. Ranking ordenado por compatibilidade (desempate: afinidade e, depois, ordem das trilhas no JSON).

### Empates parciais e confiança

- Duas trilhas do Top 3 a menos de 5 pontos percentuais uma da outra ⇒ **perfil híbrido**, sinalizado ao usuário.
- Se o par é conhecido (`pares_confundiveis`) e as notas estão a até 10 pontos, o sistema mostra uma **dica de desempate**.
- A **confiança** é alta, média ou baixa conforme a margem entre 1º e 2º lugar e o percentual do 1º.
- Respostas quase uniformes (tudo 3, tudo 5) e perfis em que nenhuma trilha chega a 55% geram alertas.

### Skill gap e roadmap

- Para a trilha escolhida, cada competência de nível Júnior é comparada ao nível informado: **atende**, **parcial** ou **ausente**.
- **Prontidão** = Σ(prioridade × nível alcançado) / Σ(prioridade × nível exigido).
- O roadmap agrupa as lacunas em fases por prioridade, respeitando pré-requisitos (ex.: Linux antes de Docker), estima horas e semanas pelo ritmo informado e indica **quando** cada projeto e certificação fica viável.

## Testes (Fases 2 a 5)

| Arquivo | Cobertura |
|---|---|
| `test_motor.py` | 10 personas (Top 1 e Top 3), penalidades, regras com várias condições, monotonicidade, 200 perfis aleatórios |
| `test_gaps_roadmap.py` | Gaps (iniciante, avançado, parcial), ordem e pré-requisitos, horas, projetos, certificações, Markdown |
| `test_robustez.py` | Perfil ambíguo dados + web, respostas uniformes, valores inválidos, respostas faltando, desacoplamento do JSON, validação da base |

## Limitações

- Pesos, regras e requisitos de nível Júnior são **heurísticas** de engenharia de conhecimento e ainda não foram calibrados com dados reais nem revisados por especialistas de mercado.
- Os requisitos de Júnior se baseiam nas 18 competências do catálogo; habilidades interpessoais não são avaliadas.
- Certificações e cursos mudam: confirme requisitos, preços e disponibilidade nos sites oficiais.
- O Top 3 é uma orientação, não uma sentença: perfis híbridos devem explorar mais de uma trilha.
