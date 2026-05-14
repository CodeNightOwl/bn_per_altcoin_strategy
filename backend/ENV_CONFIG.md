# 环境变量配置说明

本文档详细说明了backend/.env文件中各个配置项的含义和使用方法。

## 服务器配置

### FLASK_HOST
- **说明**: Flask服务器监听的地址
- **默认值**: `0.0.0.0`
- **可选值**: 
  - `0.0.0.0` - 监听所有网络接口
  - `127.0.0.1` - 仅本地访问
  - 具体IP地址 - 监听指定IP

### FLASK_PORT
- **说明**: Flask服务器监听的端口
- **默认值**: `3007`
- **注意**: 确保端口未被占用

### FLASK_DEBUG
- **说明**: 是否启用调试模式
- **默认值**: `True`
- **可选值**: `True` 或 `False`
- **说明**: 
  - `True` - 开发模式，显示详细错误信息，支持热重载
  - `False` - 生产模式，隐藏错误详情

## 数据库配置

### DB_TYPE
- **说明**: 数据库类型
- **默认值**: `sqlite`
- **可选值**: `sqlite` 或 `mysql`
- **切换方法**: 修改此值即可切换数据库

### SQLite配置

#### SQLITE_DB_PATH
- **说明**: SQLite数据库文件路径
- **默认值**: `crypto_monitor.db`
- **说明**: 相对路径或绝对路径均可

### MySQL配置

#### MYSQL_HOST
- **说明**: MySQL服务器地址
- **默认值**: `localhost`
- **示例**: `192.168.1.100` 或 `db.example.com`

#### MYSQL_PORT
- **说明**: MySQL服务器端口
- **默认值**: `3306`

#### MYSQL_USER
- **说明**: MySQL用户名
- **默认值**: `root`
- **注意**: 确保用户有足够的权限

#### MYSQL_PASSWORD
- **说明**: MySQL密码
- **默认值**: (空)
- **安全**: 生产环境请设置强密码

#### MYSQL_DATABASE
- **说明**: 数据库名称
- **默认值**: `crypto_monitor`
- **注意**: 需要提前创建数据库

#### MYSQL_CHARSET
- **说明**: 数据库字符集
- **默认值**: `utf8mb4`
- **说明**: 支持emoji等特殊字符

## 币安API配置

### BINANCE_API_KEY
- **说明**: 币安API密钥
- **默认值**: (空)
- **获取方式**: 登录币安账户 -> API管理
- **注意**: 可选配置，不填写也能获取公开数据

### BINANCE_API_SECRET
- **说明**: 币安API密钥对应的Secret
- **默认值**: (空)
- **注意**: 与API_KEY配合使用

### BINANCE_ENABLE_RATE_LIMIT
- **说明**: 是否启用API请求频率限制
- **默认值**: `True`
- **说明**: 
  - `True` - 遵循币安API频率限制，避免被封禁
  - `False` - 不限制请求频率（风险较高）

## 数据过滤配置

### MIN_VOLUME_USD
- **说明**: 最小24小时成交量过滤阈值（美元）
- **默认值**: `1000000` (100万美元)
- **说明**: 只显示成交量大于此值的币种
- **调整建议**: 
  - 降低此值可显示更多小市值币种
  - 提高此值可过滤掉流动性差的币种

### MAX_COINS_LIMIT
- **说明**: 最大币种数量限制
- **默认值**: `500`
- **说明**: 限制返回的币种总数，避免数据过多

### EXCLUDE_STABLECOINS
- **说明**: 是否排除稳定币
- **默认值**: `True`
- **可选值**: `True` 或 `False`
- **说明**: 稳定币通常波动很小，排除后更关注有波动潜力的币种

### MAJOR_COINS
- **说明**: 主流币种列表（将被过滤掉）
- **默认值**: `BTC,ETH,BNB,USDT,USDC,BUSD,DAI,XRP,ADA,DOGE,SOL,DOT,MATIC,SHIB,LTC,TRX,AVAX,LINK,ATOM,UNI`
- **格式**: 逗号分隔的币种代码
- **说明**: 这些币种不会被显示在山寨币列表中
- **自定义**: 可以根据需要添加或删除币种

## 更新间隔配置

### COIN_UPDATE_INTERVAL
- **说明**: 数据更新间隔（秒）
- **默认值**: `60`
- **说明**: 自动更新数据的时间间隔
- **注意**: 币安API有频率限制，不建议设置过小

### AUTO_UPDATE_ENABLED
- **说明**: 是否启用自动更新
- **默认值**: `False`
- **可选值**: `True` 或 `False`
- **说明**: 
  - `True` - 后台自动定时更新数据
  - `False` - 需要手动点击更新按钮

## CORS配置

### CORS_ENABLED
- **说明**: 是否启用跨域资源共享
- **默认值**: `True`
- **可选值**: `True` 或 `False`
- **说明**: 前后端分离时需要启用

### CORS_ORIGINS
- **说明**: 允许的跨域来源
- **默认值**: `*` (允许所有来源)
- **示例**: 
  - `http://localhost:3008` - 只允许本地开发服务器
  - `https://example.com` - 只允许指定域名
  - `http://localhost:3008,https://example.com` - 允许多个来源

## 日志配置

### LOG_LEVEL
- **说明**: 日志级别
- **默认值**: `INFO`
- **可选值**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **说明**: 
  - `DEBUG` - 最详细，包含调试信息
  - `INFO` - 一般信息
  - `WARNING` - 警告信息
  - `ERROR` - 错误信息
  - `CRITICAL` - 严重错误

### LOG_FILE
- **说明**: 日志文件路径
- **默认值**: `logs/app.log`
- **说明**: 相对路径或绝对路径均可

## 分页配置

### DEFAULT_PAGE_SIZE
- **说明**: 默认每页显示数量
- **默认值**: `50`
- **说明**: 列表页面默认显示的币种数量

### MAX_PAGE_SIZE
- **说明**: 每页最大显示数量
- **默认值**: `200`
- **说明**: 限制用户一次请求的最大数据量

## 配置示例

### 开发环境配置
```env
FLASK_DEBUG=True
DB_TYPE=sqlite
MIN_VOLUME_USD=1000000
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3008
```

### 生产环境配置
```env
FLASK_DEBUG=False
DB_TYPE=mysql
MYSQL_HOST=your-db-host.com
MYSQL_USER=your_user
MYSQL_PASSWORD=your_strong_password
MYSQL_DATABASE=crypto_monitor_prod
MIN_VOLUME_USD=5000000
LOG_LEVEL=WARNING
CORS_ORIGINS=https://your-domain.com
```

### 高频监控配置
```env
MIN_VOLUME_USD=500000
MAX_COINS_LIMIT=1000
COIN_UPDATE_INTERVAL=30
AUTO_UPDATE_ENABLED=True
```

## 注意事项

1. **敏感信息保护**: 
   - 不要将包含真实密码的.env文件提交到版本控制
   - 使用.env.example作为模板
   - 生产环境使用环境变量或密钥管理服务

2. **性能优化**:
   - 根据服务器性能调整MAX_COINS_LIMIT
   - 合理设置COIN_UPDATE_INTERVAL，避免API限流
   - 生产环境建议使用MySQL而非SQLite

3. **安全性**:
   - 生产环境关闭FLASK_DEBUG
   - 限制CORS_ORIGINS为具体域名
   - 设置强密码和适当的LOG_LEVEL

4. **数据过滤**:
   - 根据投资策略调整MIN_VOLUME_USD
   - 定期更新MAJOR_COINS列表
   - 考虑是否需要排除稳定币

## 故障排查

### 数据库连接失败
- 检查DB_TYPE设置是否正确
- 验证MySQL连接参数
- 确保数据库服务已启动

### API请求失败
- 检查BINANCE_ENABLE_RATE_LIMIT设置
- 验证API_KEY和API_SECRET
- 查看日志文件获取详细错误信息

### 前端无法访问后端
- 检查CORS_ENABLED是否为True
- 验证CORS_ORIGINS设置
- 确认FLASK_HOST和FLASK_PORT配置正确

### 数据更新不及时
- 检查COIN_UPDATE_INTERVAL设置
- 启用AUTO_UPDATE_ENABLED
- 查看日志确认更新是否执行