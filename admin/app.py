import secrets
from html import escape

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from bot.config import ADMIN_PASSWORD
from bot.db import init_db, list_reports, update_status, STATUSES

app = FastAPI(title='Reports Admin')
security = HTTPBasic()
init_db()

STATUS_LABELS = {
    'pending': 'Ожидает',
    'approved': 'Одобрено',
    'rejected': 'Отклонено',
    'resolved': 'Решено',
}


def auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    ok = (
        secrets.compare_digest(credentials.username, 'admin')
        and secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    )
    if not ok:
        raise HTTPException(401, 'Unauthorized', headers={'WWW-Authenticate': 'Basic'})
    return credentials.username


def render(reports: list[dict], current: str) -> str:
    rows = ''
    for r in reports:
        contact = escape(r['contact_info'] or '—')
        rows += f'''
            <tr>
                <td><code>{r['id']}</code></td>
                <td>{escape(r['category'])}</td>
                <td class="desc">{escape(r['description'])}</td>
                <td>{contact}</td>
                <td>{r['user_id'] or '—'}</td>
                <td><span class="s s-{r['status']}">{STATUS_LABELS.get(r['status'], r['status'])}</span></td>
                <td>{r['created_at'][:19].replace('T', ' ')}</td>
                <td class="actions">
                    <form method="post" action="/update/{r['id']}/approved"><button class="ok">Одобрить</button></form>
                    <form method="post" action="/update/{r['id']}/rejected"><button class="no">Отклонить</button></form>
                    <form method="post" action="/update/{r['id']}/resolved"><button class="done">Решено</button></form>
                </td>
            </tr>
        '''

    filters = ''
    for s, label in [('all', 'Все'), *[(s, STATUS_LABELS[s]) for s in STATUSES]]:
        cls = 'filter active' if s == current else 'filter'
        filters += f'<a class="{cls}" href="/?status={s}">{label}</a>'

    body = (
        '<table><thead><tr>'
        '<th>ID</th><th>Категория</th><th>Описание</th><th>Контакт</th><th>User</th>'
        '<th>Статус</th><th>Создано</th><th>Действия</th>'
        f'</tr></thead><tbody>{rows}</tbody></table>'
        if reports else '<div class="empty">Обращений нет</div>'
    )

    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Обращения</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 2rem; background: #f5f5f7; color: #222; }}
h1 {{ margin: 0 0 1rem; }}
.filters {{ margin-bottom: 1rem; }}
.filter {{ display: inline-block; padding: .4rem .8rem; margin-right: .3rem; background: #fff;
          border: 1px solid #d1d5db; border-radius: 6px; text-decoration: none; color: #374151; font-size: .9rem; }}
.filter.active {{ background: #2563eb; color: #fff; border-color: #2563eb; }}
table {{ width: 100%; background: #fff; border-collapse: collapse; box-shadow: 0 1px 3px rgba(0,0,0,.06); border-radius: 8px; overflow: hidden; }}
th, td {{ padding: .65rem .75rem; border-bottom: 1px solid #eef0f3; text-align: left; vertical-align: top; font-size: .9rem; }}
th {{ background: #fafbfc; font-weight: 600; color: #374151; }}
td.desc {{ max-width: 380px; }}
code {{ background: #f3f4f6; padding: .15rem .4rem; border-radius: 4px; font-size: .85rem; }}
.s {{ padding: .2rem .5rem; border-radius: 4px; font-size: .8rem; white-space: nowrap; }}
.s-pending {{ background: #fef3c7; color: #92400e; }}
.s-approved {{ background: #d1fae5; color: #065f46; }}
.s-rejected {{ background: #fee2e2; color: #991b1b; }}
.s-resolved {{ background: #dbeafe; color: #1e40af; }}
.actions form {{ display: inline; }}
button {{ padding: .3rem .55rem; border: none; border-radius: 4px; cursor: pointer; margin-right: .2rem;
         font-size: .8rem; color: #fff; }}
button.ok {{ background: #10b981; }}
button.no {{ background: #ef4444; }}
button.done {{ background: #3b82f6; }}
.empty {{ padding: 3rem; text-align: center; color: #6b7280; background: #fff; border-radius: 8px; }}
</style></head><body>
<h1>Обращения</h1>
<div class="filters">{filters}</div>
{body}
</body></html>'''


@app.get('/', response_class=HTMLResponse)
def index(status: str = 'all', _user: str = Depends(auth)):
    filter_status = None if status == 'all' else status
    reports = list_reports(filter_status)
    return HTMLResponse(render(reports, status))


@app.post('/update/{report_id}/{new_status}')
def update(report_id: str, new_status: str, _user: str = Depends(auth)):
    if new_status not in STATUSES:
        raise HTTPException(400, 'Bad status')
    update_status(report_id, new_status)
    return RedirectResponse('/', status_code=303)
