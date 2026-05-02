// phase2-screens.jsx
// PRLifts Phase 2 Onboarding — all 4 screens in one file.
// GoalSelectionScreen · BiometricConsentScreen · PhotoCaptureScreen · FutureSelfRevealScreen
// Each accepts a `t` prop (DK or LT tokens from screens-shared.jsx).

// ─────────────────────────────────────────────────────────────────
// GoalSelectionScreen
// ─────────────────────────────────────────────────────────────────
function GoalSelectionScreen({ t }) {
  const goals = [
    { id:'build_muscle',         label:'Build muscle',          sub:'Increase strength and size over time',
      icon:(c)=><svg width="22" height="22" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M6.5 6.5h11M6.5 12h11M6.5 17.5h8"/><circle cx="3" cy="6.5" r="1.5"/><circle cx="3" cy="12" r="1.5"/><circle cx="3" cy="17.5" r="1.5"/></svg> },
    { id:'lose_fat',             label:'Lose fat',               sub:'Reduce body fat, maintain strength',
      icon:(c)=><svg width="22" height="22" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg> },
    { id:'improve_endurance',    label:'Improve endurance',      sub:'Build cardiovascular stamina and capacity',
      icon:(c)=><svg width="22" height="22" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> },
    { id:'athletic_performance', label:'Athletic performance',   sub:'Speed, power, and sport-specific fitness',
      icon:(c)=><svg width="22" height="22" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> },
    { id:'general_fitness',      label:'General fitness',        sub:'Stay active, healthy, and feeling good',
      icon:(c)=><svg width="22" height="22" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg> },
  ];
  const sel = 'build_muscle';

  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
      <NavBar t={t} title="" border={false}
        left={<svg width="20" height="20" fill="none" stroke={t.brandLt} strokeWidth="2.5" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>}
        right={<span style={{ fontSize:14, fontWeight:600, color:t.textTer, fontFamily:t.fb }}>Skip</span>}
      />
      <div style={{ flex:1, overflowY:'auto', padding:'4px 20px 0' }}>
        <div style={{ fontFamily:t.fd, fontSize:27, fontWeight:900, color:t.textPri, letterSpacing:-0.5, lineHeight:1.15, marginBottom:7 }}>What's your main goal?</div>
        <div style={{ fontSize:14, color:t.textSec, fontFamily:t.fb, marginBottom:18, lineHeight:1.4 }}>This personalises your insights. You can change it anytime.</div>
        <div style={{ display:'flex', flexDirection:'column', gap:9 }}>
          {goals.map(g => {
            const on = g.id === sel;
            return (
              <div key={g.id} style={{
                borderRadius:16, padding:'13px 16px',
                background: on ? `${t.brand}18` : t.bgSec,
                border: `2px solid ${on ? t.brand : t.border}`,
                boxShadow: on ? `0 0 0 1px ${t.brand}, 0 4px 16px ${t.brandGlow}` : 'none',
                display:'flex', alignItems:'center', gap:14, cursor:'pointer',
              }}>
                <div style={{ width:44, height:44, borderRadius:12, flexShrink:0, background: on ? t.brand : t.bgTer, display:'flex', alignItems:'center', justifyContent:'center', boxShadow: on ? `0 4px 12px ${t.brandGlow}` : 'none' }}>
                  {g.icon(on ? '#fff' : t.textSec)}
                </div>
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:15, fontWeight:700, color:t.textPri, fontFamily:t.fb, marginBottom:2 }}>{g.label}</div>
                  <div style={{ fontSize:12, color: on ? t.brandLt : t.textTer, fontFamily:t.fb }}>{g.sub}</div>
                </div>
                <div style={{ width:22, height:22, borderRadius:'50%', flexShrink:0, background: on ? t.brand : 'transparent', border:`2px solid ${on ? t.brand : t.textTer}`, display:'flex', alignItems:'center', justifyContent:'center' }}>
                  {on && <svg width="10" height="10" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>}
                </div>
              </div>
            );
          })}
        </div>
        <div style={{ height:12 }}></div>
      </div>
      <div style={{ padding:'12px 20px 4px', borderTop:`1px solid ${t.border}`, background:t.bg, flexShrink:0 }}>
        <PBtn t={t} label="Continue" style={{ height:50 }} />
      </div>
      <TabBar t={t} active="home" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// BiometricConsentScreen
// ─────────────────────────────────────────────────────────────────
function BiometricConsentScreen({ t }) {
  const steps = [
    { text:'Send your photo to our image generation service (Fal.ai)',
      icon:(c)=><svg width="15" height="15" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg> },
    { text:'Delete your original photo within 60 seconds',
      icon:(c)=><svg width="15" height="15" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/></svg> },
    { text:'Store only the generated image, which you own',
      icon:(c)=><svg width="15" height="15" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg> },
  ];

  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
      <NavBar t={t} title="" border={false}
        left={<svg width="20" height="20" fill="none" stroke={t.brandLt} strokeWidth="2.5" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>}
      />
      <div style={{ flex:1, overflowY:'auto', padding:'8px 22px 0' }}>
        {/* Shield icon */}
        <div style={{ width:58, height:58, borderRadius:17, background:t.brandSub, border:`1px solid ${t.brand}30`, display:'flex', alignItems:'center', justifyContent:'center', marginBottom:18 }}>
          <svg width="26" height="26" fill="none" stroke={t.brandLt} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <polyline points="9 12 11 14 15 10"/>
          </svg>
        </div>

        <div style={{ fontFamily:t.fd, fontSize:25, fontWeight:900, color:t.textPri, letterSpacing:-0.4, lineHeight:1.15, marginBottom:9 }}>Your photo, your choice</div>
        <div style={{ fontSize:15, color:t.textSec, fontFamily:t.fb, marginBottom:20, lineHeight:1.5 }}>To create your future self image, PRLifts will:</div>

        {/* Steps card */}
        <div style={{ background:t.bgSec, borderRadius:14, border:`1px solid ${t.border}`, overflow:'hidden', marginBottom:14 }}>
          {steps.map((s,i) => (
            <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:12, padding:'13px 16px', borderBottom: i < steps.length-1 ? `1px solid ${t.border}` : 'none' }}>
              <div style={{ width:32, height:32, borderRadius:9, background:t.brandSub, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, marginTop:1 }}>
                {s.icon(t.brandLt)}
              </div>
              <span style={{ fontSize:14, color:t.textSec, fontFamily:t.fb, lineHeight:1.5, paddingTop:6 }}>{s.text}</span>
            </div>
          ))}
        </div>

        {/* Deletion note */}
        <div style={{ background:t.bgSec, borderRadius:12, padding:'12px 14px', border:`1px solid ${t.border}`, marginBottom:12 }}>
          <div style={{ fontSize:13, color:t.textSec, fontFamily:t.fb, lineHeight:1.55 }}>
            You can delete this image at any time from{' '}
            <span style={{ color:t.brandLt, fontWeight:600 }}>Settings → Biometric consent</span>.
            Declining skips the future self feature entirely.
          </div>
        </div>

        <div style={{ fontSize:11, color:t.textTer, fontFamily:t.fb, lineHeight:1.5, paddingBottom:18 }}>
          Your photo is never stored, sold, or used to train AI models. This consent is separate from the Terms of Service.
        </div>
      </div>

      {/* CTAs */}
      <div style={{ padding:'10px 22px 4px', borderTop:`1px solid ${t.border}`, background:t.bg, flexShrink:0, display:'flex', flexDirection:'column', gap:8 }}>
        <PBtn t={t} label="Agree" style={{ height:50 }} />
        <PBtn t={t} label="No thanks" variant="ghost" style={{ height:44, color:t.textSec }} />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// PhotoCaptureScreen
// ─────────────────────────────────────────────────────────────────
function PhotoCaptureScreen({ t }) {
  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden', background:'#000' }}>

      {/* Full-bleed camera viewfinder */}
      <div style={{ flex:1, position:'relative', background:'linear-gradient(160deg,#0C0F1E 0%,#070912 55%,#0A0D1C 100%)' }}>

        {/* Status bar */}
        <div style={{ position:'absolute', top:0, left:0, right:0, height:52, display:'flex', alignItems:'flex-start', justifyContent:'space-between', padding:'16px 24px 0', zIndex:20, pointerEvents:'none', fontFamily:t.fb, fontSize:13, fontWeight:600, color:'rgba(255,255,255,0.75)' }}>
          <span>9:41</span>
        </div>

        {/* Dynamic island */}
        <div style={{ position:'absolute', top:12, left:'50%', transform:'translateX(-50%)', width:120, height:34, borderRadius:20, background:'#000', zIndex:30 }}></div>

        {/* Top controls */}
        <div style={{ position:'absolute', top:54, left:0, right:0, display:'flex', alignItems:'center', justifyContent:'space-between', padding:'8px 20px', zIndex:20 }}>
          <span style={{ fontSize:14, fontWeight:600, color:'rgba(255,255,255,0.85)', fontFamily:t.fb }}>Cancel</span>
          <div style={{ width:36, height:36, borderRadius:'50%', background:'rgba(255,255,255,0.10)', display:'flex', alignItems:'center', justifyContent:'center' }}>
            <svg width="18" height="18" fill="none" stroke="rgba(255,255,255,0.75)" strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
        </div>

        {/* Oval framing guide */}
        <div style={{ position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-54%)', zIndex:10 }}>
          <svg width="220" height="280" viewBox="0 0 220 280" fill="none">
            <defs>
              <mask id="p2-oval-mask">
                <rect width="220" height="280" fill="white"/>
                <ellipse cx="110" cy="140" rx="100" ry="130" fill="black"/>
              </mask>
            </defs>
            <rect width="220" height="280" fill="rgba(0,0,0,0.42)" mask="url(#p2-oval-mask)"/>
            <ellipse cx="110" cy="140" rx="100" ry="130" stroke="rgba(255,255,255,0.55)" strokeWidth="1.5" strokeDasharray="7 5"/>
            {/* Corner accents */}
            <path d="M12 46 Q10 10 48 10" stroke="white" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <path d="M208 46 Q210 10 172 10" stroke="white" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <path d="M12 234 Q10 270 48 270" stroke="white" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <path d="M208 234 Q210 270 172 270" stroke="white" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            {/* Face placeholder */}
            <circle cx="110" cy="118" r="28" fill="rgba(255,255,255,0.03)"/>
            <path d="M78 214 Q78 180 110 180 Q142 180 142 214" fill="rgba(255,255,255,0.025)"/>
          </svg>
          {/* Label below oval */}
          <div style={{ position:'absolute', bottom:-30, left:'50%', transform:'translateX(-50%)', whiteSpace:'nowrap' }}>
            <div style={{ background:'rgba(0,0,0,0.55)', borderRadius:999, padding:'5px 13px' }}>
              <span style={{ fontSize:11, fontWeight:600, color:'rgba(255,255,255,0.72)', fontFamily:t.fb }}>Position your face in the frame</span>
            </div>
          </div>
        </div>

        {/* Tips */}
        <div style={{ position:'absolute', bottom:116, left:0, right:0, display:'flex', gap:6, justifyContent:'center', padding:'0 16px', zIndex:20 }}>
          {['Face the light', 'Look straight ahead', 'Neutral expression'].map((tip,i) => (
            <div key={i} style={{ background:'rgba(0,0,0,0.55)', borderRadius:999, padding:'5px 9px', border:'1px solid rgba(255,255,255,0.10)' }}>
              <span style={{ fontSize:11, fontWeight:600, color:'rgba(255,255,255,0.75)', fontFamily:t.fb, whiteSpace:'nowrap' }}>{tip}</span>
            </div>
          ))}
        </div>

        {/* Camera controls */}
        <div style={{ position:'absolute', bottom:20, left:0, right:0, display:'flex', alignItems:'center', justifyContent:'space-between', padding:'0 32px', zIndex:20 }}>
          {/* Library */}
          <div style={{ width:52, height:52, borderRadius:12, background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.12)', display:'flex', alignItems:'center', justifyContent:'center' }}>
            <svg width="22" height="22" fill="none" stroke="rgba(255,255,255,0.65)" strokeWidth="1.8" strokeLinecap="round" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          </div>
          {/* Shutter */}
          <div style={{ width:76, height:76, borderRadius:'50%', border:'3px solid rgba(255,255,255,0.88)', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer' }}>
            <div style={{ width:60, height:60, borderRadius:'50%', background:'rgba(255,255,255,0.92)' }}></div>
          </div>
          {/* Flip / retake */}
          <div style={{ width:52, height:52, borderRadius:'50%', background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.12)', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer' }}>
            <svg width="22" height="22" fill="none" stroke="rgba(255,255,255,0.65)" strokeWidth="1.8" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>
          </div>
        </div>
      </div>

      {/* Bottom hint bar */}
      <div style={{ background:'#000', padding:'10px 24px 34px', display:'flex', alignItems:'center', justifyContent:'space-between', flexShrink:0 }}>
        <span style={{ fontSize:12, color:'rgba(255,255,255,0.28)', fontFamily:t.fb }}>Photo not submitted yet</span>
        <span style={{ fontSize:13, fontWeight:600, color:'rgba(255,255,255,0.52)', fontFamily:t.fb }}>Retake</span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// FutureSelfRevealScreen
// state prop: 'warning' (content notice) | 'revealed' (image shown)
// NO gold gradient — gold is reserved for PR achievements.
// Uses brand blue for the reveal accent.
// ─────────────────────────────────────────────────────────────────
function FutureSelfRevealScreen({ t, state }) {

  if (state === 'warning') {
    return (
      <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
        <NavBar t={t} title="" border={false} />
        <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 32px', textAlign:'center', gap:0 }}>

          {/* Eye icon */}
          <div style={{ width:68, height:68, borderRadius:20, background:t.bgSec, border:`1px solid ${t.border}`, display:'flex', alignItems:'center', justifyContent:'center', marginBottom:24 }}>
            <svg width="30" height="30" fill="none" stroke={t.textSec} strokeWidth="1.8" strokeLinecap="round" viewBox="0 0 24 24">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </div>

          <div style={{ fontFamily:t.fd, fontSize:24, fontWeight:900, color:t.textPri, letterSpacing:-0.4, lineHeight:1.2, marginBottom:12 }}>
            A note before you see your image
          </div>

          <div style={{ fontSize:15, color:t.textSec, fontFamily:t.fb, lineHeight:1.65, marginBottom:32 }}>
            AI image generation is a creative interpretation — not a precise prediction. The result may look different from what you expect.
            <br /><br />
            Think of it as motivation, not a mirror.
          </div>

          <PBtn t={t} label="Show my image" style={{ width:'100%' }} />
          <div style={{ marginTop:12 }}>
            <span style={{ fontSize:14, color:t.textTer, fontFamily:t.fb, cursor:'pointer' }}>Skip for now</span>
          </div>
        </div>
      </div>
    );
  }

  // Revealed state — image is the hero
  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>

      {/* Image hero — full-width, 58% of height */}
      <div style={{ position:'relative', height:490, flexShrink:0, overflow:'hidden' }}>

        {/* Placeholder image — atmospheric gradient simulating portrait */}
        <div style={{
          position:'absolute', inset:0,
          background: t === DK
            ? 'linear-gradient(175deg, #1E2A50 0%, #152244 25%, #0D1830 50%, #08101E 75%, #080A14 100%)'
            : 'linear-gradient(175deg, #C8D4F8 0%, #A8B8F0 25%, #7A96E8 50%, #4A6AD8 75%, #1A3FBF 100%)',
        }}></div>

        {/* Simulated portrait silhouette */}
        <svg style={{ position:'absolute', bottom:0, left:'50%', transform:'translateX(-50%)' }} width="300" height="420" viewBox="0 0 300 420" fill="none">
          <ellipse cx="150" cy="90" rx="54" ry="62" fill={t === DK ? 'rgba(180,200,255,0.10)' : 'rgba(26,63,191,0.20)'}/>
          <path d="M52 420 Q52 260 150 260 Q248 260 248 420Z" fill={t === DK ? 'rgba(180,200,255,0.08)' : 'rgba(26,63,191,0.15)'}/>
        </svg>

        {/* Image content label */}
        <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', zIndex:5 }}>
          <div style={{ background:'rgba(0,0,0,0.35)', borderRadius:12, padding:'10px 18px', backdropFilter:'blur(4px)' }}>
            <span style={{ fontSize:13, color:'rgba(255,255,255,0.70)', fontFamily:t.fb }}>AI-generated image placeholder</span>
          </div>
        </div>

        {/* Brand pill — top left */}
        <div style={{ position:'absolute', top:14, left:16, zIndex:10 }}>
          <div style={{ background:'rgba(26,63,191,0.85)', borderRadius:999, padding:'5px 12px', backdropFilter:'blur(6px)' }}>
            <span style={{ fontSize:11, fontWeight:700, color:'#fff', fontFamily:t.fb }}>Your future self</span>
          </div>
        </div>

        {/* Save to camera roll — top right */}
        <div style={{ position:'absolute', top:14, right:16, zIndex:10 }}>
          <div style={{ width:36, height:36, borderRadius:'50%', background:'rgba(0,0,0,0.45)', border:'1px solid rgba(255,255,255,0.18)', display:'flex', alignItems:'center', justifyContent:'center', backdropFilter:'blur(6px)' }}>
            <svg width="16" height="16" fill="none" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          </div>
        </div>

        {/* Bottom gradient scrim */}
        <div style={{ position:'absolute', bottom:0, left:0, right:0, height:120, background:`linear-gradient(to top, ${t.bg}, transparent)`, zIndex:8 }}></div>
      </div>

      {/* Below image — warm encouraging copy + CTA */}
      <div style={{ flex:1, padding:'0 22px', display:'flex', flexDirection:'column', justifyContent:'center', gap:0 }}>

        {/* Goal chip */}
        <div style={{ display:'inline-flex', alignItems:'center', gap:6, background:t.brandSub, borderRadius:999, padding:'5px 12px', width:'fit-content', marginBottom:14 }}>
          <div style={{ width:6, height:6, borderRadius:'50%', background:t.brand, flexShrink:0 }}></div>
          <span style={{ fontSize:12, fontWeight:700, color:t.brandLt, fontFamily:t.fb }}>Goal: Build muscle</span>
        </div>

        <div style={{ fontFamily:t.fd, fontSize:22, fontWeight:900, color:t.textPri, letterSpacing:-0.3, lineHeight:1.2, marginBottom:8 }}>
          This is where your training takes you.
        </div>
        <div style={{ fontSize:14, color:t.textSec, fontFamily:t.fb, lineHeight:1.6, marginBottom:22 }}>
          Every workout you log is a step toward this. Come back and see how far you've come.
        </div>

        <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
          <PBtn t={t} label="Let's go" style={{ height:50 }} />
          <div style={{ textAlign:'center' }}>
            <span style={{ fontSize:13, color:t.textTer, fontFamily:t.fb }}>You can view this anytime from your profile</span>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  GoalSelectionScreen,
  BiometricConsentScreen,
  PhotoCaptureScreen,
  FutureSelfRevealScreen,
});
