"""
Global Trade Compliance Chatbot — 多地区清关合规智能客服

支持地区：欧洲 / 英国 / 美国 / 加拿大 / 东南亚
"""
import os, sys, time
import streamlit as st

# 确保能导入 rag
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag import RAGChatbot, REGIONS

# ========== 页面配置 ==========
st.set_page_config(
    page_title="Global Trade Compliance Chatbot",
    page_icon="📦",
    layout="wide",
)

# ========== 状态初始化 ==========
def get_base_dir():
    """知识库根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "chatbot" not in st.session_state:
    st.session_state.chatbot = RAGChatbot(base_dir=get_base_dir(), region="europe")
if "messages" not in st.session_state:
    st.session_state.messages = []

# ========== 侧边栏 ==========
with st.sidebar:
    st.title("📦 Global Trade Compliance Chatbot")
    st.caption("跨境清关合规智能客服")
    
    # 地区选择
    st.subheader("🗺️ 选择清关地区")
    region_labels = [REGIONS[r]["label"] for r in REGIONS]
    region_keys = list(REGIONS.keys())
    current_label = REGIONS.get(st.session_state.chatbot.region, REGIONS["europe"])["label"]
    
    selected_idx = region_labels.index(current_label) if current_label in region_labels else 0
    selected_label = st.radio("清关地区", region_labels, index=selected_idx)
    selected_region = region_keys[region_labels.index(selected_label)]
    
    if selected_region != st.session_state.chatbot.region:
        st.session_state.chatbot.switch_region(selected_region)
        st.session_state.messages = []  # 切地区清空对话
        st.success(f"已切换到 {selected_label}，知识库 {len(st.session_state.chatbot.chunks)} 条")
        st.rerun()
    
    st.divider()
    
    # API 配置
    st.subheader("⚙️ LLM 配置")
    with st.expander("API 设置", expanded=False):
        base_url = st.text_input("API Base URL", 
            value=os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1"))
        api_key = st.text_input("API Key", 
            value=os.environ.get("LLM_API_KEY", ""), type="password")
        model = st.text_input("Model", 
            value=os.environ.get("LLM_MODEL", "deepseek-ai/DeepSeek-V3"))
        
        os.environ["LLM_BASE_URL"] = base_url
        os.environ["LLM_API_KEY"] = api_key
        os.environ["LLM_MODEL"] = model
    
    # 检索参数
    st.subheader("🔍 检索参数")
    top_k = st.slider("Top-K 知识片段", min_value=2, max_value=10, 
                       value=st.session_state.chatbot.top_k)
    st.session_state.chatbot.top_k = top_k
    
    st.divider()
    st.caption("🧠 TF-IDF char n-gram 检索 + 自定义 prompt，RAG 架构")
    st.caption("📋 仅基于公开合规常识，不提供避税建议")

# ========== 主区域 ==========
region_info = REGIONS.get(st.session_state.chatbot.region, REGIONS["europe"])
region_label = region_info["label"]

st.title(f"📦 {region_label} 清关合规智能客服")
st.caption(f"知识库 {len(st.session_state.chatbot.chunks)} 条 · 基于公开合规常识 · 不提供规避建议")

# 欢迎语 + 示例
if not st.session_state.messages:
    st.info("👋 你好！我是清关合规专家。问我 HS 编码、查验应对、政策新规、VAT 递延……")
    
    with st.expander("💡 试试这些问题", expanded=True):
        example_q = {
            "europe": ["HS 编码怎么查？", "CBAM 碳关税怎么算？", "荷兰和比利时清关有什么区别？", "灯具需要什么认证？"],
            "uk": ["英国三种清关模式什么区别？", "IEN 码是啥？", "查验费用多少？", "2026 年新规有哪些？"],
            "us": ["美国 ACE 清关流程", "ISF 10+2 是什么？", "FDA 怎么注册？"],
            "canada": ["加拿大 B3 清关单怎么填？", "CBSA 查验流程"],
            "sea": ["新加坡清关时效", "东南亚反倾销"],
        }
        for q in example_q.get(st.session_state.chatbot.region, example_q["europe"]):
            if st.button(f"  {q}", key=f"ex_{q[:10]}"):
                st.session_state.messages.append({"role": "user", "content": q})
                st.rerun()

# ========== 对话历史 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sources" in msg:
            with st.expander("📚 参考来源"):
                for src in msg["sources"]:
                    st.write(f"- {src}")

# ========== 输入框 ==========
if prompt := st.chat_input("问我清关合规问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # 检索
    with st.spinner("🔍 检索知识库..."):
        retrieved = st.session_state.chatbot.retrieve(prompt)
    
    # 生成回答
    with st.chat_message("assistant"):
        try:
            stream = st.session_state.chatbot.stream_llm(prompt, retrieved=retrieved)
            
            # 流式显示
            full_response = ""
            placeholder = st.empty()
            for chunk in stream:
                full_response += chunk
                placeholder.markdown(full_response)
            
            # 显示来源
            sources = list(set(f"📄 {src} (相关度 {score:.2f})" 
                             for _, src, score in retrieved if score > 0.08))
            if sources:
                with st.expander("📚 参考来源"):
                    for s in sources:
                        st.write(s)
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response,
                "sources": sources
            })
            
        except Exception as e:
            st.error(f"❌ 出错了：{str(e)}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"抱歉，调用 LLM 时出错：{str(e)}"
            })
