import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getChineseErrorMessage } from '../lib/authErrors'
import { supabase } from '../lib/supabaseClient'

export default function LoginPage() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [loggedIn, setLoggedIn] = useState(false)

  // 登录成功后等 user 状态更新再跳转
  useEffect(() => {
    if (loggedIn && user) {
      navigate('/pricing')
    }
  }, [loggedIn, user, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      let loginEmail = identifier.trim()
      // 非邮箱格式 → 按昵称查找邮箱
      if (!loginEmail.includes('@')) {
        // 优先查管理员，再查普通用户（大小写不敏感）
        let { data, error: lookupErr } = await (supabase as any)
          .from('profiles')
          .select('email')
          .ilike('display_name', loginEmail)
          .eq('is_admin', true)
          .maybeSingle()
        if (!data) {
          ({ data, error: lookupErr } = await (supabase as any)
            .from('profiles')
            .select('email')
            .ilike('display_name', loginEmail)
            .maybeSingle())
        }
        if (lookupErr || !data?.email) {
          throw { message: '未找到昵称"' + loginEmail + '"对应的账户，请确认昵称或使用邮箱登录' }
        }
        loginEmail = data.email
      }
      await login(loginEmail, password)
      setLoggedIn(true)
    } catch (err: any) {
      setError(getChineseErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    }}>
      <div style={{
        background: '#fff',
        borderRadius: 16,
        padding: 40,
        width: 400,
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>🏗️</div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e', margin: '0 0 4px' }}>
            装修成本分析系统
          </h1>
          <p style={{ color: '#888', fontSize: 14, margin: 0 }}>登录您的账户</p>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div style={{
              background: '#fff2f0', border: '1px solid #ffccc7',
              borderRadius: 8, padding: '10px 16px', color: '#cf1322',
              fontSize: 14, marginBottom: 16,
            }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 6, color: '#333', fontWeight: 500, fontSize: 14 }}>
              邮箱或昵称
            </label>
            <input
              type="text"
              value={identifier}
              onChange={e => setIdentifier(e.target.value)}
              placeholder="请输入昵称或注册邮箱"
              required
              autoComplete="username"
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 8,
                border: '1px solid #d9d9d9', fontSize: 15, boxSizing: 'border-box',
                outline: 'none', transition: 'border-color 0.2s',
              }}
              onFocus={e => e.target.style.borderColor = '#0f3460'}
              onBlur={e => e.target.style.borderColor = '#d9d9d9'}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', marginBottom: 6, color: '#333', fontWeight: 500, fontSize: 14 }}>
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="请输入密码"
              required
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 8,
                border: '1px solid #d9d9d9', fontSize: 15, boxSizing: 'border-box',
                outline: 'none',
              }}
              onFocus={e => e.target.style.borderColor = '#0f3460'}
              onBlur={e => e.target.style.borderColor = '#d9d9d9'}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '12px', borderRadius: 8,
              border: 'none', background: '#0f3460', color: '#fff',
              fontSize: 16, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? '登录中...' : '登 录'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <span style={{ color: '#888', fontSize: 14 }}>还没有账户？</span>
          <Link to="/register" style={{ color: '#0f3460', fontSize: 14, fontWeight: 500, marginLeft: 4 }}>
            注册新账户
          </Link>
        </div>
      </div>
    </div>
  )
}
