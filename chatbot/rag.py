"""
RAG 检索增强生成模块 — 三选一模式：地区 / 节点 / 运输方式
知识库体量有限，三选一加载，不同时选
"""
import os, re, glob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests

# ========== 5 地区配置 ==========
REGIONS = {
    "europe": {"label": "欧洲", "dir": "knowledge/europe"},
    "uk": {"label": "英国", "dir": "knowledge/uk"},
    "us": {"label": "美国", "dir": "knowledge/us"},
    "canada": {"label": "加拿大", "dir": "knowledge/canada"},
    "sea": {"label": "东南亚", "dir": "knowledge/sea"},
}

# ========== 9 节点配置 ==========
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

# ========== 4 运输方式配置 ==========
TRANSPORT = {
    "ocean":  {"label": "海运", "dir": "knowledge/transport/ocean"},
    "air":    {"label": "空运", "dir": "knowledge/transport/air"},
    "truck":  {"label": "卡航", "dir": "knowledge/transport/truck"},
    "rail":   {"label": "铁路", "dir": "knowledge/transport/rail"},
}


class RAGChatbot:
    def __init__(self, base_dir=".", mode="region", region="europe", node=None, transport=None, top_k=5):
        """
        mode: "region" | "node" | "transport" — 三选一，不能同时选
        """
        self.base_dir = base_dir
        self.mode = mode
        
        if mode == "node" and node and node in NODES:
            self.node = node
            self.region = None
            self.transport = None
        elif mode == "transport" and transport and transport in TRANSPORT:
            self.node = None
            self.region = None
            self.transport = transport
        else:
            self.node = None
            self.transport = None
            self.region = region if region in REGIONS else "europe"
        
        self.top_k = top_k
        self.chunks = []
        self.sources = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._load_knowledge()

    def _scan_dir(self, kb_dir, tag_prefix=""):
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
        all_chunks, all_sources = [], []
        
        if self.mode == "node" and self.node and self.node in NODES:
            info = NODES[self.node]
            c, s = self._scan_dir(os.path.join(self.base_dir, info["dir"]), info["label"])
            all_chunks.extend(c); all_sources.extend(s)
        elif self.mode == "transport" and self.transport and self.transport in TRANSPORT:
            info = TRANSPORT[self.transport]
            c, s = self._scan_dir(os.path.join(self.base_dir, info["dir"]), info["label"])
            all_chunks.extend(c); all_sources.extend(s)
        else:
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
            return []
        k = k or self.top_k
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_idx = sims.argsort()[-k:][::-1]
        return [(self.chunks[i], self.sources[i], sims[i]) for i in top_idx if sims[i] > 0.05]

    def _get_scope_desc(self):
        if self.mode == "node" and self.node in NODES:
            return f"{NODES[self.node]['label']}环节"
        elif self.mode == "transport" and self.transport in TRANSPORT:
            return f"{TRANSPORT[self.transport]['label']}运输"
        else:
            return f"{REGIONS.get(self.region, REGIONS['europe'])['label']}方向"

    def stream_llm(self, query, retrieved=None, stream=True):
        import os, json
        if retrieved is None:
            retrieved = self.retrieve(query)
        
        context_parts = []
        for chunk, source, score in retrieved:
            context_parts.append(f"[来源: {source}, 相关度: {score:.2f}]\n{chunk}")
        context = "\n\n---\n\n".join(context_parts) if context_parts else "(知识库未检索到相关内容)"
        
        scope_desc = self._get_scope_desc()
        
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

    def switch_context(self, mode=None, region=None, node=None, transport=None):
        if mode is not None:
            self.mode = mode
            if mode == "node":
                self.node = node if node and node in NODES else None
                self.region = None
                self.transport = None
            elif mode == "transport":
                self.transport = transport if transport and transport in TRANSPORT else None
                self.node = None
                self.region = None
            else:
                self.region = region if region and region in REGIONS else "europe"
                self.node = None
                self.transport = None
        self._load_knowledge()

    def get_status(self):
        if self.mode == "node" and self.node in NODES:
            return {"scope": f"节点：{NODES[self.node]['label']}", "chunks": len(self.chunks)}
        elif self.mode == "transport" and self.transport in TRANSPORT:
            return {"scope": f"运输方式：{TRANSPORT[self.transport]['label']}", "chunks": len(self.chunks)}
        else:
            return {"scope": f"地区：{REGIONS.get(self.region, REGIONS['europe'])['label']}", "chunks": len(self.chunks)}
