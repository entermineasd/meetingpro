from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "meetingpro_secret_2026"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meetingpro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), default='employee')
    company = db.Column(db.String(100), nullable=False)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    company = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    person = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    task = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.String(50))
    completed = db.Column(db.Boolean, default=False)
    company = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

STYLE = """
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; color: #1a1a2e; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 220px; background: #0f172a; display: flex; flex-direction: column; padding: 20px 0; flex-shrink: 0; position: fixed; height: 100vh; }
    .sidebar-logo { color: white; font-size: 15px; font-weight: 600; padding: 0 20px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .sidebar-logo span { font-size: 11px; color: #94a3b8; display: block; margin-top: 2px; font-weight: 400; }
    .sidebar-menu { padding: 16px 12px; flex: 1; }
    .menu-label { font-size: 10px; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; padding: 0 8px; margin-bottom: 8px; margin-top: 16px; }
    .menu-item { display: flex; align-items: center; gap: 10px; padding: 9px 10px; border-radius: 8px; color: #94a3b8; font-size: 13px; cursor: pointer; margin-bottom: 2px; text-decoration: none; }
    .menu-item:hover { background: rgba(255,255,255,0.08); color: white; }
    .menu-item.active { background: rgba(255,255,255,0.12); color: white; }
    .main { flex: 1; margin-left: 220px; }
    .topbar { background: white; border-bottom: 1px solid #e5e7eb; padding: 14px 28px; display: flex; align-items: center; justify-content: space-between; }
    .topbar h1 { font-size: 16px; font-weight: 600; }
    .topbar p { font-size: 12px; color: #6b7280; }
    .topbar-user { font-size: 13px; color: #6b7280; }
    .content { padding: 28px; }
    .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
    .stat-box { background: white; border-radius: 10px; padding: 16px; border: 1px solid #e5e7eb; }
    .stat-num { font-size: 26px; font-weight: 700; }
    .stat-label { font-size: 12px; color: #6b7280; margin-top: 2px; }
    .stat-num.green { color: #10b981; }
    .stat-num.red { color: #ef4444; }
    .stat-num.blue { color: #3b82f6; }
    .card { background: white; border-radius: 10px; padding: 22px; border: 1px solid #e5e7eb; margin-bottom: 20px; }
    .card h2 { font-size: 14px; font-weight: 600; margin-bottom: 14px; }
    textarea { width: 100%; height: 180px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; font-size: 13px; resize: vertical; outline: none; line-height: 1.6; font-family: inherit; }
    textarea:focus { border-color: #0f172a; }
    input[type=text], input[type=password] { width: 100%; padding: 9px 12px; border: 1px solid #e5e7eb; border-radius: 8px; font-size: 13px; outline: none; font-family: inherit; }
    input[type=text]:focus, input[type=password]:focus { border-color: #0f172a; }
    select { width: 100%; padding: 9px 12px; border: 1px solid #e5e7eb; border-radius: 8px; font-size: 13px; outline: none; font-family: inherit; }
    .btn { padding: 9px 22px; background: #0f172a; color: white; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; }
    .btn:hover { background: #1e293b; }
    .btn-green { background: #10b981; }
    .btn-green:hover { background: #059669; }
    .section-title { font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 10px; }
    .summary-box { background: #f8fafc; border-left: 3px solid #0f172a; padding: 12px 16px; border-radius: 0 6px 6px 0; font-size: 13px; line-height: 1.8; }
    .task-item { background: #f8fafc; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; border: 1px solid #e5e7eb; }
    .task-item.completed { opacity: 0.6; }
    .person-badge { background: #0f172a; color: white; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600; white-space: nowrap; }
    .unmatched-badge { background: #fee2e2; color: #991b1b; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600; white-space: nowrap; }
    .task-text { font-size: 13px; flex: 1; }
    .task-text.done { text-decoration: line-through; color: #9ca3af; }
    .deadline-badge { background: #fef3c7; color: #92400e; padding: 3px 7px; border-radius: 4px; font-size: 11px; white-space: nowrap; }
    .complete-btn { padding: 4px 10px; border-radius: 6px; font-size: 11px; cursor: pointer; border: none; }
    .complete-btn.done { background: #d1fae5; color: #065f46; }
    .complete-btn.undone { background: #e5e7eb; color: #374151; }
    .ranking-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; background: #f8fafc; border: 1px solid #e5e7eb; }
    .rank-num { font-size: 18px; font-weight: 700; width: 28px; color: #0f172a; }
    .rank-name { flex: 1; font-size: 14px; font-weight: 500; }
    .rank-bar-wrap { width: 120px; height: 6px; background: #e5e7eb; border-radius: 3px; }
    .rank-bar { height: 6px; background: #0f172a; border-radius: 3px; }
    .rank-pct { font-size: 13px; font-weight: 600; min-width: 36px; text-align: right; }
    .loading { color: #888; font-size: 13px; margin-top: 12px; }
    .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #e5e7eb; border-top: 2px solid #0f172a; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .auth-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f5f7fa; }
    .auth-card { background: white; border-radius: 12px; padding: 32px; width: 400px; border: 1px solid #e5e7eb; }
    .auth-card h2 { font-size: 20px; font-weight: 700; margin-bottom: 20px; }
    .form-group { margin-bottom: 14px; }
    .form-group label { font-size: 12px; font-weight: 600; color: #374151; display: block; margin-bottom: 5px; }
    .error { color: #ef4444; font-size: 12px; margin-top: 8px; }
    .link { color: #0f172a; font-size: 13px; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .meeting-item { padding: 14px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 10px; cursor: pointer; }
    .meeting-item:hover { border-color: #0f172a; background: #f8fafc; }
    .meeting-title { font-size: 14px; font-weight: 600; }
    .meeting-date { font-size: 12px; color: #6b7280; margin-top: 3px; }
    .meeting-stats { font-size: 12px; color: #6b7280; margin-top: 5px; }
</style>
"""

def get_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def sidebar_html(user, active):
    if user.role == 'admin':
        items = f"""
        <div class='menu-label'>관리자</div>
        <a href='/dashboard' class='menu-item {"active" if active=="dashboard" else ""}'>📊 대시보드</a>
        <a href='/new-meeting' class='menu-item {"active" if active=="new-meeting" else ""}'>📝 새 회의록</a>
        <a href='/all-tasks' class='menu-item {"active" if active=="all-tasks" else ""}'>✅ 전체 할 일</a>
        """
    else:
        items = f"""
        <div class='menu-label'>메뉴</div>
        <a href='/my-tasks' class='menu-item {"active" if active=="my-tasks" else ""}'>✅ 내 할 일</a>
        """
    return f"""
    <div class='sidebar'>
        <div class='sidebar-logo'>📋 MeetingPro<span>{user.company}</span></div>
        <div class='sidebar-menu'>
            {items}
            <div class='menu-label'>계정</div>
            <a href='/logout' class='menu-item'>🚪 로그아웃</a>
        </div>
    </div>
    """

def task_toggle_script():
    return """
    <script>
        async function toggleTask(id) {
            const res = await fetch('/toggle-task/' + id, {method: 'POST'});
            const data = await res.json();
            const item = document.getElementById('task-' + id);
            const btn = item.querySelector('.complete-btn');
            const text = item.querySelector('.task-text');
            if (data.completed) {
                item.classList.add('completed');
                btn.className = 'complete-btn done';
                btn.textContent = '완료';
                text.classList.add('done');
            } else {
                item.classList.remove('completed');
                btn.className = 'complete-btn undone';
                btn.textContent = '미완료';
                text.classList.remove('done');
            }
        }
    </script>
    """

def render_tasks(tasks):
    html = ""
    for t in tasks:
        done_class = 'done' if t.completed else 'undone'
        done_text = '완료' if t.completed else '미완료'
        text_class = 'done' if t.completed else ''
        badge = f"<span class='person-badge'>{t.person}</span>" if t.user_id else f"<span class='unmatched-badge'>{t.person} ⚠️미매칭</span>"
        html += f"""
        <div class='task-item {"completed" if t.completed else ""}' id='task-{t.id}'>
            {badge}
            <span class='task-text {text_class}'>{t.task}</span>
            {f"<span class='deadline-badge'>⏰ {t.deadline}</span>" if t.deadline else ''}
            <button class='complete-btn {done_class}' onclick='toggleTask({t.id})'>{done_text}</button>
        </div>"""
    return html

@app.route('/')
def index():
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    if user.role == 'admin':
        return redirect(url_for('dashboard'))
    return redirect(url_for('my_tasks'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        error = "아이디 또는 비밀번호가 틀렸어요."
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>MeetingPro</title>{STYLE}</head>
    <body>
    <div class='auth-wrap'>
        <div class='auth-card'>
            <h2>📋 MeetingPro</h2>
            <form method='POST'>
                <div class='form-group'><label>아이디</label><input type='text' name='username' required placeholder='아이디 입력'></div>
                <div class='form-group'><label>비밀번호</label><input type='password' name='password' required placeholder='비밀번호 입력'></div>
                <button type='submit' class='btn' style='width:100%;margin-top:6px;'>로그인</button>
            </form>
            <p style='margin-top:14px;text-align:center;'><a href='/register' class='link'>계정이 없나요? 회원가입</a></p>
            <div class='error'>{error}</div>
        </div>
    </div>
    </body></html>
    """)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        company = request.form['company']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            error = "이미 존재하는 아이디예요."
        else:
            db.session.add(User(username=username, password=generate_password_hash(password), name=name, company=company, role=role))
            db.session.commit()
            return redirect(url_for('login'))
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>회원가입</title>{STYLE}</head>
    <body>
    <div class='auth-wrap'>
        <div class='auth-card'>
            <h2>📋 회원가입</h2>
            <form method='POST'>
                <div class='form-group'><label>회사명</label><input type='text' name='company' required placeholder='회사명 입력'></div>
                <div class='form-group'><label>이름</label><input type='text' name='name' required placeholder='본인 이름'></div>
                <div class='form-group'><label>역할</label>
                    <select name='role'><option value='admin'>대표/관리자</option><option value='employee'>직원</option></select>
                </div>
                <div class='form-group'><label>아이디</label><input type='text' name='username' required placeholder='아이디 입력'></div>
                <div class='form-group'><label>비밀번호</label><input type='password' name='password' required placeholder='비밀번호 입력'></div>
                <button type='submit' class='btn' style='width:100%;margin-top:6px;'>가입하기</button>
            </form>
            <p style='margin-top:14px;text-align:center;'><a href='/login' class='link'>이미 계정이 있나요? 로그인</a></p>
            <div class='error'>{error}</div>
        </div>
    </div>
    </body></html>
    """)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    user = get_user()
    if not user or user.role != 'admin':
        return redirect(url_for('login'))
    tasks = Task.query.filter_by(company=user.company).all()
    meetings = Meeting.query.filter_by(company=user.company).order_by(Meeting.created_at.desc()).limit(5).all()
    total = len(tasks)
    completed = len([t for t in tasks if t.completed])
    persons = {}
    for t in tasks:
        if t.person not in persons:
            persons[t.person] = {'total': 0, 'done': 0}
        persons[t.person]['total'] += 1
        if t.completed:
            persons[t.person]['done'] += 1
    ranking = sorted(persons.items(), key=lambda x: (x[1]['done']/x[1]['total'] if x[1]['total'] > 0 else 0), reverse=True)
    ranking_html = ""
    for i, (name, data) in enumerate(ranking):
        pct = round(data['done'] / data['total'] * 100) if data['total'] > 0 else 0
        ranking_html += f"""
        <div class='ranking-item'>
            <div class='rank-num'>{i+1}</div>
            <div class='rank-name'>{name}</div>
            <div class='rank-bar-wrap'><div class='rank-bar' style='width:{pct}%'></div></div>
            <div class='rank-pct'>{pct}%</div>
        </div>"""
    meetings_html = ""
    for m in meetings:
        t_count = Task.query.filter_by(meeting_id=m.id).count()
        d_count = Task.query.filter_by(meeting_id=m.id, completed=True).count()
        meetings_html += f"""
        <div class='meeting-item' onclick="location.href='/meeting/{m.id}'">
            <div class='meeting-title'>{m.title}</div>
            <div class='meeting-date'>{m.created_at.strftime('%Y-%m-%d %H:%M')}</div>
            <div class='meeting-stats'>액션 아이템 {t_count}개 · 완료 {d_count}개</div>
        </div>"""
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>대시보드</title>{STYLE}</head>
    <body>
    <div class='layout'>
        {sidebar_html(user, 'dashboard')}
        <div class='main'>
            <div class='topbar'><div><h1>대시보드</h1><p>전체 업무 현황</p></div><div class='topbar-user'>{user.name}</div></div>
            <div class='content'>
                <div class='stats'>
                    <div class='stat-box'><div class='stat-num'>{total}</div><div class='stat-label'>전체 할 일</div></div>
                    <div class='stat-box'><div class='stat-num green'>{completed}</div><div class='stat-label'>완료</div></div>
                    <div class='stat-box'><div class='stat-num red'>{total-completed}</div><div class='stat-label'>미완료</div></div>
                    <div class='stat-box'><div class='stat-num blue'>{len(persons)}</div><div class='stat-label'>담당자</div></div>
                </div>
                <div class='grid2'>
                    <div class='card'><h2>🏆 완료율 랭킹</h2>{ranking_html or "<p style='color:#9ca3af;font-size:13px;'>아직 데이터가 없어요</p>"}</div>
                    <div class='card'><h2>📁 최근 회의</h2>{meetings_html or "<p style='color:#9ca3af;font-size:13px;'>아직 회의록이 없어요</p>"}</div>
                </div>
            </div>
        </div>
    </div>
    </body></html>
    """)

@app.route('/new-meeting')
def new_meeting():
    user = get_user()
    if not user or user.role != 'admin':
        return redirect(url_for('login'))
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>새 회의록</title>{STYLE}</head>
    <body>
    <div class='layout'>
        {sidebar_html(user, 'new-meeting')}
        <div class='main'>
            <div class='topbar'><div><h1>새 회의록</h1><p>회의 내용을 입력하면 AI가 자동으로 정리해요</p></div></div>
            <div class='content'>
                <div class='card'>
                    <h2>📝 회의 정보</h2>
                    <div class='form-group' style='margin-bottom:12px;'>
                        <label style='font-size:12px;font-weight:600;color:#374151;display:block;margin-bottom:5px;'>회의 제목</label>
                        <input type='text' id='title' placeholder='예) 3분기 마케팅 전략 회의'>
                    </div>
                    <div class='form-group' style='margin-bottom:12px;'>
                        <label style='font-size:12px;font-weight:600;color:#374151;display:block;margin-bottom:5px;'>회의 내용</label>
                        <textarea id='content' placeholder='회의록 내용을 붙여넣어요.'></textarea>
                    </div>
                    <button class='btn' onclick='analyze()'>📋 회의록 분석하기</button>
                    <div id='loading'></div>
                </div>
                <div id='result'></div>
            </div>
        </div>
    </div>
   <script>
    async function analyze() {{
        const title = document.getElementById('title').value;
        const content = document.getElementById('content').value;
        if (!title.trim() || !content.trim()) return;
        document.getElementById('loading').innerHTML = '<p class="loading"><span class="spinner"></span>AI 분석 중...</p>';
        document.getElementById('result').innerHTML = '';
        const res = await fetch('/analyze', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{title: title, content: content}})
        }});
        const data = await res.json();
        document.getElementById('loading').innerHTML = '';
        if (data.error) return;
        window._analysisData = data;
        let html = '<div class="card"><h2>📌 분석 결과</h2>';
        html += '<div class="section-title" style="margin-bottom:8px;">회의 요약</div>';
        html += '<div class="summary-box" style="margin-bottom:16px;">' + data.summary + '</div>';
        html += '<div class="section-title" style="margin-bottom:8px;">담당자별 액션 아이템</div>';
        data.actions.forEach(function(a) {{
            html += '<div class="task-item">';
            html += '<span class="person-badge">' + a.person + '</span>';
            html += '<span class="task-text">' + a.task + '</span>';
            if (a.deadline) html += '<span class="deadline-badge">⏰ ' + a.deadline + '</span>';
            html += '</div>';
        }});
        html += '<button class="btn btn-green" style="margin-top:14px;" onclick="saveMeeting()">💾 저장하기</button></div>';
        document.getElementById('result').innerHTML = html;
    }}

    async function saveMeeting() {{
        const title = document.getElementById('title').value;
        const content = document.getElementById('content').value;
        const data = window._analysisData;
        const res = await fetch('/save-meeting', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{title: title, content: content, summary: data.summary, actions: data.actions}})
        }});
        const result = await res.json();
        if (result.ok) location.href = '/dashboard';
    }}
</script>
    </body></html>
    """)

@app.route('/analyze', methods=['POST'])
def analyze():
    user = get_user()
    if not user:
        return jsonify({"error": "로그인 필요"}), 401
    try:
        data = request.json
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": '''너는 회의록 분석 전문가야. 반드시 JSON만 출력해. 다른 텍스트 절대 금지.
형식: {"summary": "회의 핵심 내용 3줄 요약", "actions": [{"person": "담당자명", "task": "해야 할 일", "deadline": "기한 (없으면 null)"}]}'''},
                {"role": "user", "content": data['content']}
            ],
            response_format={"type": "json_object"}
        )
        return jsonify(json.loads(response.choices[0].message.content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save-meeting', methods=['POST'])
def save_meeting():
    user = get_user()
    if not user:
        return jsonify({"ok": False}), 401
    try:
        data = request.json
        meeting = Meeting(title=data['title'], content=data['content'], summary=data['summary'], company=user.company)
        db.session.add(meeting)
        db.session.flush()
        for a in data['actions']:
            matched_user = User.query.filter_by(name=a['person'], company=user.company).first()
            db.session.add(Task(
                meeting_id=meeting.id,
                person=a['person'],
                task=a['task'],
                deadline=a.get('deadline'),
                company=user.company,
                user_id=matched_user.id if matched_user else None
            ))
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/meeting/<int:meeting_id>')
def meeting_detail(meeting_id):
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    meeting = Meeting.query.get_or_404(meeting_id)
    tasks = Task.query.filter_by(meeting_id=meeting_id).all()
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>{meeting.title}</title>{STYLE}</head>
    <body>
    <div class='layout'>
        {sidebar_html(user, '')}
        <div class='main'>
            <div class='topbar'><div><h1>{meeting.title}</h1><p>{meeting.created_at.strftime('%Y-%m-%d %H:%M')}</p></div></div>
            <div class='content'>
                <div class='card'><div class='section-title'>📌 회의 요약</div><div class='summary-box'>{meeting.summary}</div></div>
                <div class='card'><h2>✅ 담당자별 액션 아이템</h2>{render_tasks(tasks)}</div>
            </div>
        </div>
    </div>
    {task_toggle_script()}
    </body></html>
    """)

@app.route('/toggle-task/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    user = get_user()
    if not user:
        return jsonify({"error": "로그인 필요"}), 401
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    return jsonify({"completed": task.completed})

@app.route('/all-tasks')
def all_tasks():
    user = get_user()
    if not user or user.role != 'admin':
        return redirect(url_for('login'))
    tasks = Task.query.filter_by(company=user.company).order_by(Task.completed, Task.deadline).all()
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전체 할 일</title>{STYLE}</head>
    <body>
    <div class='layout'>
        {sidebar_html(user, 'all-tasks')}
        <div class='main'>
            <div class='topbar'><div><h1>전체 할 일</h1><p>모든 담당자의 할 일 현황</p></div></div>
            <div class='content'>
                <div class='card'>{render_tasks(tasks) or "<p style='color:#9ca3af;font-size:13px;'>아직 할 일이 없어요</p>"}</div>
            </div>
        </div>
    </div>
    {task_toggle_script()}
    </body></html>
    """)

@app.route('/my-tasks')
def my_tasks():
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    tasks = Task.query.filter_by(company=user.company, user_id=user.id).order_by(Task.completed, Task.deadline).all()
    total = len(tasks)
    completed = len([t for t in tasks if t.completed])
    tasks_html = ""
    for t in tasks:
        done_class = 'done' if t.completed else 'undone'
        done_text = '완료' if t.completed else '미완료'
        text_class = 'done' if t.completed else ''
        tasks_html += f"""
        <div class='task-item {"completed" if t.completed else ""}' id='task-{t.id}'>
            <span class='task-text {text_class}'>{t.task}</span>
            {f"<span class='deadline-badge'>⏰ {t.deadline}</span>" if t.deadline else ''}
            <button class='complete-btn {done_class}' onclick='toggleTask({t.id})'>{done_text}</button>
        </div>"""
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>내 할 일</title>{STYLE}</head>
    <body>
    <div class='layout'>
        {sidebar_html(user, 'my-tasks')}
        <div class='main'>
            <div class='topbar'><div><h1>내 할 일</h1><p>{user.name}님의 할 일 목록</p></div></div>
            <div class='content'>
                <div class='stats'>
                    <div class='stat-box'><div class='stat-num'>{total}</div><div class='stat-label'>전체</div></div>
                    <div class='stat-box'><div class='stat-num green'>{completed}</div><div class='stat-label'>완료</div></div>
                    <div class='stat-box'><div class='stat-num red'>{total-completed}</div><div class='stat-label'>미완료</div></div>
                    <div class='stat-box'><div class='stat-num blue'>{round(completed/total*100) if total > 0 else 0}%</div><div class='stat-label'>완료율</div></div>
                </div>
                <div class='card'>{tasks_html or "<p style='color:#9ca3af;font-size:13px;'>아직 할 일이 없어요 🎉</p>"}</div>
            </div>
        </div>
    </div>
    {task_toggle_script()}
    </body></html>
    """)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)