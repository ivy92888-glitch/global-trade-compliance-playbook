"""
RAG 检索增强生成模块 — 支持多地区知识库
"""
import os, re, glob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests

# 地区配置
REGIONS = {
    "europe": {"label": "🇪🇺 欧洲清关", "dir": "knowledge/europe", "prompt_suffix": "（欧洲清关语境）"},
    "uk": {"label": "🇬🇧 英国清关", "dir": "knowledge/uk", "prompt_suffix": "（英国清关语境）"},
    "us": {"label": "🇺🇸 美国清关", "dir": "knowledge/us", "prompt_suffix": "（美国清关语境）"},
    "canada": {"label": "🇨🇦 加拿大清关", "dir": "knowledge/canada", "prompt_suffix": "（加拿大清关语境）"},
    "sea": {"label": "🌏 东南亚清关", "dir": "knowledge/sea", "prompt_suffix": "（东南亚清关语境）"},
}

# 地区对应的语言/术语偏好
REGION_HINTS = {
    "europe": "欧盟 (EU) / MRN / EORI / VAT 递延 / 鹿特丹 / 安特卫普 / CBAM",
    "uk": "英国 (UK) / IEN / PVA / C88 / DPD / 菲利克斯托 / 南安普顿",
    "us": "美国 (US) / ACE / ISF / HTS / FDA / 洛杉矶港 / 纽约港",
    "canada": "加拿大 (CA) / B3 / CBSA / HS / 温哥华 / 多伦多",
    "sea": "东南亚 (SEA) / 新加坡 / 曼谷 / 雅加达 / 巴生港",
}


class RAGChatbot:
    def __init__(self, base_dir=".", region="europe", top_k=5):
        self.base_dir = base_dir
        self.region = region
        self.top_k = top_k
        self.chunks = []
        self.sources = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._load_knowledge()

    def _load_knowledge(self):
        """加载指定地区的所有知识文件"""
        region_info = REGIONS.get(self.region, REGIONS["europe"])
        kb_dir = os.path.join(self.base_dir, region_info["dir"])
        
        if not os.path.exists(kb_dir):
            self.chunks = ["知识库尚未就绪，敬请期待。"]
            self.vectorizer = TfidfVectorizer()
            self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
            return

        files = sorted(glob.glob(os.path.join(kb_dir, "*.md")))
        self.chunks = []
        self.sources = []

        for fpath in files:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            fname = os.path.basename(fpath)
            
            # 按 ## 标题拆 chunk
            sections = re.split(r'\n(?=## )', content)
            for sec in sections:
                sec = sec.strip()
                if len(sec) > 30:  # 跳过太短的
                    self.chunks.append(sec)
                    self.sources.append(f"{fname}")

        # 构建 TF-IDF
        if self.chunks:
            self.vectorizer = TfidfVectorizer(
                analyzer='char', ngram_range=(2, 4), min_df=1
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)

    def retrieve(self, query, k=None):
        """检索 top-k 相关 chunk"""
        if not self.chunks or self.vectorizer is None:
            return [], []
        
        k = k or self.top_k
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_idx = sims.argsort()[-k:][::-1]
        
        results = [(self.chunks[i], self.sources[i], sims[i]) for i in top_idx if sims[i] > 0.05]
        return results

    def stream_llm(self, query, retrieved=None, stream=True):
        """调用 LLM（流式）"""
        import os
        
        # 1. 检索
        if retrieved is None:
            retrieved = self.retrieve(query)
        
        # 2. 构建 prompt
        region_info = REGIONS.get(self.region, REGIONS["europe"])
        region_hint = REGION_HINTS.get(self.region, "")
        
        context_parts = []
        for i, (chunk, source, score) in enumerate(retrieved):
            context_parts.append(f"[来源: {source}, 相关度: {score:.2f}]\n{chunk}")
        
        context = "\n\n---\n\n".join(context_parts) if context_parts else "(知识库未检索到相关内容，以下为通用合规建议)"
        
        system_prompt = f"""你是一位跨境清关合规专家，{region_info['label'].replace('🇪🇺 ','').replace('🇬🇧 ','').replace('🇺🇸 ','').replace('🇨🇦 ','').replace('🌏 ','')}方向。
请基于以下知识库内容回答用户的清关合规问题。

要求：
1. 优先使用知识库中的信息，确保准确
2. 如果知识库没有直接答案，基于通用清关合规常识回答，并明确标注"以下为通用建议，具体请以当地海关最新政策为准"
3. 给出的建议必须合规合法，不提供任何规避海关、少交税的操作建议
4. 关键合规点（如申报真实、编码准确、认证齐全、追溯期长等）务必强调
5. 回答结构清晰，分点列出

术语参考：{region_hint}"""

        user_prompt = f"""【知识库内容】

{context}

【用户问题】
{query}

请根据以上知识库内容，针对用户问题给出合规、准确、结构清晰的回答。"""

        # 3. 调用 LLM
        base_url = os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        api_key = os.environ.get("LLM_API_KEY", "")
        model = os.environ.get("LLM_MODEL", "deepseek-ai/DeepSeek-V3")

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": stream,
            "max_tokens": 1500,
            "temperature": 0.3,
        }

        resp = requests.post(url, headers=headers, json=body, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"LLM 调用失败 ({resp.status_code}): {resp.text[:500]}")

        # 强制 UTF-8 解码（Windows GBK 兼容）
        resp.encoding = "utf-8"

        if stream:
            def gen():
                buffer = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            obj = json.loads(data)
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
            return gen()
        else:
            import json
            return json.loads(resp.text)["choices"][0]["message"]["content"]

    def switch_region(self, region):
        """切换地区"""
        self.region = region
        self._load_knowledge()
