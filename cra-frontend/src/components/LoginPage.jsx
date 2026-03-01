/**
 * components/LoginPage.jsx
 * Charte CRA Analytics — panneau gauche navy + panneau droit blanc.
 * Deux modes : connexion / création de compte (toggle sans navigation).
 */
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { login as apiLogin } from '../api/client'
import { register as apiRegister } from '../api/client'

/* ── Icônes SVG ──────────────────────────────────────────────────── */
const IconChart = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <path d="M3 3v18h18M7 16l4-4 4 4 4-8"/>
  </svg>
)
const IconUser = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 text-gray-400">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
  </svg>
)
const IconMail = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 text-gray-400">
    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
    <polyline points="22,6 12,13 2,6"/>
  </svg>
)
const IconLock = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 text-gray-400">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
)
const IconEye = ({ off }) => off ? (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
) : (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
)
const IconChat = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
)
const IconGraph = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>
)

/* ── Blocs 3D décoratifs ─────────────────────────────────────────── */
const Cubes3D = () => (
  <svg viewBox="0 0 420 320" className="absolute top-0 right-0 w-full h-72 opacity-25 pointer-events-none">
    <g transform="translate(260,30)">
      <polygon points="60,0 120,35 120,105 60,70" fill="#1e40af" opacity="0.9"/>
      <polygon points="0,35 60,0 60,70 0,105" fill="#1d4ed8" opacity="0.7"/>
      <polygon points="0,35 60,70 120,35 60,0" fill="#3b82f6" opacity="0.8"/>
    </g>
    <g transform="translate(170,90)">
      <polygon points="40,0 80,23 80,70 40,47" fill="#1e3a8a" opacity="0.85"/>
      <polygon points="0,23 40,0 40,47 0,70" fill="#1e40af" opacity="0.65"/>
      <polygon points="0,23 40,47 80,23 40,0" fill="#2563eb" opacity="0.75"/>
    </g>
    <g transform="translate(330,10)">
      <polygon points="25,0 50,14 50,44 25,30" fill="#1e3a8a" opacity="0.8"/>
      <polygon points="0,14 25,0 25,30 0,44" fill="#1e40af" opacity="0.6"/>
      <polygon points="0,14 25,30 50,14 25,0" fill="#3b82f6" opacity="0.7"/>
    </g>
    <g transform="translate(310,75)">
      <polygon points="35,0 70,20 70,60 35,40" fill="#172554" opacity="0.7"/>
      <polygon points="0,20 35,0 35,40 0,60" fill="#1e3a8a" opacity="0.5"/>
      <polygon points="0,20 35,40 70,20 35,0" fill="#1d4ed8" opacity="0.6"/>
    </g>
    <line x1="290" y1="65" x2="210" y2="113" stroke="#3b82f6" strokeWidth="0.5" opacity="0.3"/>
    <line x1="355" y1="24" x2="300" y2="47" stroke="#60a5fa" strokeWidth="0.5" opacity="0.25"/>
  </svg>
)

/* ── Input avec icône ────────────────────────────────────────────── */
const InputField = ({ label, type = 'text', value, onChange, placeholder, icon, rightEl }) => (
  <div>
    <label className="block text-sm font-medium text-slate-700 mb-1.5">{label}</label>
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2">{icon}</span>
      <input type={type} value={value} onChange={onChange} placeholder={placeholder} required
        className="w-full pl-9 pr-10 py-2.5 rounded-lg border border-slate-200 bg-white
                   text-slate-800 placeholder-slate-400 text-sm
                   focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition"
      />
      {rightEl && <span className="absolute right-3 top-1/2 -translate-y-1/2">{rightEl}</span>}
    </div>
  </div>
)

/* ── Composant principal ─────────────────────────────────────────── */
export default function LoginPage() {
  const { login }                       = useAuth()
  const [mode, setMode]                 = useState('login')   // 'login' | 'register'

  // Champs login
  const [username, setUsername]         = useState('')
  const [password, setPassword]         = useState('')
  const [remember, setRemember]         = useState(true)

  // Champs inscription
  const [regPrenom, setRegPrenom]       = useState('')
  const [regNom, setRegNom]             = useState('')
  const [regEmail, setRegEmail]         = useState('')
  const [regPassword, setRegPassword]   = useState('')
  const [regConfirm, setRegConfirm]     = useState('')

  const [showPwd, setShowPwd]           = useState(false)
  const [showConfirm, setShowConfirm]   = useState(false)
  const [error, setError]               = useState('')
  const [success, setSuccess]           = useState('')
  const [loading, setLoading]           = useState(false)

  const switchMode = (m) => { setMode(m); setError(''); setSuccess('') }

  /* ── Connexion ── */
  const handleLogin = async (e) => {
  e.preventDefault()
  setError('')
  setLoading(true)

  try {
    const data = await apiLogin(username, password) // Appel au backend
    // Le backend renvoie { access_token: "...", token_type: "bearer" }
    login({ email: username }, data.access_token) 
  } catch (err) {
    setError(err.response?.data?.detail || 'Identifiants invalides')
  } finally {
    setLoading(false)
  }
  }

  /* ── Inscription ── */
const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    if (regPassword !== regConfirm) { setError('Les mots de passe ne correspondent pas.'); return }
    if (regPassword.length < 6)    { setError('Le mot de passe doit contenir au moins 6 caractères.'); return }
    
    setLoading(true)
    try {
      // CRÉATION DE L'OBJET ATTENDU PAR LE BACKEND (UserCreateDTO)
      const userData = {
        prenom: regPrenom,
        nom: regNom,
        email: regEmail,
        password: regPassword,
        role: 'user'
      };

      await apiRegister(userData); // Appel avec l'objet unique
      
      setSuccess('Compte créé avec succès ! Connectez-vous.');
      setRegPrenom(''); setRegNom(''); setRegEmail(''); setRegPassword(''); setRegConfirm('')
      setTimeout(() => { switchMode('login'); setUsername(regEmail); setSuccess('') }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la création du compte.');
    } finally { setLoading(false) }
  }

  const eyeBtn = (show, setShow) => (
    <button type="button" onClick={() => setShow(v => !v)}
      className="text-slate-400 hover:text-slate-600 transition">
      <IconEye off={show} />
    </button>
  )

  return (
    <div className="min-h-screen flex">

      {/* ════ PANNEAU GAUCHE ══════════════════════════════════════════ */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-10 overflow-hidden"
        style={{ background: 'linear-gradient(160deg, #060d1a 0%, #0a1628 45%, #0d2244 100%)' }}>

        {/* Étoiles */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(40)].map((_, i) => (
            <div key={i} className="absolute rounded-full bg-white"
              style={{
                width: Math.random() * 2 + 1 + 'px', height: Math.random() * 2 + 1 + 'px',
                top: Math.random() * 100 + '%', left: Math.random() * 100 + '%',
                opacity: Math.random() * 0.5 + 0.1,
              }} />
          ))}
        </div>
        <Cubes3D />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center text-white">
            <IconChart />
          </div>
          <span className="text-white font-bold text-lg tracking-tight">CRA Analytics</span>
        </div>

        {/* Baseline */}
        <div className="relative z-10 space-y-8">
          <div>
            <h1 className="text-4xl font-extrabold text-white leading-tight">
              AI that drives<br />your business.
            </h1>
            <p className="text-slate-400 text-sm mt-3 leading-relaxed max-w-xs">
              Get instant insights and optimize your business reports in just a few clicks with our smart platform.
            </p>
          </div>
          <div className="space-y-3">
            {[
              { icon: <IconChat />, title: 'Interactive AI Assistant',
                desc: 'Chat naturally with your activity report data using our next-generation chatbot.' },
              { icon: <IconGraph />, title: 'Dynamic graphs',
                desc: 'Visualize your activity in real time with accurate dashboards and graphs.' },
            ].map(({ icon, title, desc }) => (
              <div key={title} className="flex gap-3 p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
                <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-brand-600/30 border border-brand-500/30
                                flex items-center justify-center text-brand-400">{icon}</div>
                <div>
                  <p className="text-white text-sm font-semibold">{title}</p>
                  <p className="text-slate-400 text-xs mt-0.5 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ════ PANNEAU DROIT ═══════════════════════════════════════════ */}
      <div className="flex-1 flex items-center justify-center bg-white px-8 py-12 overflow-y-auto">
        <div className="w-full max-w-sm">

          {/* Logo mobile */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white">
              <IconChart />
            </div>
            <span className="font-bold text-slate-800 text-base">CRA Analytics</span>
          </div>

          {/* ── FORMULAIRE CONNEXION ─────────────────────────────── */}
          {mode === 'login' && (
            <>
              <div className="mb-7">
                <h2 className="text-3xl font-bold text-slate-900">Login</h2>
                <p className="text-slate-500 text-sm mt-1.5">
                  Please enter your credentials to access your account.
                </p>
              </div>

              <form onSubmit={handleLogin} className="space-y-5">
                <InputField label="Email" value={username}
                  onChange={e => setUsername(e.target.value)} placeholder="Email"
                  icon={<IconUser />} />

                <InputField label="Password" type={showPwd ? 'text' : 'password'}
                  value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••"
                  icon={<IconLock />} rightEl={eyeBtn(showPwd, setShowPwd)} />

                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 accent-brand-600" />
                    <span className="text-sm text-slate-600">Remember me</span>
                  </label>
                  <button type="button"
                    className="text-sm text-brand-600 hover:text-brand-700 hover:underline transition">
                    Forgot password?
                  </button>
                </div>

                {error && <Alert type="error">{error}</Alert>}

                <SubmitBtn loading={loading}>Sign in</SubmitBtn>
              </form>

              <p className="text-center text-slate-500 text-sm mt-6">
                You don't have an account yet?{' '}
                <button onClick={() => switchMode('register')}
                  className="text-brand-600 font-semibold hover:underline transition">
                  Create an account
                </button>
              </p>
            </>
          )}

          {/* ── FORMULAIRE INSCRIPTION ───────────────────────────── */}
          {mode === 'register' && (
            <>
              <div className="mb-7">
                <h2 className="text-3xl font-bold text-slate-900">Create an account</h2>
                <p className="text-slate-500 text-sm mt-1.5">
                  Enter your information to join CRA Analytics.
                </p>
              </div>

              <form onSubmit={handleRegister} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <InputField label="First name" value={regPrenom}
                    onChange={e => setRegPrenom(e.target.value)} placeholder="Jean"
                    icon={<IconUser />} />
                  <InputField label="Last name" value={regNom}
                    onChange={e => setRegNom(e.target.value)} placeholder="Dupont"
                    icon={<IconUser />} />
                </div>

                <InputField label="Email" type="email" value={regEmail}
                  onChange={e => setRegEmail(e.target.value)} placeholder="jean@example.com"
                  icon={<IconMail />} />

                <InputField label="Password" type={showPwd ? 'text' : 'password'}
                  value={regPassword} onChange={e => setRegPassword(e.target.value)}
                  placeholder="Min. 6 characters" icon={<IconLock />}
                  rightEl={eyeBtn(showPwd, setShowPwd)} />

                <InputField label="Confirm password"
                  type={showConfirm ? 'text' : 'password'}
                  value={regConfirm} onChange={e => setRegConfirm(e.target.value)}
                  placeholder="Repeat the password" icon={<IconLock />}
                  rightEl={eyeBtn(showConfirm, setShowConfirm)} />

                {error   && <Alert type="error">{error}</Alert>}
                {success && <Alert type="success">{success}</Alert>}

                <SubmitBtn loading={loading}>Create my account</SubmitBtn>
              </form>

              <p className="text-center text-slate-500 text-sm mt-6">
                You already have an account?{' '}
                <button onClick={() => switchMode('login')}
                  className="text-brand-600 font-semibold hover:underline transition">
                  Sign in
                </button>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── Sous-composants utilitaires ─────────────────────────────────── */
const Alert = ({ type, children }) => {
  const styles = type === 'error'
    ? 'text-red-600 bg-red-50 border-red-200'
    : 'text-green-700 bg-green-50 border-green-200'
  return (
    <div className={`flex items-start gap-2 text-sm border rounded-lg px-3 py-2.5 ${styles}`}>
      {type === 'error'
        ? <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
          </svg>
        : <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
          </svg>
      }
      {children}
    </div>
  )
}

const SubmitBtn = ({ loading, children }) => (
  <button type="submit" disabled={loading}
    className="w-full py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700
               text-white font-semibold text-sm tracking-wide transition
               disabled:opacity-60 disabled:cursor-not-allowed shadow-sm shadow-brand-600/30">
    {loading
      ? <span className="flex items-center justify-center gap-2">
          <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"
              strokeDasharray="31.4" strokeDashoffset="10"/>
          </svg>
          Chargement…
        </span>
      : children}
  </button>
)