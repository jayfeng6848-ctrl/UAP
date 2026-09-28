# P15 RELEASE VERSION DECISION

日期：2026-09-28
轮次：P15 RELEASE GATE（前身：P15 RELEASE PREPARATION 的版本候选登记）
性质：**Release Metadata Consistency** —— 不是新增架构决策

---

## 1. 版本身份

```text
Historical release:   0.1.10   （UAP-V0.1.10-P14-RUNTIME-SLICE · commit 15feebad）
P15 candidate:        0.1.11   （tag candidate UAP-V0.1.11-P15-EVENT-CONSUMER）

Version authority:
    release identity（release tag chain + explicit release decision）
  + synchronized static runtime metadata（静态源已同步）

Static synchronized sources:
    pyproject.toml
    config/settings.py
    docker-compose.yml
```

```text
TAG CANDIDATE             = UAP-V0.1.11-P15-EVENT-CONSUMER
COMMIT SUBJECT CANDIDATE  = release(p15): accept event consumer slice
RELEASE TITLE CANDIDATE   = UAP v0.1.11 — P15 Event Consumer Slice
```

---

## 2. Version Authority Audit（同步后实测）

| Source | Before | After | 说明 |
|---|---|---|---|
| `pyproject.toml` `[project].version` | `0.1.0` | **`0.1.11`** | Release Metadata Sync |
| `config/settings.py` `APP_VERSION` 默认值 | `0.1.0` | **`0.1.11`** | Release Metadata Sync |
| `docker-compose.yml` `APP_VERSION` | `0.1.0` | **`0.1.11`** | Release Metadata Sync |
| `config/build_info.py` | 不承载版本号 | 不变 | 仅承载 `EXPECTED_ALEMBIC_REVISION` |
| Release tag 链 | `…UAP-V0.1.10-P14-RUNTIME-SLICE` | 不变 | 历史发布身份 |

```text
sha256（同步后）
  pyproject.toml      = cb078a79739a77a008965f4f95e58655a389a30a022c6aae14f147a6f25abdfe
  config/settings.py  = 4c3bb4519519b4fa359b8ca95172baa8729f8d2b8f8b4b6eaea1530225a5cc1c
  docker-compose.yml  = 2c70e0588216497a7534bc2c823a9990e9ae7009729707d52e9f0d4cb3103326
```

---

## 3. VERSION AUTHORITY DISCREPANCY — 裁决结果

```text
VERSION AUTHORITY DISCREPANCY
Status         = CLOSED
Classification = RELEASE METADATA CONSISTENCY
Target         = 0.1.11
```

处置方式（依 P15 RELEASE GATE §14/§15）：

```text
1. 不再保留 “0.1.0 与 0.1.11 同时作为当前版本” 的歧义状态
2. 三处静态源同步为 0.1.11，仅做 Release Metadata Synchronization：
   · 未升级依赖
   · 未改变 config 语义
   · 未改变 Docker topology
   · 未改变 runtime 行为
3. repository-wide version scan：除历史记录 / 明确标注的历史基线说明外，
   不存在 “current runtime version = 0.1.0” 的歧义
```

```text
本次同步解决的是 Release Metadata consistency，不是新增架构决策。
```

---

## 4. 结论

```text
CURRENT RELEASED VERSION = 0.1.10
NEXT RELEASE CANDIDATE   = 0.1.11
VERSION AUTHORITY        = RESOLVED（release identity + synchronized static metadata）
VERSION AUTHORITY DISCREPANCY = CLOSED / RELEASE METADATA CONSISTENCY
```

