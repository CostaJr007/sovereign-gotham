# SOVEREIGN GOTHAM // MANUAL DO SISTEMA DE INTELIGÊNCIA & TREINAMENTO NEURAL
**Arquitetura Cognitiva Soberana Inspirada no Palantir Gotham alimentada por DeepSeek-R1**
*Aceleração Local por Hardware: AMD Radeon RX 7600 XT (16 GB GDDR6) via DirectML*

---

## 1. Visão Geral Executiva & Perfil da Missão

O **Sovereign Gotham** é uma plataforma autônoma de inteligência, fusão de dados e análise de ameaças desenhada para operar de maneira **100% soberana, local e air-gapped** (sem dependência de nuvens externas, telemetria ou envio de dados confidenciais a terceiros).

### Capacidades Centrais:
* **Fusão de Inteligência Multiatômica**: Ingestão contínua de relatórios desclassificados da CIA (acervo CREST / History Lab da Universidade de Columbia), FBI Vault, NSA, DoD e Foreign Broadcast Information Service (FBIS).
* **Ontologia Operacional Palantir Gotham (OSDK)**: Modelagem rigorosa de entidades (`Target_Entity`), operações (`Operation`), procedimentos (`Procedure`) e documentos (`Document`) com controle de classificação estrita segundo o padrão **CAPCO** (ex: `TOP SECRET // SI / TK // NOFORN`).
* **Núcleo Cognitivo Reflexivo (DeepSeek-R1)**: Modelo de linguagem treinado localmente com capacidade nativa de raciocínio passo-a-passo (`<thought>...</thought>`), gerando pareceres analíticos justificados e JSONs operacionais.

---

## 2. Arquitetura de Hardware & Treinamento

| Componente | Especificação de Produção |
| :--- | :--- |
| **GPU Primária** | `AMD Radeon RX 7600 XT` (16 GB GDDR6, 128-bit, 2048 Stream Processors) |
| **Backend de Aceleração** | Microsoft DirectML via DirectX 12 Compute (`torch-directml`) |
| **Dispositivo DirectML** | `Device 1: AMD Radeon RX 7600 XT` (`privateuseone:1`) |
| **Modelo Base** | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` |
| **Técnica de Treinamento** | Fine-Tuning Paramétrico Eficiente (PEFT / LoRA) |
| **Otimização de VRAM** | Gradient Checkpointing (`model.gradient_checkpointing_enable()`) |
| **Precisão** | `float32` (eliminando estouro de precisão e buffers no driver DirectML) |
| **Hiperparâmetros** | Batch Size: 1 \| Grad Accum: 4 \| LoRA Rank: 16 \| Alpha: 32 \| LR: 2e-4 |
| **Dataset de Treino** | 1.788 amostras de inteligência tática com blocos `<thought>` |
| **Convergência do Loss** | **4.2924 $\to$ 0.8754** (100% dos 447 passos completados) |
| **Tempo de Treino** | ~36 minutos na GPU dedicados |

---

## 3. Estrutura de Diretórios e Pesos no Disco D:

Todos os pesos e dados pesados foram isolados no disco `D:/` para preservar a integridade do sistema operacional:

```text
D:/
├── sovereign_models/
│   ├── deepseek_r1_sovereign_agent/
│   │   ├── final_adapter/                      <-- ADAPTADOR LORA FINAL TREINADO
│   │   │   ├── adapter_config.json             (Configuração PEFT LoRA)
│   │   │   ├── adapter_model.safetensors       (8,73 MB de tensores neurais afinados)
│   │   │   ├── README.md                       (Metadados do modelo)
│   │   │   ├── tokenizer.json                  (Vocabulário DeepSeek-R1)
│   │   │   ├── tokenizer_config.json           (Chat templates e tokens especiais)
│   │   │   └── special_tokens_map.json         (Mapeamento de marcadores <thought>)
│   │   └── checkpoint-400/                     (Checkpoint intermediário preservado)
│   └── training_status.json                    (Status em tempo real do dashboard)
└── sovereign_gotham_data/                      (Data Lake de inteligência bruta e OCR)
```

---

## 4. Como Executar Inferência Local com a GPU AMD

Disponibilizamos um executor CLI nativo [cli/sovereign_inference.py](file:///c:/Users/adeil/.gemini/antigravity/scratch/sovereign_gotham/cli/sovereign_inference.py) que carrega o modelo base e aplica o adaptador treinado na sua **AMD Radeon RX 7600 XT**:

### A. Consulta Rápida (One-Shot Directive):
```powershell
python cli/sovereign_inference.py "Analise a desclassificação do Projeto MKULTRA e identifique os riscos para agentes de campo."
```

### B. Modo Interativo de Inteligência (Estação de Trabalho Contínua):
```powershell
python cli/sovereign_inference.py --interactive
```
*Digite sua consulta operacional no prompt `SovereignGotham>` e receba imediatamente o raciocínio reflexivo `<thought>` e o parecer técnico.*

### C. Ajuste de Criatividade / Temperatura:
```powershell
python cli/sovereign_inference.py --temperature 0.4 --max_tokens 1024 "Gere uma ordem de batalha para neutralizar ameaças no setor ALPHA."
```

---

## 5. Dashboard de Monitoramento em Tempo Real

O servidor de telemetria visual continua disponível e pode ser consultado a qualquer momento:

* **Endereço**: `http://localhost:8888`
* **Script**: [training/monitor_server.py](file:///c:/Users/adeil/.gemini/antigravity/scratch/sovereign_gotham/training/monitor_server.py)
* **Recursos**:
  - Exibe a porcentagem exata (`100.0%`).
  - Gráfico de convergência do Loss.
  - Alocação de VRAM e perfil de hardware da AMD Radeon RX 7600 XT.

Para reiniciar o dashboard caso feche a janela:
```powershell
python training/monitor_server.py
```

---

## 6. Integração com o Agente Autônomo & Grafo Ontológico (OSDK)

O agente soberano conecta o modelo de linguagem diretamente ao **Grafo de Conhecimento Gotham** (`GothamKnowledgeGraph`):

```python
from ontology.graph import GothamKnowledgeGraph
from ontology.osdk_client import SovereignOSDKClient
from agents.sovereign_deepseek_agent import SovereignDeepSeekAgent

# 1. Inicializar grafo ontológico
graph = GothamKnowledgeGraph()
osdk = SovereignOSDKClient(graph)

# 2. Ingerir nós de inteligência
osdk.ingest_document(
    doc_id="CIA-RDP96-00788R001700210016-5",
    title="PROJECT GRILL FLAME - DEFENSE INTELLIGENCE AGENCY",
    classification="SECRET // NOFORN",
    text_content="Operações psicotrônicas e observação remota conduzidas no Fort Meade..."
)

# 3. Consultar agente analítico
agent = SovereignDeepSeekAgent(graph)
result = agent.investigate("Identifique as operações ativas no Fort Meade e seu nível de classificação.")

print("CADEIA DE RACIOCÍNIO:", result.thought_trace)
print("PARECER OPERACIONAL:", result.decision)
```

---

## 7. Relatório de Testes e Validação do Sistema

Todos os testes unitários e de integração foram executados e auditados com sucesso:

* **`pytest tests/test_sovereign_gotham.py`**: 6/6 testes aprovados (100%).
  - Ingestão ontológica OSDK.
  - Validação de marcações CAPCO de segurança nacional.
  - Criação de links semânticos e topologia de rede.
* **`pytest tests/test_sovereign_osdk_and_scrapers.py`**: 7/7 testes aprovados (100%).
  - Raspadores do acervo da Universidade de Columbia (History Lab).
  - Parser de documentos desclassificados CIA/NSA/DoD.
  - Geração de subgrafos de evidência.
* **Auditoria de Tensores**: 112 tensores LoRA verificados e validados no arquivo `adapter_model.safetensors`.

---

## 8. Procedimento para Novos Ciclos de Treinamento

Se desejar expandir o treinamento para mais épocas ou incorporar novos documentos baixados no data lake:

```powershell
python training/train_directml_r1.py `
  --dataset_path training_data/sovereign_deepseek_r1_agent.jsonl `
  --output_dir D:/sovereign_models/deepseek_r1_sovereign_agent `
  --epochs 2 `
  --batch_size 1 `
  --grad_accum 4 `
  --max_seq_length 512 `
  --lora_r 16 `
  --lora_alpha 32 `
  --lr 1.5e-4
```
*O pipeline salvará checkpoints automáticos a cada 100 passos no Drive D: com gravação instantânea e zero risco de estouro de memória.*
