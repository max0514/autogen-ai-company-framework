import streamlit as st
import autogen
import os
import time
from collections import Counter

# ==============================================================================
# 1. 網頁與 UI 設定
# ==============================================================================
st.set_page_config(page_title="AI 狼人殺 2026", page_icon="🐺", layout="wide")
st.title("🐺 AI 狼人殺：LLM 全自動邏輯推演")

# 左側邊欄設定
with st.sidebar:
    st.header("⚙️ 系統設定")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=os.environ.get("GEMINI_API_KEY", ""),
        type="password"
    )
    max_days = st.number_input("強制結束天數", min_value=1, max_value=15, value=5)
    max_chat_rounds = st.slider("白天群聊最大發言數", min_value=3, max_value=15, value=6)

    st.markdown("---")
    st.header("🕵️‍♂️ 觀戰模式")
    # --- [NEW] 新增：隱藏身份圖標的開關 ---
    hide_icons = st.checkbox("隱藏玩家身份圖標", value=True, help="勾選時，所有玩家對話將顯示統一般圖標，讓你無法分辨誰是狼人。遊戲結束後取消勾選即可揭曉身份。")
    # -------------------------------------

if not api_key_input:
    st.warning("⚠️ 請在左側輸入你的 Gemini API Key 以啟動遊戲。")
    st.stop()
os.environ["GEMINI_API_KEY"] = api_key_input

# ==============================================================================
# 2. 遊戲主迴圈 (一鍵全自動播放)
# ==============================================================================
if st.button("🚀 開始全自動狼人殺", type="primary"):
    
    status_box = st.empty()
    game_log = st.container()

    # 初始化遊戲狀態
    alive_players = ["Player_1", "Player_2", "Player_3", "Player_4", "Player_5", "Player_6"]
    dead_players = []
    ROLE_MAP = {
        "Player_1": "狼人", "Player_2": "狼人", 
        "Player_3": "預言家", "Player_4": "女巫", 
        "Player_5": "平民", "Player_6": "平民"
    }

    def update_status_ui(day):
        with status_box.container():
            st.info(f"**⏳ 目前進度**：第 {day} 天 | **🟢 存活**：{', '.join(alive_players)} | **💀 死亡**：{', '.join(dead_players) if dead_players else '無'}")

    def check_win_condition():
        wolves = sum(1 for p in alive_players if ROLE_MAP[p] == "狼人")
        good = len(alive_players) - wolves
        if wolves == 0:
            game_log.success("🎉 【遊戲結束】：所有狼人皆已死亡，好人陣營勝利！")
            return True
        if wolves >= good:
            game_log.error("💀 【遊戲結束】：狼人數量大於等於好人，狼人陣營勝利！")
            return True
        return False

    # 初始化 AutoGen Agents
    config_list = [{"model": "gemini-3.1-pro-preview", "api_key": api_key_input, "api_type": "google"}]
    llm_config = {"config_list": config_list, "temperature": 0.7}
    
    judge = autogen.UserProxyAgent(name="Judge", system_message="遊戲主持人", human_input_mode="NEVER", code_execution_config=False)
    
    agents = {}
    for p in alive_players:
        role = ROLE_MAP[p]
        mission = f"你是【{role}】。白天請隱藏真實身份參與群聊。"
        if role == "狼人":
            mission += "你的隊友是另一個狼人。晚上你要選擇殺人，白天你要栽贓好人。"
        agents[p] = autogen.AssistantAgent(
            name=p, 
            system_message=f"你的名字是 {p}。{mission} 請用第一人稱精簡發言。",
            llm_config=llm_config
        )

    # --------------------------------------------------------------------------
    # 🎬 開始日夜循環
    # --------------------------------------------------------------------------
    for day in range(1, max_days + 1):
        update_status_ui(day)
        
        # 🌙 【黑夜階段】
        with game_log.expander(f"🌙 第 {day} 天：黑夜行動 (上帝視角)", expanded=False):
            night_deaths = []
            alive_wolves = [p for p in alive_players if ROLE_MAP[p] == "狼人"]
            
            if alive_wolves:
                wolf_leader = alive_wolves[0]
                st.write(f"🐺 狼人 ({wolf_leader}) 正在悄悄決定殺誰...")
                
                kill_res = judge.initiate_chat(
                    agents[wolf_leader], 
                    message=f"現在是黑夜。你要殺誰？請只回覆目前存活玩家的名字之一：{', '.join(alive_players)}。請勿回覆其他廢話。", 
                    max_turns=1,
                    clear_history=False
                )
                
                target = kill_res.chat_history[-1]['content'].strip() if kill_res.chat_history else ""
                killed = None
                for p in alive_players:
                    if p in target:
                        killed = p
                        break
                
                if killed:
                    night_deaths.append(killed)
                    st.error(f"🩸 狼人殘酷地殺害了：{killed}")
                else:
                    st.warning("🐺 狼人猶豫了，今晚沒有殺人。")

            for d in night_deaths:
                if d in alive_players:
                    alive_players.remove(d)
                    dead_players.append(d)

        if check_win_condition(): break
        update_status_ui(day)
        time.sleep(0.5)

        # ☀️ 【白天討論階段】
        game_log.header(f"☀️ 第 {day} 天：白天群聊與投票")
        if night_deaths:
            game_log.warning(f"📢 昨晚死亡的玩家是：{', '.join(night_deaths)}")
        else:
            game_log.info("📢 昨晚是平安夜。")

        game_log.markdown("💬 **開始自由辯論...**")
        
        alive_agents = [judge] + [agents[p] for p in alive_players]
        groupchat = autogen.GroupChat(agents=alive_agents, messages=[], max_round=max_chat_rounds, speaker_selection_method="auto")
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
        
        chat_res = judge.initiate_chat(
            manager, 
            message="天亮了，請存活的大家開始推理昨晚發生的事，試圖找出狼人並為等一下的投票做準備！",
            clear_history=True
        )

        # --- [NEW] 修改後的對話渲染邏輯 ---
        for msg in chat_res.chat_history:
            speaker = msg.get("name", "")
            content = msg.get("content", "")
            if speaker and speaker != "Judge" and content:
                # 根據 checkbox 的狀態決定顯示什麼圖標
                if hide_icons:
                    avatar = "👤" # 隱藏時顯示統一的神祕人圖標
                else:
                    # 揭曉時顯示真實身份圖標
                    avatar = "🐺" if ROLE_MAP.get(speaker) == "狼人" else "🧑‍🌾"
                
                game_log.chat_message(speaker, avatar=avatar).write(content)
        # ----------------------------------

        # 🗳️ 【投票處決階段】
        game_log.markdown("---")
        game_log.markdown("🗳️ **進入投票環節**")
        votes = []
        
        for p in alive_players:
            vote_res = judge.initiate_chat(
                agents[p],
                message=f"辯論結束，必須淘汰一人。目前存活名單：{', '.join(alive_players)}。請直接回覆你要投出的玩家名字，不要說多餘的話。",
                max_turns=1,
                clear_history=False
            )
            vote_target = vote_res.chat_history[-1]['content'].strip()
            
            voted = None
            for candidate in alive_players:
                if candidate in vote_target:
                    voted = candidate
                    break
            
            if voted:
                votes.append(voted)
                game_log.write(f"👉 **{p}** 投票給了 **{voted}**")
            else:
                game_log.write(f"👉 **{p}** 選擇棄票")

        if votes:
            vote_counts = Counter(votes)
            most_voted, count = vote_counts.most_common(1)[0]
            game_log.error(f"🔨 **開票結果**：**{most_voted}** 獲得最高票 ({count}票)，遭到處決！")
            
            if most_voted in alive_players:
                alive_players.remove(most_voted)
                dead_players.append(most_voted)
        else:
            game_log.info("⚖️ 大家皆棄票，今日無人被處決。")

        if check_win_condition(): break
        
        game_log.markdown("---")
        time.sleep(1)

    if day >= max_days and not check_win_condition():
        game_log.info(f"⏳ 已達到最大天數 ({max_days} 天)，遊戲強制平局結束！")
    
    # 遊戲結束後的提示
    st.success("遊戲已結束！請取消左側的「隱藏身份圖標」勾選，查看大家的真實身份！")