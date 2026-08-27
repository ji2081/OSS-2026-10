# Third Party Notices

이 프로젝트는 아래 오픈소스 소프트웨어를 사용합니다. 각 소프트웨어의 저작권과 라이선스는 해당 프로젝트에 귀속됩니다.

본 프로젝트가 직접 작성한 코드는 [MIT License](./LICENSE)를 따릅니다.

## Backend (`backend/requirements.txt`)

| 라이브러리 | 버전 | 라이선스 | 저장소 |
|---|---|---|---|
| fastapi | 0.135.3 | MIT | https://github.com/fastapi/fastapi |
| uvicorn | 0.44.0 | BSD-3-Clause | https://github.com/encode/uvicorn |
| starlette | 1.0.0 | BSD-3-Clause | https://github.com/encode/starlette |
| sqlalchemy | 2.0.49 | MIT | https://github.com/sqlalchemy/sqlalchemy |
| psycopg2-binary | 2.9.11 | LGPL-3.0-or-later (with exceptions) | https://github.com/psycopg/psycopg2 |
| alembic | 1.18.4 | MIT | https://github.com/sqlalchemy/alembic |
| pydantic | 2.12.5 | MIT | https://github.com/pydantic/pydantic |
| pydantic-settings | 2.0.0 | MIT | https://github.com/pydantic/pydantic-settings |
| python-dotenv | 1.2.2 | BSD-3-Clause | https://github.com/theskumar/python-dotenv |
| python-jose | 3.5.0 | MIT | https://github.com/mpdavis/python-jose |
| cryptography | 48.0.0 | Apache-2.0 OR BSD-3-Clause | https://github.com/pyca/cryptography |
| anyio | 4.13.0 | MIT | https://github.com/agronholm/anyio |
| python-multipart | 0.0.27 | Apache-2.0 | https://github.com/Kludex/python-multipart |
| httpx | 0.28.0 | BSD-3-Clause | https://github.com/encode/httpx |
| requests | 2.32.3 | Apache-2.0 | https://github.com/psf/requests |
| pytest | 8.3.4 | MIT | https://github.com/pytest-dev/pytest |

## ETL (`etl/requirements.txt`)

| 라이브러리 | 버전 | 라이선스 | 저장소 |
|---|---|---|---|
| httpx | - | BSD-3-Clause | https://github.com/encode/httpx |
| pydantic[email] | - | MIT | https://github.com/pydantic/pydantic |
| sqlalchemy[asyncio] | - | MIT | https://github.com/sqlalchemy/sqlalchemy |
| asyncpg | - | Apache-2.0 | https://github.com/MagicStack/asyncpg |
| python-dotenv | - | BSD-3-Clause | https://github.com/theskumar/python-dotenv |
| openai | - | Apache-2.0 | https://github.com/openai/openai-python |

## Frontend (`frontend/package.json`)

| 라이브러리 | 버전 | 라이선스 | 저장소 |
|---|---|---|---|
| react | 19.2.4 | MIT | https://github.com/facebook/react |
| react-dom | 19.2.4 | MIT | https://github.com/facebook/react |
| react-router-dom | 7.14.0 | MIT | https://github.com/remix-run/react-router |
| react-scripts | 5.0.1 | MIT | https://github.com/facebook/create-react-app |
| reactflow | 11.11.4 | MIT | https://github.com/xyflow/xyflow |
| d3 | 7.9.0 | ISC | https://github.com/d3/d3 |
| zustand | 5.0.12 | MIT | https://github.com/pmndrs/zustand |
| @supabase/supabase-js | 2.108.0 | MIT | https://github.com/supabase/supabase-js |
| web-vitals | 2.1.4 | Apache-2.0 | https://github.com/GoogleChrome/web-vitals |
| @testing-library/react | 16.3.2 | MIT | https://github.com/testing-library/react-testing-library |
| @testing-library/jest-dom | 6.9.1 | MIT | https://github.com/testing-library/jest-dom |
| @testing-library/dom | 10.4.1 | MIT | https://github.com/testing-library/dom-testing-library |
| @testing-library/user-event | 13.5.0 | MIT | https://github.com/testing-library/user-event |

## 라이선스 관련 참고

- `psycopg2-binary`는 LGPL-3.0-or-later(예외 조항 포함) 라이선스입니다. 본 프로젝트는 해당 라이브러리를 수정하지 않고 표준 DB-API 인터페이스로 호출하여 사용하므로 MIT 배포와 충돌하지 않습니다.
- `openai` 패키지는 ETL 파이프라인에서만 사용하며, 서비스 실행 경로에는 포함되지 않습니다. 자세한 내용은 [`etl/README.md`](./etl/README.md)를 참고하십시오.
- 그 외 모든 의존성은 MIT, BSD-3-Clause, Apache-2.0, ISC 등 허용적(permissive) 라이선스입니다.
