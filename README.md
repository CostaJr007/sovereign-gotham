# Sovereign Gotham // Operational Intelligence & Universal Cognitive Engine

[![Hugging Face Model](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Sovereign--Anthology--Gemma--2--2B-ffd21e)](https://huggingface.co/KolmogorovAcc/sovereign-anthology-gemma-2-2b)
[![License: Gemma](https://img.shields.io/badge/License-Gemma-blue.svg)](https://ai.google.dev/gemma/terms)
[![DirectML Accelerated](https://img.shields.io/badge/Hardware-AMD%20Radeon%20RX%207600%20XT-ed1c24)](https://www.amd.com)
[![Ollama Ready](https://img.shields.io/badge/Ollama-sovereign--gemma2-black)](https://ollama.com)

Plataforma de inteligência tática, resolução de problemas e tomada de decisão fundamentada no metamodelo da **Palantir (Gotham, Foundry e AIP)**. O sistema opera de forma **100% soberana, local e air-gapped**, acelerado nativamente por hardware **AMD Radeon RX 7600 XT (16 GB GDDR6)** via DirectML e destilado a partir do tradecraft metodológico autêntico da Comunidade de Inteligência e Defesa dos EUA (**CIA, NSA, US Army e DoD**).

---

## 🏛️ 1. A Filosofia: Metodologia Pura vs. Fatos Históricos

Um erro comum em IA aplicada a dados de inteligência é tentar forçar o modelo a memorizar fatos passados ou cabogramas antigos da Guerra Fria. Isso gera poluição por ruído de OCR e alucinações burocráticas irrelevantes.

O **Sovereign Gotham** implementa uma separação ontológica estrita em duas camadas:

1. **Camada de Evidências Fáticas (Vector Store / ChromaDB + Knowledge Graph)**:
   - Documentos governamentais brutos residem no banco vetorial para recuperação factual (RAG) sob demanda estrita.
2. **Camada de Disciplina Cognitiva (O "Cérebro" Soberano Gemma 2 / DeepSeek)**:
   - O modelo **não memoriza fatos passados mortos**. Ele aprendeu a **metodologia cirúrgica de resolução de problemas** das agências e a projeta sobre crises reais do mundo moderno (startups, incidentes de infraestrutura crítica, segurança cibernética, fraudes societárias, trade-offs de alta complexidade).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          DIRETIVA OPERACIONAL / DILEMA REAL                            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CAMADA 1: TRIAGEM DE SINAIS E TELEMETRIA (NSA)                                         │
│ • Isolação de sinal frio vs. ruído opinativo via limites estatísticos (2.5-sigma)      │
│ • Alocação de capacidade de pipeline por taxa de perecibilidade do dado (PPCATP)       │
│ • Retificação semântica: segregação rigorosa entre modelo conceitual e schema de dados │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CAMADA 2: ENGENHARIA FORENSE E REDE DE INCENTIVOS (FBI)                                │
│ • Mapeamento de assimetria de risco moral e trilha causal Follow-The-Money             │
│ • Corroboração cega independente: nenhuma alegação unilateral é aceita sem rastro     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CAMADA 3: ANÁLISE DE HIPÓTESES CONCORRENTES - ACH (CIA)                                │
│ • Construção de matriz de hipóteses mutuamente exclusivas (Richards Heuer)             │
│ • Eliminação por inconsistência diagnóstica para erradicar o viés de confirmação       │
│ • Leitura do "espaço negativo": auditoria de silêncios deliberados e omissões          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CAMADA 4: COMANDO DE MISSÃO E OODA LOOP FASEADO (DOD / US ARMY)                        │
│ • Planejamento temporal determinístico: T+24h (Contenção), T+7d (Manobra), T+30d       │
│ • Quantificação empírica de degradação por atrito (Friction Tax / EPDQ-ODR)            │
│ • Regras de Engajamento (ROE) invioláveis e Critério Quantitativo de Aborto (Stop-Loss)│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SAÍDA: AUDITABLE PALANTIR ACTION BLUEPRINT (JSON / PROTOCOL)                           │
│ • Objects: NSASignalVector, FBIActorProfile, CIAHypothesisMatrix, DoDDoctrine          │
│ • Links: CORRELATES_WITH, EVALUATES_HYPOTHESIS, COMMANDS_ACTION                        │
│ • Actions: Fases cronológicas, limites de engajamento e gatilhos de aborto imediato    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 2. Novo Marco: Sovereign Anthology — Gemma 2 2B

Evoluindo a partir das primeiras iterações experimentais, consolidamos o modelo de produção **Sovereign Anthology — Gemma 2 2B**:

* **Base Foundation**: Google Gemma 2 2B-IT (Arquitetura moderna com Sliding Window Attention e Logit Soft-capping).
* **Destilação Cognitiva Teacher-Student**: Extração supervisionada via **Google Gemini**, transformando doutrinas de inteligência em 2.334 amostras ricas em telemetria analítica real (P99, saturação de filas, ARR em risco, retração de erros).
* **Treinamento SFT de Precisão Total (DirectML)**:
  - 1.752 passos de otimização (3 épocas completas, ~8h15m de treino dedicado na GPU AMD Radeon RX 7600 XT 16GB).
  - Curva de convergência: Loss inicial **7.38** $\rightarrow$ Loss final **0.0001**.
  - All-Linear LoRA ($r=16, \alpha=32$) em todos os módulos lineares (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`).
* **Fusão Standalone (Merged Weights)**: Pesos LoRA absorvidos sem latência residual em precisão FP16 SafeTensors.
* **Formatos de Distribuição**:
  - **FP16 SafeTensors**: Para inferência nativa em Python via Hugging Face Transformers.
  - **GGUF FP16**: Binário completo de 5.2 GB para Ollama / llama.cpp.
  - **GGUF Q4_K_M**: Binário quantizado ultra-rápido de 1.6 GB (>30 tokens/s localmente).

---

## ⚡ 3. Engenharia de Aceleração AMD Radeon (DirectML)

Para viabilizar o treinamento e fusão em hardware de consumo AMD (RDNA3 / RX 7600 XT 16GB GDDR6), foram desenvolvidas soluções de kernel pioneiras:

1. **DirectML Soft-Capping Kernel Fix**:
   - O `torch.tanh` nativo do operador Gemma 2 falha em tensores FP16 no dispatcher DirectML (`CreateOperator`). O cálculo foi redirecionado em ponto flutuante FP32:
     $$\text{scores} = \text{softcap} \times \tanh\left(\frac{QK^T}{\sqrt{d_k} \times \text{softcap}}\right)_{\text{float32}}$$
2. **Chunked Cross-Entropy Loss**:
   - Evitou picos de memória de vocabulário (256.000 tokens) segmentando o cálculo de perda em fatias de 64 tokens, mantendo o consumo de VRAM estável em ~8.2 GB dos 16 GB disponíveis.
3. **OpaqueTensor DirectML LoRA Offloading**:
   - Extração e offload seguro de estado do adaptador para a RAM do sistema (`v.cpu()`), contornando restrições de ponteiro do backend Windows.

---

## 📦 4. Como Executar Localmente

### Via Ollama (Recomendado)

O modelo já está totalmente compatível e registrado no Ollama:

```powershell
# Versão ultra-rápida quantizada (1.6 GB):
ollama run sovereign-gemma2:q4

# Versão precisão total FP16 (5.2 GB):
ollama run sovereign-gemma2
```

### Via Hugging Face Transformers (Python)

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "KolmogorovAcc/sovereign-anthology-gemma-2-2b"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto"
)

prompt = """<bos><start_of_turn>user
Civilian problem [business]: A critical payment processing queue is failing with 450% backlog.
Operating principle (NSA): Prioritize processing operations by evaluating time-sensitivity, anticipated volume, and value.
<end_of_turn>
<start_of_turn>model
"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=400, temperature=0.6, top_p=0.9)
print(tokenizer.decode(outputs[0], skip_special_tokens=False))
```

---

## 🎯 5. Estrutura de Resposta Operacional do Modelo

O modelo responde estruturando todo o fluxo de tomada de decisão:

1. **`<thought>` (Matriz Cognitiva Richards Heuer - CIA)**:
   - **Hypotheses ($H_1, H_2, H_3$)**: Formulação de hipóteses concorrentes e mutuamente exclusivas.
   - **Diagnostic Evidence**: Foco na busca por evidências que *refutam* hipóteses fracas, combatendo o viés de confirmação.
   - **Known Gaps**: Lacunas de informação crítica identificadas.
   - **Observable Indicators**: Indicadores empíricos de validação ou aborto.
2. **`Protocol:`**: Passos de ação numerados, com *circuit breakers* e limites quantitativos estritos.
3. **`After-action (30d):`**: Plano de revisão em 30 dias para calibrar desvios de desempenho (*performance drift*).

---

## 🌐 6. Repositórios e Artefatos

* **Hugging Face Hub**: [KolmogorovAcc/sovereign-anthology-gemma-2-2b](https://huggingface.co/KolmogorovAcc/sovereign-anthology-gemma-2-2b)
* **Dataset de Treinamento**: `anthology_gemma_v1.jsonl` (2.334 amostras estruturadas)
* **Checkpoints de Treino**: `D:\sovereign_models\sovereign_anthology_gemma2_lora`
* **Modelo Standalone Unificado**: `D:\sovereign_models\sovereign_anthology_gemma2_2b`
