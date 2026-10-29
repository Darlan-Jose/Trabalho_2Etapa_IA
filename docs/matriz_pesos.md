# Matriz de pesos e regras (gerada do JSON)

Fonte: `base_conhecimento/regras_carreiras.json`. Não edite este arquivo: edite o JSON e rode `python gerar_docs.py`.

## Como a compatibilidade é calculada

1. Cada resposta é normalizada para 0–1 (`(resposta − mín) / (máx − mín)`).
2. Para cada trilha e cada grupo: `score_grupo = Σ(peso × resposta) / Σ(pesos)`.
3. Os grupos são combinados pela `composicao` afinidade 85%, conhecimento 15%.
4. Regras lógicas somam (bônus) ou subtraem (penalidade) pontos percentuais quando **todas** as condições são verdadeiras.
5. O resultado é limitado a 0–100% e ordenado (Top 3 em destaque).

## Matriz pergunta × trilha (pesos 0–10)

| Pergunta | Grupo | Back-end | Front-end/UX | Ciência de Dados | Eng. de Dados | Cibersegurança | DevOps/SRE | Cloud | Mobile | QA | Produto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `perf_pessoas` | afinidade |  | 3 |  |  |  |  |  | 2 | 2 | 8 |
| `perf_pressao` | afinidade |  |  |  |  | 5 | 7 | 3 |  |  |  |
| `perf_detalhe` | afinidade | 2 | 3 |  | 2 | 6 |  |  |  | 8 |  |
| `perf_abstracao` | afinidade | 2 |  |  | 3 |  |  | 7 |  |  | 6 |
| `perf_foco` | afinidade | 5 |  | 5 | 4 | 5 |  |  |  |  |  |
| `af_matematica` | afinidade | 2 |  | 9 | 3 | 3 |  |  |  |  |  |
| `af_logica` | afinidade | 8 | 3 | 4 | 5 | 4 | 3 |  | 5 | 3 |  |
| `af_design` | afinidade |  | 9 |  |  |  |  |  | 5 |  | 3 |
| `af_infra` | afinidade | 2 |  |  | 4 | 4 | 9 | 9 |  |  |  |
| `af_dados` | afinidade | 3 |  | 8 | 9 |  |  |  |  |  | 2 |
| `af_seguranca` | afinidade |  |  |  |  | 10 | 3 | 3 |  |  |  |
| `af_automacao` | afinidade |  |  |  | 3 |  | 9 | 3 |  | 5 |  |
| `af_mobile` | afinidade |  |  |  |  |  |  |  | 10 |  |  |
| `af_testes` | afinidade | 2 |  |  |  |  | 2 |  |  | 10 |  |
| `af_gestao` | afinidade |  |  |  |  |  |  | 2 |  |  | 10 |
| `af_web` | afinidade | 5 | 7 |  |  |  |  |  |  |  | 1 |
| `af_ia` | afinidade |  |  | 9 | 2 |  |  |  |  |  |  |
| `af_nuvem` | afinidade | 2 |  |  | 3 | 2 | 5 | 10 |  |  |  |
| `sk_python` | conhecimento | 3 |  | 4 | 4 |  | 2 |  |  | 2 |  |
| `sk_javascript` | conhecimento | 2 | 5 |  |  |  |  |  | 2 | 2 |  |
| `sk_html_css` | conhecimento |  | 5 |  |  |  |  |  |  |  |  |
| `sk_sql` | conhecimento | 4 |  | 3 | 5 |  |  |  |  |  |  |
| `sk_git` | conhecimento |  |  |  |  |  |  |  |  |  |  |
| `sk_apis` | conhecimento | 4 | 1 |  |  |  |  |  |  |  |  |
| `sk_linux` | conhecimento |  |  |  | 1 | 3 | 4 | 3 |  |  |  |
| `sk_redes` | conhecimento |  |  |  |  | 4 | 2 | 3 |  |  |  |
| `sk_docker` | conhecimento | 1 |  |  |  |  | 4 | 2 |  |  |  |
| `sk_cloud` | conhecimento |  |  |  | 2 |  | 3 | 5 |  |  |  |
| `sk_estatistica` | conhecimento |  |  | 5 | 1 |  |  |  |  |  |  |
| `sk_testes` | conhecimento | 1 |  |  |  |  |  |  |  | 5 |  |
| `sk_agil` | conhecimento |  |  |  |  |  |  |  |  | 1 | 4 |
| `sk_mobile` | conhecimento |  |  |  |  |  |  |  | 6 |  |  |
| `sk_seguranca` | conhecimento |  |  |  |  | 5 |  |  |  |  |  |
| `sk_design` | conhecimento |  | 4 |  |  |  |  |  | 1 |  | 1 |
| `sk_etl` | conhecimento |  |  |  | 5 |  |  |  |  |  |  |
| `sk_ml` | conhecimento |  |  | 5 |  |  |  |  |  |  |  |
| `ob_lideranca` | afinidade |  |  |  |  |  |  | 4 |  |  | 8 |
| `ob_especialista` | afinidade |  |  | 6 | 4 | 6 |  | 4 |  |  |  |
| `ob_usuario` | afinidade | 2 | 6 |  |  |  |  |  | 7 |  | 5 |
| `ob_escala` | afinidade | 5 |  |  | 6 |  | 4 | 6 |  |  |  |
| `ob_inovacao` | afinidade |  |  | 6 |  | 4 |  |  |  |  |  |
| `ob_processos` | afinidade |  |  |  |  |  | 4 | 2 |  | 6 | 3 |

## Regras lógicas (bônus, penalidades e desambiguação)

| Regra | Tipo | Condições (E) | Efeitos (pontos %) |
|---|---|---|---|
| PEN01 | penalidade | `af_matematica <= 2` | Ciência de Dados -15 |
| PEN02 | penalidade | `af_infra <= 2` | DevOps/SRE -15, Cloud -15 |
| PEN03 | penalidade | `af_design <= 2` | Front-end/UX -15, Mobile -6 |
| PEN04 | penalidade | `af_seguranca <= 2` | Cibersegurança -15 |
| PEN05 | penalidade | `af_gestao <= 2` **e** `perf_pessoas <= 2` | Produto -15 |
| PEN06 | penalidade | `af_logica <= 2` | Back-end -15, Eng. de Dados -10, Mobile -8 |
| PEN07 | penalidade | `af_testes <= 2` **e** `perf_detalhe <= 2` | QA -15 |
| PEN08 | penalidade | `af_mobile <= 2` | Mobile -15 |
| PEN09 | penalidade | `af_dados <= 2` | Ciência de Dados -12, Eng. de Dados -12 |
| PEN10 | penalidade | `perf_pressao <= 2` | DevOps/SRE -8 |
| PEN11 | penalidade | `af_nuvem <= 2` | Cloud -12 |
| BON01 | bonus | `af_dados >= 4` **e** `af_matematica >= 4` **e** `af_ia >= 4` | Ciência de Dados +8 |
| BON02 | bonus | `af_dados >= 4` **e** `af_infra >= 4` | Eng. de Dados +8 |
| BON03 | desambiguacao | `af_dados >= 4` **e** `af_matematica <= 3` | Eng. de Dados +6, Ciência de Dados -6 |
| BON04 | bonus | `af_infra >= 4` **e** `af_automacao >= 4` | DevOps/SRE +8 |
| BON05 | bonus | `af_infra >= 4` **e** `af_nuvem >= 4` **e** `perf_abstracao >= 4` | Cloud +8 |
| BON06 | bonus | `af_design >= 4` **e** `af_web >= 4` | Front-end/UX +8 |
| BON07 | bonus | `af_design >= 4` **e** `af_mobile >= 4` | Mobile +6 |
| BON08 | desambiguacao | `af_logica >= 4` **e** `af_web >= 4` **e** `af_design <= 3` | Back-end +8, Front-end/UX -5 |
| BON09 | desambiguacao | `af_web >= 4` **e** `af_design >= 4` **e** `af_logica >= 4` | Front-end/UX +4, Back-end +4 |
| BON10 | bonus | `af_seguranca >= 4` **e** `af_infra >= 4` | Cibersegurança +6 |
| BON11 | bonus | `af_testes >= 4` **e** `af_automacao >= 4` | QA +8 |
| BON12 | bonus | `af_gestao >= 4` **e** `perf_pessoas >= 4` **e** `ob_lideranca >= 4` | Produto +8 |

## Requisitos de nível Júnior por trilha

Níveis: 0 = Nunca estudei, 1 = Básico, 2 = Intermediário, 3 = Avançado

**Desenvolvimento Back-end**: Python ≥ 2 (prioridade 3); SQL e bancos de dados ≥ 2 (prioridade 3); APIs REST ≥ 2 (prioridade 3); Git e GitHub ≥ 2 (prioridade 2); Testes de software ≥ 1 (prioridade 2); Linux e linha de comando ≥ 1 (prioridade 1); Contêineres (Docker) ≥ 1 (prioridade 1)

**Desenvolvimento Front-end & UI/UX**: HTML e CSS ≥ 2 (prioridade 3); JavaScript/TypeScript ≥ 2 (prioridade 3); Git e GitHub ≥ 2 (prioridade 2); Design de interfaces e UX ≥ 1 (prioridade 2); APIs REST ≥ 1 (prioridade 2); Testes de software ≥ 1 (prioridade 1)

**Ciência de Dados e Machine Learning**: Python ≥ 2 (prioridade 3); Estatística e probabilidade ≥ 2 (prioridade 3); Machine Learning ≥ 1 (prioridade 3); SQL e bancos de dados ≥ 1 (prioridade 2); Git e GitHub ≥ 1 (prioridade 1)

**Engenharia de Dados**: SQL e bancos de dados ≥ 2 (prioridade 3); Python ≥ 2 (prioridade 3); Pipelines de dados ≥ 1 (prioridade 3); Computação em nuvem ≥ 1 (prioridade 2); Git e GitHub ≥ 1 (prioridade 2); Linux e linha de comando ≥ 1 (prioridade 1); Contêineres (Docker) ≥ 1 (prioridade 1)

**Cibersegurança (Security / Pentesting)**: Redes de computadores ≥ 2 (prioridade 3); Linux e linha de comando ≥ 2 (prioridade 3); Fundamentos de segurança ≥ 2 (prioridade 3); Python ≥ 1 (prioridade 2); Git e GitHub ≥ 1 (prioridade 1)

**DevOps & SRE**: Linux e linha de comando ≥ 2 (prioridade 3); Contêineres (Docker) ≥ 2 (prioridade 3); Git e GitHub ≥ 2 (prioridade 2); Computação em nuvem ≥ 1 (prioridade 2); Redes de computadores ≥ 1 (prioridade 2); Python ≥ 1 (prioridade 2)

**Computação em Nuvem (Cloud Architecture)**: Computação em nuvem ≥ 2 (prioridade 3); Redes de computadores ≥ 2 (prioridade 3); Linux e linha de comando ≥ 2 (prioridade 3); Contêineres (Docker) ≥ 1 (prioridade 2); Fundamentos de segurança ≥ 1 (prioridade 1); Git e GitHub ≥ 1 (prioridade 1)

**Desenvolvimento Mobile**: Desenvolvimento mobile ≥ 2 (prioridade 3); APIs REST ≥ 1 (prioridade 2); Git e GitHub ≥ 2 (prioridade 2); Design de interfaces e UX ≥ 1 (prioridade 1); Testes de software ≥ 1 (prioridade 1)

**Engenharia de Qualidade e Testes (QA)**: Testes de software ≥ 2 (prioridade 3); Python ≥ 1 (prioridade 2); APIs REST ≥ 1 (prioridade 2); Git e GitHub ≥ 1 (prioridade 2); Metodologias ágeis e produto ≥ 1 (prioridade 2); SQL e bancos de dados ≥ 1 (prioridade 1)

**Gestão de Produtos (Product Management)**: Metodologias ágeis e produto ≥ 2 (prioridade 3); Design de interfaces e UX ≥ 1 (prioridade 2); SQL e bancos de dados ≥ 1 (prioridade 1); Estatística e probabilidade ≥ 1 (prioridade 1)

