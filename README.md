### Command

```sh
# app 追加
$ mkdir web
$ docker compose run --rm backend uv run django-admin startapp web web
$ docker compose run --rm backend uv run ruff check . --fix
$ docker compose run --rm backend uv run ruff format .
# djlint によるフォーマット
$ docker compose run --rm backend uv run djlint templates/*/*.html --extension=html.j2 --reformat

http://127.0.0.1:8000/web/

# セキュリティチェック
$ docker compose run --rm backend uv tool run djcheckup http://host.docker.internal:8000/web/
```

### Devin

- [Devin's Machine](https://app.devin.ai/workspace) でリポジトリ追加

#### 1.Git Pull
- そのまま

#### 2.Configure Secrets
```sh
# 環境変数用のファイル作成
$ touch .envrc
$ cp .envrc.example .envrc
$ direnv allow
```

- ローカル用
```sh
$ brew install direnv
```
#### 4.Maintain Dependencies
```sh
$ docker compose up -d

# コンテナ作り直し
$ source ./remake_container.sh
```

#### 5.SetUp Lint
```sh
$ docker compose run --rm backend uv run ruff check .

# 参考 フォーマット
$ docker compose run --rm backend uv run ruff format .

# mypy による型ヒントチェック
$ docker compose run --rm backend uv run mypy .

$ docker compose run --rm backend uv run djlint templates/*/*.html --extension=html.j2 --lint
```

#### 6.SetUp Tests
- no tests ran in 0.00s だと Devin の Verify が通らないっぽい
```sh
$ docker compose run --rm backend uv run pytest
```

### 7.Setup Local App

```sh
$ http://localhost:8000/ がアプリケーションのURL
```

#### 8.Additional Notes
- 必ず日本語で回答してください
- Python, Django を利用する
- データベースは Postgres
- テストは pytest を利用する
を入力

