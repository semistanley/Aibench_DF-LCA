# Docker 部署指南

## 快速开始

### 方式一：单容器模式（推荐）

同时运行 API 和 Web UI：

```bash
# 构建镜像
docker build -t dflca-benchmark .

# 运行容器
docker run -d \
  --name dflca-benchmark \
  -p 8000:8000 \
  -p 8501:8501 \
  -v $(pwd)/evaluations.db:/app/evaluations.db \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/reports:/app/reports \
  dflca-benchmark
```

或使用 docker-compose：

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式二：分离模式

API 和 Web UI 分别运行在不同的容器中：

```bash
# 启动分离模式
docker-compose --profile separated up -d

# 查看日志
docker-compose logs -f api web

# 停止服务
docker-compose --profile separated down
```

## 访问服务

启动成功后，可以通过以下地址访问：

- **API 服务**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs
- **Web 界面**：http://localhost:8501

## Docker Compose 命令

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f app

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 重新构建
docker-compose build --no-cache

# 查看运行状态
docker-compose ps
```

## 数据持久化

以下目录/文件会被持久化到宿主机：

- `evaluations.db` - SQLite 数据库（评测结果）
- `logs/` - 日志文件
- `reports/` - 生成的报告

## 环境变量

可以通过环境变量配置：

```bash
docker run -d \
  -e JWT_SECRET=your-secret-key \
  -e OPENAI_API_KEY=your-api-key \
  dflca-benchmark
```

或在 `docker-compose.yml` 中配置：

```yaml
environment:
  - JWT_SECRET=your-secret-key
  - OPENAI_API_KEY=your-api-key
```

## 健康检查

容器包含健康检查，可以通过以下命令查看：

```bash
docker ps
# 查看 HEALTH STATUS 列

docker inspect dflca-benchmark | grep -A 10 Health
```

## 故障排除

### 端口被占用

如果 8000 或 8501 端口已被占用，可以修改端口映射：

```yaml
ports:
  - "8001:8000"  # 将宿主机端口改为 8001
  - "8502:8501"  # 将宿主机端口改为 8502
```

### 查看容器日志

```bash
# 查看所有日志
docker-compose logs

# 实时查看日志
docker-compose logs -f

# 查看最后 100 行
docker-compose logs --tail=100
```

### 进入容器调试

```bash
# 进入运行中的容器
docker exec -it dflca-benchmark bash

# 查看进程
ps aux

# 测试 API
curl http://localhost:8000/health
```

### 重建镜像

```bash
# 完全重建（不使用缓存）
docker-compose build --no-cache

# 重新启动
docker-compose up -d
```

## 生产环境建议

1. **使用环境变量文件**：
   ```bash
   docker-compose --env-file .env.production up -d
   ```

2. **配置资源限制**：
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

3. **使用反向代理**（如 Nginx）：
   ```yaml
   nginx:
     image: nginx:alpine
     ports:
       - "80:80"
     volumes:
       - ./nginx.conf:/etc/nginx/nginx.conf
     depends_on:
       - app
   ```

4. **启用 HTTPS**：使用 Let's Encrypt 或类似服务

5. **定期备份数据库**：
   ```bash
   docker exec dflca-benchmark sqlite3 /app/evaluations.db ".backup /app/backup.db"
   ```

## 多环境部署

### 开发环境

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 生产环境

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
