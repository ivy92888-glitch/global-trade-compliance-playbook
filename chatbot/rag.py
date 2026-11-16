"""
RAG 检索增强生成模块 — 支持 5 地区 × 9 节点 交叉检索
"""
import os, re, glob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests

# ========== 5 地区配置 ==========
REGIONS = {
    "europe": {"label": "欧洲", "dir": "knowledge/europe", "hint": "欧盟/EORI/VAT递延/鹿特丹/CBAM"},
    "uk": {"label": "英国", "dir": "knowledge/uk", "hint": "英国/IEN/PVA/C88/DPD/菲利克斯托"},
    "us": {"label": "美国", "dir": "knowledge/us", "hint": "美国/ACE/ISF/HTS/FDA/洛杉矶港"},
    "canada": {"label": "加拿大", "dir": "knowledge/canada", "hint": "加拿大/B3/CBSA/HS/温哥华"},
    "sea": {"label": "东南亚", "dir": "knowledge/sea", "hint": "东南亚/新加坡/曼谷/巴生港"},
}

# ========== 9 节点配置（无"全部节点"） ==========
NODES = {
    "pre-shipment":      {"label": "港前",     "dir": "knowledge/nodes/pre-shipment"},
    "loading":           {"label": "装柜",     "dir": "knowledge/nodes/loading"},
    "booking":            {"label": "订舱",     "dir": "knowledge/nodes/booking"},
    "customs-declaration":{"label": "报关",     "dir": "knowledge/nodes/customs-declaration"},
    "insurance":          {"label": "投保",     "dir": "knowledge/nodes/insurance"},
    "clearance":          {"label": "清关",     "dir": "knowledge/nodes/clearance"},
    "post-harbor":        {"label": "港后",     "dir": "knowledge/nodes/post-harbor"},
    "claims":             {"label": "理赔",     "dir": "knowledge/nodes/claims"},
    "finance":            {"label": "财务",     "dir": "knowledge/nodes/finance"},
}


class RAGChatbot:
    def __init__(self, base_dir=".", region="europe", node=None, top_k=5):
        self.base_dir = base_dir
        # 过滤掉已删除的 "all" 等无效节点
        if node and node in NODES:
            self.node = node
        else:
            self.node = None
        self.region = region
        self.top_k = top_k
        self.chunks = []
        self.sources = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._load_knowledge()

    def _scan_dir(self, kb_dir, tag_prefix=""):
        """扫描一个目录，返回 (chunks, sources)"""
        chunks, sources = [], []
        if not os.path.exists(kb_dir):
            return chunks, sources
        
        files = sorted(glob.glob(os.path.join(kb_dir, "*.md")))
        for fpath in files:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            fname = os.path.basename(fpath)
            label = f"{tag_prefix}/{fname}" if tag_prefix else fname
            
            sections = re.split(r'\n(?=## )', content)
            for sec in sections:
                sec = sec.strip()
                if len(sec) > 30:
                    chunks.append(sec)
                    sources.append(label)
        return chunks, sources

    def _load_knowledge(self):
        """二选一：选了 node → 只加载节点知识库；否则加载地区知识库"""
        all_chunks, all_sources = [], []
        
        if self.node and self.node in NODES:
            # 选了节点 → 只加载节点
            node_info = NODES[self.node]
            if node_info["dir"]:
                c, s = self._scan_dir(os.path.join(self.base_dir, node_info["dir"]), node_info["label"])
                all_chunks.extend(c); all_sources.extend(s)
        else:
            # 选地区
            region_info = REGIONS.get(self.region, REGIONS["europe"])
            c, s = self._scan_dir(os.path.join(self.base_dir, region_info["dir"]), region_info["label"])
            all_chunks.extend(c); all_sources.extend(s)
        
        self.chunks = all_chunks
        self.sources = all_sources
        
        if self.chunks:
            self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), min_df=1)
            self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
        else:
            self.vectorizer = None
            self.tfidf_matrix = None

    def retrieve(self, query, k=None):
        if not self.chunks or self.vectorizer is None:
            return [], []
        k = k or self.top_k
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_idx = sims.argsort()[-k:][::-1]
        return [(self.chunks[i], self.sources[i], sims[i]) for i in top_idx if sims[i] > 0.05]

    def stream_llm(self, query, retrieved=None, stream=True):
        import os, json
        if retrieved is None:
            retrieved = self.retrieve(query)
        
        context_parts = []
        for i, (chunk, source, score) in enumerate(retrieved):
            context_parts.append(f"[来源: {source}, 相关度: {score:.2f}]\n{chunk}")
        context = "\n\n---\n\n".join(context_parts) if context_parts else "(知识库未检索到相关内容)"
        
        # system prompt：节点时用节点语境，地区时用地区语境
        if self.node and self.node in NODES:
            scope_desc = f"{NODES[self.node]['label']}环节"
        else:
            scope_desc = f"{REGIONS.get(self.region, REGIONS['europe'])['label']}方向"
        
        system_prompt = f"""你是一位跨境物流专家，专注于{scope_desc}的业务知识。
请基于以下知识库内容回答用户的跨境物流问题。

要求：
1. 优先使用知识库中的信息，确保准确
2. 如果知识库没有直接答案，基于通用跨境物流合规常识回答，并标注"以下为通用建议，具体请以当地最新政策为准"
3. 给出的建议必须合规合法，不提供任何规避监管、少交税的操作建议
4. 关键合规点（如申报真实、编码准确、认证齐全、追溯期长等）务必强调
5. 回答结构清晰，分点列出
6. 涉及特定地区的问题，先说明该地区的特殊性，再给出通用建议"""

        user_prompt = f"""【知识库内容】

{context}

【用户问题】
{query}

请根据以上知识库内容，针对用户问题给出合规、准确、结构清晰的回答。"""

        base_url = os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        api_key = os.environ.get("LLM_API_KEY", "")
        model = os.environ.get("LLM_MODEL", "deepseek-ai/DeepSeek-V3")

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": stream,
            "max_tokens": 1800,
            "temperature": 0.3,
        }

        resp = requests.post(url, headers=headers, json=body, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"LLM 调用失败 ({resp.status_code}): {resp.text[:500]}")
        resp.encoding = "utf-8"

        if stream:
            def gen():
                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        delta = obj.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue
            return gen()
        else:
            return json.loads(resp.text)["choices"][0]["message"]["content"]

    def switch_context(self, region=None, node=None):
        """切换时自动二选一：设了 node 就优先用 node"""
        if node is not None:
            self.node = node
        elif region is not None:
            self.region = region
            self.node = None  # 选地区就清空节点
        self._load_knowledge()

    def get_status(self):
        if self.node and self.node in NODES:
            return {"scope": f"节点：{NODES[self.node]['label']}", "chunks": len(self.chunks)}
        else:
            return {"scope": f"地区：{REGIONS.get(self.region, REGIONS['europe'])['label']}", "chunks": len(self.chunks)}
