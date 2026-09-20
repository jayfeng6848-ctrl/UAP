# P09_API_DESIGN

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE（API = 0）**
**DESIGN**: **NOT STARTED** · **0011**: **ABSENT** · **IMPLEMENTATION**: NOT STARTED
**权威记录**: `P09_DECISION_LOG.md`（`D-P09-07` = A：P09 = SCHEMA ONLY）

---

## 1. 结论：P09 的 API 面 = **0**

`D-P09-07` = FROZEN — A：**P09 = SCHEMA ONLY**，明确不实现 HTTP API / Socket / Worker / Scheduler。

```
本阶段新增 API endpoint      = 0
本阶段新增 service 接口       = 0
本阶段新增 runtime            = 0
本阶段修改 apps/api           = 0
本阶段修改 apps/worker        = 0
```

---

## 2. 依据

| 来源 | 内容 |
|---|---|
| `D-P09-07` | P09 = SCHEMA ONLY；不修改 `agent/`；不实现任何 Runtime |
| `P09_SCOPE.md §3` | OUT OF SCOPE：HTTP API / Socket / Worker / Scheduler / Celery / 分区自动化 |
| `STEP1A_DESIGN_REPORT.md:560` | 「明确不在 STEP 1-B：… 具体 Agent / Tool 实现」 |
| `B1-1` … `B1-6` 先例 | 各阶段均为**零业务代码**（仅 schema + 测试）；`B1-6_API_DESIGN.md` 亦结论 API = 0 |

---

## 3. 现状（只读实测，本阶段未改动）

```
apps/api/routes/        = { __init__.py, health.py, meta.py }
apps/worker/main.py     = placeholder
apps/api/routes/health.py: OPTIONAL_COMPONENTS = ("cache", "queue", "ai_gateway")
                           （P09 未新增任何 optional component）
```

---

## 4. 未来契约（仅登记，**不是**本次冻结内容）

- P09 之后的 Agent / Tool 运行时若需要接口，必须在**新的阶段与新的授权**下设计
- `agent/` 的 STEP 0 Protocol 骨架（`AgentRuntime` / `AgentRegistry` / `Tool` / `ToolRegistry` /
  `MemoryStore` / `WorkflowRunner`）**保持原样**，P09 不实现、不绑定、不实例化
- 授权解释（ALLOW / DENY）属 **Authorization Layer**，不在 P09 也不在任何 DB trigger 中实现

---

## 5. Gate

```
P09 API = 0（FROZEN）
P09 DESIGN = NOT STARTED · IMPLEMENTATION = NOT STARTED · 0011 = ABSENT
未修改 apps/ = 确认 · 未修改 agent/ = 确认
```
