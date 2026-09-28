# P15 EVENT CONTRACT ALIGNMENT

## 0. 目的

本文件把已冻结的 Event 契约语义固定为一处可追溯的说明，并记录它与
实现、测试、决策日志之间的对应关系。

```text
Human Decision = HD-FRP-FOUNDATION-01（2026-09-28 · FROZEN）
Authority      = PLATFORM_DECISION_LOG.md 附录 U（append-only）
                 · D-P10-02（Domain Event ID = UUIDv7 canonical；Outbox/EventBus 区分）
                 · D-AUTH-22（Audit / Event ID = UUIDv7）
                 · D-P10-17（五类承载面边界 + 守卫）
性质           = foundation correction（不是新的 Decision System；不产生新 subject / schema）
```

---

## 1. Event identity（事件标识）

```text
Domain Event ID = canonical UUIDv7（应用层生成）
Canonical generator = core.audit.interfaces.new_event_id()
DB 约束 = events.id uuid NOT NULL（无 server default、无格式 CHECK）
         ⇒ 身份由应用层生成；数据库不校验、也不默认生成 UUIDv7
```

```text
core/event/interfaces.py
  · 不再使用 uuid.uuid4()（D-P10-02 决策①：uuid4 = 实现遗留）
  · 直接复用 core.audit.interfaces.new_event_id()
  · 不定义第二个 generator（禁 new_uuid7 / uuid_generator / system_uuid_generator）
```

顺序性影响（事实陈述，不构成新决策）：

```text
uniqueness = 不受影响（uuid 类型）
ordering   = UUIDv7 时间有序 ⇒ 对 audit_logs / events 的分区裁剪与归档有益（D-AUTH-22 理由段）
```

---

## 2. tenant_id 契约（租户归属）

```text
DomainEvent.tenant_id : str | None = None

tenant_id != NULL  → tenant-scoped event
tenant_id == NULL  → platform-scoped event
```

明确语义边界：

```text
NULL ≠ 「未知 tenant」
NULL ≠ 「绕过 tenant isolation」
NULL ≠ platform_admin
NULL ≠ 隐式平台租户替换（实现不得把 None 替换为某个平台 tenant id）
```

一致性依据：

```text
committed DB schema（0013）: events.tenant_id nullable = TRUE · audit_logs.tenant_id = TRUE
live DB 实测              : events.tenant_id is_nullable = YES
⇒ 本轮为 application contract alignment（schema mutation = 0 · migration mutation = 0 · 0018+ = 0）
```

---

## 3. Platform-scoped event 的安全语义

```text
actor provenance remains present   —— 事件仍携带 originating actor（不伪造 system/service actor）
authorization remains required     —— platform scope 不豁免授权判定
space isolation cannot be bypassed —— space_id 独立，不从 tenant_id = NULL 推导
tenant-scoped actor cannot silently elevate to platform scope
```

```text
subject vocabulary = user / role / agent（不新增 worker_subject / service_subject /
                     consumer_subject / system_subject）
若未来出现必须新增平台主体语义的用例 ⇒ STOP · AUTHORIZATION DECISION REQUIRED
```

---

## 4. 事件身份与投递

```text
event_id = primary delivery identity（O-6）
Outbox   = durable / reliable delivery authority（events 表）
EventBus = optional in-process auxiliary；MUST NOT 替代 outbox 持久化、
           MUST NOT 作为持久边界、MUST NOT 成为跨进程投递机制（D-P10-02 决策②③ · C-3）
禁止实现：exactly-once 承诺 · 新增 dedup 表 · 新增 schema
```

---

## 5. 可追溯性（decision → contract → test → implementation）

| 语义 | Decision | Contract（本文件/其他） | Test | Implementation |
|---|---|---|---|---|
| Domain Event ID = UUIDv7 canonical | `D-P10-02` 决策① · `D-AUTH-22` | §1 · PDL 附录 U | `tests/architecture/test_event_contract_alignment.py` · `test_p10_event_audit_boundary.py::test_event_contract_uses_the_canonical_uuid7_generator` | `core/event/interfaces.py`（委托 `new_event_id()`） |
| EventBus != Outbox | `D-P10-02` 决策②③ · `C-3` | §4 · PDL 附录 U | `test_event_contract_alignment.py::test_event_bus_is_documented_as_distinct_from_the_outbox` | `core/event/interfaces.py` docstring |
| tenant_id 可空语义 | `HD-FRP-FOUNDATION-01`（附录 U）· schema `0013` | §2 · PDL 附录 U | `test_event_contract_alignment.py`（tenant-scoped / platform-scoped 两路径） | `core/event/interfaces.py` |
| NULL tenant ≠ 授权旁路 | `HD-FRP-FOUNDATION-01`（附录 U） | §3 · PDL 附录 U | `test_event_contract_alignment.py::test_platform_scope_is_not_an_authorization_bypass` · `::test_actor_provenance_survives_platform_scope` | `core/event/interfaces.py`（无特权字段/无旁路 token） |
| 五类承载面 | `D-P10-17` | `docs/architecture/DEPENDENCY_RULES.md` §Carrier faces | `test_p10_event_audit_boundary.py` | 文档（守卫见测试） |

---

## 6. 本轮明确不做（边界）

```text
AGENT_RUNTIME future scope            = 不进入本 release（单独 future-scope candidate）
P09 Authorization status block 重写    = 不做（保持 committed 历史文本）
tests/conftest.py                      = 未授权（F-RP-02 remaining open）
infrastructure/database/__init__.py    = 未授权（F-RP-02 remaining open）
schema / migration / role / grant / ACL / subject vocabulary = 0 变更
```

**END OF P15 EVENT CONTRACT ALIGNMENT**
