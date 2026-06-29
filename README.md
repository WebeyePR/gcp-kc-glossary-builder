# Google Knowledge Catalog 术语自动化引擎 (GCP KC Glossary Builder)

> **一句话钩子**：专治大模型 Text-to-SQL 的“业务名词幻觉”。将散落的非结构化业务文档自动蒸馏为 Google Dataplex 中结构化的数据字典，并建立从术语到 BigQuery 物理字段的双向血缘绑定。

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-blue.svg)](https://github.com/WebeyePR/gcp-kc-glossary-builder) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 你什么时候需要它？

1. **RAG / Text-to-SQL 落地卡壳**：大模型把“5水门店”理解成了“5个卖水的店”，导致生成的 SQL 完全跑错。你需要把真正的业务逻辑喂给 AI 的检索底座。
2. **人工整理数据字典太痛苦**：业务侧写了一堆 PRD 和 Wiki，数据开发每天要手工一条条往 Google Knowledge Catalog 里录入分类、名称、公式，还容易遗漏。
3. **指标和物理表脱节**：字典是字典，数仓是数仓。看字典不知道去哪查数，查数时看字段名不知道业务含义。

## 📦 它会交付什么？

1. **一份高密度的 JSON 知识图谱**：从一堆烂文档中提取出标准化的 JSON，包含：`分类、名称、定义、计算逻辑、关联表、关联列、同义词、责任人、数据密级、生命周期`。
2. **Dataplex 的自动化注入结果**：自动生成的分类目录与术语树，且支持异步导入。
3. **BigQuery 的双向列级切面 (Column-Level Aspects)**：在数据仓库最底层的物理列上，直接挂载业务定义与 SQL 公式。看表即看文档。

## 🚀 快速开始

**一键安装 (作为 Agent Skill 注入)：**
本套件完美兼容开放智能体技能生态，你可以在任何支持 `npx skills` 的终端直接安装：
```bash
npx skills add WebeyePR/gcp-kc-glossary-builder -g -y
```

**作为本地自动化工具链独立使用：**
```bash
git clone git@github.com:WebeyePR/gcp-kc-glossary-builder.git
cd gcp-kc-glossary-builder
pip install -r requirements.txt
```

## 💬 触发方式

把这些话发给安装了本 Skill 的 AI Agent：
- *"帮我把这份 PRD 提取成业务术语表 JSON。"*
- *"执行 glossary builder，帮我把提取好的术语深度绑定到 `retail_dwh` 数据集。"*
- *"把 `my-gcp-project` 下的 `retail-glossary` 全清空，重置一下字典。"*
- *"把这段文档里的业务指标补充到我的术语表记忆里。"*

## 💡 示例

更多交互示例请参考 [examples/test-prompts.md](examples/test-prompts.md)。

## 🆚 它和同类工具/手写脚本有什么不同？

| 维度 | 普通正则/爬虫脚本 | 通用 LLM 对话 | GCP KC Glossary Builder (本工具) |
|---|---|---|---|
| **上下文限制** | 无法理解自然语言 | 超长文档会被截断或遗忘 | **Map-Reduce 分块提取**，全局内存去重消歧 |
| **反幻觉设计** | 无 | 生成发散的文本 | **强约束结构化**，逻辑扁平化压入 Description |
| **GCP 深度对接** | 需要自己查 API 文档 | 容易在 LRO 异步操作上失败 | 内置**健壮重试与反向 BigQuery 列级切面绑定** |
| **清理机制** | 只能手动在网页点 | 经常报 `400 Failed Precondition` | 提供原生**安全级联删除**脚本 |

## 🛡️ 安全边界

- **不会乱覆盖已有的手动定义**：实体对齐阶段采用软合并，不会粗暴覆盖更高质量的 SQL 公式。
- **不会私自读取非授权的 GCP 项目**：所有底层脚本需要你显式传入 `--project_id` 和 `--glossary_id`，并依赖你本地的 ADC (Application Default Credentials)。
- **操作前可拦截**：Agent 会先将提纯的 JSON 打印成面板或写在本地，明确询问你 *"是否继续执行导入?"*，不会背着你偷偷写生产库。

## 📁 文件结构

- `SKILL.md`: 给 AI Agent 看的技能执行全流路（Map-Reduce、Schema 要求、指令）。
- `scripts/`: 给 AI 和你执行 GCP 操作的物理工具箱：
  - `import_glossary.py`: 负责异步写入 KC 术语。
  - `bind_aspects.py`: 负责建立实体链接与双向列级切面 (Column-Level Aspects)。
  - `delete_glossary.py`: 负责一键清理，解决级联依赖报错。
- `examples/`: 存放用户可直接复制使用的触发样例 (`test-prompts.md`)。

## 📄 许可协议 (License)
本项目基于 MIT 协议开源 - 详情请参阅 [LICENSE](LICENSE) 文件。
