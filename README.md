# 🚀 OSS-2026-10 프로젝트

원활한 진행을 위해 아래 세팅 방법과 협업 규칙을 반드시 확인해 주세요!

---

## 🛠️ 1. 내 컴퓨터 환경 세팅하기

### 공통 
1. **코드 내려받기:** `git pull origin main` (최신 상태 유지)
2. **DB 실행:** 최상위 폴더에서 `.env` 생성 후 `docker-compose up -d`

### 🐍 백엔드 (Backend)
1. `cd backend` 이동
2. 가상환경 활성화: `source venv/Scripts/activate` (Windows 기준)
3. 라이브러리 설치: `pip install -r requirements.txt`
4. 서버 실행: `uvicorn main:app --reload`

### ⚛️ 프론트엔드 (Frontend)
1. `cd frontend` 이동
2. 라이브러리 설치: `npm install`
3. 서버 실행: `npm start`

---

## 🌿 2. Git 브랜치(Branch) 규칙

`main` 브랜치를 직접 수정하지 않고, 각자의 작업용 가지를 만듭니다.

* **브랜치 생성:** `feature/기능이름` (예: `feature/login-ui`)
* **작업 시작 전 필수 순서:**
  ```bash
  git checkout main
  git pull
  git checkout -b feature/기능이름

---

## 🤝 3. 작업 완료 후 코드 합치기 (PR 규칙)
1. 내 브랜치에 푸시: git push origin feature/기능이름
2. Pull Request (PR) 생성: 깃허브 상단 Pull Requests 탭에서 생성
3. 병합(Merge): 팀원 리뷰 및 승인 후, 최종 병합.

---

## 📚 4. 상세 컨벤션 (Conventions)
상세한 커밋 메시지 및 코드 스타일 규칙은 아래 노션을 참고해 주세요!

**📘 Git & 커밋 메시지 컨벤션 (Notion)**
https://www.notion.so/Git-Commit-Message-Convention-32642591390981bc9c9eef2530525d28?source=copy_link

**📙 코드 컨벤션 가이드 (Notion)**
https://www.notion.so/Code-Convention-3264259139098179b7aed263bd251104?source=copy_link
