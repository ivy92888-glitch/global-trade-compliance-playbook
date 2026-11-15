"""RAG 管道：加载知识 → TF-IDF 检索 → LLM 生成

轻量级实现，不依赖任何本地 ML 模型。
检索用 scikit-learn TF-IDF 余弦相似度，对领域强词汇的知识库（如清关合规）效果很好。
"""
import os, re, glob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import config


# ==================== 加载与切分 ====================

def load_knowledge(knowledge_dir=None):
    """加载 knowledge/ 下所有 .md 文件"""
    if knowledge_dir is None:
        knowledge_dir = config.KNOWLEDGE_DIR
    
    chunks = []
    for md_path in sorted(glob.glob(os.path.join(knowledge_dir, "*.md"))):
        fname = os.path.basename(md_path)
        with open(md_path, encoding="utf-8") as f:
            content = f.read()
        
        # 按 H2 / H3 标题切分，每个 section 是一个 chunk
        sections = re.split(r'\n(?=##)', content)
        for sec in sections:
            sec = sec.strip()
            if len(sec) < 30:
                continue  # 跳过太短的
            chunks.append({
                "text": sec,
                "source": fname,
                "title": _extract_section_title(sec),
            })
    
    return chunks


def _extract_section_title(chunk):
    """从 chunk 开头提取 section 标题"""
    first_line = chunk.split("\n")[0].strip()
    # 去掉 markdown heading 标记
    title = re.sub(r'^#+\s*', '', first_line)
    return title[:60] if title else "(无标题)"


# ==================== 检索 ====================

class Retriever:
    """TF-IDF 向量检索器"""
    
    def __init__(self, chunks):
        self.chunks = chunks
        # 对中文 + 英文做分词：unigram + bigram，覆盖中英混合场景
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",      # char n-gram，不用空格分词
            ngram_range=(1, 3),      # 1-3 字组合，覆盖 HS 编码、术语等
            max_features=8000,
            sublinear_tf=True,       # 次线性 TF，避免长文分数爆炸
        )
        # 预先计算所有 chunk 的 TF-IDF 矩阵
        texts = [c["text"] for c in chunks]
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
    
    def search(self, query, top_k=None):
        """检索 top-K 个相关 chunk"""
        if top_k is None:
            top_k = config.TOP_K
        
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # 取 top-K
        top_idx = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_idx:
            if scores[idx] > 0.01:  # 过滤完全不相关的
                results.append({
                    "chunk": self.chunks[idx],
                    "score": float(scores[idx]),
                })
        
        return results


# ==================== LLM 调用 ====================

def build_context(retrieved):
    """把检索结果拼成 LLM 可读的 context"""
    if not retrieved:
        return "（暂无相关知识，可能这个问题不在本知识库覆盖范围内）"
    
    parts = []
    for i, r in enumerate(retrieved, 1):
        src = r["chunk"]["source"]
        title = r["chunk"]["title"]
        text = r["chunk"]["text"]
        # 截断过长的 chunk
        if len(text) > 800:
            text = text[:800] + "…（截断）"
        parts.append(f"【参考 {i}｜{src} → {title}】\n{text}")
    
    return "\n\n".join(parts)


def call_llm(messages, base_url=None, api_key=None, model=None):
    """OpenAI-compatible API 调用（也兼容 Ollama）"""
    import requests
    
    base_url = (base_url or config.LLM_BASE_URL).rstrip("/")
    api_key = api_key or config.LLM_API_KEY
    model = model or config.LLM_MODEL
    
    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    
    resp = requests.post(url, headers=headers, json=body, stream=True, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"LLM 调用失败 ({resp.status_code}): {resp.text[:500]}")
    
    # 流式解析 SSE
    full_text = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        line = line[6:]
        if line == "[DONE]":
            break
        try:
            import json
            data = json.loads(line)
            delta = data.get("choices", [{}])[0].get("delta", {})
            token = delta.get("content", "")
            if token:
                full_text += token
        except Exception:
            continue
    
    return full_text


# ==================== 入口函数 ====================

class CustomsChatbot:
    """整合 RAG 管道：知识加载 → 检索 → LLM 生成"""
    
    def __init__(self, knowledge_dir=None):
        print("📚 加载知识库...")
        self.chunks = load_knowledge(knowledge_dir)
        print(f"   共 {len(self.chunks)} 个知识 chunk")
        print("🔧 构建 TF-IDF 检索器...")
        self.retriever = Retriever(self.chunks)
        print("✅ 就绪")
    
    def answer(self, query, history=None, top_k=None):
        """回答一个问题"""
        # 1. 检索
        retrieved = self.retriever.search(query, top_k=top_k)
        
        # 2. 拼消息
        messages = [
            {"role": "system", "content": config.SYSTEM_PROMPT},
        ]
        
        # 历史（最多保留 6 轮）
        if history:
            for msg in history[-12:]:
                messages.append(msg)
        
        # 把检索结果作为 system context 注入
        context = build_context(retrieved)
        messages.append({
            "role": "system",
            "content": f"以下是针对用户问题检索到的参考材料，**严格基于这些材料回答**，不要引入外部知识：\n\n{context}",
        })
        
        # 用户问题
        messages.append({"role": "user", "content": query})
        
        # 3. 调 LLM
        answer = call_llm(messages)
        
        return answer, retrieved


if __name__ == "__main__":
    # 命令行测试
    bot = CustomsChatbot()
    while True:
        q = input("\n你: ").strip()
        if q in ("quit", "exit", ""):
            break
        ans, refs = bot.answer(q)
        print(f"\n助手: {ans}\n")
        for r in refs:
            print(f"  📚 [{r['score']:.3f}] {r['chunk']['source']} → {r['chunk']['title']}")
