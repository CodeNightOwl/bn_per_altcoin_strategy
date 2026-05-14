# 山寨币涨跌幅监控系统

基于CCXT库的币安山寨币涨跌幅实时监控系统，支持前后端分离架构。

## 技术栈

### 后端
- Python 3.8+
- Flask - Web框架
- Flask-SQLAlchemy - ORM
- CCXT - 加密货币交易所API
- SQLite/MySQL - 数据库

### 前端
- Vue 3 - 前端框架
- Vite - 构建工具
- Element Plus - UI组件库
- Axios - HTTP客户端

## 功能特性

- 实时获取币安交易所所有山寨币数据
- 支持按涨跌幅、成交量、价格等多维度排序
- 极端波动币种监控（可自定义涨跌幅阈值）
- 短期波动检测（1小时内涨跌幅监控，可配置阈值）
- 成交量过滤（默认500万美元以上）
- 统计面板展示市场概况
- 数据库持久化存储
- 支持SQLite和MySQL数据库切换
- 前端热更新开发
- 美观的渐变UI设计

## 项目结构

```
山寨策略/
├── backend/                 # 后端项目
│   ├── app.py              # Flask应用入口
│   ├── config.py           # 配置文件
│   ├── models.py           # 数据库模型
│   ├── routes.py           # API路由
│   ├── binance_service.py  # 币安服务
│   ├── requirements.txt    # Python依赖
│   └── .env                # 环境变量
└── frontend/               # 前端项目
    ├── index.html          # HTML模板
    ├── package.json        # Node依赖
    ├── vite.config.js      # Vite配置
    └── src/
        ├── main.js         # 入口文件
        ├── App.vue         # 根组件
        ├── api/            # API接口
        └── components/     # Vue组件
```

## 快速开始

### 一键启动（Windows）

直接双击运行 `start_all.bat` 即可同时启动前后端服务。

或者分别启动：

1. 启动后端：双击 `start_backend.bat`
2. 启动前端：双击 `start_frontend.bat`

### 手动启动

#### 后端启动

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量（可选）：
编辑 `.env` 文件，根据需要修改配置

5. 启动后端服务：
```bash
python app.py
```

后端将在 `http://localhost:3007` 启动

#### 前端启动

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端将在 `http://localhost:3008` 启动

## 数据库配置

### 使用SQLite（默认）
无需额外配置，系统会自动创建 `crypto_monitor.db` 文件

### 切换到MySQL
1. 修改 `backend/.env` 文件：
```
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=crypto_monitor
```

2. 确保MySQL服务已启动并创建了数据库

## 环境变量配置

系统通过 `backend/.env` 文件进行配置，支持以下主要配置项：

### 服务器配置
- `FLASK_HOST` - 服务器监听地址（默认：0.0.0.0）
- `FLASK_PORT` - 服务器端口（默认：3007）
- `FLASK_DEBUG` - 调试模式（默认：True）

### 数据库配置
- `DB_TYPE` - 数据库类型：sqlite 或 mysql（默认：sqlite）
- `SQLITE_DB_PATH` - SQLite数据库路径（默认：crypto_monitor.db）
- `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE` - MySQL连接参数

### 数据过滤配置
- `MIN_VOLUME_USD` - 最小成交量过滤（默认：5000000美元）
- `MAX_COINS_LIMIT` - 最大币种数量限制（默认：500）
- `EXCLUDE_STABLECOINS` - 是否排除稳定币（默认：True）
- `MAJOR_COINS` - 主流币种列表，将被过滤掉

### 短期波动检测配置
- `SHORT_TERM_CHANGE_THRESHOLD` - 短期涨跌幅阈值（默认：5.0%）
- `SHORT_TERM_TIMEFRAME` - 短期时间范围（默认：1h）
- `ENABLE_SHORT_TERM_DETECTION` - 是否启用短期波动检测（默认：True）

### 币安API配置
- `BINANCE_API_KEY` - 币安API密钥（可选）
- `BINANCE_API_SECRET` - 币安API密钥Secret（可选）
- `BINANCE_ENABLE_RATE_LIMIT` - 是否启用API频率限制（默认：True）

### 其他配置
- `COIN_UPDATE_INTERVAL` - 数据更新间隔秒数（默认：60）
- `AUTO_UPDATE_ENABLED` - 是否自动更新（默认：False）
- `CORS_ENABLED` - 是否启用跨域（默认：True）
- `LOG_LEVEL` - 日志级别（默认：INFO）

详细配置说明请参考 [backend/ENV_CONFIG.md](backend/ENV_CONFIG.md)

## API接口

### 更新币种数据
```
POST /api/coins/update
```

### 获取币种列表
```
GET /api/coins?page=1&per_page=50&sort_by=change_24h&order=desc
```

### 获取涨幅榜
```
GET /api/coins/gainers?limit=20
```

### 获取跌幅榜
```
GET /api/coins/losers?limit=20
```

### 获取极端波动币种
```
GET /api/coins/extreme?threshold=10
```

### 获取短期波动币种
```
GET /api/coins/short-term-movers?threshold=5&volume_threshold=5000000&limit=50
```

### 获取系统配置
```
GET /api/config
```

### 获取统计数据
```
GET /api/stats
```

### 健康检查
```
GET /api/health
```

## 使用说明

1. 首次使用需要点击"更新数据"按钮从币安获取最新数据
2. 主页面"币种监控"包含：
   - 顶部统计面板：显示山寨币总数、平均涨跌幅、上涨/下跌币种数量
   - 中间极端波动区域：左侧显示大涨币种（24H≥10%），右侧显示大跌币种（24H≤-10%）
   - 底部完整列表：所有山寨币的详细数据，支持排序和分页
3. 在"短期波动"页面可以设置涨跌幅阈值和成交量阈值来筛选短期内快速波动的币种
4. 点击币种名称可以查看详细信息
5. 数据会定期更新，也可以手动点击更新按钮

### 短期波动检测功能

- **功能说明**: 检测1小时内涨跌幅超过设定阈值的币种
- **默认设置**: 
  - 涨跌幅阈值: 5%
  - 最小成交量: 500万美元
  - 显示数量: 50个
- **使用场景**: 
  - 发现短期内快速上涨的币种（追涨）
  - 发现短期内快速下跌的币种（抄底）
  - 过滤掉流动性差的小市值币种
- **配置方法**: 在"短期波动"页面顶部调整参数，系统会自动刷新数据

### 极端波动监控

- **功能说明**: 在主页面直接显示24小时内涨跌幅超过10%的币种
- **显示位置**: 主页面中间区域，左右分栏显示
- **左侧**: 大涨币种（24H涨跌幅 ≥10%）
- **右侧**: 大跌币种（24H涨跌幅 ≤-10%）
- **优势**: 无需切换页面，一目了然看到市场极端波动情况

## 注意事项

- 币安API有请求频率限制，建议不要频繁更新数据
- 系统默认过滤掉主流币种（BTC、ETH等），只显示山寨币
- 成交量过滤默认为100万美元以上，可根据需要调整
- 建议在生产环境中使用MySQL数据库以获得更好的性能

## 开发说明

### 后端开发
- 后端使用Flask框架，遵循RESTful API设计
- 所有API路由在 `routes.py` 中定义
- 数据库模型在 `models.py` 中定义
- 币安API交互逻辑在 `binance_service.py` 中

### 前端开发
- 前端使用Vue 3 Composition API
- 所有API调用封装在 `src/api/index.js` 中
- 组件存放在 `src/components/` 目录
- 支持热更新，修改代码后自动刷新

## 许可证

MIT License