import { useEffect,useState } from 'react';
import { Moon,Sun } from 'lucide-react';
import { applyTheme,savedTheme } from './themes';
export function ThemePicker(){
  const [theme,setTheme]=useState(savedTheme);
  useEffect(()=>{applyTheme(theme);try{localStorage.setItem('callatlas-theme',theme);}catch{/* Preference storage may be disabled. */}},[theme]);
  return <div className="appearance-switch" role="group" aria-label="Appearance"><button type="button" aria-label="Light theme" title="Light theme" aria-pressed={theme==='corporate-navy'} onClick={()=>setTheme('corporate-navy')}><Sun size={17}/></button><button type="button" aria-label="Dark theme" title="Dark theme" aria-pressed={theme==='soft-charcoal'} onClick={()=>setTheme('soft-charcoal')}><Moon size={17}/></button></div>;
}
