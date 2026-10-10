# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。

你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    """TODO(Q1)：血量百分比，返回 0-100 的 int；计算与边界规则见题面 Q1 规范。"""
    ratio=int(hp*100/max_hp)
    if ratio>100:
        ratio=100
    elif ratio<0:
        ratio=0
    return ratio
    # raise NotImplementedError("Q1 hp_ratio：题面 Q1·血量百分比与精度保障")


def status_report(name, robot_type, hp, max_hp, battery):
    """TODO(Q1)：一行自检报告字符串；档位判定与逐字符格式见题面 Q1 规范。"""
    ratio=hp_ratio(hp,max_hp)
    tmp="a"
    if battery>=60:
        tmp="OK"
    elif battery>=20:
        tmp="WARNING"
    else:
        tmp="LOW"
    ans=f"{name:<10}|{robot_type:^10}|HP {ratio:>3}%|BAT {battery:>3}%|{tmp}"
    return ans
    # raise NotImplementedError("Q1 status_report：题面 Q1·电量映射与报告格式")


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
def analyze_damage_log(lines):
    """TODO(Q2)：解析混合格式伤害日志，返回固定契约的统计 dict；
    行格式、去重与统计口径见题面 Q2 规范。"""
    Id=[]
    Front=0
    Left=0
    Right=0
    for line in lines:
        line=line.strip().replace(" ","")
        if line=="":
            continue
        if line.startswith("#"):
            continue
        if 'F' in line or 'L' in line or 'R' in line:
            b=line.strip().split(',')
            tmpF=0
            tmpR=0
            tmpL=0
            sign=True
            for tmp in b:
                if ':' not in tmp:
                    sign=False
                    break
                tm=tmp.strip().split(':')
                p=tm[0]
                num_str=tm[-1]
                num=int(num_str)
                if not isinstance(num,int) or num<=0:
                    sign=False
                    break
                if p=="F":
                    tmpF+=num
                elif p=="R":
                    tmpR+=num
                elif p=="L":
                    tmpL+=num
                else:
                    sign=False
                    break
                continue
            if sign:
                Front+=tmpF
                Right+=tmpR
                Left+=tmpL
            continue
        try:
            a=json.loads(line)
        except json.JSONDecodeError:
            continue
        if "armor" in a and "damage" in a:
            armor=a["armor"]
            damage=a["damage"]
            if not isinstance(damage,int) or damage<=0:
                continue
            if not armor in ["left","right","front"]:
                continue
            if "id" in a:
                nid=a["id"]
                if nid in Id:
                    continue
                else:
                    Id.append(nid)
            if armor=="front":
                Front+=damage
            elif armor=="right":
                Right+=damage
            elif armor=="left":
                Left+=damage
            continue
    Total=Front+Right+Left
    most_hit=None
    # 我突然就知道为什么要插空格写了
    if Front > 0 or Right > 0 or Left > 0:
        if Front >= Right and Front >= Left:
            most_hit="front"
        elif Right >= Front and Right >= Left:
             most_hit="right"
        elif Left >= Front and Left >= Right:
            most_hit="left"
    num=1
    if Front and Right and Left:
        num=3
    elif Front and Right and not Left:
        num=2
    elif Front and not Right and Left:
        num=2
    elif not Front and Right and Left:
        num=2
    robot={
        "total":Total,
        "by_armor": {"front": Front, "left": Left, "right": Right},
        "most_hit": most_hit,
        "avg": float((Front+Right+Left)/num)
    }
    return robot
    # raise NotImplementedError("Q2 analyze_damage_log：题面 Q2·多源日志解析与统计")


# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------
class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        # self._pos = self._clamp_cell(start_pos)
        #一开始想了半天self哪来的
        self.current_pos=start_pos
        if self._pos in self._obstacles:
            raise ValueError("start_pos 不能位于障碍物上")

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        """TODO(Q3)：位置 setter；三重输入校验见题面 Q3 规范第 1 条。"""
        if not isinstance(value,(tuple,list)) or len(value)!=2:
            raise TypeError
        self._pos=tuple(value)
        return
        # raise NotImplementedError("Q3 current_pos.setter：题面 Q3·位置校验三步")

    def move_forward(self):
        """TODO(Q3)：朝当前 facing 前进一格，返回执行后的位置；
        碰撞、耗电与断电语义见题面 Q3 规范。"""
        if self._fuel<=0:
            return self.current_pos
        dx,dy=self._facing.delta
        x,y=self.current_pos
        x+=dx
        y+=dy
        if (x,y) in self._obstacles or not (0<=x<self._width and 0<=y<self._height):
            self._collision_count+=1
            self._fuel-=1
            return self.current_pos
        self.current_pos=(x,y)
        self._fuel-=1
        return self.current_pos
        # raise NotImplementedError("Q3 move_forward：题面 Q3·前进、碰撞与断电")

    def turn_left(self):
        """TODO(Q3)：原地左转 90°，返回新的 Facing（不耗电）。"""
        if self._facing==Facing.UP:
            self._facing=Facing.LEFT
        elif self._facing==Facing.LEFT:
            self._facing=Facing.DOWN
        elif self._facing==Facing.DOWN:
            self._facing=Facing.RIGHT
        elif self._facing==Facing.RIGHT:
            self._facing=Facing.UP
        return self._facing
        # raise NotImplementedError("Q3 turn_left")

    def turn_right(self):
        """TODO(Q3)：原地右转 90°，返回新的 Facing（不耗电）。"""
        if self._facing==Facing.DOWN:
            self._facing=Facing.LEFT
        elif self._facing==Facing.LEFT:
            self._facing=Facing.UP
        elif self._facing==Facing.UP:
            self._facing=Facing.RIGHT
        elif self._facing==Facing.RIGHT:
            self._facing=Facing.DOWN
        return self._facing
        # raise NotImplementedError("Q3 turn_right")


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    """TODO(Q4)：返回下一步应朝向的 Facing；
    候选判定、优先级与回退规则见题面 Q4 规范。"""
    x,y=pos
    tx,ty=target
    dis=abs(x-tx)+abs(y-ty)
    go=0
    ans=current_facing
    for i in Facing:
        dx,dy=i.delta
        #真觉得没啥问题
        tmp=abs(dx)*abs(x-tx)+abs(dy)*abs(y-ty)
        x+=dx
        y+=dy
        Dis=abs(x-tx)+abs(y-ty)
        if Dis<dis and (x,y) not in obstacles and tmp>=go:
            ans=i
            go=tmp
        x-=dx
        y-=dy
    return ans
    #写到这对python数据结构还是有点懵逼
    # raise NotImplementedError("Q4  next_step_toward：题面 Q4·贪心策略与回退")


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------
class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


def decide(sensor, state, hp, heat):
    """TODO(Q5)：纯函数决策，返回 (action: str, new_state: SentryState)；
    sensor 字段契约、R1-R7 规则表与非法输入处理见题面 Q5 规范。"""

    req=["enemy_frames","enemy_dist","robot_type","max_hp"]
    if not isinstance(sensor,dict) or not all(k in sensor for k in req):
        raise ValueError
    enemy_frames=sensor["enemy_frames"]
    if len(enemy_frames)<1 or len(enemy_frames)>6 or not isinstance(enemy_frames,(tuple,list)):
        raise ValueError
    if not isinstance(state,SentryState):
        raise ValueError
    vis=enemy_frames[-1]
    if vis:
        dis=int(sensor["enemy_dist"])
    else:
        dis=None
    typ=sensor["robot_type"]
    hp_pct=int(hp/sensor["max_hp"]*100)
    # R1
    if hp_pct<=30:
        return ("RETREAT",SentryState.RETREAT)
    # R2
    if state==SentryState.RETREAT:
        if hp_pct>30:
            return ("RETURN",SentryState.RETURN)
        else:
            return ("RETREAT",SentryState.RETREAT)
    # R3
    if state==SentryState.RETURN:
        return ("MOVE_BASE",SentryState.PATROL)
    # R4
    if state==SentryState.ENGAGE and vis:
        if dis<=3:
            return ("SHOOT",SentryState.ENGAGE)
        elif typ=="HERO":
            return ("MOVE_RIGHT",SentryState.ENGAGE)
        elif typ=="INFANTRY":
            return ("MOVE_LEFT",SentryState.ENGAGE)
    # R5
    if state==SentryState.ENGAGE and not vis:
        if sum(enemy_frames)>0:
            return ("HOLD_FIRE",SentryState.ENGAGE)
        elif sum(enemy_frames)==0:
            return ("SCAN",SentryState.SUSPECT)
    # R6
    if (state==SentryState.PATROL or state==SentryState.SUSPECT) and vis:
        if len(enemy_frames)>=2 and enemy_frames[-1] and enemy_frames[-2]:
            if dis<=3:
                return ("SHOOT",SentryState.ENGAGE)
            elif typ=="HERO":
                return ("MOVE_RIGHT",SentryState.ENGAGE)
            elif typ=="INFANTRY":
                return ("MOVE_LEFT",SentryState.ENGAGE)
        else:
            return ("SCAN",SentryState.SUSPECT)
    # R7
    if state==SentryState.PATROL and not vis:
        return ("PATROL_MOVE",SentryState.PATROL)
    if state==SentryState.SUSPECT and not vis:
        return ("SCAN",SentryState.SUSPECT)
    # raise NotImplementedError("Q5 decide：题面 Q5·决策规则表 R1-R7")


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def run_patrol(grid, max_steps=500):
    """TODO(Q6)：sense → decide → act 主循环；
    循环结构、终止条件、脱困自由度与统计返回契约见题面 Q6 规范。"""
    raise NotImplementedError("Q6 run_patrol：题面 Q6·主循环与统计契约")


def report_to_json(stats):
    """TODO(Q6)：把 stats 序列化为确定性的 JSON 字符串，见题面 Q6 规范。"""
    raise NotImplementedError("Q6 report_to_json：题面 Q6·报告序列化")


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    """TODO(Bonus)：BFS 全局最短路步数；返回语义与边界职责见题面 Bonus 规范。"""
    raise NotImplementedError("Bonus bfs_path_length")


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
