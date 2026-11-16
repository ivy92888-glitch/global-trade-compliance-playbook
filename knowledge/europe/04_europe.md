## 启动与提问

在项目目录执行 `python -m streamlit run app.py --server.headless true`，浏览器打开 `http://localhost:8501` 即可提问。每个回答下方会显示参考来源，标明答案来自哪份知识文件的哪个章节——这正是 RAG 的价值：可追溯、可核查。
表 15-2　常见问题排查
问题 | 原因 | 处理
浏览器打不开 localhost:8501 | 服务进程已退出 | 重新执行启动命令
一直 Loading 无回答 | 模型账户余额不足或网络异常 | 检查账户与网络
回答不准确 | 知识库未更新或切片不合理 | 补充知识文件、调整切片策略
不想每次输命令 | 把环境变量写入 .env | 之后只运行一条启动命令
附录 A　6 份源资料去向对照
表 A-1　源资料处理对照
源资料 | 处理方式 | 内容落点 / 删除原因
智能客服操作手册.docx | 改写保留 | 第 15 章通用 RAG 部署指南；删除本机路径、项目名、API Key 截图与充值信息
清关智能客服.docx | 脱敏保留 | 第 1–2、4–5、9–11 章；删除内部渠道代号、报价与低申报比例细节
欧洲.docx | 脱敏保留 | 第 1、4、6 章；删除团队与对接人、内部报价；保留港口、运输流程、查验方式
基础知识与合规指南.docx | 脱敏保留 | 第 1–3、7–11 章；删除内部运营数据、申报比例表、渠道收费与内部截图
递延与包税清关资料.docx | 部分删除 + 脱敏保留 | 保留第 12–13 章合规框架；删除控税操作、低申报、规避编码、改税号/P 图、客户与税号信息、单证样例
风险防控与问题处理.docx | 脱敏保留 | 第 9–11、14 章；删除代理代号与公司名、内部数据、装柜躲查验与规则信息差
附录 B　术语与缩写总表
表 B-1　术语与缩写总表
缩写 | 全称 / 含义 | 中文说明
MRN | Movement Reference Number | 货物在欧盟海关的唯一编号
EORI | Economic Operators Registration and Identification | 欧盟经济经营者注册识别号
VAT | Value Added Tax | 增值税；进口增值税可递延
Duty / A00 | Import Duty | 进口关税，进口时缴纳
PVA | Postponed VAT Accounting | 进口增值税递延申报
T1 / T2 | Transit / Free circulation | 未完税过境 / 已完税自由流通
POA | Power of Attorney | 授权委托书
HS Code | Harmonized System Code | 海关商品编码
BTI | Binding Tariff Information | 约束性税率信息
TARIC | Tarif Intégré de la Communauté | 欧盟综合关税数据库
CE | Conformité Européenne | 欧盟符合性认证标志
EPR | Extended Producer Responsibility | 生产者责任延伸
EUDR | EU Deforestation Regulation | 欧盟零毁林法案
CBAM | Carbon Border Adjustment Mechanism | 碳边境调节机制
MTC | Material Test Certificate | 材质证明证书
POD | Proof of Delivery | 签收回执
ICS2 | Import Control System 2 | 欧盟进口管制系统
FBA | Fulfillment by Amazon | 亚马逊仓配服务
附录 C　官方查询资源（公开）
表 C-1　官方公开查询资源
用途 | 官方渠道
欧盟税率与监管条件 | 欧盟海关 TARIC 数据库
欧盟归类裁定 | 欧盟海关 EBTI / BTI 平台
英国税率与反倾销税 | 英国海关税则（trade-tariff.service.gov.uk）
英国反倾销公告 | 英国政府网站（gov.uk，搜索 China dumping）
中国出口商品编码 | 中国海关总署
包装法 / EPR | 各成员国官方注册平台
EUDR 备案 | 欧盟 EUDR 注册系统
CBAM 政策 | 欧盟委员会气候行动总司
注：本表只列官方渠道名称，具体网址请以各国政府官网最新公布为准。
附录 D　开源发布前自查清单
☐ 全文无前雇主 / 客户公司名称、联系人姓名、代理内部代号。
☐ 全文无内部系统网址、账号、API Key、本地路径、项目仓库名。
☐ 全文无柜号、VAT / EORI / 税号、发票号、报价与金额数据。
☐ 全文无身份证、VAT 证书、申报回执、处罚单、聊天记录等单证截图。
☐ 全文无压低申报、调数量控税、换链接、规避反倾销编码等违规操作指引。
☐ 所有政策类内容（CBAM / EPR / EUDR / MRN）已标注「以官方最新规定为准」。
☐ 13 张自绘图表仅含公开知识，无数据泄露。
☐ 已完成单位内部信息安全与开源合规审批。