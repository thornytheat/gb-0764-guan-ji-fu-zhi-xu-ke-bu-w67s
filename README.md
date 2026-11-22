# 馆际复制许可簿

文献传递岗据持权馆条款审理复本申请。许可簿对齐旧刊号和馆号，逐日裁决条款，再按规范页段和剩余额度签发，保留订单的原判与撤销流水。

运行 `docker compose up --build` 后访问 `http://localhost:18463/`。本机安装 `requirements.txt` 后可用 `flask --app app.main:create_app run --port 18463` 启动。执行 `pytest -q` 验证。`LICENSE_DB` 指定 SQLite 路径，切换为空文件路径可建立新档案。

从十一月混合来件检查材料采信、刊号机构、许可裁决、覆盖页段和请求勾稽。前五项 API 可用 GET 调样例或用 POST 的 `csv` 字段提交订单文本。进入批次页归卷，再用签发印版生成下载件。每次归卷复算整份来件，年度池占用保存在该次快照内。

[字段与术语](docs/DATA-DICTIONARY.md) · [规则复核表](docs/DEPTH.md)
