# 📦 Global Trade Compliance Playbook

跨境物流合规知识库 + 可运行的 RAG 问答助手。5 个地区知识体系，一键切换。

**仓库地址：** https://github.com/ivy92888-glitch/global-trade-compliance-playbook

---

## ✨ 功能截图

| 侧边栏（地区 + 节点双维度） | 主界面 |
|---|---|
| <img src="docs/assets/chatbot-new-sidebar.png" width="280"/> | <img src="docs/assets/chatbot-new-home.png" width="420"/> |

---

## 🗂️ 双维度知识库（地区 × 节点）

**问问题更精准：选「欧洲 + 清关」= 欧洲清关；选「港后」+ 地区可选 = 全地区港后通用知识。**

### 📍 9 个运营节点

| 节点 | 英文名 | 核心内容 |
|------|--------|----------|
| 港前 | pre-shipment | 揽收、地址校验、入仓预约 |
| 装柜 | loading | 配载、柜型选择、装柜规范 |
| 订舱 | booking | 船期、舱位确认、提单信息 |
| 报关 | customs-declaration | 报关单制作、申报要素 |
| 投保 | insurance | 保险方案、理赔流程 |
| 清关 | clearance | 查验应对、VAT 递延、HS 编码、合规红线 |
| 港后 | post-harbor | 海外仓入仓、尾端派送、系统操作 |
| 理赔 | claims | 货损、延误、丢件的索赔流程 |
| 财务 | finance | 报价、对账、开票、成本核算 |

### 🌍 5 个地区

| 地区 | 知识库 | 核心内容 |
|------|--------|----------|
| 欧洲 | 4 文件 / 29 KB | 鹿特丹港清、VAT 递延、CBAM 碳关税、EPR 包装法、EUDR 零毁林 |
| 英国 | 3 文件 / 16 KB | IEN 码、PVA 递延、C88 税金单、DPD 派送、菲利克斯托港 |
| 美国 | 6 文件 / 55 KB | ACE 清关、ISF 10+2、HTS 编码、FDA 注册、洛杉矶/纽约港 |
| 加拿大 | 4 文件 / 35 KB | B3 清关单、CBSA 查验、HS 编码、温哥华/多伦多港 |
| 东南亚 | 3 文件 / 28 KB | 新加坡清关、泰国/印尼/马来西亚、巴生港、汽运专线 |

**总计 102 KB 结构化知识，可直接用于 RAG 检索。**

---

## 🚀 快速开始（5 分钟跑起问答助手）

### 1. 安装依赖
```bash
pip install streamlit scikit-learn requests numpy
```

### 2. 配置 LLM（三选一）

**方案 A：硅基流动 API（推荐，国内原生）**
```powershell
$env:LLM_BASE_URL="https://api.siliconflow.cn/v1"
$env:LLM_API_KEY="sk-你的Key"
$env:LLM_MODEL="deepseek-ai/DeepSeek-V3"
```

**方案 B：本地 Ollama**
```powershell
$env:LLM_BASE_URL="http://localhost:11434/v1"
$env:LLM_API_KEY="ollama"
$env:LLM_MODEL="qwen2.5:7b"
```

**方案 C：OpenAI / DeepSeek / 通义**
改 `LLM_BASE_URL` + `LLM_API_KEY` + `LLM_MODEL` 即可，OpenAI-compatible 的端点全都能用。

### 3. 启动
```powershell
python -m streamlit run chatbot/app.py --server.headless true
```

浏览器自动打开 `http://localhost:8501`，侧边栏选地区，开始提问。

---

## 📁 目录结构

```
global-trade-compliance-playbook/
├── chatbot/                     # RAG 问答助手代码
│   ├── app.py                  # Streamlit 前端（地区选择器 + 对话界面）
│   ├── rag.py                  # TF-IDF 检索 + LLM 调用（5 地区支持）
│   ├── config.py               # 系统提示词 + 可配置项
│   └── requirements.txt        # 4 个 pip 包（零 ML 模型下载）
├── knowledge/                  # 分地区知识库
│   ├── europe/ (4 文件, 29 KB) # 欧洲清关合规
│   ├── uk/    (3 文件, 16 KB)  # 英国清关合规
│   ├── us/    (6 文件, 55 KB)  # 美国清关合规
│   ├── canada/(4 文件, 35 KB)  # 加拿大清关合规
│   └── sea/   (3 文件, 28 KB)  # 东南亚跨境汽运
├── docs/assets/                # Demo 截图
├── LICENSE                     # MIT
└── README.md
```

---

## 🔧 技术栈

| 组件 | 选型 | 为什么 |
|------|------|--------|
| 检索 | sklearn TF-IDF char n-gram | 零 ML 模型下载，秒级响应，领域词汇检索精准 |
| 向量存储 | 不需要 | 每次启动内存构建矩阵（< 1 秒） |
| LLM 调用 | OpenAI-compatible API（requests） | Ollama / 硅基流动 / OpenAI / DeepSeek 全部兼容 |
| 前端 | Streamlit | 30 行代码，聊天界面 + 流式输出 + 来源可追溯 |
| 依赖 | streamlit + sklearn + requests + numpy | **4 个 pip 包，零下载** |

---

## 💡 问答示例

**切换到「欧洲」：**
> "CBAM 碳关税怎么算？"
> → 召回 knowledge/europe/04_europe.md，给出碳密集产品清单、计算公式、2026 政策时间表

**切换到「英国」：**
> "IEN 码是什么？哪些渠道提供？"
> → 召回 knowledge/uk/01_uk.md，对比三种模式的 IEN 码支持情况

**切换到「美国」：**
> "ISF 10+2 是什么？什么时候要申报？"
> → 召回 knowledge/us/02_us.md，给出 10 项数据要求 + 申报时限

**每个回答底部显示 📚 参考来源（文件名 + 相关度分数），可追溯。**

---

## 🛡️ 合规声明

- 本知识库基于公开行业常识 + 脱敏后的内部培训资料整理，**不引用任何前雇主的专有代码或业务文档**
- 知识库已做开源前合规审查 + 隐私脱敏：删除灰色清关操作、内部系统名、公司/员工姓名、报价、VAT/EORI 号
- 系统 prompt 明确约束：**不提供任何规避监管、少交税的操作建议**
- 政策类内容（CBAM/EPR/IEN/ISF）时效性强，使用前请核对官方最新规定
- MIT License 覆盖作者本人贡献，不构成对任何第三方权利的处分

---

## 📖 知识来源

| 地区 | 源文档 | 处理方式 |
|------|--------|----------|
| 欧洲 | 6 份内部培训资料（已开源版） | 合规审查 → 隐私脱敏 → 跨文件去重 → 重组为 4 文件 |
| 英国 | 英国渠道运营文档 | 删灰色清关方案 + 内部薪酬数据 → 脱敏 → 重组为 3 文件 |
| 美国 | 美国清关合规手册（已开源版） | 合规审查 → 隐私脱敏 → 重组为 6 文件 |
| 加拿大 | 加拿大清关合规手册（已开源版） | 合规审查 → 隐私脱敏 → 重组为 4 文件 |
| 东南亚 | 东南亚跨境汽运手册（已开源版） | 合规审查 → 隐私脱敏 → 重组为 3 文件 |

---

## 🗺️ 后续计划

- [x] 欧洲知识库
- [x] 英国知识库
- [x] 美国知识库
- [x] 加拿大知识库
- [x] 东南亚知识库
- [ ] 每季度更新政策法规
- [ ] 增加更多国家（澳洲、墨西哥、拉美）

---

**作者：** ivy92888-glitch | **License：** MIT
