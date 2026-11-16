# Global Trade Compliance Playbook

## 跨境物流合规知识库 + 可运行的 RAG 问答助手

你是一家跨境物流公司的新人客服，面对运单上的欧洲 VAT 递延申报、英国 IEN 码、美国 ACE 录入、加拿大 B3 报关、东南亚汽运清关……还有港前装柜、订舱、清关、港后派送这些节点上的各种问题，不知道去哪找答案。

现在，打开一个浏览器窗口，选一个方向提问，知识库自动从几百页的跨境物流合规手册里翻出相关段落，帮你快速定位。

> 原始知识库来自前公司职务作品，已做 clean-room 脱敏重写。10+ 份业务培训资料、覆盖 5 大地区、9 大操作节点、4 种运输方式。

---

## 功能总览

| 功能 | 人话总结 | 数字例子 |
|---|---|---|
| 知识检索 | 给你一段业务问题，自动从知识库里精准定位相关段落 | "灯具走欧洲哪个渠道？" → 命中欧洲清关 3 条 + 产品认证 2 条 |
| 三选一范围 | 选地区、选节点、或选运输方式，知识库按需加载 | 节点"清关"= 173 条知识；运输"海运"= 4 条 |
| RAG 问答 | 把检索到的段落喂给 LLM，生成结构化、合规的回答 | 每个回答下面显示参考来源和相关度 |
| 一键启动 | Windows 双击 run.bat，浏览器自动打开 | 5 秒启动，零下载依赖 |

---

## 适用场景

- **货代新人入职培训**：不用翻几百页 PDF，直接问"欧洲 VAT 递延怎么申报"
- **清关岗日常查资料**：碰到异常单时快速查找对应环节的操作规范
- **客服应对客户咨询**：客户问"我这票到英国走什么渠道清关最快"，秒答
- **合规岗内部审核**：核对最新政策（CBAM/包装法/EUDR 等）

---

## 范围选择（三选一）

### 地区（5 个）
| 地区 | 核心内容 |
|---|---|
| 欧洲 | VAT 递延、EORI、CBAM、清关行评估、港清/监管仓 |
| 英国 | IEN 码、PVA 申报、C88 文件、DPD 派送、2026 新规 |
| 美国 | ACE/ISF 申报、HTS 编码、FDA/洛杉矶港 |
| 加拿大 | B3 报关、CBSA、温哥华港 |
| 东南亚 | 新加坡/曼谷/巴生港、跨境汽运清关 |

### 操作节点（9 个）
| 节点 | 内容 |
|---|---|
| 港前 | 收货验收、备货贴标 |
| 装柜 | 排柜、贴标签、点数 |
| 订舱 | 船期选择、托书制作、放舱 |
| 报关 | 出口报关资料、AMS/ISF |
| 投保 | 保险条款、理赔范围 |
| 清关 | 清关行选择、查验应对、VAT 递延 |
| 港后 | 海外仓系统、尾端入仓、派送 |
| 理赔 | 货损索赔、保险流程 |
| 财务 | 账单核对、费用结算 |

### 运输方式（4 个）
| 方式 | 内容 |
|---|---|
| 海运 | 航运联盟、船期、甩柜应对、时效 |
| 空运 | 快线/慢线 SOP、分泡、DPD 派送 |
| 卡航 | TIR 公约、中越/中欧线路、GPS 追踪 |
| 铁路 | 中欧班列、换装、SMGS 运单 |

---

## 快速开始

### 前置条件
- Windows / Mac / Linux（支持 Steamlit）
- Python 3.10+
- 一个 LLM API Key（硅基流动 / Ollama / OpenAI 都行）

### Windows（双击 run.bat）

```powershell
# 1. 克隆仓库
git clone https://github.com/ivy92888-glitch/global-trade-compliance-playbook.git
cd global-trade-compliance-playbook

# 2. 安装依赖
pip install -r chatbot/requirements.txt

# 3. 配置 API Key（硅基流动示例）
set LLM_BASE_URL=https://api.siliconflow.cn/v1
set LLM_API_KEY=sk-你的key
set LLM_MODEL=deepseek-ai/DeepSeek-V3

# 4. 启动
run.bat
```

浏览器自动打开 http://localhost:8501

### Mac / Linux

```bash
git clone https://github.com/ivy92888-glitch/global-trade-compliance-playbook.git
cd global-trade-compliance-playbook
pip install -r chatbot/requirements.txt

export LLM_BASE_URL=https://api.siliconflow.cn/v1
export LLM_API_KEY=sk-你的key
export LLM_MODEL=deepseek-ai/DeepSeek-V3

python -m streamlit run chatbot/app.py --server.headless true
```

### 用本地 Ollama（零费用）

```bash
ollama pull qwen2.5:7b   # 拉中文模型
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_API_KEY=ollama
export LLM_MODEL=qwen2.5:7b
python -m streamlit run chatbot/app.py --server.headless true
```

---

## 文件清单

```
global-trade-compliance-playbook/
├── chatbot/                      # RAG 问答助手代码
│   ├── app.py                    # Streamlit 前端界面
│   ├── rag.py                    # TF-IDF 检索 + LLM 调用
│   ├── config.py                 # 常量配置
│   └── requirements.txt          # 依赖（4 个 pip 包）
├── knowledge/                    # 知识库（markdown 格式）
│   ├── europe/                   # 欧洲清关知识（4 文件，29 KB）
│   ├── uk/                       # 英国清关知识（3 文件，16 KB）
│   ├── us/                       # 美国清关知识（6 文件，55 KB）
│   ├── canada/                   # 加拿大清关知识（4 文件，35 KB）
│   ├── sea/                      # 东南亚知识（3 文件，28 KB）
│   ├── nodes/                    # 9 大操作节点
│   │   ├── pre-shipment/         # 港前
│   │   ├── loading/              # 装柜
│   │   ├── booking/              # 订舱
│   │   ├── customs-declaration/  # 报关
│   │   ├── insurance/            # 投保
│   │   ├── clearance/            # 清关
│   │   ├── post-harbor/          # 港后
│   │   ├── claims/               # 理赔
│   │   └── finance/              # 财务
│   └── transport/                # 4 种运输方式
│       ├── ocean/                # 海运
│       ├── air/                  # 空运
│       ├── truck/                # 卡航
│       └── rail/                 # 铁路
├── run.bat                       # Windows 一键启动
├── LICENSE                       # MIT
└── README.md                     # 你现在看的这份
```

---

## 技术栈

`Python 3.10+` · `Streamlit` · `scikit-learn TF-IDF` · `requests` · `OpenAI-compatible API`

---

## 合规声明

本项目知识库已完成 clean-room 脱敏重写：
- 删除所有涉及货代行业灰色操作、规避海关的内容
- 所有前公司名、内部系统、员工姓名、客户信息已脱敏或删除
- 所有申报须基于真实属性，不提供任何规避监管的操作建议
- 如有合规问题或不当内容，欢迎提交 Issue

---

# English

## Global Trade Compliance Playbook

### Cross-border logistics compliance knowledge base + runnable RAG Q&A assistant

You're a new客服 at a cross-border logistics company. A European VAT deferred declaration pops up. An IEN code for UK customs needs to be verified. An ACE entry for a US shipment has errors. A Canadian B3 form is missing fields. Southeast Asia trucking clearance — where do you even start? Not to mention the operational nodes before harbor, loading, booking, clearance, post-harbor dispatch...

Now open a browser window, pick a direction to ask questions, and the system automatically finds relevant sections from hundreds of pages of cross-border logistics compliance manuals.

> The original knowledge base originated from prior employment work and has been rewritten from scratch through clean-room desensitization. 10+ business training references, covering 5 regions, 9 operational nodes, and 4 transport modes.

---

## What It Does

| Feature | Plain-language Summary | Concrete Example |
|---|---|---|
| Smart Retrieval | Type a business question, system pinpoints relevant paragraphs from the knowledge base | "Which channel for lamps in Europe?" → Returns 3 clearance + 2 product certification matches |
| Three-way Scope Picker | Region, operational node, or transport mode — pick one, knowledge loads on demand | Node "清关" = 173 entries; Transport "海运" = 4 entries |
| RAG Q&A | Retrieved paragraphs sent to LLM → structured, compliant answers | Each answer shows source + relevance score |
| One-click Launch | Double run.bat on Windows, browser opens automatically | 5-second startup, zero heavy downloads |

---

## Who Uses It

- **Onboarding new hires** at freight forwarders — ask directly instead of flipping through hundreds of PDF pages
- **Customs officers** looking up standard operating procedures during exception handling
- **Customer service agents** answering client queries like "What's the fastest clearance channel to the UK?"
- **Compliance auditors** checking latest regulatory updates (CBAM, Packaging Regulation, EUDR, etc.)

---

## Scope Options (Pick One)

### Regions (5)
| Region | Key Content |
|---|---|
| Europe | VAT deferral, EORI, CBAM, customs broker evaluation, port clearance / bonded warehouse |
| UK | IEN code, PVA declaration, C88 documents, DPD dispatch, 2026 new regulations |
| US | ACE/ISF filing, HTS coding, FDA, Los Angeles port |
| Canada | B3 customs declaration, CBSA, Vancouver port |
| Southeast Asia | Singapore / Bangkok / Port Klang, cross-border trucking clearance |

### Operational Nodes (9)
| Node | Content |
|---|---|
| Pre-shipment | Goods acceptance, prep and labeling |
| Loading | Container stuffing, labeling, inventory check |
| Booking | Voyage selection, booking form preparation, space allocation |
| Export Customs | Declaration documents, AMS/ISF filing |
| Insurance | Policy terms, claim coverage |
| Clearance | Broker selection, inspection response, VAT deferral |
| Post-harbor | Overseas warehouse systems, final-mile dispatch |
| Claims | Damage claims, insurance process |
| Finance | Invoice reconciliation, fee settlement |

### Transport Modes (4)
| Mode | Content |
|---|---|
| Ocean | Shipping alliances, voyage schedules, rollover handling, transit times |
| Air | Express / economy SOP, chargeable weight, DPD dispatch |
| Trucking (卡航) | TIR convention, China-Vietnam / China-EU routes, GPS tracking |
| Rail | China-Europe Railway Express, gauge-change transloading, SMGS waybill |

---

## Quick Start

### Prerequisites
- Windows / Mac / Linux (Streamlit-compatible)
- Python 3.10+
- An LLM API key (SiliconFlow / Ollama / OpenAI all work)

### Windows (Double-click run.bat)

```powershell
# 1. Clone
git clone https://github.com/ivy92888-glitch/global-trade-compliance-playbook.git
cd global-trade-compliance-playbook

# 2. Install dependencies
pip install -r chatbot/requirements.txt

# 3. Set API key (SiliconFlow example)
set LLM_BASE_URL=https://api.siliconflow.cn/v1
set LLM_API_KEY=sk-your-key
set LLM_MODEL=deepseek-ai/DeepSeek-V3

# 4. Launch
run.bat
```

Browser opens http://localhost:8501 automatically.

### Mac / Linux

```bash
git clone https://github.com/ivy92888-glitch/global-trade-compliance-playbook.git
cd global-trade-compliance-playbook
pip install -r chatbot/requirements.txt

export LLM_BASE_URL=https://api.siliconflow.cn/v1
export LLM_API_KEY=sk-your-key
export LLM_MODEL=deepseek-ai/DeepSeek-V3

python -m streamlit run chatbot/app.py --server.headless true
```

### Local Ollama (Free, Zero Cost)

```bash
ollama pull qwen2.5:7b
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_API_KEY=ollama
export LLM_MODEL=qwen2.5:7b
python -m streamlit run chatbot/app.py --server.headless true
```

---

## File Structure

```
global-trade-compliance-playbook/
├── chatbot/                      # RAG Q&A assistant code
│   ├── app.py                    # Streamlit frontend
│   ├── rag.py                    # TF-IDF retrieval + LLM caller
│   ├── config.py                 # Constants
│   └── requirements.txt          # Dependencies (4 pip packages)
├── knowledge/                    # Knowledge base (markdown)
│   ├── europe/                   # EU clearance (4 files, 29 KB)
│   ├── uk/                       # UK clearance (3 files, 16 KB)
│   ├── us/                       # US clearance (6 files, 55 KB)
│   ├── canada/                   # Canada clearance (4 files, 35 KB)
│   ├── sea/                      # SE Asia (3 files, 28 KB)
│   ├── nodes/                    # 9 operational nodes
│   └── transport/                # 4 transport modes
├── run.bat                       # Windows one-click launcher
├── LICENSE                       # MIT
└── README.md
```

---

## Tech Stack

`Python 3.10+` · `Streamlit` · `scikit-learn TF-IDF` · `requests` · `OpenAI-compatible API`

---

## Compliance Notice

This knowledge base has undergone a full clean-room desensitization rewrite:
- All grey-area and customs-evasion operations removed
- All prior-company names, internal systems, employee names, and client data desensitized or deleted
- All declarations must be based on actual cargo attributes; no regulatory circumvention guidance provided
- Issues welcome for any compliance concerns or inappropriate content
