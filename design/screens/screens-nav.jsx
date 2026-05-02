// screens-nav.jsx — PRLifts Core Navigation Screens
// HistoryScreen · ExerciseLibraryScreen · ProfileScreen
// Each accepts a `t` prop (DK or LT tokens).

// ─────────────────────────────────────────────────────────────────
// HistoryScreen
// ─────────────────────────────────────────────────────────────────
function HistoryScreen({ t, empty }) {
  const workouts = [
    { id:1, name:'Upper Body',  date:'Today, Apr 28',    dur:'52 min', exCount:5, prs:2  },
    { id:2, name:'Leg Day',     date:'Apr 25',           dur:'48 min', exCount:4, prs:1  },
    { id:3, name:'Push Day',    date:'Apr 23',           dur:'61 min', exCount:6, prs:0  },
    { id:4, name:'Pull Day',    date:'Apr 21',           dur:'45 min', exCount:5, prs:3  },
    { id:5, name:'Full Body',   date:'Apr 18',           dur:'70 min', exCount:7, prs:0  },
    { id:6, name:'Cardio',      date:'Apr 16',           dur:'35 min', exCount:3, prs:1  },
  ];

  // Empty state barbell SVG illustration
  const BarbellIllustration = () => (
    <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
      <rect x="8"  y="29" width="8"  height="14" rx="4"   fill={t.bgTer}/>
      <rect x="56" y="29" width="8"  height="14" rx="4"   fill={t.bgTer}/>
      <rect x="4"  y="31" width="10" height="10" rx="5"   fill={t.bgQuad}/>
      <rect x="58" y="31" width="10" height="10" rx="5"   fill={t.bgQuad}/>
      <rect x="16" y="33" width="40" height="6"  rx="3"   fill={t.bgTer}/>
      <rect x="14" y="27" width="8"  height="18" rx="4"   fill={t.textTer} opacity="0.5"/>
      <rect x="50" y="27" width="8"  height="18" rx="4"   fill={t.textTer} opacity="0.5"/>
    </svg>
  );

  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
      <NavBar t={t} title="History"
        right={
          <div style={{ width:32, height:32, borderRadius:9, background:t.bgTer, display:'flex', alignItems:'center', justifyContent:'center' }}>
            <svg width="16" height="16" fill="none" stroke={t.textSec} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="14" y2="12"/><line x1="4" y1="18" x2="18" y2="18"/></svg>
          </div>
        }
      />

      {empty ? (
        /* ── Empty state ── */
        <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 40px', gap:14, textAlign:'center' }}>
          <BarbellIllustration />
          <div style={{ fontFamily:t.fd, fontSize:20, fontWeight:800, color:t.textSec, letterSpacing:-0.2 }}>No workouts yet</div>
          <div style={{ fontSize:14, color:t.textTer, fontFamily:t.fb, lineHeight:1.5 }}>Your logged workouts will appear here after your first session.</div>
          <div style={{ marginTop:8, width:'100%' }}>
            <PBtn t={t} label="Log your first workout" style={{ height:48, fontSize:15 }} />
          </div>
        </div>
      ) : (
        /* ── Populated state ── */
        <div style={{ flex:1, overflowY:'auto', padding:'10px 16px 16px', display:'flex', flexDirection:'column', gap:8 }}>
          {workouts.map(w => (
            <div key={w.id} style={{ background:t.bgSec, borderRadius:16, padding:'14px 16px', border:`1px solid ${t.border}`, display:'flex', alignItems:'center', gap:12, cursor:'pointer' }}>
              {/* Icon */}
              <div style={{ width:42, height:42, borderRadius:12, background:t.bgTer, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                <svg width="19" height="19" fill="none" stroke={t.textSec} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M6.5 6.5h11M6.5 12h11M6.5 17.5h7"/><circle cx="3" cy="6.5" r="1.2"/><circle cx="3" cy="12" r="1.2"/><circle cx="3" cy="17.5" r="1.2"/></svg>
              </div>

              {/* Content */}
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ display:'flex', alignItems:'center', gap:7, marginBottom:4, flexWrap:'wrap' }}>
                  <span style={{ fontFamily:t.fd, fontSize:16, fontWeight:700, color:t.textPri }}>{w.name}</span>
                  {w.prs > 0 && (
                    <span style={{ display:'inline-flex', alignItems:'center', gap:3, background:`linear-gradient(135deg,${t.celStart},${t.celEnd})`, color:'#0A0A0F', borderRadius:999, padding:'2px 8px', fontSize:11, fontWeight:700 }}>
                      🏆 {w.prs} PR{w.prs > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                <div style={{ display:'flex', gap:12, alignItems:'center' }}>
                  <span style={{ fontSize:12, color:t.textSec, fontFamily:t.fb }}>{w.date}</span>
                  <div style={{ width:3, height:3, borderRadius:'50%', background:t.textTer, flexShrink:0 }}></div>
                  <span style={{ fontSize:12, color:t.textSec, fontFamily:t.fb }}>{w.dur}</span>
                  <div style={{ width:3, height:3, borderRadius:'50%', background:t.textTer, flexShrink:0 }}></div>
                  <span style={{ fontSize:12, color:t.textSec, fontFamily:t.fb }}>{w.exCount} exercises</span>
                </div>
              </div>

              {/* Chevron */}
              <svg width="16" height="16" fill="none" stroke={t.textTer} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>
            </div>
          ))}
        </div>
      )}

      <TabBar t={t} active="history" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// ExerciseLibraryScreen
// ─────────────────────────────────────────────────────────────────
function ExerciseLibraryScreen({ t }) {
  const [activeFilter] = React.useState('All');
  const filters = ['All','Chest','Back','Legs','Shoulders','Arms','Core'];

  const exercises = [
    { name:'Bench Press',          muscle:'Chest',     equip:'Barbell',    pr:'225 lbs' },
    { name:'Incline Dumbbell Press',muscle:'Chest',     equip:'Dumbbell',   pr:null },
    { name:'Squat',                muscle:'Legs',      equip:'Barbell',    pr:'315 lbs' },
    { name:'Romanian Deadlift',    muscle:'Legs',      equip:'Barbell',    pr:null },
    { name:'Deadlift',             muscle:'Back',      equip:'Barbell',    pr:'405 lbs' },
    { name:'Pull-up',              muscle:'Back',      equip:'Bodyweight', pr:'15 reps' },
    { name:'Overhead Press',       muscle:'Shoulders', equip:'Barbell',    pr:'145 lbs' },
    { name:'Lateral Raise',        muscle:'Shoulders', equip:'Dumbbell',   pr:null },
    { name:'Bicep Curl',           muscle:'Arms',      equip:'Dumbbell',   pr:null },
    { name:'Tricep Pushdown',      muscle:'Arms',      equip:'Cable',      pr:null },
    { name:'Plank',                muscle:'Core',      equip:'Bodyweight', pr:null },
  ];

  const muscleColor = { Chest:'#FF6B6B', Back:'#4ECDC4', Legs:'#45B7D1', Shoulders:'#A78BFA', Arms:'#FB923C', Core:'#34D399' };

  const equipIcon = (eq) => {
    if (eq === 'Barbell') return <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M6.5 6.5h11M6.5 12h11"/><circle cx="3" cy="6.5" r="1.2"/><circle cx="3" cy="12" r="1.2"/></svg>;
    if (eq === 'Dumbbell') return <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><rect x="2" y="9" width="5" height="6" rx="2"/><rect x="17" y="9" width="5" height="6" rx="2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>;
    if (eq === 'Cable') return <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 3v6m0 6v6"/></svg>;
    return <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>;
  };

  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
      <NavBar t={t} title="Exercises" />

      {/* Search bar */}
      <div style={{ padding:'8px 16px 4px', flexShrink:0 }}>
        <div style={{ background:t.bgTer, borderRadius:12, height:40, display:'flex', alignItems:'center', gap:8, padding:'0 12px', border:`1px solid ${t.border}` }}>
          <svg width="15" height="15" fill="none" stroke={t.textTer} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <span style={{ fontSize:15, color:t.textTer, fontFamily:t.fb }}>Search exercises…</span>
        </div>
      </div>

      {/* Filter chips */}
      <div style={{ display:'flex', gap:6, padding:'8px 16px', overflowX:'auto', scrollbarWidth:'none', flexShrink:0 }}>
        {filters.map(f => {
          const on = f === activeFilter;
          return (
            <div key={f} style={{ padding:'5px 13px', borderRadius:999, fontSize:13, fontWeight:500, fontFamily:t.fb, background: on ? t.brand : t.bgSec, color: on ? '#fff' : t.textSec, border:`1px solid ${on ? t.brand : t.border}`, flexShrink:0, cursor:'pointer' }}>{f}</div>
          );
        })}
      </div>

      {/* Divider */}
      <div style={{ height:1, background:t.border, margin:'0 16px', flexShrink:0 }}></div>

      {/* Exercise list */}
      <div style={{ flex:1, overflowY:'auto' }}>
        {exercises.map((ex, i) => {
          const mc = muscleColor[ex.muscle] || t.brand;
          return (
            <div key={i}>
              <div style={{ padding:'11px 16px', display:'flex', alignItems:'center', gap:12, cursor:'pointer' }}>
                {/* Muscle dot icon */}
                <div style={{ width:40, height:40, borderRadius:11, background:`${mc}18`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                  <div style={{ width:10, height:10, borderRadius:'50%', background:mc }}></div>
                </div>

                {/* Name + meta */}
                <div style={{ flex:1, minWidth:0 }}>
                  <div style={{ fontSize:15, fontWeight:600, color:t.textPri, fontFamily:t.fb, marginBottom:3 }}>{ex.name}</div>
                  <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                    <span style={{ fontSize:12, color:mc, fontWeight:600, fontFamily:t.fb }}>{ex.muscle}</span>
                    <div style={{ width:3, height:3, borderRadius:'50%', background:t.textTer }}></div>
                    <span style={{ fontSize:12, color:t.textSec, fontFamily:t.fb, display:'flex', alignItems:'center', gap:3 }}>
                      <span style={{ color:t.textTer }}>{equipIcon(ex.equip)}</span>
                      {ex.equip}
                    </span>
                  </div>
                </div>

                {/* PR badge if exists */}
                {ex.pr && (
                  <div style={{ textAlign:'right', flexShrink:0 }}>
                    <div style={{ fontSize:10, color:t.textTer, marginBottom:1 }}>PR</div>
                    <div style={{ fontFamily:t.fm, fontSize:13, fontWeight:600, color:t.accent }}>{ex.pr}</div>
                  </div>
                )}

                <svg width="14" height="14" fill="none" stroke={t.textTer} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>
              </div>
              {i < exercises.length - 1 && <div style={{ height:1, background:t.border, margin:'0 16px' }}></div>}
            </div>
          );
        })}
        <div style={{ height:16 }}></div>
      </div>

      <TabBar t={t} active="exercises" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// ProfileScreen
// ─────────────────────────────────────────────────────────────────
function ProfileScreen({ t }) {
  const Row = ({ icon, label, value, chevron, destructive, onPress }) => (
    <div style={{ display:'flex', alignItems:'center', gap:12, padding:'13px 16px', cursor:'pointer' }}>
      {icon && (
        <div style={{ width:32, height:32, borderRadius:9, background: destructive ? `${t.error}18` : t.bgTer, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
          {icon}
        </div>
      )}
      <div style={{ flex:1 }}>
        <span style={{ fontSize:15, fontWeight:600, color: destructive ? t.error : t.textPri, fontFamily:t.fb }}>{label}</span>
      </div>
      {value && <span style={{ fontSize:14, color:t.textSec, fontFamily:t.fb }}>{value}</span>}
      {chevron && <svg width="14" height="14" fill="none" stroke={t.textTer} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>}
    </div>
  );

  const SectionHeader = ({ label }) => (
    <div style={{ padding:'16px 16px 6px', fontSize:11, fontWeight:700, color:t.textTer, fontFamily:t.fb, textTransform:'uppercase', letterSpacing:0.7 }}>{label}</div>
  );

  const Divider = () => <div style={{ height:1, background:t.border, margin:'0 16px' }}></div>;

  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
      <NavBar t={t} title="Profile" />

      <div style={{ flex:1, overflowY:'auto' }}>
        {/* Avatar + name hero */}
        <div style={{ display:'flex', flexDirection:'column', alignItems:'center', padding:'24px 20px 20px', gap:12 }}>
          {/* Avatar placeholder */}
          <div style={{ position:'relative' }}>
            <div style={{ width:72, height:72, borderRadius:'50%', background:`linear-gradient(135deg,${t.brand}40,${t.brand}20)`, border:`2px solid ${t.brand}50`, display:'flex', alignItems:'center', justifyContent:'center' }}>
              <svg width="32" height="32" fill="none" stroke={t.brandLt} strokeWidth="1.8" strokeLinecap="round" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <div style={{ position:'absolute', bottom:0, right:0, width:22, height:22, borderRadius:'50%', background:t.brand, display:'flex', alignItems:'center', justifyContent:'center', border:`2px solid ${t.bg}` }}>
              <svg width="10" height="10" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </div>
          </div>
          <div>
            <div style={{ fontFamily:t.fd, fontSize:20, fontWeight:900, color:t.textPri, textAlign:'center', marginBottom:2 }}>Alex Johnson</div>
            <div style={{ fontSize:13, color:t.textSec, fontFamily:t.fb, textAlign:'center' }}>Member since April 2026</div>
          </div>

          {/* Stats row */}
          <div style={{ display:'flex', gap:0, background:t.bgSec, borderRadius:14, border:`1px solid ${t.border}`, width:'100%', overflow:'hidden', marginTop:4 }}>
            {[['42','Workouts'],['18','PRs'],['7','Streak']].map(([v,l],i) => (
              <div key={l} style={{ flex:1, textAlign:'center', padding:'12px 8px', borderRight: i<2 ? `1px solid ${t.border}` : 'none' }}>
                <div style={{ fontFamily:t.fm, fontSize:22, fontWeight:700, color:t.textPri, fontVariantNumeric:'tabular-nums' }}>{v}</div>
                <div style={{ fontSize:11, color:t.textSec, marginTop:2, fontFamily:t.fb }}>{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Preferences */}
        <SectionHeader label="Preferences" />
        <div style={{ background:t.bgSec, borderRadius:14, margin:'0 16px', border:`1px solid ${t.border}`, overflow:'hidden' }}>
          <Row
            icon={<svg width="15" height="15" fill="none" stroke={t.textSec} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>}
            label="Display name" value="Alex Johnson" chevron
          />
          <Divider />
          <Row
            icon={<svg width="15" height="15" fill="none" stroke={t.textSec} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="7 8 3 12 7 16"/><polyline points="17 8 21 12 17 16"/></svg>}
            label="Units" value="lbs / in" chevron
          />
          <Divider />
          <Row
            icon={<svg width="15" height="15" fill="none" stroke={t.textSec} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>}
            label="Notifications" chevron
          />
        </div>

        {/* Account */}
        <SectionHeader label="Account" />
        <div style={{ background:t.bgSec, borderRadius:14, margin:'0 16px', border:`1px solid ${t.border}`, overflow:'hidden' }}>
          <Row
            icon={<svg width="15" height="15" fill="none" stroke={t.textSec} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>}
            label="Privacy settings" chevron
          />
          <Divider />
          <Row
            icon={<svg width="15" height="15" fill="none" stroke={t.textSec} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>}
            label="Sign out" chevron
          />
        </div>

        {/* Danger zone */}
        <SectionHeader label="Danger zone" />
        <div style={{ background:t.bgSec, borderRadius:14, margin:'0 16px', border:`1px solid ${t.error}30`, overflow:'hidden' }}>
          <Row
            icon={<svg width="15" height="15" fill="none" stroke={t.error} strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>}
            label="Delete account" destructive chevron
          />
        </div>

        {/* Version */}
        <div style={{ textAlign:'center', padding:'20px 0 8px' }}>
          <span style={{ fontSize:12, color:t.textTer, fontFamily:t.fm }}>PRLifts 1.0.0 (build 42)</span>
        </div>
      </div>

      <TabBar t={t} active="profile" />
    </div>
  );
}

Object.assign(window, { HistoryScreen, ExerciseLibraryScreen, ProfileScreen });
