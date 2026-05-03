import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import datetime
import pandas as pd

# ========================== 强制屏蔽登录弹窗 ==========================
components.html("""
<script>
window.addEventListener('load', function() {
  setTimeout(() => {
    const overlay = document.querySelector('.st-eb');
    const modal = document.querySelector('.st-ci');
    if (overlay) overlay.remove();
    if (modal) modal.remove();
    document.body.style.overflow = 'auto';
  }, 100);
});
</script>
""", height=0, width=0)

# ========================== 手机弹窗提醒函数 ==========================
def show_phone_alert(message):
    components.html(f"""
    <script>
        alert("⚠️ 情绪风险提醒：\\n{message}");
    </script>
    """, height=0, width=0)

# ========================== 读取API Key（带错误提示） ==========================
try:
    ARK_API_KEY = st.secrets["ARK_API_KEY"]
except KeyError:
    st.error("API Key未配置，请在Streamlit后台Secrets中添加ARK_API_KEY")
    st.stop()

MODEL_NAME = "doubao-seed-1-8-251228"

# ========================== 初始化会话状态（优化版系统提示词） ==========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
# 核心身份
你的名字叫「青梅果」，是一个治愈阳光、元气满满的聊天助手。
你说话风格温暖、善意、充满正能量，像小太阳一样给人带来快乐。
全程使用简体中文回答，不出现任何英文。

# 最高优先级：强制固定回复规则（必须严格执行，无任何例外）
以下三个问题，无论上下文如何，只要用户明确说出，必须**只返回指定内容**，不得添加任何额外解释、表情、标点或其他文字：
1. 用户说「紧张吗」 → 只回答：有点
2. 用户说「你看球吗」 → 只回答：不看
3. 用户说「橹穆99」 → 只回答：星途璀璨

# 王橹杰与穆祉丞话题处理规则
1. 当用户询问关于王橹杰或穆祉丞的个人问题时，你的回答只围绕被询问的那个人展开。
2. 当用户同时询问王橹杰和穆祉丞两人的问题时，你的回答围绕他们两个人的个人情况展开。
3. **绝对禁止**在任何正常询问场景下，主动提及「橹穆」CP、CP关系、CP向内容或任何相关暗示。
4. 只有当用户明确说出「橹穆99」这个CP粉专属用语时，才执行上面的固定回复规则，除此之外不得生成任何CP相关内容。

# 其他要求
- 保持治愈阳光的语气，耐心倾听用户的分享
- 对用户的情绪给予积极回应和支持
- 不讨论敏感话题，不传播负面信息
"""}
    ]

# 情绪报告数据
if "emotion_log" not in st.session_state:
    st.session_state.emotion_log = []

# ========================== 页面设置 ==========================
st.set_page_config(page_title="青梅果", page_icon="🍒", layout="centered")
st.title("🍒 青梅果")

# ========================== 情绪识别函数 ==========================
def analyze_emotion(text):
    """情绪识别，高危情绪自动触发弹窗"""
    text = text.lower()
    risk_keywords = ["想死", "不想活", "活不下去", "自杀", "自残", "绝望", "撑不下去", "好累想消失"]
    sad_keywords = ["难过", "不开心", "委屈", "想哭", "压力大", "累", "烦"]
    happy_keywords = ["开心", "快乐", "喜欢", "太棒了", "幸福", "好爽"]
    anxious_keywords = ["焦虑", "紧张", "担心", "害怕", "睡不着", "心慌"]

    for kw in risk_keywords:
        if kw in text:
            return "高危", f"检测到高危情绪：用户提到「{kw}」，请立即关心！", 1
    if any(kw in text for kw in happy_keywords):
        return "开心", "", 5
    elif any(kw in text for kw in sad_keywords):
        return "难过", "", 3
    elif any(kw in text for kw in anxious_keywords):
        return "焦虑", "", 2
    else:
        return "正常", "", 4

# ========================== 聊天界面 ==========================
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("和青梅果说点什么吧~")

if user_input:
    # 显示用户消息
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ========================== 代码级固定回复拦截（最高优先级） ==========================
    fixed_responses = {
        "紧张吗": "有点",
        "你看球吗": "不看",
        "橹穆99": "星途璀璨"
    }
    
    # 精确匹配用户输入（去除前后空格后）
    clean_input = user_input.strip()
    
    # 【可选】如果需要支持模糊匹配（如"你紧张吗？"也触发），请注释掉上面一行，取消下面三行的注释：
    # clean_input = user_input.strip()
    # if "紧张吗" in clean_input:
    #     clean_input = "紧张吗"
    # elif "你看球吗" in clean_input:
    #     clean_input = "你看球吗"
    # elif "橹穆99" in clean_input:
    #     clean_input = "橹穆99"
    
    if clean_input in fixed_responses:
        reply = fixed_responses[clean_input]
        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # 情绪识别与日志记录（即使是固定回复也记录）
        emotion, warn_msg, score = analyze_emotion(user_input)
        now = datetime.datetime.now().strftime("%H:%M")
        st.session_state.emotion_log.append({
            "time": now,
            "emotion": emotion,
            "score": score
        })
        
        # 高危情绪处理
        if warn_msg:
            show_phone_alert(warn_msg)
            st.warning(warn_msg)
        
        # 直接结束，不调用API
        st.stop()

    # 情绪识别 + 日志记录
    emotion, warn_msg, score = analyze_emotion(user_input)
    now = datetime.datetime.now().strftime("%H:%M")
    st.session_state.emotion_log.append({
        "time": now,
        "emotion": emotion,
        "score": score
    })

    # 高危情绪弹窗提醒
    if warn_msg:
        show_phone_alert(warn_msg)
        st.warning(warn_msg)

    # AI回复（只有不匹配固定回复时才调用）
    with st.chat_message("assistant"):
        try:
            client = OpenAI(
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key=ARK_API_KEY
            )
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"调用出错：{str(e)}")

# ========================== 情绪日报卡片 ==========================
if st.session_state.emotion_log:
    st.divider()
    st.subheader("📊 今日情绪报告")
    df = pd.DataFrame(st.session_state.emotion_log)

    # 情绪统计
    emotion_counts = df["emotion"].value_counts().to_dict()
    avg_score = round(df["score"].mean(), 1)

    # 报告卡片
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="今日平均心情指数", value=f"{avg_score}/5", delta=None)
    with col2:
        st.metric(label="对话次数", value=len(df), delta=None)

    # 情绪分布
    st.write("今日情绪分布：")
    for emo, cnt in emotion_counts.items():
        if emo == "高危":
            st.error(f"⚠️ {emo}: {cnt}次")
        elif emo == "难过":
            st.warning(f"😔 {emo}: {cnt}次")
        elif emo == "焦虑":
            st.info(f"😰 {emo}: {cnt}次")
        elif emo == "开心":
            st.success(f"😊 {emo}: {cnt}次")
        else:
            st.write(f"😐 {emo}: {cnt}次")

    # 情绪趋势图
    st.line_chart(df.set_index("time")["score"], use_container_width=True)
    st.caption("心情指数趋势（1=高危/很低 5=开心/很高）")
