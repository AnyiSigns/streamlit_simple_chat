# ==================== 导入模块 ====================
from os import remove
import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="诶喂",
    page_icon="🤡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)


# ==================== 函数定义区 ====================

# 1. 加载指定会话
def load_sessions(session_name):
    try:
        if os.path.exists("./sessions"):
            with open(f"./sessions/{session_name}.json", "r", encoding="utf-8") as f:
                load_name = json.load(f)
                st.session_state.messages = load_name["message"]
                st.session_state.system_name = load_name["system_name"]
                st.session_state.nature = load_name["nature"]
                st.session_state.current_session = session_name
    except Exception:
        st.error("加载失败")


# 2. 获取所有历史会话列表（倒序）
def load_session():
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for file_name in file_list:
            if file_name.endswith(".json"):
                session_list.append(file_name[:-5:])
    return session_list[::-1]


# 3. 删除会话
def delects_session(seesion):
    if os.path.exists(f"./sessions/{seesion}.json"):
        remove(f"./sessions/{seesion}.json")
        if st.session_state.current_session == seesion:
            st.session_state.messages = []
            st.session_state.current_session = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        st.rerun()


# 4. 保存当前会话到文件
def converse():
    if st.session_state.current_session:
        session_data = {
            "system_name": st.session_state.system_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "message": st.session_state.messages
        }
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)


# ==================== 初始化配置 ====================

# AI客户端
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY') or st.secrets.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 系统提示词模板
system_set = ("""
你叫%s
是一名%s的ai伴侣
""")

# 初始化 session_state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "system_name" not in st.session_state:
    st.session_state.system_name = "干点啥好呢"
if "nature" not in st.session_state:
    st.session_state.nature = "懵懂女性大学生，干啥啥不会，一问三不知"
if "current_session" not in st.session_state:
    st.session_state.current_session = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# ==================== 主界面渲染 ====================

# 标题
st.title("叫啥好呢")
st.divider()
# 显示历史消息
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# ==================== 侧边栏 ====================
with st.sidebar:
    # 新建会话按钮
    if st.button("新建会话", width="stretch"):
        if st.session_state.messages:
            converse()
            st.session_state.messages = []
            st.session_state.current_session = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.rerun()
            converse()

    # 历史会话列表
    st.subheader("历史会话🛐")
    session_lists = load_session()
    if session_lists:
        for session in session_lists:
            col1, col2 = st.columns([5, 2])
            with col1:
                if st.button(session, width="stretch", key=f"load_{session}",
                             type="primary" if session == st.session_state.current_session else "secondary"):
                    load_sessions(session)
                    st.rerun()
            with col2:
                if st.button("🚮", width="stretch", key=f"delete_{session}"):
                    delects_session(session)
    else:
        st.caption("OMG！！！")
    #分割线
    st.divider()
    # 虚拟人格设置
    st.subheader("虚拟人格设置")
    system_name = st.text_input("昵称", placeholder="请输入昵称", value=st.session_state.system_name)
    if system_name:
        st.session_state.system_name = system_name
    nature = st.text_area("性格", placeholder="请输入性格", value=st.session_state.nature)
    if nature:
        st.session_state.nature = nature

# ==================== 聊天交互区 ====================

# 输入框
prompt = st.chat_input("聊天")
if prompt:
    # 显示用户消息
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    print("------->用户:", prompt)

    # 调用AI大模型
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": system_set % (st.session_state.system_name, st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )

    # 流式输出
    response_message = st.empty()
    response_content = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            print("<-----------大模型", chunk.choices[0].delta.content)
            content = chunk.choices[0].delta.content
            response_content += content
            response_message.chat_message("assistant").write(response_content)

    st.session_state.messages.append({"role": "assistant", "content": response_content})

# 保存会话
if st.session_state.messages:
    converse()
