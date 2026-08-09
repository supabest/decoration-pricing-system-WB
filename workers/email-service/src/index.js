/**
 * Cloudflare Worker — 装修成本AI系统邮件发送出口
 *
 * 职责：接收 Render FastAPI 的授权请求 → 调用 Resend API → 返回结果
 * 不读 Supabase，不保存状态，不管理业务逻辑。
 */
export default {
  async fetch(request, env) {
    // 1. 只接受 POST
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ ok: false, error: 'Method not allowed' }), {
        status: 405,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // 2. 验证 EMAIL_SERVICE_TOKEN
    const authHeader = request.headers.get('Authorization') || '';
    const expectedToken = `Bearer ${env.EMAIL_SERVICE_TOKEN}`;
    if (authHeader !== expectedToken) {
      return new Response(JSON.stringify({ ok: false, error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // 3. 解析请求体
    let body;
    try {
      body = await request.json();
    } catch {
      return new Response(JSON.stringify({ ok: false, error: 'Invalid JSON body' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    const { to, subject, html, idempotency_key } = body;
    if (!to || !subject || !html || !idempotency_key) {
      return new Response(JSON.stringify({ ok: false, error: 'Missing required fields: to, subject, html, idempotency_key' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // 4. 调用 Resend REST API
    const headers = {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotency_key,
    };
    const payload = {
      from: `${env.EMAIL_FROM_NAME} <${env.EMAIL_FROM}>`,
      to: [to],
      subject,
      html,
    };

    try {
      const resendResp = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
      const result = await resendResp.json();

      if (resendResp.ok) {
        return new Response(JSON.stringify({ ok: true, message_id: result.id, error: null }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response(JSON.stringify({ ok: false, message_id: null, error: JSON.stringify(result).substring(0, 200) }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (e) {
      return new Response(JSON.stringify({ ok: false, message_id: null, error: e.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  },
};
