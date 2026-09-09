# PaperForge Docker 部署

本文档用于通过 Docker Compose 启动 PaperForge Verified Academic Document Agent。Docker 部署不改变现有 API、Agent pipeline 或前端功能。

## 1. 环境要求

- Docker Engine 24+ 或 Docker Desktop
- Docker Compose v2，使用 `docker compose` 命令
- 建议至少 4 GB 可用内存
- 首次构建需要访问 Docker Hub、PyPI 和 npm registry

Windows 和 macOS 可安装 [Docker Desktop](https://docs.docker.com/desktop/)；Linux 可按 [Docker Engine 官方指南](https://docs.docker.com/engine/install/) 安装 Docker Engine 和 Compose 插件。

安装后检查：

```powershell
docker --version
docker compose version
```

## 2. 环境变量

在项目根目录执行：

```powershell
Copy-Item .env.example .env
```

然后按需编辑根目录 `.env`，至少替换 `POSTGRES_PASSWORD` 和 `JWT_SECRET_KEY`。密钥只会作为容器运行时环境变量传入；`.env` 已从 Git 和 Docker build context 中排除。`paper-ai/backend/.env.example` 仍用于非 Docker 本地启动。

没有 API Key 时，可以保持 `DEEPSEEK_API_KEY` 为空并使用 `local` 模式。

前端默认请求 `http://localhost:8000`。如果使用其他地址，必须在构建前设置：

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://your-server:8000"
```

`NEXT_PUBLIC_API_BASE_URL` 是 Next.js 公开构建变量，会进入浏览器端产物。修改后需要重新构建前端镜像。

## 3. 一键启动

在项目根目录执行：

```powershell
docker compose up --build
```

后台启动：

```powershell
docker compose up --build -d
```

查看状态和日志：

```powershell
docker compose ps
docker compose logs -f
```

停止服务：

```powershell
docker compose down
```

## 4. 访问地址

- 前端：<http://localhost:3000>
- 后端健康检查：<http://localhost:8000/health>
- FastAPI 接口文档：<http://localhost:8000/docs>

## 5. 配置检查

为避免将环境变量展开到终端，使用静默校验：

```powershell
docker compose config --quiet
```

重新构建：

```powershell
docker compose build
```

## 6. 常见问题

### Compose 提示找不到 `.env`

先复制 `paper-ai/backend/.env.example` 为 `paper-ai/backend/.env`。不要将真实密钥提交到 Git。

### 修改 API 地址后前端仍请求旧地址

`NEXT_PUBLIC_API_BASE_URL` 在 `npm run build` 时写入前端产物。设置新值后执行：

```powershell
docker compose build --no-cache frontend
docker compose up -d
```

### 容器无法访问宿主机代理

如果 `API_PROXY_URL` 使用 `127.0.0.1`，它指向的是后端容器自身。Docker Desktop 可尝试使用 `host.docker.internal`；Linux 需根据宿主机网关和防火墙配置代理地址。

### 服务器 IP 或域名访问出现 CORS 错误

后端默认 CORS 白名单包含 `localhost:3000` 和 `127.0.0.1:3000`。服务器 IP 或域名部署时，在 `paper-ai/backend/.env` 设置逗号分隔的 `CORS_ORIGINS`，例如 `CORS_ORIGINS=https://paperforge.example.com`，然后重启后端容器。

### 输出文件在删除容器后丢失

当前 Compose 保持最小部署配置，没有默认挂载持久化卷。上传、输出和 task state 位于容器可写层，删除容器时会一并删除。
