MeetingPro

회의록을 입력하면 AI가 담당자별 할 일을 자동으로 추출하고, 완료율까지 추적하는 B2B SaaS 서비스

사용 기술
- Python, Flask
- SQLite (Flask-SQLAlchemy)
- OpenAI API (gpt-4o-mini)
- HTML/CSS

주요 기능
- 대표/직원 역할 분리 로그인
- 회의록 입력 → AI 담당자별 액션 아이템 자동 추출
- 직원 계정과 자동 매칭 (user_id 기반)
- 완료/미완료 체크
- 완료율 랭킹 대시보드
- 회의 기록 히스토리

역할
- **대표**: 회의록 입력, 전체 할 일 현황, 완료율 랭킹 확인
- **직원**: 본인 할 일만 확인, 완료 체크

실행 방법
1. 필요한 라이브러리 설치
pip install flask flask-sqlalchemy openai werkzeug

2. OpenAI API 키 환경변수 설정
export OPENAI_API_KEY="your-api-key"

3. 실행
python3 app.py

4. 브라우저에서 접속
http://127.0.0.1:5000