# P20 COMPANY DOMAIN DECISION FREEZE REPORT

```yaml
Decision: FROZEN
Appendix: AF
Implementation: NOT AUTHORIZED
API: NOT AUTHORIZED
Event: NOT AUTHORIZED
Worker: NOT AUTHORIZED
Migration: DONE (0019_p20_company · ACCEPTED)
Permission grant: NOT EXECUTED (role_permissions Company rows = 0)
Resource projection: NOT EXECUTED (no company_* resources rows)
Commit: NO
Tag: NO
Push: NO
Hard Stop: ACTIVE
```

## 1. 阶段与基线

```text
阶段     = P20 COMPANY DOMAIN DECISION FREEZE（仅决策冻结文档）
基线     = UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）+ 附录 AD / AE + 0019_p20_company（ACCEPTED）
本轮产物 = ① PDL 附录 AF（append-only）② 本报告
本轮禁止 = 代码实现 / Domain Service / Repository / API / DTO / Worker / Event /
           Permission Grant / Role 修改 / Migration 修改 / commit / tag / push
```

## 2. Phase 1 只读验证（实测）

```text
Core → Domain = 0                    PASS（tests/architecture/test_dependency_rules.py = 14 passed）
0019_p20_company exists              PASS（sha256 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0
                                          · alembic heads = ['0019_p20_company'] 单 head）
company_employees / company_assignments PASS（一次性隔离库 tables = 2）
canonical actions = 12               PASS（core.permission.vocabulary.ACTIONS = 12；
                                          隔离库 db_distinct_actions = 7「既有 canonical 动作的数据使用面」）
Company permissions = 11             PASS（隔离库 permissions 12 → 23）
ACL subject types = 3 only           PASS（USER / ROLE / AGENT · 隔离库 acl_subject_types = 3）
Events EMPTY                         PASS（production_allowlist().is_empty = True · events = 0）

常驻库未受影响（前后一致）：
  uap_b1_test = 0017_p13_seed · permissions 12 · company 表 0 · events 0
  uap（正式库）= 0 public 表
  探针库已 DROP · 无残留临时库
⇒ 未发现冲突，无需 STOP
```

## 3. Phase 2 冻结内容（附录 AF · D-P20D-01…11）

```text
D-P20D-01 授权主体      = platform_admin 先行持有 Company 权限（授予动作推迟到实现轮独立授权）
D-P20D-02 资源投影      = tenant 级集合资源（每 tenant × 每 resource_type 一行；无实例级资源）
D-P20D-03 删除权限      = RESERVED（无用例 / 无授予 / 无 API）
D-P20D-04 管理权限      = RESERVED
D-P20D-05 身份绑定      = A（可空创建 · 后续可绑定 · 绑定不产生授权）
D-P20D-06 空间生命周期  = C（既有分配不变 · 不修改 P18 · 无自动级联）
D-P20D-07 SELF 访问     = A（V1 不支持）
D-P20D-08 授权引擎      = CONFIRM（单一引擎 · 无旁路 · 域无权限逻辑）
D-P20D-09 事件边界      = CONFIRM（Allowlist EMPTY · 未来须重新通过 P19）
D-P20D-10 域落点        = A（domains/company/ · 实现前保持 placeholder · 守卫变更需显式授权）
D-P20D-11 依赖方向      = A（域禁 ORM / SQLAlchemy / infrastructure；Core → Domain Contract → Services/Infra）
```

## 4. Phase 3 一致性闸门

```text
D1 ↔ Authorization          PASS
D2 ↔ Resource Model         PASS
D3/D4 ↔ Permission Vocabulary PASS
D5 ↔ Schema                 PASS
D6 ↔ P18                    PASS
D7 ↔ ACL Capability         PASS
D8 ↔ Existing Authorization PASS
D9 ↔ P19 附录 AB            PASS
D10/D11 ↔ Core→Domain=0     PASS
⇒ ALL PASS（逐项依据见 PDL 附录 AF.4）
```

## 5. 本轮未执行（授权边界）

```text
权限授予（role_permissions Company allow 行）= 0 → 未执行
资源投影（resources 集合行）= 未创建
代码 / 测试实现 = 无
migration = 未新增 / 未修改（0019 保持已验收状态）
事件 = 未激活
正式库与共享测试库 = 未触碰
commit / tag / push = NO
```

## 6. 停止点与下一阶段

```java
P20 COMPANY DOMAIN DECISION = FROZEN
P20 DOMAIN IMPLEMENTATION = NOT AUTHORIZED
P20 API = NOT AUTHORIZED
P20 EVENT = NOT AUTHORIZED
P20 WORKER = NOT AUTHORIZED
COMMIT/TAG/PUSH = NO
HARD STOP = ACTIVE
```

```text
下一阶段（须独立授权）：P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION
  届时范围：domain contracts · repository interfaces · services/use_cases ·
            authorization integration · tests
  实现轮前需一并裁定（附录 AF 已登记为未决边界）：
    ① platform_admin 的 11 条 Company 权限授予方式（新迁移 or 受控脚本）
    ② 集合资源投影的 natural_key 取值与投影归属（实现轮契约确定）
    ③ domains/company/manifest.py 与 manifest 守卫的显式修改授权
  禁止：因本次冻结自动进入实现；API / Worker / 事件仍须各自独立授权
```

**END OF P20 COMPANY DOMAIN DECISION FREEZE REPORT（附录 AF 已追加 · D-P20D-01…11 FROZEN · 一致性闸门 ALL PASS · 11 项决策均未触发任何实现/授予动作 · HARD STOP ACTIVE；2026-10-02）**
