# P18 ACCEPTANCE EVIDENCE

```text
阶段   = P18 ACCEPTANCE GATE（独立验收 · NO IMPLEMENTATION / NO RELEASE）
结论   = P18 ACCEPTANCE = PASSED
基线   = UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME
         HEAD = origin/main = 9fe282b009aba3965236402971ab963694f7ce05（tags 15 · staged 0）
权威   = PDL 附录 Y（P18 PREP）· 附录 Z（P18 FREEZE）· 附录 AA（B′ 澄清）
         + P18 Implementation Contract（FROZEN）· P18 Implementation Evidence · Gap Record
日期   = 2026-10-01
```

## 1. Acceptance scope（本轮无任何代码变更）

```text
验收对象 = P18 PLATFORM CONTROL PLANE / TENANT-SPACE LIFECYCLE 全部冻结决策（D01–D14 · Q14–Q20）
验收方式 = 独立复跑全量显式 allowlist + 独立 DB/权限/正式库/Git 复核 + 证据归档
未执行   = 任何代码修改 · migration · DDL/DML · GRANT/REVOKE · commit/tag/push
```

## 2. Decision baseline（冻结复核）

```text
D01 dedicated uap_control ✓（7 个 uap* 角色 · uap_control 属性：LOGIN / NOSUPERUSER / NOCREATEDB /
    NOCREATEROLE / NOREPLICATION / NOBYPASSRLS / NOINHERIT）
D02 既有 tenant 5 态 + soft lifecycle ✓（无物理 DELETE；deleted = terminal）
D03 显式 initial tenant admin ✓   D04 显式 initial space admin（须已属 tenant）✓
D05 非 system 作用域管理员角色（不新增 permission）✓
D06 platform_admin-only 控制面授权 ✓（唯一引擎 canonical AuthorizationService）
D07 既有一次性平台 bootstrap 不变（未 initialized ⇒ 结构 provisioning DENY）✓
D08 natural-key 幂等 + exact replay + conflict ✓
D09 单事务 + 原子审计 ✓   D10 独立 /control 命名空间（无 DELETE 端点）✓
D11 结构操作全审计（actor = 真实平台主体）✓   D12 Production Event REJECT ✓
D13 专用最小权限面（uap_control 23 grants · uap_runtime 不扩张 56）✓
D14 仅 ACTIVE Tenant/Space 可建立普通运行时上下文 + Agent Run 门禁 ✓
附录 AA：Control Plane 授权一律 PLATFORM scope；resource identity 仅作审计/用例上下文 ✓
```

## 3. Test results（本轮独立复跑 · 显式 allowlist · 0 skipped / 0 xfail / 0 deselected）

```text
P18 = 33 passed / 0 failed
  tests/unit/test_p18_pre_resource_authorization.py                9
  tests/integration/test_p18_control_plane_authorization.py        5
  tests/integration/test_p18_control_plane_provisioning.py          9
  tests/integration/test_p18_control_plane_metadata_and_gate.py     5
  tests/integration/test_p18_control_api_http.py                    5
P17 = 97 passed / 0 failed（8 文件显式 allowlist · 含 acceptance/metadata/agent/authz/API）
P15 = 65 passed / 0 failed
P16 = 24 passed（单元+安全）/ 0 · 8 passed（集成 6 场景 + durability）/ 0
architecture guards = 63 passed / 0 failed（含 6 项 P18 守卫）· Core → Domain = 0
合计 290 项通过 / 0 失败 · forbidden tests（test_generate_build_info.py）= 0 次执行 · OI-G-4 = 0
```

## 4. 覆盖的验收类别（对应指令 §8–§55）

```text
platform bootstrap gate（未 initialized ⇒ DENY · 不得自动初始化）
tenant provisioning（对象 + 投影 + 角色/权限 + 初始成员 + 审计 + active 同事务）
space provisioning（tenant 必须 active · 初始空间管理员须已属 tenant）
初始 tenant/space 管理员（显式输入 · 存在且 active）
资源投影（tenant/space/member 集合 · natural key 幂等 · 缺失 ⇒ DENY）
orphan / completeness（无半初始化：审计失败 ⇒ 全量回滚，独立连接确认无残留）
生命周期（合法迁移矩阵 · 非法迁移 DENY（active→deleted 等）· deleted terminal · 软删除保留历史）
运行时上下文门禁（suspended/archived/deleted ⇒ TENANT_NOT_ACTIVE / SPACE_NOT_ACTIVE）
membership 生命周期门禁（同门禁覆盖 · 行保留 · 无级联）
D14 Agent Run 门禁（tenant/space inactive ⇒ admission DENY · active 语义逐字不变）
控制面 API（/control 命名空间 · 无 DELETE 端点 · 无通用 CRUD · 防枚举）
API 认证与主体验分离（runtime=uap_runtime / control=uap_control · audit actor = 真实用户）
metadata / visibility / owner（visibility 仅元数据 · 不产生 membership/role/ACL · owner 非授权）
审计（全操作审计 · 内容安全 · append-only：UPDATE/DELETE 被拒 · 原子性）
并发/幂等（exact replay replayed=true · 不一致 ⇒ 409）
权限（uap_control 23 · 自校验 missing/unexpected/forbidden/drift 全空 · 无 DELETE/DDL/SET ROLE）
架构（Core → Domain = 0 · runtime 不得 provisioning · role provisioning 不可从应用路径触达）
回归（P16 33/0+8/0 · P15 65/0 · P17 97/0）
正式库（uap public 表 0 · 未触碰）；临时库全部清理（现存 uap / uap_b1_test / uap_test）
```

**END OF P18 ACCEPTANCE EVIDENCE（P18 ACCEPTANCE = PASSED · 290/0 · 无 blocker · Formal DB unchanged · 未 commit / tag / push；2026-10-01）**
