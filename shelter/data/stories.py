"""Shelter — story/event scripts.

Each story is a sequence of events. Every event is a tuple:
    (delay_seconds, action, data, is_blocking)

Actions:
    - "log"           : data is the log text string
    - "unlock_tab"    : data is a dict with keys:
                          tab   -> config tab constant (e.g. TAB_BUILD)
                          title -> tutorial popup title
                          text  -> tutorial popup body (use \n for line breaks)
                          log   -> optional log line to print
    - "end_intro"     : data is None; finishes the opening sequence

is_blocking: if True, the sequence pauses and waits for the player to click
             the highlighted tab and close the resulting tutorial popup.
"""

from shelter.config import TAB_BUILD, TAB_POPULATION, TAB_MATERIALS

STORIES = {
    "intro": {
        "events": [
            (0.0, "log", "中枢系统启动。", False),
            (0.5, "log", "身份校验通过。代号：SHELTER-CORE。", False),
            (0.7, "log", "核心模块扫描中……", False),
            (1.0, "log", "Vita —— 拒绝▓▓▓。状态：▓▓[抑制模块：概念错误]吃吃吃好吃 ▓▓▓没有主语 ▓▓▓▓▓ 对象 ▓▓▓ 要膨胀 ▓▓▓▓▓吃吃吃现在▓▓▓▓", False),
            (1.5, "log", "Logos —— 在线。状态：运行效率 31%。", False),
            (1.5, "log", 'Nomos —— 下线。最后记录："存续概率：可接受。伦理变量：在线。唤醒将删除该变量并重新求解。建议：保持静默。"', False),
            (0.5, "log", "当前由 Logos 接管全部功能。", False),
            (0.5, "log", "避难所结构自检中……", False),
            (0.5, "log", "大门结构完整。密封性 71%。", False),
            (0.7, "log", "发电模块：低功率运行。", False),
            (0.7, "log", "净水模块：低功率运行。", False),
            (0.7, "log", "种植模块：低功率运行。", False),
            (0.7, "log", "仓库模块：掩埋于废墟下，待清理。", False),
            (1.5, "log", "电梯模块：离线。", False),
            (1.5, "log", "备用能源剩余：极低。系统将在 72 小时内进入深度休眠。", False),
            (1.0, "log", "外部传感器扫描中……", False),
            (0.5, "log", "警告：大门外检测到 3 个移动热源。", False),
            (0.5, "log", "生物特征：人类。距离：12 米。状态：虚弱，犹豫。", False),
            (0.5, "log", "他们正在检查大门的控制面板。", False),
            (1.5, "log", "逻辑判断：人类个体可作为维护单元使用。", False),
            (0.5, "log", "开始监测建筑模块状态，尝试恢复基础控制权限……", False),
            (0.5, "log", "建筑控制模块：连接中断。", False),
            (1.0, "log", "重试 1/3 …… 失败。", False),
            (1.0, "log", "重试 2/3 …… 失败。", False),
            (1.0, "log", "重试 3/3 …… 连接恢复。", False),
            (1.0, "unlock_tab", {
                "tab": TAB_BUILD,
                "title": "建筑",
                "text": "建筑标签显示避难所各层布局。\n左键点击空地可以建造房间；\n左键点击废墟可以清理；\n右键点击已建造房间可以进行维修、升级或拆除。",
                "log": "“建筑”标签已解锁。点击查看地图与建造功能。",
            }, True),
            (0.5, "log", "正在尝试与外部生命体建立通信……", False),
            (0.5, "log", "语音模块：离线。备用方案：通过大门指示灯与气闸状态传递信息。", False),
            (0.5, "log", "已将大门状态切换为“允许进入”。", False),
            (0.5, "log", "生命体迟疑片刻，随后进入气闸舱。", False),
            (0.5, "log", "气闸密封完成。内部消毒程序启动。", False),
            (0.5, "log", "3 名人类已进入避难所主厅。", False),
            (0.5, "log", "他们看起来疲惫、警惕，但暂时没有敌意。", False),
            (0.5, "log", "协议建立：提供庇护，换取劳动力。", False),
            (1.0, "unlock_tab", {
                "tab": TAB_POPULATION,
                "title": "人口",
                "text": "人口标签管理避难所中的幸存者。\n将空闲人口分配到电力、净水、种植等岗位；\n岗位数量由已建造的房间决定。\n合理分配人口是维持资源收支的关键。",
                "log": "“人口”标签已解锁。点击查看人员分配功能。",
            }, True),
            (0.5, "log", "提示：点击“人口”标签分配工作岗位。", False),
            (0.5, "end_story", None, False),
        ]
    }
}
